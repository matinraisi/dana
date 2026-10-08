from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string
import string


def _default_slug():
    while True:
        s = get_random_string(8, string.ascii_lowercase + string.digits)
        if not School.objects.filter(slug=s).exists():
            return s


class School(models.Model):
    """Canonical Academy Organization for this instance.

    Deployment model: one customer → one instance → one database → one org.
    One organization per Academy instance.
    """

    title = models.CharField(max_length=255, verbose_name="نام سازمان آموزشگاه")
    slug = models.SlugField(unique=True, default=_default_slug, verbose_name="شناسه یکتا")
    logo = models.ImageField(upload_to='schools/logos/', blank=True, null=True, verbose_name="لوگو")
    favicon = models.ImageField(upload_to='schools/favicons/', blank=True, null=True, verbose_name="فاوآیکون")
    primary_color = models.CharField(max_length=7, default='#2563eb', verbose_name="رنگ اصلی (hex)")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن تماس")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_schools',
        verbose_name="مدیر / مالک آموزشگاه",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "سازمان آموزشگاه"
        verbose_name_plural = "سازمان آموزشگاه"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        # Exactly one organization row per Academy instance.
        others = School.objects.exclude(pk=self.pk) if self.pk else School.objects.all()
        if others.exists():
            raise ValidationError(
                'این Instance فقط یک سازمان آموزشگاه می‌تواند داشته باشد.'
            )

    def save(self, *args, **kwargs):
        others = School.objects.exclude(pk=self.pk) if self.pk else School.objects.all()
        if others.exists():
            raise ValidationError(
                'این Instance فقط یک سازمان آموزشگاه می‌تواند داشته باشد.'
            )
        # Singleton instance always stays the active org.
        self.is_active = True
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Return the single Academy Organization for this instance, or None."""
        return cls.objects.filter(is_active=True).first() or cls.objects.first()
