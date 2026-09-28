from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(MonthlySalaryPayment)
admin.site.register(Penalty)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_filter = ('invoice_type',)

@admin.register(Product)
class PrpductAdmin(admin.ModelAdmin):
    list_filter = ('status',)    