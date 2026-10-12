from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(MonthlySalaryPayment)
admin.site.register(Penalty)
@admin.register(Customer)

@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    search_fields = [
        'receipt_number',
        'customer__full_name',
        'customer__phone',
    ]
    list_display = (
        'receipt_number',
        'customer',
        'amount',
        'payment_date',
        'invoice',
    )
    list_filter = ('payment_date',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_filter = ('invoice_type',)

@admin.register(Product)
class PrpductAdmin(admin.ModelAdmin):
    list_filter = ('status',)    