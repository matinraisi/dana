from django.db import models


class SMSLog(models.Model):
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE,
        null=True, blank=True, related_name='sms_logs',
        verbose_name='آموزشگاه',
    )
    SMS_TYPE_CHOICES = [
        ('registration', 'تأیید ثبت‌نام'),
        ('payment', 'تأیید پرداخت'),
        ('document_approved', 'تأیید مدارک'),
        ('document_rejected', 'رد مدارک'),
        ('attendance_absent', 'اطلاع غیبت'),
        ('installment_reminder', 'یادآوری قسط'),
        ('course_start', 'شروع دوره'),
        ('bulk_plain', 'ارسال دسته‌جمعی'),
        ('template', 'پیامک الگو'),
        ('profile_link', 'لینک پروفایل'),
    ]

    receptor = models.CharField(max_length=11, verbose_name="شماره گیرنده")
    message = models.TextField(verbose_name="متن پیامک")
    sms_type = models.CharField(max_length=30, choices=SMS_TYPE_CHOICES, verbose_name="نوع پیامک")
    is_sent = models.BooleanField(default=False, verbose_name="وضعیت ارسال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")

    class Meta:
        verbose_name = "لاگ پیامک"
        verbose_name_plural = "گزارشات لاگ پیامک‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.receptor} - {self.get_sms_type_display()}"
