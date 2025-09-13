from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/admin/',views.admin_dashboard, name='admin_dashboard'),
    path('admin_profile/',views.admin_profile, name='admin_profile'),
    path('update_admin_profile/',views.update_admin_profile, name='update_admin_profile'),

    path('forgot_password/', views.request_password_reset, name='forgot_password'),
    path('verify_otp/<str:email>/', views.verify_otp, name='verify_otp'),
    path('reset_password/<str:email>/', views.reset_password, name='reset_password'),
    
    path('change_password/', views.change_password, name='change_password'),
    path('password_change_complete/', views.password_change_complete, name='password_change_complete'),


    path('see_all_delears', views.see_all_delears, name='see_all_delears'),
    path('individuals_delear_details/<int:id>/', views.individuals_delear_details, name='individuals_delear_details'),

    path('see_all_manager', views.see_all_manager, name='see_all_manager'),
    path('individual_manager_details/<int:id>/', views.individual_manager_details, name='individual_manager_details'),
    

    path('see_all_customers', views.see_all_customers, name='see_all_customers'),
    path('individual_customer_details/<int:id>/', views.individual_customer_details, name='individual_customer_details'),


    path('delete_customer/<int:id>/', views.delete_customer, name='delete_customer'),
    path('delete_manager/<int:id>/', views.delete_manager, name='delete_manager'),
    path('delete_delear/<int:id>/', views.delete_delear, name='delete_delear'),
    
    
    path('customer_rice_purchases_history_seen_by_admin/<int:id>/', views.customer_rice_purchases_history_seen_by_admin, name='customer_rice_purchases_history_seen_by_admin'),
    path('dealer_purchases_history/<int:id>/', views.dealer_purchases_history, name='dealer_purchases_history'),
    
    
]
