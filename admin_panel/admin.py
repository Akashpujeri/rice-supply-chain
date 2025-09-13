from django.contrib import admin
from .models import AdminProfile
# Register your models here.
class AdminProfileModel(admin.ModelAdmin):
        list_display = ['full_name','phone_number','license_number','address','bio']


admin.site.register(AdminProfile,AdminProfileModel)

