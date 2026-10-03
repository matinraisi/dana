from django.db import models


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'حاضر'),
        ('absent', 'غایب'),
        ('excused', 'غیبت موجه'),
        ('late', 'تأخیر'),
    ]

    session = models.ForeignKey(
        'academy.Session',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="جلسه"
    )
    student = models.ForeignKey(
        'academy.StudentEnrollment',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="هنرجو"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='absent',
        verbose_name="وضعیت"
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name="یادداشت")
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "حضور و غیاب"
        verbose_name_plural = "حضور و غیاب"
        unique_together = ('session', 'student')
        ordering = ['-session__date']

    def __str__(self):
        return f"{self.student} - {self.session} - {self.get_status_display()}"