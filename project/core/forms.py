from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.utils import timezone


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
        fields = ['product', 'kind', 'status', 'finish_at', 'total_cost', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
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
            'finish_at': 'تاريخ الانتهاء',
            'total_cost': 'تكلفة الصيانة',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['finish_at'].initial = timezone.now().date()
        self.fields['status'].initial = 'inwork'
        
        for field in self.fields:
            if field == 'notes':
                self.fields[field].required = False
            else:
                self.fields[field].required = True
    
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
    