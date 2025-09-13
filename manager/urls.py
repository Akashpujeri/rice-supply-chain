from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/manager/',views.manager_dashboard, name='manager_dashboard'),
    path('manager_profile/',views.manager_profile, name='manager_profile'),
    path('update_manager_profile/',views.update_manager_profile, name='update_manager_profile'),
    path('update_manager_profile/<int:id>/',views.update_manager_profile_by_admin, name='update_manager_profile_by_admin'),
    
    
    path('show_my_rice_post/',views.show_my_rice_post, name='show_my_rice_post'),
    path('explore_all_rice_post/',views.explore_all_rice_post, name='explore_all_rice_post'),
    path('individual_rice_post_detail/<int:id>',views.individual_rice_post_detail, name='individual_rice_post_detail'),
    
    
    path('create_rice_post/<int:id>',views.create_rice_post, name='create_rice_post'),
    path('update_rice_post/<int:id>',views.update_rice_post, name='update_rice_post'),
    path('delete_rice_post/<int:id>',views.delete_rice_post, name='delete_rice_post'),
    
    path('explore_paddy_post/', views.explore_paddy_post, name='explore_paddy_post'),    
    

    path('purchase_paddy/<int:id>/', views.purchase_paddy, name='purchase_paddy'),
    path('purchase_rice/<int:id>/', views.purchase_rice, name='purchase_rice'),
    path('purchase_history/', views.purchase_history, name='purchase_history'),
    path('purchase_history_seen_admin/<int:id>', views.purchase_history_seen_admin, name='purchase_history_seen_admin'),
    
    # path('Mock_Payment_UI/', views.Mock_Payment_UI, name='Mock_Payment_UI'),
    


    path('mock_paddy_payment/<int:purchase_id>/', views.mock_paddy_payment, name='mock_paddy_payment'),    
    path('mock_paddy_payment_success/', views.mock_paddy_payment_success, name='mock_paddy_payment_success'),
    path('mock_paddy_payment_fail/', views.mock_paddy_payment_fail, name='mock_paddy_payment_fail'),

    
    path('insert-phone-number/<int:purchase_id>/', views.insert_phone_number, name='insert_phone_number'),
    path('insert-otp/<int:purchase_id>/<str:email>/', views.insert_otp, name='insert_otp'),
    path('insert-password/<int:purchase_id>/<str:email>', views.insert_password, name='insert_password'),
    
    path("verify_purchases_otp/<str:email>/<int:purchase_id>/<int:otp>/",views.verify_purchases_otp,name="verify_purchases_otp"),
    path("send_purchases_otp/<str:email>/<int:purchase_id>/",views.send_purchases_otp,name="send_purchases_otp"),
    
    path('mock_rice_payment/<int:rice_id>/', views.mock_rice_payment, name='mock_rice_payment'),
    path('mock_rice_payment_success/', views.mock_rice_payment_success, name='mock_rice_payment_success'),
    path('mock_rice_payment_fail/', views.mock_rice_payment_fail, name='mock_rice_payment_fail'),
    path('insert_phone_number_for_rice/<int:purchase_id>', views.insert_phone_number_for_rice, name='insert_phone_number_for_rice'),
    path('insert-otp-for-rice/<int:purchase_id>/<str:email>/', views.insert_otp_for_rice, name='insert_otp_for_rice'),
    path('insert-password-for-rice/<int:purchase_id>/<str:email>', views.insert_password_for_rice, name='insert_password_for_rice'),
    
    path("verify_purchases_otp_for_rice/<str:email>/<int:purchase_id>/<int:otp>/",views.verify_purchases_otp_for_rice,name="verify_purchases_otp_for_rice"),
    path("send_purchases_otp_for_rice/<str:email>/<int:purchase_id>/",views.send_purchases_otp_for_rice,name="send_purchases_otp_for_rice"),
    
    # Search url
    path('search/',views.search, name="search"),
    
    # Rice order review page for Manager
    path('incoming_order/', views.incoming_order, name='incoming_order'),
    path('my_rice_orders/', views.my_rice_order, name='my_rice_order'),
    path('accept_rice_order_from_customer/<int:id>/', views.accept_rice_order_from_customer, name='accept_rice_order_from_customer'),
    path('update_order_status_for_customer/<int:id>/', views.update_order_status_for_customer, name='update_order_status_for_customer'),
    path('confirm_rice_delivery_done_by_other_manager/<int:id>/', views.confirm_rice_delivery_done_by_other_manager, name='confirm_rice_delivery_done_by_other_manager'),
    
    path('accept_rice_order_from_manager/<int:id>/', views.accept_rice_order_from_manager, name='accept_rice_order_from_manager'),
    path('update_order_status_for_manager/<int:id>/', views.update_order_status_for_manager, name='update_order_status_for_manager'),
    
    # order and delivery track
    path('my_paddy_order/', views.my_paddy_order, name='my_paddy_order'),
    path('confirm_paddy_delivery/<int:id>/', views.confirm_paddy_delivery, name='confirm_paddy_delivery'),
    
    
    # Paddy quantity report
    path('paddy_stock_report/', views.paddy_stock_report, name='paddy_stock_report'),
    path("manager_stock_management/",views.manager_stock_management,name="manager_stock_management"),

    path("process_paddy_to_rice/<int:stock_id>/",views.process_paddy_to_rice,name="process_paddy_to_rice"),
    path("rice_stock_report/",views.rice_stock_report,name="rice_stock_report"),
    path("rice_stock_report/download/", views.download_rice_stock_report, name="download_rice_stock_report"),
    
    
    path("download_paddy_stock_report/",views.download_paddy_stock_report,name="download_paddy_stock_report"),
    path("download_receipt_for_buying_paddy_for_manager/<int:id>",views.download_receipt_for_buying_paddy_for_manager,name="download_receipt_for_buying_paddy_for_manager"),
    path("download_receipt_for_buying_rice_for_manager/<int:id>",views.download_receipt_for_buying_rice_for_manager,name="download_receipt_for_buying_rice_for_manager"),
    path("download_receipt_for_selling_rice_to_customer_for_manager/<int:id>",views.download_receipt_for_selling_rice_to_customer_for_manager,name="download_receipt_for_selling_rice_to_customer_for_manager"),
    path("download_receipt_for_selling_rice_to_others_manager_for_manager/<int:id>",views.download_receipt_for_selling_rice_to_others_manager_for_manager,name="download_receipt_for_selling_rice_to_others_manager_for_manager"),
    
    
    path("edit_rice_stock/<int:id>",views.edit_rice_stock,name="edit_rice_stock"),
    path("rice_stock_update/",views.rice_stock_update,name="rice_stock_update"),
    path("delete_rice_stock/<int:id>",views.delete_rice_stock,name="delete_rice_stock"),
    
    
    path("edit_paddy_stock/<int:id>",views.edit_paddy_stock,name="edit_paddy_stock"),
    path("paddy_stock_update/",views.paddy_stock_update,name="paddy_stock_update"),
    path("delete_paddy_stock/<int:id>",views.delete_paddy_stock,name="delete_paddy_stock"),
    
    path("profit_loss_report_for_rice_to_manager/",views.profit_loss_report_for_rice_to_manager,name="profit_loss_report_for_rice_to_manager"),
    path("profit_loss_report_for_rice_to_customer/",views.profit_loss_report_for_rice_to_customer,name="profit_loss_report_for_rice_to_customer"),
    
]