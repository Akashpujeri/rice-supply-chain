from django.db import models
from accounts.models import CustomUser
from manager.models import RicePost
# Create your models here.
class CustomerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role':'customer'},related_name="customerprofile")
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=11)
    Transaction_password = models.CharField(max_length=11,null=True,blank=True)
    address =models.TextField()
    image = models.ImageField(upload_to="customer_profile/",blank=True,null=True)
    date_of_birth = models.DateField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)


class Purchase_Rice(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Cancel', 'Cancel'),
        ('Shipping', 'Shipping'),
        ('Delivered', 'Delivered'),
        ('Successful', 'Successful'),
    ]

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_rice_purchases')
    rice = models.ForeignKey(RicePost, on_delete=models.CASCADE, related_name='customer_rice_orders')
    quantity_purchased = models.FloatField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit_or_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_confirmed = models.BooleanField(default=False)
    payment = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # ✅ New field
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rice Purchase by {self.customer.username} - {self.rice.rice_name}"
    
    
    
class Payment_For_Rice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='customer_rice_payments')
    rice = models.ForeignKey(RicePost, on_delete=models.CASCADE, related_name='rice_customer_payments')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"