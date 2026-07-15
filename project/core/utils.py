from django.utils import timezone
from django.db.models import Q
from .models import Invoice, InvoiceStatus

def get_today_reservations_count():

    today = timezone.now().date()
    
    count = Invoice.objects.filter(
        invoice_type='rent', 
        status__in=InvoiceStatus.PENDING,
        rent_start_date=today
    ).count()
    
    return count

def get_reservations_context_processor(request):

    today = timezone.now().date()
    
    if request.user.is_authenticated:
        return {'today_reservations_count': get_today_reservations_count(),   'today': today.strftime('%Y-%m-%d')}
    return {'today_reservations_count': 0,    'today': today.strftime('%Y-%m-%d')}