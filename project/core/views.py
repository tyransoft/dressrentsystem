from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from .forms import *
from django.core.paginator import Paginator
from decimal import Decimal
from django.db.models import Q ,Sum, Count
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta,time
from django.utils import timezone
from django.urls import reverse



@login_required
def home(request):
    user = request.user
    if not request.user.is_authenticated:
        return redirect('user_login')
    else:  
      if user.is_accountant() or user.can_see_all_data():
        return redirect('statistics')
      else:
        return redirect('create_invoice')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('statistics')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user and user.is_active:
                login(request, user)
                if user.is_accountant() or user.can_see_all_data():
                  return redirect('statistics')
  
                return redirect('create_invoice')
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):

    logout(request)
    return redirect('user_login')


@login_required
def users_list(request):
    if not request.user.can_see_all_data():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('statistics')
    users = CustomUser.objects.all().order_by('username')
    return render(request, 'accounts/users_list.html', {'users': users})


@login_required
def user_create(request):
    if not request.user.can_see_all_data():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('statistics')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
    
            messages.success(request, f'تم إنشاء المستخدم {user.username} بنجاح')
            return redirect('users_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'إضافة مستخدم جديد'})


@login_required
def user_edit(request, pk):
    if not request.user.can_see_all_data():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('statistics')
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
          
            messages.success(request, 'تم تحديث بيانات المستخدم بنجاح')
            return redirect('users_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'تعديل المستخدم', 'user_obj': user})


@login_required
def user_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'غير مصرح لك بهذه العملية')
        return redirect('users_list')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if user == request.user:
        messages.error(request, 'لا يمكنك حذف حسابك الخاص')
        return redirect('users_list')
    
    user.delete()
    messages.success(request, f'تم حذف المستخدم {user.get_full_name() or user.username} بنجاح')
    return redirect('users_list')



@login_required
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    products = Product.objects.select_related('category').filter(is_active=True)
    if query:
        products = products.filter(Q(name__icontains=query)  | Q(barcode__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    categories = Category.objects.filter(is_active=True)
    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    })



@login_required
def product_create(request):

    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()        
            messages.success(request,"تم اضافة الفستان بنجاح")            
            return redirect('products_list')
    else:
        form = ProductForm()
    
    return render(request, 'products/form.html', {'form': form, 'title': 'إضافة منتج جديد'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not request.user.is_main_admin():
        messages.error(request, 'فقط الفرع الرئيسي يمكنه تعديل أسعار المنتجات')
        return redirect('products_list')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
        
            messages.success(request, 'تم تحديث بيانات المنتج بنجاح')
            return redirect('products_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/form.html', {'form': form, 'title': f'تعديل: {product.name}', 'product': product})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    history = []
    
    invoice_items = InvoiceItem.objects.filter(product=product)
    total_revenue = 0
    total_rentals = 0
    
    for item in invoice_items:
        if item.invoice.invoice_type == InvoiceType.RENT:
            total_rentals += 1
            total_revenue += item.total_price
            history.append({
                'type': 'rent',
                'type_display': 'إيجار',
                'details': f'فاتورة {item.invoice.invoice_number} - {item.days} أيام',
                'amount': item.total_price,
                'date': item.invoice.created_at.date()
            })
        elif item.invoice.invoice_type == InvoiceType.SALE:
            total_revenue += item.total_price
            history.append({
                'type': 'sale',
                'type_display': 'بيع',
                'details': f'فاتورة {item.invoice.invoice_number}',
                'amount': item.total_price,
                'date': item.invoice.created_at.date()
            })
    
    repairs = RepairAndClean.objects.filter(product=product)
    total_maintenance = repairs.count()
    
    for repair in repairs:
        history.append({
            'type': 'repair' if repair.kind == 'repair' else 'clean',
            'type_display': 'تصليح' if repair.kind == 'repair' else 'تنظيف',
            'details': f'{repair.notes or "بدون ملاحظات"}',
            'amount': repair.total_cost,
            'date': repair.created_at
        })
    
    history.sort(key=lambda x: x['date'], reverse=True)
    
    total_profit = total_revenue - product.cost_price
    
    context = {
        'product': product,
        'history': history,
        'total_rentals': total_rentals,
        'total_maintenance': total_maintenance,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
    }
    return render(request, 'products/detail.html', context)

@login_required
def product_delete(request, pk):
    if not request.user.is_main_admin():
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save()
    return JsonResponse({'success': True})


@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'products/categories.html', {'categories': categories})


@login_required
def category_create(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية لإضافة فئات')
        return redirect('categories')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الفئة بنجاح')
            return redirect('categories')
    else:
        form = CategoryForm()
    return render(request, 'products/category_form.html', {'form': form, 'title': 'إضافة فئة جديدة'})


@login_required
def product_search_ajax(request):
    query = request.GET.get('q', '')
    branch_id = request.GET.get('branch_id', '')
    products = Product.objects.filter(
        Q(name__icontains=query) |  Q(barcode__icontains=query),
        is_active=True
    )[:20]
    data = []
    for p in products:
        stock = 0
        if branch_id:
            stock = p.get_branch_stock(branch_id)
        data.append({
            'id': p.pk,
            'name': p.name,
            'sell_price':float(p.sell_price),
        })

    return JsonResponse({'products': data})

@login_required
def products_bulk_price_update(request):
    if not request.user.is_main_admin():
        messages.error(request, 'غير مصرح لك بتعديل أسعار المنتجات')
        return redirect('products_list')
    
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(Q(name__icontains=query) | Q(barcode__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    
    products = products.order_by('name')
    
    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(page)
    
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        selected_products_str = request.POST.get('selected_products', '')
        
        if selected_products_str:
            selected_products = [int(x) for x in selected_products_str.split(',') if x.strip().isdigit()]
        else:
            selected_products = []
        
        increase_type = request.POST.get('increase_type', 'fixed')
        increase_value = Decimal(request.POST.get('increase_value', 0))
        
        if not selected_products:
            messages.error(request, 'الرجاء اختيار منتج واحد على الأقل')
            return redirect('products_bulk_price_update')
        
        if increase_value <= 0:
            messages.error(request, 'الرجاء إدخال قيمة زيادة أكبر من صفر')
            return redirect('products_bulk_price_update')
        
        updated_count = 0
        for product_id in selected_products:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                old_price = product.selling_price
                
                if increase_type == 'fixed':
                    new_price = old_price + increase_value
                else:  
                    new_price = old_price + (old_price * increase_value / 100)
                
                product.selling_price = round(new_price, 2)
                product.save()
                updated_count += 1
                
            except Product.DoesNotExist:
                continue
        
        messages.success(request, f'تم تحديث {updated_count} منتج بنجاح')
        return redirect('products_bulk_price_update')
    
    context = {
        'products': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'total_count': products.count(),
    }
    return render(request, 'products/bulk_price_update.html', context)



def payment_methods_list(request):
    payment_methods = PaymentMethod.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        payment_methods = payment_methods.filter(name__icontains=search_query)
    
    sort_by = request.GET.get('sort', 'name')
    payment_methods = payment_methods.order_by(sort_by)
    
    paginator = Paginator(payment_methods, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'payment_methods/list.html', context)

def payment_method_create(request):
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save()
            messages.success(request, f'تم إضافة طريقة الدفع "{payment_method.name}" بنجاح')
            return redirect('payment_methods_list')
    else:
        form = PaymentMethodForm()
    
    context = {'form': form}
    return render(request, 'payment_methods/form.html', context)

def payment_method_edit(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=payment_method)
        if form.is_valid():
            payment_method = form.save()
            messages.success(request, f'تم تعديل طريقة الدفع "{payment_method.name}" بنجاح')
            return redirect('payment_methods_list')
    else:
        form = PaymentMethodForm(instance=payment_method)
    
    context = {'form': form, 'payment_method': payment_method}
    return render(request, 'payment_methods/form.html', context)

def payment_method_delete(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    
    if request.method == 'POST':
        method_name = payment_method.name
        payment_method.delete()
        messages.success(request, f'تم حذف طريقة الدفع "{method_name}" بنجاح')
        return redirect('payment_methods_list')
    
    context = {'payment_method': payment_method}
    return render(request, 'payment_methods/confirm_delete.html', context)

def payment_method_toggle_status(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    payment_method.is_active = not payment_method.is_active
    payment_method.save()
    
    status = 'مفعلة' if payment_method.is_active else 'غير مفعلة'
    messages.success(request, f'تم {status} طريقة الدفع "{payment_method.name}"')
    return redirect('payment_methods_list')


@login_required
def repair_list(request):
    repairs = RepairAndClean.objects.select_related('product').all()
    
    query = request.GET.get('q','')
    kind_filter = request.GET.get('kind')
    status_filter = request.GET.get('status')
    
    if query:
        repairs = repairs.filter(
            Q(product__name__icontains=query) |
            Q(product__barcode__icontains=query) |
            Q(notes__icontains=query)
        )
    
    if kind_filter:
        repairs = repairs.filter(kind=kind_filter)
    
    if status_filter:
        repairs = repairs.filter(status=status_filter)
    
    paginator = Paginator(repairs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'repairs': page_obj,
        'query': query,
        'kind_filter': kind_filter,
        'status_filter': status_filter,
        'kind_choices': RepairAndClean.KIND,
        'status_choices': RepairAndClean.STATUS,
        'title': 'قائمة الصيانة والتنظيف',
    }
    return render(request, 'repairs/repair_list.html', context)

@login_required
def reservations_list(request):
    today = timezone.now().date()
    
    reservations = Invoice.objects.filter(
        status=InvoiceStatus.PENDING,
        invoice_type=InvoiceType.RENT
    ).select_related('customer', 'payment_method').prefetch_related('items__product')

    if request.GET.get('start_date') == today:
        reservations = reservations.filter(rent_start_date=today)
    

    total_pending = Invoice.objects.filter(
        status=InvoiceStatus.PENDING,
        invoice_type=InvoiceType.RENT
    ).count()
    
    today_reservations = Invoice.objects.filter(
        status=InvoiceStatus.PENDING,
        invoice_type=InvoiceType.RENT,
        rent_start_date=today
    ).count()
    
    context = {
        'reservations': reservations,
        'total_pending': total_pending,
        'today_reservations': today_reservations,
        'today': today.strftime('%Y-%m-%d'),
        'is_today_filter': request.GET.get('today') == '1', 
    }
    return render(request, 'reservations_list.html', context)
@login_required
def reservation_detail(request, invoice_id):
    try:
        reservation = Invoice.objects.get(
            id=invoice_id,
            invoice_type=InvoiceType.RENT
        )
        

        
    except Invoice.DoesNotExist:
        messages.error(request, 'الحجز غير موجود')
        return redirect('reservations_list')
    
    rental_days = 0
    if reservation.rent_start_date and reservation.rent_end_date:
        rental_days = (reservation.rent_end_date - reservation.rent_start_date).days + 1
    
    items_data = []
    for item in reservation.items.all():  
        items_data.append({
            'item': item,
            'product': item.product,
            'days': item.days,
            'unit_price': item.unit_price,
            'total_price': item.total_price,
        })
    
    context = {
        'reservation': reservation,
        'items_data': items_data,
        'rental_days': rental_days,
        'total_items': reservation.items.count(),
    }
    return render(request, 'reservation_detail.html', context)
@login_required
def repair_create(request):
    if request.method == 'POST':
        form = RepairAndCleanForm(request.POST)
        if form.is_valid():
            repair = form.save()
            messages.success(request, 'تم إضافة طلب الصيانة/التنظيف بنجاح')
            return redirect('repair_detail', pk=repair.pk)
    else:
        form = RepairAndCleanForm()
    
    context = {
        'form': form,
        'title': 'إضافة طلب صيانة/تنظيف',
        'is_edit': False,
    }
    return render(request, 'repairs/repair_form.html', context)

@login_required
def repair_edit(request, pk):
    repair = get_object_or_404(RepairAndClean, pk=pk)
    
    if request.method == 'POST':
        form = RepairAndCleanForm(request.POST, instance=repair)
        if form.is_valid():
            repair = form.save()
            messages.success(request, 'تم تحديث طلب الصيانة/التنظيف بنجاح')
            return redirect('repair_detail', pk=repair.pk)
    else:
        form = RepairAndCleanForm(instance=repair)
    
    context = {
        'form': form,
        'repair': repair,
        'title': 'تعديل طلب صيانة/تنظيف',
        'is_edit': True,
    }
    return render(request, 'repairs/repair_form.html', context)

@login_required
def repair_detail(request, pk):
    repair = get_object_or_404(RepairAndClean.objects.select_related('product'), pk=pk)
    
    context = {
        'repair': repair,
        'title': 'تفاصيل الصيانة/التنظيف',
    }
    return render(request, 'repairs/repair_detail.html', context)

@login_required
def repair_delete(request, pk):
    repair = get_object_or_404(RepairAndClean, pk=pk)
    
    if request.method == 'POST':
   
        
        repair.delete()
        messages.success(request, 'تم حذف طلب الصيانة/التنظيف بنجاح')
        return redirect('repair_list')
    
    context = {
        'repair': repair,
        'title': 'حذف طلب الصيانة/التنظيف',
    }
    return render(request, 'repairs/repair_delete.html', context)

@login_required
def repair_finish(request, pk):
    repair = get_object_or_404(RepairAndClean, pk=pk)
    
    if request.method == 'POST':
        repair.mark_as_finished()
        repair.product.status = Dstatus.AVAILABLE
            
        repair.product.save()
        messages.success(request, 'تم تغيير حالة الصيانة إلى "تم الاستلام"')
        return redirect('repair_detail', pk=repair.pk)
    
    context = {
        'repair': repair,
        'title': 'تأكيد الاستلام',
    }
    return render(request, 'repairs/repair_finish.html', context)

















@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(is_active=True)
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query) | Q(phone__icontains=query)
        )
    return render(request, 'customers/list.html', {'customers': customers, 'query': query})


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.save()
           
            messages.success(request, f'تم إضافة العميل "{customer.full_name}" بنجاح')
            return redirect('customers_list')
    else:
        form = CustomerForm()
    return render(request, 'customers/form.html', {'form': form, 'title': 'إضافة عميل جديد'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات العميل بنجاح')
            return redirect('customers_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customers/form.html', {'form': form, 'title': f'تعديل: {customer.full_name}', 'customer': customer})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    invoices = Invoice.objects.filter(customer=customer).order_by('-created_at')
    
    total_invoices = invoices.count()
    total_purchases = sum(inv.total_amount for inv in invoices)
    total_paid = sum(inv.paid_amount for inv in invoices)
    total_remaining = sum(inv.remaining_amount for inv in invoices)
    
    penalties = Penalty.objects.filter(invoice__customer=customer)
    total_penalties = sum(p.amount for p in penalties)
    penalties_count = penalties.count()
    
    payments = CustomerPayment.objects.filter(customer=customer).order_by('-payment_date')
    total_payments = sum(p.amount for p in payments)
    
    history = []
    
    for invoice in invoices:
        history.append({
            'type': 'invoice',
            'type_display': 'فاتورة',
            'invoice_number': invoice.invoice_number,
            'invoice_type': invoice.get_invoice_type_display(),
            'total': invoice.total_amount,
            'paid': invoice.paid_amount,
            'remaining': invoice.remaining_amount,
            'status': invoice.get_status_display(),
            'status_class': invoice.status,
            'date': invoice.created_at,
            'items': invoice.items.all()
        })
    
    for penalty in penalties:
        history.append({
            'type': 'penalty',
            'type_display': 'غرامة',
            'invoice_number': penalty.invoice.invoice_number,
            'reason': penalty.reason,
            'amount': penalty.amount,
            'date': penalty.created_at
        })
    
    for payment in payments:
        history.append({
            'type': 'payment',
            'type_display': 'تسديد',
            'amount': payment.amount,
            'notes': payment.notes,
            'receipt_number': payment.receipt_number,
            'date': payment.payment_date
        })
    
    history.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'customer': customer,
        'invoices': invoices,
        'total_invoices': total_invoices,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'total_penalties': total_penalties,
        'penalties_count': penalties_count,
        'total_payments': total_payments,
        'history': history,
        'payments': payments,
    }
    
    return render(request, 'customers/detail.html', context)


@login_required
def customer_search_ajax(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(
        Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(customer_id__icontains=query),
        is_active=True
    )[:10]
    data = [{
        'id': c.pk, 
        'full_name': c.full_name, 
        'phone': c.phone, 
        'customer_id': c.customer_id,
        'loyalty_points': c.loyalty_points, 
        'debt_balance': float(c.debt_balance)
    } for c in customers]
    return JsonResponse({'customers': data})






@login_required
def customer_payment_create(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        notes = request.POST.get('notes', '')
        
        if amount <= 0:
            messages.error(request, 'المبلغ يجب أن يكون أكبر من صفر')
            return redirect('customer_payment_create', pk=pk)
        
        if amount > customer.debt_balance:
            messages.error(request, f'المبلغ المدخل أكبر من الدين المستحق ({customer.debt_balance:,.2f} د.ل)')
            return redirect('customer_payment_create', pk=pk)
        
        payment = CustomerPayment.objects.create(
            customer=customer,
            amount=amount,
            notes=notes,
            created_by=request.user
        )
        
        customer.debt_balance -= amount
        customer.save()
        
        
        messages.success(request, f'تم تسديد {amount:,.2f} د.ل من دين العميل {customer.full_name}')
        
        return redirect('customer_payment_receipt', pk=payment.pk)
    
    context = {
        'customer': customer,
        'debt_amount': customer.debt_balance,
    }
    return render(request, 'customers/payment_create.html', context)


@login_required
def customer_payment_receipt(request, pk):
    payment = get_object_or_404(CustomerPayment, pk=pk)
    
    if not request.user.is_main_admin() and payment.created_by != request.user:
        messages.error(request, 'غير مصرح لك بمشاهدة هذا الإيصال')
        return redirect('customers_list')
    
    return render(request, 'customers/payment_receipt.html', {'payment': payment})


@login_required
def customer_payments_history(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    payments = CustomerPayment.objects.filter(customer=customer).order_by('-payment_date')
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return render(request, 'customers/payments_history.html', {
        'customer': customer,
        'total_paid':total_paid,
        'payments': payments,
    })    


@csrf_exempt
def confirm_return(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm_return') == 'true'
        
        if confirm:
            if invoice.remaining_amount > 0:
                remaining = invoice.remaining_amount
                invoice.paid_amount += remaining
                invoice.remaining_amount = 0
                
                CustomerPayment.objects.create(
                    customer=invoice.customer,
                    amount=remaining,
                    notes=f'تسوية  عند استلام الفاتورة {invoice.invoice_number}'
                )
            
            for item in invoice.items.all():
                item.product.status = Dstatus.AVAILABLE
                item.product.save()
            
            invoice.status = InvoiceStatus.RECIEVED
            invoice.identity_verified_return=True
            invoice.save()
            
            messages.success(request, 'تم تأكيد استلام جميع المنتجات بنجاح')
            return redirect('invoice_list')
    
    penalties = invoice.penalties.all() if hasattr(invoice, 'penalties') else []
    total_penalties = invoice.penalties.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'invoice': invoice,
        'penalties': penalties,
        'total_penalties': total_penalties,
        'can_confirm': True,
        'delay_info': {
            'is_delayed': False,
            'delay_days': 0,
            'delay_hours': 0
        }
    }
    
    if invoice.rent_end_date and invoice.invoice_type == InvoiceType.RENT:
        now = timezone.now()
        end_date = invoice.rent_end_date
        
        end_datetime = None
        
        if end_date.weekday() == 4:
            end_datetime = timezone.make_aware(
                datetime.combine(end_date, time(16, 0, 0))
            )
        else:
            end_datetime = timezone.make_aware(
                datetime.combine(end_date, time(22, 0, 0))
            )
        
        if end_datetime and now > end_datetime:
            diff = now - end_datetime
            total_seconds = diff.total_seconds()
            total_hours = total_seconds / 3600
            delay_days = int(total_hours // 24)
            delay_hours = int(total_hours % 24)
            
            context['delay_info'] = {
                'is_delayed': True,
                'delay_days': delay_days,
                'delay_hours': delay_hours + (delay_days * 24)
            }
    
    return render(request, 'invoices/confirm_return.html', context)

@csrf_exempt
def add_penalty(request):
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        penalty_type = request.POST.get('penalty_type', 'تأخير')
        
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        penalty = Penalty.objects.create(
            invoice=invoice,
            customer=invoice.customer,
            amount=amount,
            reason=reason,
            notes=f"نوع الغرامة: {penalty_type}"
        )
        
        invoice.total_amount += Decimal(amount)
        invoice.remaining_amount = invoice.total_amount - invoice.paid_amount
        invoice.save()
        
        messages.success(request, 'تم إضافة الغرامة بنجاح')
        return redirect('confirm_return', invoice_id=invoice_id)
    
    return redirect('invoice_list')


def calculate_delay(invoice):
    if not invoice.rent_end_date:
        return {'is_delayed': False, 'delay_days': 0, 'delay_hours': 0}
    
    now = timezone.now().date()
    end_date = invoice.rent_end_date
    
    if now > end_date:
        delay_days = (now - end_date).days
        return {
            'is_delayed': True,
            'delay_days': delay_days,
            'delay_hours': delay_days * 24,
        }
    
    return {'is_delayed': False, 'delay_days': 0, 'delay_hours': 0}



def print_receipt(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)  
    penalties = Penalty.objects.filter(invoice=invoice)
    
    context = {
        'invoice': invoice,
        'penalties': penalties,
  
    }
    return render(request, 'invoices/print_receipt.html', context)


@login_required
def create_invoice(request):
    if request.method == 'GET':
        products = Product.objects.filter(is_active=True)
        customers = Customer.objects.filter(is_active=True)
        payment_methods = PaymentMethod.objects.filter(is_active=True)
        
        context = {
            'products': products,
            'customers': customers,
            'payment_methods': payment_methods,
            'invoice_types': InvoiceType.choices,
        }
        return render(request, 'invoices/create_invoice.html', context)
    
    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            
            cart = request.session.get('cart', [])
            
            if not cart:
                products_data = []
                for key, value in data.items():
                    if key.startswith('product_') and key.endswith('_id'):
                        product_id = value
                        days_key = key.replace('_id', '_days')
                        price_key = key.replace('_id', '_price')
                        
                        if days_key in data and price_key in data:
                            products_data.append({
                                'product_id': int(product_id),
                                'days': int(data[days_key]),
                                'price': float(data[price_key])
                            })
                if products_data:
                    cart = products_data
                    request.session['cart'] = cart
                    request.session.modified = True
            
            if not cart:
                messages.error(request, 'السلة فارغة')
                return redirect('invoice_list')
            
            invoice_type = data.get('invoice_type', InvoiceType.RENT)
            
            if invoice_type == InvoiceType.RENT:
                rent_start_date = data.get('rent_start_date')
                rent_end_date = data.get('rent_end_date')
                
                if not rent_start_date or not rent_end_date:
                    messages.error(request, 'يرجى تحديد تاريخ بداية ونهاية الإيجار')
                    return redirect('invoice_list')
                
                try:
                    rent_start_date = datetime.strptime(rent_start_date, '%Y-%m-%d').date()
                    rent_end_date = datetime.strptime(rent_end_date, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'صيغة التاريخ غير صحيحة')
                    return redirect('invoice_list')
                
                if rent_start_date > rent_end_date:
                    messages.error(request, 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية')
                    return redirect('invoice_list')
                
                for item in cart:
                    try:
                        product = Product.objects.get(id=item['product_id'])
                        
                        if product.status == Dstatus.SOLD:
                            messages.error(request, f'المنتج {product.name} تم بيعه ولا يمكن تأجيره')
                            return redirect('invoice_list')
                        
                        if product.status == Dstatus.INCLEAN:
                            messages.error(request, f'المنتج {product.name} قيد التنظيف')
                            return redirect('invoice_list')
                        
                        if product.status == Dstatus.INREPAIR:
                            messages.error(request, f'المنتج {product.name} قيد الصيانة')
                            return redirect('invoice_list')
                        
                        is_available, message = Invoice.check_product_availability(
                            product, rent_start_date, rent_end_date
                        )
                        
                        if not is_available:
                            messages.error(request, f'المنتج {product.name}: {message}')
                            return redirect('invoice_list')
                            
                    except Product.DoesNotExist:
                        messages.error(request, f'المنتج غير موجود')
                        return redirect('invoice_list')
            
            invoice = Invoice()
            invoice.invoice_number = invoice.generate_invoice_number()
            invoice.invoice_type = invoice_type
            
            customer_id = data.get('customer_id')
            is_cash_customer = data.get('is_cash_customer', '0') == '1'
            
            if is_cash_customer:
                invoice.customer = None
            elif customer_id:
                try:
                    invoice.customer = Customer.objects.get(id=int(customer_id))
                except Customer.DoesNotExist:
                    messages.error(request, 'العميل غير موجود')
                    return redirect('invoice_list')
            
            if invoice_type == InvoiceType.RENT:
                invoice.rent_start_date = rent_start_date
                invoice.rent_end_date = rent_end_date
            else:
                invoice.rent_start_date = None
                invoice.rent_end_date = None
                invoice.sale_price = Decimal(str(data.get('sale_price', '0')))
            
            invoice.discount = Decimal(str(data.get('discount', '0')))
            invoice.commission = Decimal(str(data.get('commission', '0')))
            invoice.paid_amount = Decimal(str(data.get('paid_amount', '0')))
            
            payment_method_id = data.get('payment_method')
            if payment_method_id:
                try:
                    invoice.payment_method = PaymentMethod.objects.get(id=int(payment_method_id))
                except PaymentMethod.DoesNotExist:
                    pass
            
            invoice.notes = data.get('notes', '')
            invoice.identity_verified = data.get('identity_verified', 'true') in ['true', 'True', '1', 'on']
            
            invoice.save()
            
            invoice.total_amount = Decimal('0')
            
            for cart_item in cart:
                product = Product.objects.get(id=cart_item['product_id'])
                
                if invoice_type == InvoiceType.RENT:
                    is_available, message = Invoice.check_product_availability(
                        product, rent_start_date, rent_end_date, exclude_invoice=invoice
                    )
                    
                    if not is_available:
                        invoice.delete()
                        messages.error(request, f'المنتج {product.name}: {message}')
                        return redirect('invoice_list')
                    
                    product.status = Dstatus.RENTED
                    product.save()
                    
                    days = cart_item.get('days', 1)
                    
                    invoice_item = InvoiceItem.objects.create(
                        invoice=invoice,
                        product=product,
                        days=days,
                        unit_price=product.selling_price
                    )
                    invoice.total_amount += invoice_item.days * invoice_item.unit_price
                    
                else:
                    if product.status == Dstatus.RENTED:
                        invoice.delete()
                        messages.error(request, f'المنتج {product.name} مؤجر حالياً ولا يمكن بيعه')
                        return redirect('invoice_list')
                    
                    product.status = Dstatus.SOLD
                    product.save()
                    
                    invoice_item = InvoiceItem.objects.create(
                        invoice=invoice,
                        product=product,
                        days=1,
                        unit_price=invoice.sale_price
                    )
                    invoice.total_amount += invoice_item.days * invoice_item.unit_price
            
            invoice.total_amount -= invoice.discount
            invoice.total_amount += invoice.commission
            
            invoice.remaining_amount = invoice.total_amount - invoice.paid_amount
            
            invoice.status = InvoiceStatus.PENDING
            
            if invoice.customer and invoice.remaining_amount > Decimal('0'):
                invoice.customer.debt_balance += invoice.remaining_amount
                invoice.customer.save()
            
            invoice.save()
            
            request.session['cart'] = []
            request.session.modified = True
            
            messages.success(request, 'تم إضافة الفاتورة بنجاح')
            return redirect('print_receipt', invoice.pk)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
            return redirect('invoice_list')
    
    messages.error(request, 'حدث خطأ غير معروف!')
    return redirect('invoice_list')

@login_required
def mark_as_delivered(request, invoice_id):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'طريقة غير مدعومة'
        })
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if invoice.status != InvoiceStatus.PENDING:
        return JsonResponse({
            'success': False,
            'message': 'الفاتورة ليست قيد الانتظار'
        })
    
    if invoice.invoice_type != 'rent':
        return JsonResponse({
            'success': False,
            'message': 'هذه العملية مخصصة لفواتير الايجار فقط'
        })
    
    try:
        invoice.status = InvoiceStatus.DELIVERED
        invoice.identity_verified = True
        invoice.save()
        
        for item in invoice.items.all():
            item.product.status = Dstatus.RENTED
            item.product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'تم تسليم الفستان للعميل بنجاح',
            'invoice_number': invoice.invoice_number,
            'redirect_url': reverse('print_receipt', args=[invoice.id])
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    search_query = request.GET.get('search','')
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__full_name__icontains=search_query) |
            Q(customer_name__icontains=search_query)
        )
    
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    total_remaining = invoices.aggregate(Sum('remaining_amount'))['remaining_amount__sum'] or 0
    
    context = {
        'invoices': invoices,
        'status_choices': InvoiceStatus.choices,
        'current_status': status_filter,
        'search_query': search_query,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
    }
    return render(request, 'invoices/invoice_list.html', context)


@csrf_exempt
def cancel_invoice(request, invoice_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'طريقة غير صحيحة'})
    
    try:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        if invoice.status == InvoiceStatus.PAID:
            return JsonResponse({'success': False, 'message': 'لا يمكن إلغاء فاتورة مدفوعة'})
        
        if invoice.status == InvoiceStatus.CANCELLED:
            return JsonResponse({'success': False, 'message': 'الفاتورة ملغاة بالفعل'})
        
        invoice.mark_as_cancelled()
        
        return JsonResponse({
            'success': True,
            'message': 'تم إلغاء الفاتورة وإعادة جميع المنتجات'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})




@login_required
def statistics(request):

    today = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = today
    
    invoices = Invoice.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    rent_invoices = invoices.filter(invoice_type=InvoiceType.RENT)
    sale_invoices = invoices.filter(invoice_type=InvoiceType.SALE)
    
    total_invoices = invoices.count()
    total_rent_invoices = rent_invoices.count()
    total_sale_invoices = sale_invoices.count()
    
    total_revenue = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_rent_revenue = rent_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_sale_revenue = sale_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    total_paid = invoices.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
    total_remaining = invoices.aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0')
    
    total_discount = invoices.aggregate(total=Sum('discount'))['total'] or Decimal('0')
    total_commission = invoices.aggregate(total=Sum('commission'))['total'] or Decimal('0')
    
    customer_payments = CustomerPayment.objects.filter(
        payment_date__date__gte=start_date,
        payment_date__date__lte=end_date
    )
    total_payments = customer_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    repairs = RepairAndClean.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    total_repairs = repairs.count()
    total_repair_cost = repairs.aggregate(total=Sum('total_cost'))['total'] or Decimal('0')
    repair_count = repairs.filter(kind='repair').count()
    clean_count = repairs.filter(kind='clean').count()
    
    invoice_items = InvoiceItem.objects.filter(invoice__in=invoices)
    total_items_sold = invoice_items.count()
    total_rent_days = invoice_items.aggregate(total=Sum('days'))['total'] or 0
    
    total_products_rented = Product.objects.filter(status=Dstatus.RENTED).count()
    total_products_sold = Product.objects.filter(status=Dstatus.SOLD).count()
    total_products_available = Product.objects.filter(status=Dstatus.AVAILABLE).count()
    total_products_inclean = Product.objects.filter(status=Dstatus.INCLEAN).count()
    total_products_inrepair = Product.objects.filter(status=Dstatus.INREPAIR).count()
    
    top_rented_products = Product.objects.filter(
        invoiceitem__invoice__in=invoices,
        invoiceitem__invoice__invoice_type=InvoiceType.RENT
    ).annotate(
        rental_count=Count('invoiceitem'),
        total_rental_revenue=Sum('invoiceitem__total_price')
    ).order_by('-rental_count')[:10]
    
    top_sold_products = Product.objects.filter(
        invoiceitem__invoice__in=invoices,
        invoiceitem__invoice__invoice_type=InvoiceType.SALE
    ).annotate(
        sale_count=Count('invoiceitem'),
        total_sale_revenue=Sum('invoiceitem__total_price')
    ).order_by('-sale_count')[:10]
    
    total_product_cost = invoice_items.aggregate(total=Sum('product__cost_price'))['total'] or Decimal('0')
    
    total_profit = total_revenue - total_product_cost
    
    profit_margin = 0
    if total_revenue > 0:
        profit_margin = (total_profit / total_revenue) * 100
    
    rent_percent = 0
    sale_percent = 0
    if total_revenue > 0:
        rent_percent = (total_rent_revenue / total_revenue) * 100
        sale_percent = (total_sale_revenue / total_revenue) * 100
    
    total_rent_items = invoice_items.filter(invoice__invoice_type=InvoiceType.RENT)
    total_sale_items = invoice_items.filter(invoice__invoice_type=InvoiceType.SALE)
    
    rent_product_cost = total_rent_items.aggregate(total=Sum('product__cost_price'))['total'] or Decimal('0')
    sale_product_cost = total_sale_items.aggregate(total=Sum('product__cost_price'))['total'] or Decimal('0')
    
    rent_profit = total_rent_revenue - rent_product_cost
    sale_profit = total_sale_revenue - sale_product_cost
    
    expenses = Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date
    )
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    expenses_by_category = ExpenseCategory.objects.annotate(
        total=Sum('expenses__amount', filter=Q(expenses__expense_date__gte=start_date, expenses__expense_date__lte=end_date))
    ).filter(total__gt=0)
    
    total_salaries_paid = MonthlySalaryPayment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_employees = Employee.objects.filter(status='active').count()
    total_employee_salary_cost = Employee.objects.filter(status='active').aggregate(total=Sum('monthly_salary'))['total'] or Decimal('0')
    
    total_absences = AbsenceRecord.objects.filter(
        absence_date__gte=start_date,
        absence_date__lte=end_date
    ).count()
    total_absence_deductions = AbsenceRecord.objects.filter(
        absence_date__gte=start_date,
        absence_date__lte=end_date
    ).aggregate(total=Sum('deduction_amount'))['total'] or Decimal('0')
    
    expenses_by_category_list = []
    for cat in expenses_by_category:
        expenses_by_category_list.append({
            'name': cat.name,
            'total': cat.total
        })
    
    total_cost_of_goods_sold = total_product_cost
    total_operating_expenses = total_expenses + total_salaries_paid
    total_net_profit = total_profit - total_operating_expenses
    total_gross_profit = total_profit
    
    net_profit_margin = 0
    if total_revenue > 0:
        net_profit_margin = (total_net_profit / total_revenue) * 100
    
    daily_stats = []
    for i in range(7):
        date = today - timedelta(days=i)
        day_invoices = invoices.filter(created_at__date=date)
        daily_stats.append({
            'date': date,
            'count': day_invoices.count(),
            'revenue': day_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        })
    daily_stats.reverse()
    
    total_penalties = Penalty.objects.filter(
        invoice__in=invoices
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    top_customers = Customer.objects.filter(
        invoice__in=invoices
    ).annotate(
        total_spent=Sum('invoice__total_amount'),
        total_invoices=Count('invoice')
    ).order_by('-total_spent')[:10]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_invoices': total_invoices,
        'total_rent_invoices': total_rent_invoices,
        'total_sale_invoices': total_sale_invoices,
        'total_revenue': total_revenue,
        'total_rent_revenue': total_rent_revenue,
        'total_sale_revenue': total_sale_revenue,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'total_penalties': total_penalties,
        'total_discount': total_discount,
        'total_commission': total_commission,
        'total_payments': total_payments,
        'total_repairs': total_repairs,
        'total_repair_cost': total_repair_cost,
        'repair_count': repair_count,
        'clean_count': clean_count,
        'total_items_sold': total_items_sold,
        'total_rent_days': total_rent_days,
        'total_products_rented': total_products_rented,
        'total_products_sold': total_products_sold,
        'total_products_available': total_products_available,
        'total_products_inclean': total_products_inclean,
        'total_products_inrepair': total_products_inrepair,
        'top_rented_products': top_rented_products,
        'top_sold_products': top_sold_products,
        'total_product_cost': total_product_cost,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'rent_profit': rent_profit,
        'sale_profit': sale_profit,
        'rent_percent': rent_percent,
        'sale_percent': sale_percent,
        'daily_stats': daily_stats,
        'total_expenses': total_expenses,
        'expenses_by_category': expenses_by_category_list,
        'total_salaries_paid': total_salaries_paid,
        'total_employees': total_employees,
        'total_employee_salary_cost': total_employee_salary_cost,
        'total_absences': total_absences,
        'total_absence_deductions': total_absence_deductions,
        'total_operating_expenses': total_operating_expenses,
        'total_net_profit': total_net_profit,
        'net_profit_margin': net_profit_margin,
        'total_gross_profit': total_gross_profit,
        'top_customers': top_customers,
        'total_cost_of_goods_sold': total_cost_of_goods_sold,
    }
    
    return render(request, 'statistics.html', context)


@login_required
def inventory_report(request):
    products = Product.objects.filter(is_active=True).order_by('name')
    
    total_products = products.count()
    total_rental_revenue = Decimal('0')
    total_profit = Decimal('0')
    
    for product in products:
        rental_count = InvoiceItem.objects.filter(
            product=product,
            invoice__invoice_type=InvoiceType.RENT
        ).count()
        
        rental_revenue = InvoiceItem.objects.filter(
            product=product,
            invoice__invoice_type=InvoiceType.RENT
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
        
        profit = rental_revenue - product.cost_price if rental_revenue > 0 else Decimal('0')
        
        product.rental_count = rental_count
        product.rental_revenue = rental_revenue
        product.profit = profit
        
        total_rental_revenue += rental_revenue
        total_profit += profit
    
    rented_count = Product.objects.filter(status=Dstatus.RENTED).count()
    available_count = Product.objects.filter(status=Dstatus.AVAILABLE).count()
    sold_count = Product.objects.filter(status=Dstatus.SOLD).count()
    inclean_count = Product.objects.filter(status=Dstatus.INCLEAN).count()
    inrepair_count = Product.objects.filter(status=Dstatus.INREPAIR).count()
    
    context = {
        'products': products,
        'total_products': total_products,
        'total_rental_revenue': total_rental_revenue,
        'total_profit': total_profit,
        'rented_count': rented_count,
        'available_count': available_count,
        'sold_count': sold_count,
        'inclean_count': inclean_count,
        'inrepair_count': inrepair_count,
    }
    
    return render(request, 'inventory_report.html', context)




@login_required
def unreturned_invoices(request):
    invoices = Invoice.objects.filter(
        status= InvoiceStatus.DELIVERED,
        invoice_type=InvoiceType.RENT
    ).order_by('rent_end_date')
    
    for invoice in invoices:
        is_delayed = False
        delay_days = 0
        delay_hours = 0
        
        if invoice.rent_end_date:
            now = timezone.now()
            end_date = invoice.rent_end_date
            
            if end_date.weekday() == 4:
                end_datetime = timezone.make_aware(
                    datetime.combine(end_date, time(16, 0, 0))
                )
            else:
                end_datetime = timezone.make_aware(
                    datetime.combine(end_date, time(22, 0, 0))
                )
            
            if now > end_datetime:
                diff = now - end_datetime
                total_hours = diff.total_seconds() / 3600
                delay_days = int(total_hours // 24)
                delay_hours = int(total_hours % 24)
                is_delayed = True
        
        invoice.is_delayed = is_delayed
        invoice.delay_days = delay_days
        invoice.delay_hours = delay_hours
    
    context = {
        'invoices': invoices,
        'total_count': invoices.count(),
        'delayed_count': sum(1 for inv in invoices if inv.is_delayed),
    }
    
    return render(request, 'invoices/unreturned_invoices.html', context)


@login_required
def select_barcodes(request):
    products = Product.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'select_barcodes.html', context)

@login_required
def print_qr_preview(request):
    if request.method != 'POST':
        return redirect('select_barcodes')
    
    product_ids = request.POST.getlist('product_ids')
    copies = int(request.POST.get('copies', 1))
    label_size = request.POST.get('label_size', 'medium')
    
    if not product_ids:
        messages.warning(request, 'الرجاء اختيار منتج واحد على الأقل')
        return redirect('select_barcodes')
    
    products = Product.objects.filter(id__in=product_ids, is_active=True)
    
    if not products:
        messages.warning(request, 'المنتجات المحددة غير موجودة')
        return redirect('select_barcodes')
    
    for product in products:
        if not product.qr:
            product.generate_qr()
            product.save()
    
    context = {
        'products': products,
        'copies': copies,
        'copies_range': range(copies),
        'label_size': label_size,
    }
    
    return render(request, 'print_barcodes.html', context)


@login_required
def product_by_barcode(request, barcode):
    product = get_object_or_404(Product, barcode=barcode, is_active=True)
    return render(request, 'products/product_by_barcode.html', {'product': product})    



@login_required
def check_product_availability_api(request):
    if request.method == 'GET':
        product_id = request.GET.get('product_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not all([product_id, start_date, end_date]):
            return JsonResponse({
                'available': False,
                'message': 'جميع الحقول مطلوبة'
            })
        
        try:
            product = Product.objects.get(id=product_id)
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if product.status == Dstatus.SOLD:
                return JsonResponse({
                    'available': False,
                    'message': 'المنتج تم بيعه'
                })
            
            if product.status == Dstatus.INCLEAN:
                return JsonResponse({
                    'available': False,
                    'message': 'المنتج قيد التنظيف'
                })
            
            if product.status == Dstatus.INREPAIR:
                return JsonResponse({
                    'available': False,
                    'message': 'المنتج قيد الصيانة'
                })
            
            is_available, message = Invoice.check_product_availability(
                product, start_date, end_date
            )
            
            return JsonResponse({
                'available': is_available,
                'message': message
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'available': False,
                'message': 'المنتج غير موجود'
            })
        except ValueError:
            return JsonResponse({
                'available': False,
                'message': 'صيغة التاريخ غير صحيحة'
            })
    
    return JsonResponse({
        'available': False,
        'message': 'طريقة غير مدعومة'
    })




@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})

@login_required
def employee_create(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        position = request.POST.get('position')
        phone = request.POST.get('phone')
        monthly_salary = request.POST.get('monthly_salary', 0)
        
        employee = Employee(
            full_name=full_name,
            position=position,
            phone=phone,

            payment_type='monthly',
            

            monthly_salary=monthly_salary,
        )
        employee.save()
        messages.success(request, f'تم إضافة الموظف {full_name} بنجاح')
        return redirect('employee_list')
    
    return render(request, 'employee_form.html', {'title': 'إضافة موظف جديد'})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.full_name = request.POST.get('full_name')
        employee.position = request.POST.get('position')
        employee.phone = request.POST.get('phone')
        employee.monthly_salary = request.POST.get('monthly_salary', 0)
        employee.status = request.POST.get('status')
        employee.save()
        messages.success(request, f'تم تعديل بيانات {employee.full_name}')
        return redirect('employee_list')
    
    return render(request, 'employee_form.html', {'employee': employee, 'title': 'تعديل بيانات موظف'})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'تم حذف الموظف بنجاح')
        return redirect('employee_list')
    return render(request, 'employee_confirm_delete.html', {'employee': employee})

@login_required
def absence_create(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        absence_date = request.POST.get('absence_date')
        deduction_amount = request.POST.get('deduction_amount')
        reason = request.POST.get('reason')
        
        employee = get_object_or_404(Employee, pk=employee_id)
        
        AbsenceRecord.objects.create(
            employee=employee,
            absence_date=absence_date,
            deduction_amount=deduction_amount,
            reason=reason
        )
        messages.success(request, f'تم تسجيل غياب {employee.full_name} بتاريخ {absence_date}')
        return redirect('absence_list')
    
    employees = Employee.objects.filter(payment_type='monthly', status='active')
    return render(request, 'absence_form.html', {'employees': employees, 'title': 'تسجيل غياب'})

@login_required
def absence_list(request):
    absences = AbsenceRecord.objects.all().select_related('employee')
    return render(request, 'absence_list.html', {'absences': absences})

@login_required
def absence_delete(request, pk):
    absence = get_object_or_404(AbsenceRecord, pk=pk)
    if request.method == 'POST':
        absence.delete()
        messages.success(request, 'تم حذف تسجيل الغياب')
        return redirect('absence_list')
    return render(request, 'absence_confirm_delete.html', {'absence': absence})

@login_required
def monthly_salary_payment(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id, payment_type='monthly')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_date = request.POST.get('payment_date')
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes')
        
        payment = MonthlySalaryPayment(
            employee=employee,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            notes=notes,
            created_by=request.user
        )
        payment.save()
        messages.success(request, f'تم تسديد {amount}د.ل للموظف {employee.full_name}')
        return redirect('employee_list')
    
    return render(request, 'monthly_payment_form.html', {'employee': employee})

@login_required
def monthly_salary_statement(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id, payment_type='monthly')
    absences = AbsenceRecord.objects.filter(employee=employee)
    payments = MonthlySalaryPayment.objects.filter(employee=employee)
    
    total_deductions = absences.aggregate(total=Sum('deduction_amount'))['total'] or 0
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
    net_salary = employee.monthly_salary - total_deductions
    remaining = net_salary - total_paid
    
    context = {
        'employee': employee,
        'absences': absences,
        'payments': payments,
        'total_deductions': total_deductions,
        'total_paid': total_paid,
        'net_salary': net_salary,
        'remaining': remaining,
    }
    return render(request, 'monthly_statement.html', context)




@login_required
def expense_list(request):
    qs = Expense.objects.select_related('category').order_by('-expense_date')
    cat = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if cat:
        qs = qs.filter(category_id=cat)
    if date_from:
        qs = qs.filter(expense_date__gte=date_from)
    if date_to:
        qs = qs.filter(expense_date__lte=date_to)
    
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    expenses = paginator.get_page(page_number)
    
    total = qs.aggregate(t=Sum('amount'))['t'] or 0
    
    context = {
        'expenses': expenses,
        'categories': ExpenseCategory.objects.all(),
        'selected_category': cat,
        'date_from': date_from,
        'date_to': date_to,
        'total_amount': total,
    }
    return render(request, 'expense_list.html', context)


@login_required
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'تم تسجيل المصروف بنجاح')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expense_form.html', {'form': form})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المصروف')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expense_form.html', {'form': form})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'تم حذف المصروف')
        return redirect('expense_list')
    return render(request, 'confirm_delete.html', {'object': expense})


@login_required
def expense_category_list(request):
    categories = ExpenseCategory.objects.all()
    return render(request, 'expense_category_list.html', {'categories': categories})


@login_required
def expense_category_add(request):
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الفئة')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm()
    return render(request, 'expense_category_form.html', {'form': form})


