from datetime import date
from decimal import Decimal
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Sum
from django.core.validators import MinValueValidator
import random
import json
import qrcode

from io import BytesIO
from django.conf import settings
from django.core.files import File
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'مدير النظام'
    EMPLOYEE = 'employee', 'موظف'
    ACCOUNTANT = 'accountant', 'محاسب'


class CustomUser(AbstractUser):
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.EMPLOYEE, verbose_name='الدور')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_main_admin(self):
        return self.role == Role.SUPER_ADMIN

    def is_accountant(self):
        return self.role == Role.ACCOUNTANT

    def can_see_all_data(self):
        return self.role in [Role.SUPER_ADMIN,  Role.ACCOUNTANT]


    def is_employee(self):
        return self.role == Role.EMPLOYEE


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم الفئة')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فئة'
        verbose_name_plural = 'الفئات'
        ordering = ['name']

    def __str__(self):
        return self.name


class Dstatus(models.TextChoices):
    RENTED = 'rented' ,'مستأجر'
    AVAILABLE ='available' ,'متاح'
    INCLEAN = 'inclean','قيد التنظيف'
    INREPAIR ='inrepair','قيد الصيانة'
    SOLD='sold','تم بيعه'



class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم الفستان')

    barcode = models.CharField(max_length=100, blank=True, verbose_name='الباركود')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='الفئة', related_name='products'
    )
    
    cost_price = models.DecimalField(max_digits=12, decimal_places=2,default=0.0, verbose_name='سعر التكلفة')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='سعر الايجار')
    status = models.CharField(max_length=20,choices=Dstatus.choices, default=Dstatus.AVAILABLE, verbose_name='حالة الفستان')
    size= models.CharField(max_length=20,blank=True,null=True, verbose_name='مقاس الفستان')
    color = models.CharField(max_length=20,blank=True,null=True , verbose_name='لون  الفستان')
    image = models.ImageField(upload_to='products/',blank=True,null=True,verbose_name='الصورة الرئيسية',)
    image_2 = models.ImageField(upload_to='products/',blank=True,null=True,verbose_name='الصورة الثانية',)
    image_3 = models.ImageField(upload_to='products/',blank=True,null=True,verbose_name='الصورة الثالثة',)
    qr = models.ImageField(upload_to='qr/',blank=True,null=True)

    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فستان'
        verbose_name_plural = 'الفساتين'
        ordering = ['name']
    def generate_qr(self):
     base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

     product_url = f"{base_url}/products/qr/{self.barcode}/"

     qr_data = {
        "product_id": self.id,
        "barcode": self.barcode,
        "url": product_url
     }

     qr = qrcode.QRCode(
        version=1,
        box_size=10,
         border=4
     )

     qr.add_data(json.dumps(qr_data))
     qr.make(fit=True)

     img = qr.make_image(fill_color="black", back_color="white")

     buffer = BytesIO()
     img.save(buffer, format="PNG")
     buffer.seek(0)

     filename = f"product_qr_{self.id}.png"

     self.qr.save(filename, File(buffer), save=False)   
    @staticmethod
    def generate_barcode():
        while True:
            barcode = ''.join(str(random.randint(0, 9)) for _ in range(5))
            if not Product.objects.filter(barcode=barcode).exists():
                return barcode

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)
        if not self.qr:
         self.generate_qr()
         super().save(update_fields=['qr'])
    def __str__(self):
        return f"{self.name} ({self.barcode})"

    def is_available(self):
        return self.status == Dstatus.AVAILABLE

    def is_rented(self):
        return self.status == Dstatus.RENTED

    def is_inclean(self):
        return self.status == Dstatus.INCLEAN

    def is_inrepair(self):
        return self.status == Dstatus.INREPAIR

    def is_sold(self):
        return self.status == Dstatus.SOLD    





