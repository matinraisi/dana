from django.db import models
from django.utils import timezone


class StudentIDCard(models.Model):
    student = models.OneToOneField(
        'academy.StudentEnrollment',
        on_delete=models.CASCADE,
        related_name='id_card',
        verbose_name="هنرجو",
    )
    card_number = models.CharField(
        max_length=30, unique=True, verbose_name="شماره کارت"
    )
    qr_code = models.ImageField(
        upload_to='idcards/', blank=True, null=True, verbose_name="QR Code"
    )
    is_valid = models.BooleanField(default=True, verbose_name="معتبر")
    issued_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ صدور")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "کارت شناسایی"
        verbose_name_plural = "کارت‌های شناسایی هنرجویان"

    def __str__(self):
        return f"کارت {self.card_number} — {self.student}"

    @property
    def payment_status(self):
        enrollments = self.student.active_enrollments.all()
        if not enrollments.exists():
            return 'no_enrollment'
        if all(e.is_fully_paid for e in enrollments):
            return 'paid'
        if any(e.paid_amount > 0 for e in enrollments):
            return 'partial'
        return 'unpaid'

    @property
    def payment_status_display(self):
        mapping = {
            'paid': 'پرداخت کامل',
            'partial': 'پرداخت ناقص',
            'unpaid': 'بدهکار',
            'no_enrollment': 'بدون ثبت‌نام',
        }
        return mapping.get(self.payment_status, '—')
