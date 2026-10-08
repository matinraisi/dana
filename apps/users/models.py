import random

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Kernel auth user. Product-domain profiles live outside this app."""

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
        return self.role in ('OWNER', 'PARTNER', 'MANAGER_ACADEMY', 'MANAGER_COMPANY')

    @property
    def is_school_user(self):
        return self.role in ('SCHOOL_ADMIN', 'SCHOOL_TEACHER', 'SCHOOL_STUDENT', 'SCHOOL_GUARDIAN')


class OTPToken(models.Model):
    """One-time login code — kernel auth primitive."""

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
        return age <= 300
