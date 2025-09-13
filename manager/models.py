from django.db import models

from accounts.models import CustomUser
from dealer.models import Marketplace, PaddyStock

# Create your models here.

class ManagerProfile(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,limit_choices_to={'role':'manager'},related_name="managerprofile")
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=11)
    transaction_password = models.CharField(max_length=128)
    address = models.TextField()
    mill_name = models.CharField(max_length=100)
    mill_location = models.TextField()
    profile_image = models.ImageField(upload_to="manager_profile/",blank=True,null=True)
    experience_year = models.PositiveIntegerField(blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.mill_name})"
    
    
class RicePost(models.Model):
    manager = models.ForeignKey(CustomUser,on_delete=models.CASCADE, limit_choices_to={'role':'manager'},related_name="managerPost")
    rice_name = models.CharField(max_length=200, blank=True, null=True)
    quality = models.CharField(max_length=100)
    quantity_kg = models.FloatField()
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField()
    is_sold = models.BooleanField(default=False)
    rice_image = models.ImageField(upload_to="rice_image/",blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class Purchase_paddy(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Cancel', 'Cancel'),
        ('Shipping', 'Shipping'),
        ('Delivered', 'Delivered'),
        ('Successful', 'Successful'),
    ]
    manager = models.ForeignKey(CustomUser,on_delete=models.CASCADE,limit_choices_to={'role':'manager'})
    paddy = models.ForeignKey(Marketplace,on_delete=models.CASCADE,related_name="purchase_paddy")
    quantity_purchased = models.FloatField()
    moisture_content = models.DecimalField(max_digits=4, decimal_places=1, help_text="Moisture content (%)", null=True,blank=True)
    total_price = models.DecimalField(max_digits=10,decimal_places=2)
    transport_cost = models.DecimalField(max_digits=6,decimal_places=2,default=0)
    is_confirmed = models.BooleanField(default=False)
    payment = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # ✅ New field
    purchase_date = models.DateTimeField(auto_now_add=True)
        
    def __str__(self):
        return f"Purchases By {self.manager.full_name} from {self.paddy.dealer.username}"
        

class PurchaseRice(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Shipping', 'Shipping'),
        ('Delivered', 'Delivered'),
        ('Successful', 'Successful'),
        ('Cancelled', 'Cancelled'),
    ]

    manager = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rice = models.ForeignKey(RicePost, on_delete=models.CASCADE, related_name="PurchaseRice")
    quantity_purchased = models.FloatField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit_or_loss = models.FloatField(null=True, blank=True)
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_confirmed = models.BooleanField(default=False)
    payment = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # ✅ Add this line
    purchase_date = models.DateTimeField(auto_now_add=True)

class PaymentForPaddy(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    paddy = models.ForeignKey(Marketplace, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"
    
    
class PaymentForRice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rice = models.ForeignKey(RicePost, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"
        
class PaddyStockOfManager(models.Model):
    # one manager can be owner of multiple paddy stock
    manager = models.ForeignKey(
        CustomUser,on_delete=models.CASCADE,
        limit_choices_to={"role":"manager"},
        related_name="paddy_stock"
        )
    paddy_name = models.CharField(max_length=100)
    moisture_content = models.DecimalField(max_digits=4, decimal_places=1, help_text="Moisture content (%)",null=True,blank=True)

    rice_type = models.CharField(max_length=100,blank=True,null=True)
    
    total_quantity = models.FloatField(help_text="In kg")
    total_price = models.DecimalField(max_digits=10,decimal_places=2)
    average_price_per_kg = models.DecimalField(max_digits=6,decimal_places=2)
    description = models.TextField(blank=True,null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Manager's Paddy Stock"
        verbose_name_plural = "Manager's Paddy Stocks"

    def __str__(self):
        return f"{self.paddy_name} - {self.manager.managerprofile.full_name} ({self.total_quantity} kg)"
    
    
class RiceStock(models.Model):
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'manager'},
        related_name='rice_stock'
    )
    
    rice_name = models.CharField(max_length=100)
    quality = models.CharField(max_length=100, blank=True, null=True)
    rice_type = models.CharField(max_length=100, blank=True, null=True)
    
    stock_quantity = models.FloatField(help_text='In kg')
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total value of current stock"
    )
    average_price_per_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00
    )
    
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rice Stock"
        verbose_name_plural = "Rice Stocks"

    def __str__(self):
        return f"{self.rice_name} - {self.manager.managerprofile.full_name} ({self.stock_quantity} kg)"