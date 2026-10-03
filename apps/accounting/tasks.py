from celery import shared_task
from django.utils import timezone
from .models import Transaction

@shared_task
def check_overdue_payments():
    overdue_count = Transaction.objects.filter(
        status='PENDING', 
        due_date__lt=timezone.now().date()
    ).update(status='CANCELLED') # یا هر اکشن دیگری مثل ارسال پیامک
    return f"{overdue_count} تراکنش معوقه شناسایی و بروزرسانی شد."

# این بخش را به انتهای فایل apps/accounting/tasks.py اضافه کن:

@shared_task
def check_and_send_subscription_reminders():
    """
    بررسی روزانه سرویس‌های تمدیدی و ارسال پیامک تمدید خودکار در مایل‌استون‌های ۷ روز و ۳ روز مانده به انقضا
    """
    from apps.crm.models import SubscriptionService
    from apps.crm.services import SMSService
    from django.utils import timezone
    
    today = timezone.now().date()
    # مایل‌استون‌های زمانی برای یادآوری
    milestones = [7, 3] 
    
    triggered_reminders = 0
    services = SubscriptionService.objects.filter(auto_sms_reminder=True)
    
    for service in services:
        remaining_days = (service.expiry_date - today).days
        
        if remaining_days in milestones:
            # آماده‌سازی متن پیامک کاملاً شخصی‌سازی شده
            message = (
                f"مشتری گرامی {service.lead.name}،\n"
                f"سرویس {service.get_service_type_display()} شما برای دامنه/آدرس ({service.domain_or_ip}) "
                f"در تاریخ {service.expiry_date} (حدود {remaining_days} روز آینده) منقضی می‌شود.\n"
                f"لطفاً جهت تمدید و جلوگیری از قطع سرویس اقدام نمایید.\n"
                f"واحد پشتیبانی {service.business_unit.name}"
            )
            
            # ارسال پیامک با وب‌سرویس داینامیک بیزینس یونیت مربوطه
            success = SMSService.send_sms(
                business_unit=service.business_unit,
                phone=service.lead.phone,
                message=message,
                lead=service.lead
            )
            
            if success:
                service.last_reminder_sent_at = timezone.now()
                service.save(update_fields=['last_reminder_sent_at'])
                triggered_reminders += 1
                
    return f"تعداد {triggered_reminders} پیامک یادآوری تمدید هاست و دامنه با موفقیت ارسال شد."