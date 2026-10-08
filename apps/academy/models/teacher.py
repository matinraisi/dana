from django.conf import settings
from django.db import models


class Teacher(models.Model):
    """Academy teacher profile — domain-owned by the Academy product."""

    SESSION_DURATION_HOURS = 1.5

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name="حساب کاربری",
    )
    bio = models.TextField(blank=True, null=True, verbose_name="بیوگرافی")
    specialization = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="تخصص"
    )
    national_code = models.CharField(
        max_length=10, blank=True, null=True, unique=True, verbose_name="کد ملی"
    )
    phone_number = models.CharField(
        max_length=11, blank=True, null=True, verbose_name="شماره تماس"
    )
    card_number = models.CharField(
        max_length=16, blank=True, null=True, verbose_name="شماره کارت بانکی"
    )
    shaba_number = models.CharField(
        max_length=24, blank=True, null=True, verbose_name="شماره شبا"
    )
    hire_date = models.DateField(blank=True, null=True, verbose_name="تاریخ استخدام")
    salary_per_session = models.PositiveIntegerField(
        default=0, verbose_name="دستمزد هر جلسه (تومان)"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "استاد"
        verbose_name_plural = "مدیریت اساتید"
        # Preserve existing physical table from users.Teacher
        db_table = 'users_teacher'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def total_earnings(self):
        from django.db.models import Sum

        from .student import CourseEnrollment

        return (
            CourseEnrollment.objects.filter(course__teacher=self)
            .aggregate(t=Sum('paid_amount'))['t'] or 0
        )

    @property
    def total_sessions(self):
        from .course import Session

        return Session.objects.filter(course__teacher=self).count()

    @property
    def total_hours(self):
        return self.total_sessions * self.SESSION_DURATION_HOURS

    @property
    def total_salary_due(self):
        return self.total_sessions * self.salary_per_session

    @property
    def hourly_rate(self):
        if self.salary_per_session:
            return round(self.salary_per_session / self.SESSION_DURATION_HOURS)
        return 0
