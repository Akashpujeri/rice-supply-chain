from django.core.management.base import BaseCommand
from manager.models import PurchaseRice, RiceStock
from decimal import Decimal

class Command(BaseCommand):
    help = 'Calculate profit or loss for previously successful rice sales'

    def handle(self, *args, **kwargs):
        updated_count = 0
        failed_count = 0

        sales = PurchaseRice.objects.filter(status="Successful", profit_or_loss__isnull=True)

        if not sales.exists():
            self.stdout.write(self.style.WARNING("No eligible sales found to update."))
            return

        for sale in sales:
            try:
                stock = RiceStock.objects.get(manager=sale.rice.manager, rice_name=sale.rice.rice_name)
                cost_per_kg = Decimal(str(stock.average_price_per_kg))
                total_cost = cost_per_kg * Decimal(str(sale.quantity_purchased))
                profit = Decimal(str(sale.total_price)) - total_cost

                sale.profit_or_loss = float(profit)
                sale.save(update_fields=["profit_or_loss"])
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Sale ID {sale.id} updated. Profit/Loss: {profit:.2f}"))

            except RiceStock.DoesNotExist:
                sale.profit_or_loss = 0.0
                sale.save(update_fields=["profit_or_loss"])
                failed_count += 1
                self.stdout.write(self.style.WARNING(f"⚠️ Sale ID {sale.id}: Stock not found. Set to 0"))

        self.stdout.write(self.style.SUCCESS(f"\n✔ Done! {updated_count} updated, {failed_count} had missing stock info."))
        
        
# python manage.py calculate_profit_or_loss