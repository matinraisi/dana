from django.db import models


class InstallationConfig(models.Model):
    """
    Singleton model holding operational branding and customer configuration
    for this physical installation of AI House EDU.
    """
    organization_name = models.CharField(
        max_length=200,
        default="AI House EDU",
        verbose_name="نام مجموعه",
    )
    logo = models.ImageField(
        upload_to="installation/logos/",
        blank=True,
        null=True,
        verbose_name="لوگو",
    )
    favicon = models.ImageField(
        upload_to="installation/favicons/",
        blank=True,
        null=True,
        verbose_name="فاوآیکون",
    )
    primary_color = models.CharField(
        max_length=10,
        default="#4f46e5",
        verbose_name="رنگ اصلی",
    )
    secondary_color = models.CharField(
        max_length=10,
        default="#06b6d4",
        verbose_name="رنگ فرعی",
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره تماس",
    )
    contact_address = models.TextField(
        blank=True,
        verbose_name="نشانی",
    )
    support_email = models.EmailField(
        blank=True,
        verbose_name="ایمیل پشتیبانی",
    )
    footer_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="متن فوتر",
    )

    class Meta:
        verbose_name = "تنظیمات و برندینگ سامانه"
        verbose_name_plural = "تنظیمات و برندینگ سامانه"

    def __str__(self):
        return self.organization_name

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "organization_name": "AI House EDU",
            },
        )
        return obj