class PaymentMethod(models.Model):
  
    name = models.CharField(max_length=100, verbose_name='اسم طريقة الدفع')
    increase_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name='نسبة الزيادة %',
        help_text='النسبة المئوية التي تضاف على إجمالي الفاتورة'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_default = models.BooleanField(default=False, verbose_name='الطريقة الافتراضية')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'طريقة دفع'
        verbose_name_plural = 'طرق الدفع'
        ordering = ['-is_default', 'name']

    def __str__(self):
        increase_text = f" (+{self.increase_percentage}%)" if self.increase_percentage > 0 else ""
        return f"{self.name}{increase_text}"

    def save(self, *args, **kwargs):
        if self.is_default:
            PaymentMethod.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default_method(cls):
        default = cls.objects.filter(is_default=True, is_active=True).first()
        if not default:
            default = cls.objects.filter(is_active=True).first()
        return default        



class RepairAndClean(models.Model):
    KIND = {
        ('repair', 'تصليح'),
        ('clean', 'تنظيف')
    }
    STATUS = {
        ('inwork', 'قيد التنفيذ'),
        ('finished', 'تم الاستلام')
    }

    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE,
        verbose_name='الفستان',
        related_name='repairs'
    )
    status = models.CharField(max_length=20, choices=STATUS, verbose_name='حالة الصيانة')
    kind = models.CharField(max_length=20, choices=KIND, verbose_name='نوع الصيانة')
    start_date = models.DateField(verbose_name='تاريخ بداية الصيانة')  # حقل جديد
    finish_at = models.DateField(verbose_name='تاريخ انتهاء الصيانة')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='تكلفة الصيانة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'التنظيف والصيانة'
        verbose_name_plural = 'التنظيف والصيانة'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.get_kind_display()} - {self.created_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        if self.start_date and self.finish_at and self.start_date > self.finish_at:
            raise ValueError("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
        
        is_new = self.pk is None
        old_cost = 0
        
        if not is_new:
            old_instance = RepairAndClean.objects.get(pk=self.pk)
            old_cost = old_instance.total_cost
        
        super().save(*args, **kwargs)
        
        if self.product:
            if is_new:
                self.product.cost_price += self.total_cost
            else:
                self.product.cost_price -= old_cost
                self.product.cost_price += self.total_cost
            
            if self.kind == 'clean':
                self.product.status = Dstatus.INCLEAN 
            else:
                self.product.status = Dstatus.INREPAIR
            
            self.product.save()
    
    def mark_as_finished(self):
        self.status = 'finished'
        self.save()

class Customer(models.Model):
    full_name = models.CharField(max_length=20, verbose_name='الاسم الكامل')
    phone = models.CharField(max_length=20, unique=True, verbose_name='رقم الهاتف')

    debt_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='رصيد الدين'
    )

    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'عميل'
        verbose_name_plural = 'العملاء'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


    @property
    def total_debt(self):
        return self.debt_balance
    



class CustomerPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ المسدد')
    payment_date = models.DateTimeField(default=timezone.now, verbose_name='تاريخ التسديد')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name='رقم الإيصال')
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, verbose_name='تم بواسطة')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تسديد دين عميل'
        verbose_name_plural = 'تسديدات ديون العملاء'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.amount} - {self.payment_date}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()
        super().save(*args, **kwargs)
    
    def _generate_receipt_number(self):
        date_str = timezone.now().strftime('%Y%m%d')
        count = CustomerPayment.objects.filter(
            payment_date__date=timezone.now().date()
        ).count() + 1
        return f"{date_str}{count:04d}"



class InvoiceType(models.TextChoices):
    RENT = 'rent', 'إيجار'
    SALE = 'sale', 'بيع'

