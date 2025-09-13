from django.core.management.base import BaseCommand
from manager.models import PurchaseRice, RiceStock
from decimal import Decimal

class Command(BaseCommand):
    help = 'Update RiceStock using old successful PurchaseRice records'

    def handle(self, *args, **kwargs):
        successful_purchases = PurchaseRice.objects.filter(status='Successful')

        count = 0
        for purchase in successful_purchases:
            manager = purchase.manager
            rice_post = purchase.rice

            rice_name = rice_post.rice_name

            quality = rice_post.quality

            quantity = purchase.quantity_purchased
            total_price = purchase.total_price
            avg_price = float(total_price) / float(quantity)

            stock, created = RiceStock.objects.get_or_create(
                manager=manager,
                rice_name=rice_name,

                quality=quality,
                defaults={
                    'stock_quantity': quantity,
                    'total_price': total_price,
                    'average_price_per_kg': avg_price
                }
            )

            if not created:
                # update existing stock
                new_quantity = stock.stock_quantity + quantity
                new_total_price = stock.total_price + total_price
                new_avg_price = new_total_price / new_quantity

                stock.stock_quantity = new_quantity
                stock.total_price = new_total_price
                stock.average_price_per_kg = round(new_avg_price, 2)
                stock.save()

            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} rice stock entries.'))