from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/customer/',views.customer_dashboard, name='customer_dashboard'),
    path("customer_profile/",views.customer_profile,name="customer_profile"),

    path("update_customer_profile/",views.update_customer_profile,name="update_customer_profile"),
    path("update_customer_profile_by_admin/<int:id>",views.update_customer_profile_by_admin,name="update_customer_profile_by_admin"),

    path("purchase_rice_from_manager/<int:id>/",views.purchase_rice_from_manager,name="purchase_rice_from_manager"),
    path("explore_rice_post/",views.explore_rice_post,name="explore_rice_post"),
    path('rice_purchases_history/', views.rice_purchases_history, name='rice_purchases_history'),

    path("mock_customer_rice_payment/<int:purchase_id>/", views.mock_customer_rice_payment, name="mock_customer_rice_payment"),
    path('insert-phone-number/<int:purchase_id>/', views.insert_phone_number_customer, name='insert_phone_number_customer'),
    path('insert-otp/<int:purchase_id>/<str:email>/', views.insert_otp_customer, name='insert_otp_customer'),
    path('insert-password/<int:purchase_id>/<str:email>', views.insert_password_customer, name='insert_password_customer'),
    
    path("verify_purchases_otp/<str:email>/<int:purchase_id>/<int:otp>/",views.verify_purchases_otp_customer,name="verify_purchases_otp_customer"),
    path("send_purchases_otp/<str:email>/<int:purchase_id>/",views.send_purchases_otp_customer,name="send_purchases_otp_customer"),
    
    path("mock_customer_rice_payment_success/", views.mock_customer_rice_payment_success, name="mock_customer_rice_payment_success"),
    path("mock_customer_rice_payment_fail/", views.mock_customer_rice_payment_fail, name="mock_customer_rice_payment_fail"),

    # Oder track
    path('my_rice_orders/', views.my_order_page, name='my_order_page'),
    path('confirm_delivery/<int:id>/', views.confirm_delivery, name='confirm_delivery'),
    
    
    
    path('download_receipt_for_buying_rice_for_customer/<int:id>/', views.download_receipt_for_buying_rice_for_customer, name='download_receipt_for_buying_rice_for_customer'),

]