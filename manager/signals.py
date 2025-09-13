from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Purchase_paddy, PaddyStockOfManager,PurchaseRice, RiceStock
from customer.models import Purchase_Rice


@receiver(post_save, sender=Purchase_paddy)
def update_paddy_stock_of_manager(sender, instance, created, **kwargs):
    if instance.status == "Successful":
        manager = instance.manager
        paddy = instance.paddy
        
        stock, created = PaddyStockOfManager.objects.get_or_create(
            manager=manager,
            paddy_name = paddy.name,
            moisture_content = paddy.moisture_content,
            defaults={
                'total_quantity' : 0,
                'total_price' : 0,
                'average_price_per_kg' : 0,
            }
        )
        
        stock.total_quantity += instance.quantity_purchased
        stock.total_price += instance.total_price
        
        if stock.total_quantity > 0:
            stock.average_price_per_kg = round(Decimal(stock.total_price)/Decimal(stock.total_quantity),2)
        
        stock.save()
        
        

@receiver(post_save, sender=PurchaseRice)
def add_purchased_rice_to_stock(sender, instance, created, **kwargs):
    if instance.status == 'Successful':
        if not hasattr(instance, '_already_processed'):
            manager = instance.manager
            rice_post = instance.rice

            rice_name = rice_post.rice_name
            quality = rice_post.quality

            stock, created = RiceStock.objects.get_or_create(
                manager=manager,
                rice_name=rice_name,
                quality=quality,
                defaults={
                    'stock_quantity': 0,
                    'total_price': 0,
                    'average_price_per_kg': 0,
                }
            )

            stock.stock_quantity += instance.quantity_purchased
            stock.total_price += instance.total_price

            if stock.stock_quantity > 0:
                stock.average_price_per_kg = round(
                    Decimal(stock.total_price) / Decimal(stock.stock_quantity), 2
                )
            stock.save()

            instance._already_processed = True


@receiver(post_save, sender=Purchase_Rice)
def profit_loss_report_for_rice_to_customer(sender, instance, created, **kwargs):
    # Avoid recursion by updating only when needed
    if instance.status == "Successful" and instance.profit_or_loss in [None, 0]:
        try:
            stock = RiceStock.objects.get(
                manager=instance.rice.manager,
                rice_name=instance.rice.rice_name
            )

            cost_price = Decimal(stock.average_price_per_kg or 0)
            quantity = Decimal(instance.quantity_purchased or 0)
            total_cost = cost_price * quantity
            total_sale = Decimal(instance.total_price or 0)
            profit = total_sale - total_cost

            # ✅ Only update if value has changed
            if instance.profit_or_loss != profit:
                Purchase_Rice.objects.filter(id=instance.id).update(profit_or_loss=profit)

        except RiceStock.DoesNotExist:
            Purchase_Rice.objects.filter(id=instance.id).update(profit_or_loss=0)
            
            
@receiver(post_save, sender=PurchaseRice)
def profit_loss_report_for_rice_to_manager(sender, instance, created, **kwargs):
    # Only recalculate if status is Successful and profit_or_loss not already set
    if instance.status == "Successful" and instance.profit_or_loss is None:
        try:
            stock = RiceStock.objects.get(
                manager=instance.rice.manager,
                rice_name=instance.rice.rice_name
            )
            cost_price = Decimal(str(stock.average_price_per_kg))
            total_cost = cost_price * Decimal(str(instance.quantity_purchased))
            profit = Decimal(str(instance.total_price)) - total_cost

            instance.profit_or_loss = float(profit)
            instance.save(update_fields=['profit_or_loss'])

        except RiceStock.DoesNotExist:
            instance.profit_or_loss = 0.0
            instance.save(update_fields=['profit_or_loss'])