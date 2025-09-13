from django.contrib import admin
from .models import CustomerProfile
# Register your models here.

class CusmerProfileModel(admin.ModelAdmin):
    list_display = ['full_name','phone_number','address','image','date_of_birth']
    
admin.site.register(CustomerProfile,CusmerProfileModel)
