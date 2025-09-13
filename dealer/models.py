from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import CustomUser
from decimal import Decimal, ROUND_HALF_UP


MOISTURE_CATEGORIES = [
    ('Easy', 'Easy (≤13.5%)'),
    ('Medium', 'Medium (13.6%–15.5%)'),
    ('Hard', 'Hard (>15.5%)'),
]

class Location(models.Model):
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    taluk = models.CharField(max_length=100, blank=True, null=True)
    village_or_city = models.CharField(max_length=150, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.village_or_city}, {self.taluk}, {self.district}, {self.state} - {self.pincode}"


class DealerProfile(Location):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50)
    storage_capacity = models.PositiveIntegerField(help_text="Capacity in Kg")

    def __str__(self):
        return f"{self.user.username}"


class PaddyStock(models.Model):
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    moisture_category = models.CharField(max_length=10, choices=MOISTURE_CATEGORIES, default='Medium')
    quantity = models.PositiveIntegerField(default=0, help_text="Total stock in Kg")
    available_quantity = models.PositiveIntegerField(default=0, help_text="Available stock in Kg")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="₹ per Kg")
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="₹ per Kg")
    other_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="₹ per Kg")
    moisture_content = models.DecimalField(max_digits=4, decimal_places=1)
    image = models.ImageField(upload_to='paddy_images/', blank=True, null=True)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0, help_text="Final avg cost per Kg")
    is_available = models.BooleanField(default=True)
    stored_since = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    quality_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-last_updated']
        unique_together = ['dealer', 'name', 'moisture_category']

    def __str__(self):
        return f"{self.name} [{self.moisture_category}] - {self.available_quantity} Kg"


class PaddyPurchaseFromFarmer(models.Model):
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE)
    paddy_stock = models.ForeignKey(PaddyStock, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    farmer_name = models.CharField(max_length=100)
    farmer_phone = models.CharField(max_length=15, blank=True)
    paddy_type = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Quantity in Kg")
    purchase_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="₹ per Kg")
    moisture_content = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(5), MaxValueValidator(25)])
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total transport cost (₹)")
    other_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total other costs (₹)")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    reference_code = models.CharField(max_length=20, unique=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference_code:
            count = PaddyPurchaseFromFarmer.objects.count()
            self.reference_code = f"PUR-{timezone.now().year}-{count + 1:04d}"

        quantity = Decimal(str(self.quantity or 0))
        purchase_price = Decimal(str(self.purchase_price_per_kg or 0))
        transport_cost = Decimal(str(self.transport_cost or 0))
        other_costs = Decimal(str(self.other_costs or 0))

        # Cost fully in Kg
        self.total_cost = (quantity * purchase_price) + transport_cost + other_costs

        old = PaddyPurchaseFromFarmer.objects.get(pk=self.pk) if self.pk else None
        super().save(*args, **kwargs)
        self._sync_stock(old)

    def _get_moisture_category(self):
        if self.moisture_content <= 13.5:
            return "Easy"
        elif self.moisture_content <= 15.5:
            return "Medium"
        return "Hard"

    def _sync_stock(self, old=None):
        moisture_category = self._get_moisture_category()

        stock, created = PaddyStock.objects.get_or_create(
            dealer=self.dealer,
            name=self.paddy_type,
            moisture_category=moisture_category,
            defaults={
                "quantity": 0,
                "available_quantity": 0,
                "purchase_price": 0,
                "transport_cost": 0,
                "other_cost": 0,
                "moisture_content": self.moisture_content,
            },
        )

        purchases = PaddyPurchaseFromFarmer.objects.filter(
            dealer=self.dealer, paddy_type=self.paddy_type
        )

        total_kg = Decimal("0.00")
        total_purchase_price = Decimal("0.00")
        total_transport = Decimal("0.00")   
        total_other = Decimal("0.00")    

        for p in purchases:
            total_kg += Decimal(p.quantity)
            total_purchase_price += Decimal(p.quantity) * (p.purchase_price_per_kg or 0)
            total_transport += Decimal(p.transport_cost or 0)
            total_other += Decimal(p.other_costs or 0)

        if total_kg > 0:
            stock.quantity = int(total_kg)
            stock.available_quantity = stock.quantity
            stock.purchase_price = (total_purchase_price / total_kg).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            stock.transport_cost = total_transport.quantize(Decimal("0.01"))
            stock.other_cost = total_other.quantize(Decimal("0.01"))
            stock.price_per_kg = (
                (total_purchase_price + total_transport + total_other) / total_kg
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        stock.moisture_content = self.moisture_content
        stock.save()

        self.paddy_stock = stock
        super().save(update_fields=["paddy_stock"])

        def delete(self, *args, **kwargs):
            stock = self.paddy_stock
            super().delete(*args, **kwargs)

            if stock:
                self._recalculate_stock(stock)

        def _recalculate_stock(self, stock):
            purchases = PaddyPurchaseFromFarmer.objects.filter(
                dealer=stock.dealer, paddy_type=stock.name
            )

            total_kg = Decimal("0.00")
            total_purchase_price = Decimal("0.00")
            total_transport = Decimal("0.00")
            total_other = Decimal("0.00")

            for p in purchases:
                total_kg += Decimal(p.quantity)
                total_purchase_price += Decimal(p.quantity) * (p.purchase_price_per_kg or 0)
                total_transport += Decimal(p.transport_cost or 0)
                total_other += Decimal(p.other_costs or 0)

            if total_kg > 0:
                stock.quantity = int(total_kg)
                stock.available_quantity = stock.quantity
                stock.purchase_price = (total_purchase_price / total_kg).quantize(Decimal("0.01"))
                stock.transport_cost = total_transport.quantize(Decimal("0.01"))
                stock.other_cost = total_other.quantize(Decimal("0.01"))
                stock.price_per_kg = (
                    (total_purchase_price + total_transport + total_other) / total_kg
                ).quantize(Decimal("0.01"))
                stock.is_available = True
            else:
                # No purchases left → reset stock
                stock.quantity = 0
                stock.available_quantity = 0
                stock.purchase_price = 0
                stock.transport_cost = 0
                stock.other_cost = 0
                stock.price_per_kg = 0
                stock.is_available = False

            stock.save()


class Marketplace(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Sold', 'Sold'),
    ]

    paddy_stock = models.ForeignKey(PaddyStock, on_delete=models.CASCADE, related_name='marketplace_posts')
    dealer = models.ForeignKey(DealerProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="uploads/", default="default.jpg")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Quantity in Kg")
    moisture_content = models.DecimalField(max_digits=4, decimal_places=1)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="₹ per Kg")
    quality_notes = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Draft')
    stored_since = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.quantity} Kg @ ₹{self.price_per_kg}/Kg"

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.quantity > self.paddy_stock.available_quantity:
                raise ValueError("Cannot list more than available quantity in stock")
            self.paddy_stock.available_quantity -= self.quantity
            self.paddy_stock.save()

            self.name = self.name or self.paddy_stock.name
            self.image = self.image or self.paddy_stock.image
            self.moisture_content = self.moisture_content or self.paddy_stock.moisture_content
            self.price_per_kg = self.price_per_kg or self.paddy_stock.price_per_kg
            self.quality_notes = self.quality_notes or self.paddy_stock.quality_notes

        super().save(*args, **kwargs)