class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'مسودة'
    PENDING = 'pending', 'قيد الانتظار'
    PAID = 'paid', 'مدفوعة غير مستلمة'
    PARTIAL = 'partial', 'مدفوعة جزئياً'
    CANCELLED = 'cancelled', 'ملغاة'
    DELIVERED = 'delivered', 'تم التسليم للعميل'
    RECIEVED='recieved','مستلمة و مدفوعة'
    OVERDUE = 'overdue', 'متأخرة'


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True, verbose_name='رقم الفاتورة')
    invoice_type = models.CharField(max_length=10, choices=InvoiceType.choices, default=InvoiceType.RENT, verbose_name='نوع الفاتورة')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, verbose_name='العميل')
    
    rent_start_date = models.DateField(null=True, blank=True, verbose_name='تاريخ بداية الإيجار')
    rent_end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ نهاية الإيجار')
    
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='سعر البيع')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='الخصم')
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='العمولة')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المدفوع')
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المتبقي') 
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, null=True, blank=True, verbose_name='طريقة الدفع')
    identity_verified = models.BooleanField(default=True)
    identity_verified_return = models.BooleanField(default=False)   
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.PENDING, verbose_name='حالة الفاتورة') 
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

    @staticmethod
    def generate_invoice_number():
        today = timezone.now()
        year = today.strftime('%Y')
        month = today.strftime('%m')
        day = today.strftime('%d')
        last_invoice = Invoice.objects.filter(
            created_at__year=today.year,
            created_at__month=today.month,
            created_at__day=today.day
        ).order_by('-created_at').first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{year}-{month}-{day}-{new_number:03d}"

    @staticmethod
    def check_product_availability(product, start_date, end_date, exclude_invoice=None):

        if start_date > end_date:
            return False, "تاريخ البداية يجب أن يكون قبل تاريخ النهاية"
        
        if start_date < timezone.now().date():
            return False, "لا يمكن الإيجار في تاريخ ماضي"
        
        invoices = Invoice.objects.filter(
            invoice_type=InvoiceType.RENT,
            status__in=[InvoiceStatus.PENDING, InvoiceStatus.PAID, InvoiceStatus.PARTIAL,InvoiceStatus.DELIVERED],
            items__product=product,
            rent_start_date__lte=end_date,
            rent_end_date__gte=start_date
        ).distinct()
        
        if exclude_invoice:
            invoices = invoices.exclude(id=exclude_invoice.id)
        
        if invoices.exists():
            conflicting_dates = []
            for invoice in invoices:
                conflicting_dates.append(f"{invoice.rent_start_date} إلى {invoice.rent_end_date}")
            
            return False, f"المنتج غير متاح في هذه الفترة. فاتورة موجودة من {', '.join(conflicting_dates)}"
        
        return True, "المنتج متاح"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        
       
        
        super().save(*args, **kwargs)

    def mark_as_paid(self):
        self.paid_amount = self.total_amount
        self.remaining_amount = 0
        self.status = InvoiceStatus.PAID
        self.save()

    def mark_as_cancelled(self):
        for item in self.items.all():
            item.product.status = Dstatus.AVAILABLE
            item.product.save()
        
        self.status = InvoiceStatus.CANCELLED
        self.save()
        
        if self.customer and self.remaining_amount > 0:
            self.customer.debt_balance -= self.remaining_amount
            self.customer.save()

    def get_all_products(self):
        return [item.product for item in self.items.all()]

    def get_all_items(self):
        items = []
        for item in self.items.all():
            items.append({
                'product': item.product,
                'quantity': item.days or 1,
                'price': item.unit_price,
                'total': item.total_price
            })
        return items

    @property
    def is_overdue(self):
        if self.rent_end_date and self.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.RECIEVED]:
            return timezone.now().date() > self.rent_end_date
        return False

    @property
    def get_total_with_commission(self):
        return self.total_amount + self.commission

    @property
    def customer_display_name(self):
        if self.customer:
            return self.customer.full_name
        return 'عميل غير مسجل'
    
    @property
    def rental_days(self):
        if self.rent_start_date and self.rent_end_date:
            return (self.rent_end_date - self.rent_start_date).days + 1
        return 0




class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)  
    days = models.IntegerField(default=0, verbose_name='عدد الأيام') 
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='سعر الوحدة')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='الإجمالي')
    

        
    class Meta:
        verbose_name = 'بند فاتورة'
        verbose_name_plural = 'بنود الفاتورة'
    
    def save(self, *args, **kwargs):
        days = self.days if self.days > 0 else 1
        self.total_price = self.unit_price * days
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} × {self.days}"        




    def __str__(self):
        return f"{self.product.name} × {self.days}"

