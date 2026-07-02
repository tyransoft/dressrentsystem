from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.utils import timezone

WIDGET_ATTRS = {
    'class': 'form-control',
    'placeholder': 'أدخل النص هنا'
}

SELECT_ATTRS = {
    'class': 'form-select'
}

DATE_ATTRS = {
    'class': 'form-control',
    'type': 'date'
      
}



class LoginForm(forms.Form):
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المستخدم', 'autofocus': True})
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'أدخل كلمة المرور'})
    )


class UserCreateForm(UserCreationForm):
    role = forms.ChoiceField(label='الدور', choices=Role.choices, widget=forms.Select(attrs={'class': 'form-select'}))


    class Meta:
        model = CustomUser
        fields = ['username', 'role',  'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].label = 'كلمة المرور'
        self.fields['password2'].label = 'تأكيد كلمة المرور'


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [ 'role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'role': 'الدور',
            'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

     
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name',  'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'name': 'اسم الفئة', 'is_active': 'نشطة'}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'barcode', 'category', 'cost_price', 'selling_price',
            'status', 'size', 'color',  
            'image', 'image_2', 'image_3',  
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم الفستان'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الباركود'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', }),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': False   
            }),
            'image_2': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'image_3': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'اسم الفستان',
            'barcode': 'الباركود',
            'category': 'الفئة',
            'cost_price': 'سعر التكلفة',
            'selling_price': 'سعر الايجار',
            'status': 'حالة الفستان',
            'size': 'المقاس',
            'color': 'اللون',
            'image': 'الصورة الرئيسية ',
            'image_2': 'الصورة الثانية',
            'image_3': 'الصورة الثالثة',
            'is_active': 'نشط',
        }
      
        error_messages = {
            'image': {
                'required': 'الصورة الرئيسية مطلوبة',
                'invalid': 'يرجى رفع ملف صورة صالح',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['image_2'].required = False
        self.fields['image_3'].required = False
        self.fields['barcode'].required = False
        self.fields['image'].required = False
        
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.TextInput, forms.NumberInput, forms.Select]:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
    

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'increase_percentage', 'is_active', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' اسم طريقة الدفع'}),
            'increase_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'اسم طريقة الدفع',
            'increase_percentage': 'نسبة الزيادة %',
            'is_active': 'نشط',
            'is_default': 'الطريقة الافتراضية',
        }        



class RepairAndCleanForm(forms.ModelForm):
    class Meta:
        model = RepairAndClean
        fields = ['product', 'kind', 'status', 'start_date', 'finish_at', 'total_cost', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'finish_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'أضف ملاحظات إضافية...'
            }),
        }
        labels = {
            'product': 'الفستان',
            'kind': 'نوع الصيانة',
            'status': 'الحالة',
            'start_date': 'تاريخ بداية الصيانة',
            'finish_at': 'تاريخ انتهاء الصيانة',
            'total_cost': 'تكلفة الصيانة',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['start_date'].initial = today
        self.fields['finish_at'].initial = today
        self.fields['status'].initial = 'inwork'
        
        for field in self.fields:
            if field == 'notes':
                self.fields[field].required = False
            else:
                self.fields[field].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        finish_at = cleaned_data.get('finish_at')
        
        if start_date and start_date < timezone.now().date():
            self.add_error('start_date', 'تاريخ البداية لا يمكن أن يكون في الماضي')
        
        if finish_at and finish_at < timezone.now().date():
            self.add_error('finish_at', 'تاريخ الانتهاء لا يمكن أن يكون في الماضي')
        
        if start_date and finish_at and start_date > finish_at:
            self.add_error('finish_at', 'تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية')
        
        return cleaned_data
    
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError('تاريخ البداية لا يمكن أن يكون في الماضي')
        return start_date
    
    def clean_finish_at(self):
        finish_at = self.cleaned_data.get('finish_at')
        if finish_at and finish_at < timezone.now().date():
            raise forms.ValidationError('تاريخ الانتهاء لا يمكن أن يكون في الماضي')
        return finish_at
    
    def clean_total_cost(self):
        total_cost = self.cleaned_data.get('total_cost')
        if total_cost and total_cost < 0:
            raise forms.ValidationError('التكلفة لا يمكن أن تكون سالبة')
        return total_cost

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'full_name': 'الاسم الكامل',
            'phone': 'رقم الهاتف',
            'is_active': 'نشط',
        }





class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'expense_date', 'category', 'description']
        widgets = {
            'title': forms.TextInput(attrs=WIDGET_ATTRS),
            'amount': forms.NumberInput(attrs=WIDGET_ATTRS),
            'expense_date': forms.DateInput(attrs=DATE_ATTRS),
            'category': forms.Select(attrs=SELECT_ATTRS),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
        }
        labels = {
            'title': 'عنوان المصروف',
            'amount': 'المبلغ (دينار)',
            'expense_date': 'التاريخ',
            'category': 'الفئة',
            'description': 'الوصف',
        }


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs=WIDGET_ATTRS),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
        }
        labels = {'name': 'اسم الفئة', 'description': 'الوصف'}            


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        exclude = ['employee_number', 'created_at']
     
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        
        if payment_type == 'monthly' and cleaned_data.get('monthly_salary', 0) <= 0:
            self.add_error('monthly_salary', 'الراتب الشهري مطلوب للموظف الشهري')

        
        return cleaned_data


                                    