from django.db import models


class AcademyInstallment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('overdue', 'معوقه'),
    ]

    enrollment = models.ForeignKey(
        'academy.CourseEnrollment',
        on_delete=models.CASCADE,
        related_name="installments",
        verbose_name="ثبت‌نام"
    )
    amount = models.PositiveIntegerField(verbose_name="مبلغ قسط (تومان)")
    due_date = models.DateField(verbose_name="تاریخ سررسید")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ پرداخت")

    class Meta:
        verbose_name = "قسط شهریه"
        verbose_name_plural = "اقساط شهریه هنرجویان"
        ordering = ['due_date']

    def __str__(self):
        return f"قسط {self.amount:,} تومان — {self.enrollment.student}"
