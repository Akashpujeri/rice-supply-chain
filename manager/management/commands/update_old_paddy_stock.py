from django.core.management.base import BaseCommand
from manager.models import Purchase_paddy, PaddyStockOfManager
from decimal import Decimal

class Command(BaseCommand):
    help = 'Update PaddyStockOfManager using old successful Purchase_paddy records'

    def handle(self, *args, **kwargs):
        successful_purchases = Purchase_paddy.objects.filter(status='Successful')

        count = 0
        for purchase in successful_purchases:
            manager = purchase.manager
            paddy = purchase.paddy  

            stock, created = PaddyStockOfManager.objects.get_or_create(
                manager=manager,
                paddy_name=paddy.name,
                moisture_content = paddy.moisture_content,
                # rice_type=paddy.rice_type,
                defaults={
                    'total_quantity': 0,
                    'total_price': 0,
                    'average_price_per_kg': 0,
                }
            )

            stock.total_quantity += purchase.quantity_purchased
            stock.total_price += purchase.total_price

            if stock.total_quantity > 0:
                stock.average_price_per_kg = round(Decimal(stock.total_price) / Decimal(stock.total_quantity), 2)

            stock.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully updated stock for {count} purchases.'))
        

# for manually update paddy stock
# python manage.py update_old_paddy_stock