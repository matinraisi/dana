from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
import random


class User(AbstractUser):
    ROLE_CHOICES = [
        ('OWNER', 'صاحب کسب‌وکار / مدیر کل'),
        ('PARTNER', 'شریک تجاری'),
        ('MANAGER_ACADEMY', 'مدیر آکادمی'),
        ('MANAGER_COMPANY', 'مدیر شرکت فنی'),
        ('TEACHER', 'استاد / مدرس'),
        ('STUDENT', 'هنرجو'),
        ('SCHOOL_ADMIN', 'مدیر مدرسه'),
        ('SCHOOL_TEACHER', 'دبیر مدرسه'),
        ('SCHOOL_STUDENT', 'دانش‌آموز'),
        ('SCHOOL_GUARDIAN', 'ولی دانش‌آموز'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='OWNER',
        verbose_name="نقش کاربری",
    )
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="شماره تماس"
    )
    profile_image = models.ImageField(
        upload_to="profiles/", null=True, blank=True, verbose_name="تصویر پروفایل"
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users', verbose_name="آموزشگاه"
    )

    class Meta:
        verbose_name = "کاربر پنل"
        verbose_name_plural = "کاربران پنل"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_teacher(self):
        return self.role == 'TEACHER'

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    @property
    def is_admin_staff(self):
        return self.role in ('OWNER', 'PARTNER', 'MANAGER_ACADEMY', 'MANAGER_COMPANY', 'SCHOOL_ADMIN')

    @property
    def is_school_user(self):
        return self.role in ('SCHOOL_ADMIN', 'SCHOOL_TEACHER', 'SCHOOL_STUDENT', 'SCHOOL_GUARDIAN')


class Teacher(models.Model):
    """پروفایل استاد — لینک شده به حساب کاربری سیستم"""
    SESSION_DURATION_HOURS = 1.5

    user = models.OneToOneField(
        User,
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

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def total_earnings(self):
        from apps.academy.models import CourseEnrollment
        from django.db.models import Sum
        return (
            CourseEnrollment.objects.filter(course__teacher=self)
            .aggregate(t=Sum('paid_amount'))['t'] or 0
        )

    @property
    def total_sessions(self):
        from apps.academy.models import Session
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


class StudentAccount(models.Model):
    """حساب کاربری هنرجو برای ورود به پنل شخصی"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_account',
        verbose_name="حساب کاربری",
    )
    enrollment = models.OneToOneField(
        'academy.StudentEnrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        verbose_name="پرونده هنرجو",
    )

    class Meta:
        verbose_name = "حساب هنرجو"
        verbose_name_plural = "حساب‌های هنرجویان"

    def __str__(self):
        return f"حساب: {self.user.username}"


class OTPToken(models.Model):
    """کد یکبارمصرف برای ورود با موبایل"""
    phone_number = models.CharField(max_length=15, verbose_name="شماره موبایل")
    code = models.CharField(max_length=6, verbose_name="کد")
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "کد یکبارمصرف"
        verbose_name_plural = "کدهای یکبارمصرف"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} — {self.code}"

    @staticmethod
    def generate(phone_number: str) -> 'OTPToken':
        OTPToken.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
        code = str(random.randint(100000, 999999))
        return OTPToken.objects.create(phone_number=phone_number, code=code)

    def is_valid(self) -> bool:
        if self.is_used:
            return False
        age = (timezone.now() - self.created_at).total_seconds()
        return age <= 300  # 5 minutes
