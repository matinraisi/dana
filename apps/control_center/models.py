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


class Customer(models.Model):
    """Sold/installed customer organization tracked by Dana operators."""

    PRODUCT_ACADEMY = "academy"
    PRODUCT_SCHOOL = "school"
    PRODUCT_CHOICES = [
        (PRODUCT_ACADEMY, "آموزشگاه"),
        (PRODUCT_SCHOOL, "مدرسه"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_TRIAL = "trial"
    STATUS_SUSPENDED = "suspended"
    STATUS_CHURNED = "churned"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "فعال"),
        (STATUS_TRIAL, "آزمایشی"),
        (STATUS_SUSPENDED, "معلق"),
        (STATUS_CHURNED, "قطع همکاری"),
    ]

    organization_name = models.CharField(max_length=255, verbose_name="نام مجموعه")
    product_profile = models.CharField(max_length=20, choices=PRODUCT_CHOICES, verbose_name="پروفایل محصول")
    contact_name = models.CharField(max_length=150, verbose_name="نام مسئول")
    phone_number = models.CharField(max_length=11, db_index=True, verbose_name="شماره تماس")
    email = models.EmailField(blank=True, verbose_name="ایمیل")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_TRIAL, db_index=True, verbose_name="وضعیت",
    )
    source_request = models.ForeignKey(
        ProvisioningRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
        verbose_name="درخواست مبدأ",
    )
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization_name} ({self.get_product_profile_display()})"


class License(models.Model):
    """Manual license / subscription record for an instance."""

    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_GRACE = "grace"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "فعال"),
        (STATUS_EXPIRED, "منقضی"),
        (STATUS_GRACE, "مهلت"),
        (STATUS_REVOKED, "باطل"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="licenses", verbose_name="مشتری")
    license_key = models.CharField(max_length=64, unique=True, verbose_name="کلید لایسنس")
    plan_name = models.CharField(max_length=100, default="standard", verbose_name="پلن")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True, verbose_name="وضعیت")
    starts_at = models.DateField(verbose_name="شروع")
    ends_at = models.DateField(null=True, blank=True, verbose_name="پایان")
    max_users = models.PositiveIntegerField(default=0, help_text="۰ = نامحدود", verbose_name="سقف کاربر")
    website_enabled = models.BooleanField(default=True, verbose_name="وب‌سایت فعال")
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "لایسنس"
        verbose_name_plural = "لایسنس‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.organization_name} — {self.license_key}"


class InstallRecord(models.Model):
    """Inventory of a physical customer instance + manual provisioning checklist."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="installs", verbose_name="مشتری")
    domain = models.CharField(max_length=255, verbose_name="دامنه")
    panel_url = models.URLField(blank=True, verbose_name="آدرس پنل")
    server_host = models.CharField(max_length=255, blank=True, verbose_name="سرور / هاست")
    product_mode = models.CharField(max_length=20, verbose_name="PRODUCT_MODE")
    app_version = models.CharField(max_length=64, blank=True, verbose_name="نسخه نصب‌شده")
    database_note = models.CharField(max_length=255, blank=True, verbose_name="یادداشت دیتابیس")
    # Manual checklist (no auto-provisioning yet)
    checklist_dns = models.BooleanField(default=False, verbose_name="DNS تنظیم شد")
    checklist_ssl = models.BooleanField(default=False, verbose_name="SSL فعال شد")
    checklist_env = models.BooleanField(default=False, verbose_name=".env پیکربندی شد")
    checklist_migrate = models.BooleanField(default=False, verbose_name="migrate اجرا شد")
    checklist_admin = models.BooleanField(default=False, verbose_name="ادمین اولیه ساخته شد")
    checklist_sms = models.BooleanField(default=False, verbose_name="پیامک تست شد")
    checklist_payment = models.BooleanField(default=False, verbose_name="پرداخت تست شد")
    checklist_handover = models.BooleanField(default=False, verbose_name="تحویل به مشتری")
    install_notes = models.TextField(blank=True, verbose_name="یادداشت نصب")
    last_upgraded_at = models.DateField(null=True, blank=True, verbose_name="آخرین ارتقا")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "نصب Instance"
        verbose_name_plural = "نصب‌های Instance"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.organization_name} @ {self.domain}"

    @property
    def checklist_progress(self):
        flags = [
            self.checklist_dns, self.checklist_ssl, self.checklist_env,
            self.checklist_migrate, self.checklist_admin, self.checklist_sms,
            self.checklist_payment, self.checklist_handover,
        ]
        done = sum(1 for f in flags if f)
        return done, len(flags)
