from django.contrib import admin
from .models import ManagerProfile, RicePost, RiceStock,PaddyStockOfManager,PaymentForPaddy,PaymentForRice,PurchaseRice,Purchase_paddy
# Register your models here.
class ManagerModel(admin.ModelAdmin):
    list_display = ['full_name','phone_number','mill_name','mill_location','bio']
    
class RicePostModel(admin.ModelAdmin):
    list_display = ['manager','quality','quantity_kg','price_per_kg','description','is_sold']
    
admin.site.register(ManagerProfile,ManagerModel)
admin.site.register(RicePost,RicePostModel)
admin.site.register(RiceStock)
admin.site.register(PaddyStockOfManager)
admin.site.register(PaymentForPaddy)
admin.site.register(PaymentForRice)
admin.site.register(PurchaseRice)
admin.site.register(Purchase_paddy)