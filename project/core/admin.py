from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(MonthlySalaryPayment)
@admin.register(Penalty)
class PanaltyAdmin(admin.ModelAdmin):
    list_filter = ('payment',)
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'phone',
        'debt_balance',
        'is_active',
    )


@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number',
        'customer',
        'amount',
        'payment_date',
        'invoice',
    )

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_filter = ('invoice_type',)

@admin.register(Product)
class PrpductAdmin(admin.ModelAdmin):
    list_filter = ('status',)    