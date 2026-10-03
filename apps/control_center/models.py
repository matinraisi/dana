from django.db import models


class ProvisioningRequest(models.Model):
    """A sales/onboarding request, never an operational customer tenant."""

    PRODUCT_ACADEMY = "academy"
    PRODUCT_SCHOOL = "school"
    PRODUCT_CHOICES = [
        (PRODUCT_ACADEMY, "آموزشگاه"),
        (PRODUCT_SCHOOL, "مدرسه"),
    ]

    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_DEMO = "demo"
    STATUS_PROVISIONING = "provisioning"
    STATUS_DELIVERED = "delivered"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_NEW, "جدید"),
        (STATUS_CONTACTED, "تماس گرفته شد"),
        (STATUS_DEMO, "دمو"),
        (STATUS_PROVISIONING, "در حال راه‌اندازی"),
        (STATUS_DELIVERED, "تحویل شد"),
        (STATUS_REJECTED, "رد شد"),
    ]

    organization_name = models.CharField(max_length=255, verbose_name="نام مجموعه")
    contact_name = models.CharField(max_length=150, verbose_name="نام مسئول")
    phone_number = models.CharField(max_length=11, db_index=True, verbose_name="شماره تماس")
    email = models.EmailField(blank=True, verbose_name="ایمیل")
    requested_product = models.CharField(
        max_length=20,
        choices=PRODUCT_CHOICES,
        verbose_name="محصول درخواستی",
    )
    message = models.TextField(blank=True, verbose_name="توضیحات درخواست")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
        verbose_name="وضعیت",
    )
    internal_note = models.TextField(blank=True, verbose_name="یادداشت داخلی")
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان اطلاع‌رسانی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        verbose_name = "درخواست راه‌اندازی"
        verbose_name_plural = "درخواست‌های راه‌اندازی"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization_name} — {self.get_requested_product_display()}"