class Penalty(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='penalties')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'غرامة'
        verbose_name_plural = 'الغرامات'
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.reason}: {self.amount}"    


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم الفئة')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فئة مصروف'
        verbose_name_plural = 'فئات المصروفات'

    def __str__(self):
        return self.name

    @property
    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum('amount'))['total'] or 0


class Expense(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان المصروف')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='المبلغ')
    expense_date = models.DateField(verbose_name='التاريخ')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses', verbose_name='الفئة')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='سجّل بواسطة')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مصروف'
        verbose_name_plural = 'المصروفات'
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Employee(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('monthly', 'شهري'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('on_leave', 'في إجازة'),
    ]
    
    full_name = models.CharField(max_length=200, verbose_name='الاسم الكامل')
    position = models.CharField(max_length=200, verbose_name='الوظيفة')
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='الهاتف')
    
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, verbose_name='نظام الدفع')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='الحالة')
    
    monthly_salary = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='الراتب الشهري')
    expected_work_days = models.IntegerField(default=26, verbose_name='أيام العمل المتوقعة شهرياً')
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'موظف'
        verbose_name_plural = 'الموظفون'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.position}"
    
    def get_payment_type_display_ar(self):
        return dict(self.PAYMENT_TYPE_CHOICES).get(self.payment_type, self.payment_type)
    
    @property
    def total_absence_deductions(self):
        return AbsenceRecord.objects.filter(employee=self).aggregate(total=models.Sum('deduction_amount'))['total'] or 0
    
    @property
    def total_monthly_paid(self):
        return MonthlySalaryPayment.objects.filter(employee=self).aggregate(total=models.Sum('amount'))['total'] or 0
    
    @property
    def net_monthly_salary(self):
        return self.monthly_salary - self.total_absence_deductions
    
    @property
    def monthly_remaining(self):
        return self.net_monthly_salary - self.total_monthly_paid
    
 


class AbsenceRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='absences', verbose_name='الموظف')
    absence_date = models.DateField(verbose_name='تاريخ الغياب')
    deduction_amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='قيمة الخصم')
    reason = models.CharField(max_length=200, blank=True, null=True, verbose_name='سبب الغياب')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تسجيل غياب'
        verbose_name_plural = 'سجل الغيابات'
        ordering = ['-absence_date']
        unique_together = ['employee', 'absence_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.absence_date} - خصم {self.deduction_amount}"


class MonthlySalaryPayment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'نقداً'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='monthly_payments', verbose_name='الموظف')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='المبلغ المدفوع')
    payment_date = models.DateField(verbose_name='تاريخ الدفع')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash', verbose_name='طريقة الدفع')
    receipt_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الإيصال')
    notes = models.TextField(blank=True, null=True, verbose_name='ملاحظات')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='تم بواسطة')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'دفعة راتب شهري'
        verbose_name_plural = 'مدفوعات الرواتب الشهرية'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.amount} - {self.receipt_number}"
    

    def save(self, *args, **kwargs):
        from core.models import ExpenseCategory, Expense
      
        
        if not self.receipt_number:
            last_payment = MonthlySalaryPayment.objects.order_by('-id').first()
            if last_payment and last_payment.receipt_number:
                try:
                    last_num = int(last_payment.receipt_number)
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            date_str = date.today().strftime('%Y%m%d')
            self.receipt_number = f"{date_str}{new_num:04d}"
        
        
        
        category = ExpenseCategory.objects.first()
        
        if category:
            Expense.objects.create(
                title=f'صرف راتب شهري - {self.employee.full_name}',
                amount=self.amount,
                expense_date=self.payment_date,
                category=category,
                description=f'تسديد راتب للموظف {self.employee.full_name} - إيصال رقم {self.receipt_number}',
                created_by=self.created_by
            )
        super().save(*args, **kwargs)    
    def get_method_display_ar(self):
        return dict(self.METHOD_CHOICES).get(self.payment_method, self.payment_method)
