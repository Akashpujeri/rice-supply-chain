from django.db import models
from accounts.models import CustomUser
# Create your models here.

class AdminProfile(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE, limit_choices_to={"role":'admin'})
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=11)
    address = models.TextField()
    license_number = models.CharField(max_length=100, blank=True,null=True)
    profile_image = models.ImageField(upload_to="admin_profile/",blank=True,null=True)
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name}"

