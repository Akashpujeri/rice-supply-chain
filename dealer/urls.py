from django.urls import path
from . import views
from . import urls

urlpatterns = [
    path('dashboard/', views.dealer_dashboard, name='dealer_dashboard'),
    path('dealer-profile/<int:user_id>/', views.dealer_profile_create, name='dealer_profile_create'),
    path('add-post/', views.add_paddy_post, name='add_paddy_post'),
    path('marketplace/all_post', views.see_all_paddy_posts, name='marketplace_paddy_posts'),
    path('paddy/<int:post_id>/', views.paddy_detail, name='paddy_detail'),
    
    path('paddy/edit/<int:post_id>/', views.edit_paddy_post, name='edit_paddy_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('profile/edit/',views.edit_dealer_profile, name='edit_dealer_profile'),
    path('orders/', views.dealer_order_list, name='dealer_order_list'),
    path('dealer-stats/', views.dealer_stats, name='dealer_stats'),
    
    # selling history
    path('selling_paddy_history/', views.selling_paddy_history, name='selling_paddy_history'),
    
    # paddy order review page for dealer
    path('incoming_order_for_paddy/', views.incoming_order_for_paddy, name='incoming_order_for_paddy'),
    path('accept_paddy_order/<int:id>/', views.accept_paddy_order, name='accept_paddy_order'),
    path('update_order_status_for_paddy/<int:id>/', views.update_order_status_for_paddy, name='update_order_status_for_paddy'),
    
    
    #latest update
    path('paddy-purchase/add/', views.create_purchase, name='paddy_purchase_add'),
    path('purchases/', views.all_purchases_list, name='all_purchases_list'),

    path('marketplace/create/<int:id>/', views.create_marketplace_post, name='create_marketplace_post'),

    path('purchase/<int:pk>/edit/', views.edit_purchase, name='edit_purchase'),
    path("purchase/<int:pk>/delete/", views.delete_purchase, name="delete_purchase"),



]