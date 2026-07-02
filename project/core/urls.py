from django.urls import path 
from .views import *
urlpatterns = [

    path('',home, name='home'),

    path('accounts/login/', login_view, name='user_login'),
    path('logout/', logout_view, name='logout'),
    path('users/', users_list, name='users_list'),
    path('users/create/', user_create, name='user_create'),
    path('users/<int:pk>/edit/', user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', user_delete, name='user_delete'),
    path('products/qr/<str:barcode>/', product_by_barcode, name='product_by_barcode'),

    path('products/', product_list, name='products_list'),
    path('products/create/', product_create, name='products_create'),
    path('products/<int:pk>/', product_detail, name='products_detail'),
    path('products/<int:pk>/edit/', product_edit, name='products_edit'),
    path('products/<int:pk>/delete/', product_delete, name='products_delete'),
    path('categories/', category_list, name='categories'),
    path('categories/create/', category_create, name='category_create'),
    path('products/search/', product_search_ajax, name='search_ajax'),
    path('products/bulk-price-update/', products_bulk_price_update, name='products_bulk_price_update'),
    path('api/check-product-availability/', check_product_availability_api, name='check_product_availability'),

    path('payment-methods/', payment_methods_list, name='payment_methods_list'),
    path('payment-methods/create/', payment_method_create, name='payment_method_create'),
    path('payment-methods/<int:pk>/edit/', payment_method_edit, name='payment_method_edit'),
    path('payment-methods/<int:pk>/delete/', payment_method_delete, name='payment_method_delete'),
    path('payment-methods/<int:pk>/toggle-status/', payment_method_toggle_status, name='payment_method_toggle_status'),

    path('repairs/', repair_list, name='repair_list'),
    path('repairs/create/', repair_create, name='repair_create'),
    path('repairs/<int:pk>/', repair_detail, name='repair_detail'),
    path('repairs/<int:pk>/edit/', repair_edit, name='repair_edit'),
    path('repairs/<int:pk>/delete/', repair_delete, name='repair_delete'),
    path('repairs/<int:pk>/finish/', repair_finish, name='repair_finish'),

    path('customers/', customer_list, name='customers_list'),
    path('customers/create/', customer_create, name='customers_create'),
    path('customers/<int:pk>/', customer_detail, name='customers_detail'),
    path('customers/<int:pk>/edit/', customer_edit, name='customers_edit'),
    path('customers/search/', customer_search_ajax, name='customers_search_ajax'),    
    path('customers/<int:pk>/payment/', customer_payment_create, name='customer_payment_create'),
    path('customers/payment-receipt/<int:pk>/', customer_payment_receipt, name='customer_payment_receipt'),
    path('customers/<int:pk>/payments/', customer_payments_history, name='customer_payments_history'),

    path('invoices/',invoice_list, name='invoice_list'),
    path('invoices/create/',create_invoice, name='create_invoice'),
    path('invoice/confirm-return/<int:invoice_id>/',confirm_return, name='confirm_return'),
    path('invoice/add-penalty/',add_penalty, name='add_penalty'),
    path('invoices/cancel/<int:invoice_id>/',cancel_invoice, name='cancel_invoice'),
    path('invoices/print-receipt/<int:invoice_id>/',print_receipt, name='print_receipt'),

    path('dashboard/', statistics, name='statistics'),


    path('inventory-report/', inventory_report, name='inventory_report'),
    path('print-barcodes/', print_qr_preview, name='print_barcodes_preview'),
    path('unreturned-invoices/', unreturned_invoices, name='unreturned_invoices'),
    path('select-barcodes/',select_barcodes, name='print_barcodes'),

    path('reservations/', reservations_list, name='reservations_list'),
    path('invoice/deliver/<int:invoice_id>/', mark_as_delivered, name='mark_as_delivered'),


    path('expenses/',expense_list, name='expense_list'),
    path('expenses/add/',expense_add, name='expense_add'),
    path('expenses/<int:pk>/edit/',expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/',expense_delete, name='expense_delete'),
    path('expense-categories/',expense_category_list, name='expense_category_list'),
    path('expense-categories/add/',expense_category_add, name='expense_category_add'),

    path('hr/employees/', employee_list, name='employee_list'),
    path('hr/employees/create/', employee_create, name='employee_create'),
    path('hr/employees/<int:pk>/edit/', employee_edit, name='employee_edit'),
    path('hr/employees/<int:pk>/delete/', employee_delete, name='employee_delete'),
    
    path('hr/absences/', absence_list, name='absence_list'),
    path('hr/absences/create/', absence_create, name='absence_create'),
    path('hr/absences/<int:pk>/delete/', absence_delete, name='absence_delete'),
    
    path('hr/monthly/<int:employee_id>/payment/', monthly_salary_payment, name='monthly_salary_payment'),
    path('hr/monthly/<int:employee_id>/statement/', monthly_salary_statement, name='monthly_salary_statement'),
    

]



