from django.db import models
from django.conf import settings
import string
from django.utils.crypto import get_random_string


def _default_slug():
    while True:
        s = get_random_string(8, string.ascii_lowercase + string.digits)
        if not School.objects.filter(slug=s).exists():
            return s


class School(models.Model):
    title = models.CharField(max_length=255, verbose_name="نام آموزشگاه / مدرسه")
    slug = models.SlugField(unique=True, default=_default_slug, verbose_name="شناسه یکتا")
    subdomain = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="زیردامنه (مثال: my-school)")
    domain = models.CharField(max_length=255, unique=True, blank=True, null=True, verbose_name="دامنه اختصاصی (مثال: my-school.com)")
    logo = models.ImageField(upload_to='schools/logos/', blank=True, null=True, verbose_name="لوگو")
    favicon = models.ImageField(upload_to='schools/favicons/', blank=True, null=True, verbose_name="فاوآیکون")
    primary_color = models.CharField(max_length=7, default='#2563eb', verbose_name="رنگ اصلی (hex)")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن تماس")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=False, verbose_name="فعال / تأیید شده")
    is_default = models.BooleanField(default=False, verbose_name="آموزشگاه پیش‌فرض (صفحه لاگین)")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='owned_schools', verbose_name="مدیر / مالک آموزشگاه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "آموزشگاه"
        verbose_name_plural = "مدیریت آموزشگاه‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
