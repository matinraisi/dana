from django.db import models
from django.conf import settings


class Lead(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONTACTED = 'contacted'
    STATUS_REGISTERED = 'registered'
    STATUS_ENROLLED = 'enrolled'
    STATUS_LOST = 'lost'

    STATUS_CHOICES = [
        (STATUS_NEW, 'جدید'),
        (STATUS_CONTACTED, 'تماس گرفته شده'),
        (STATUS_REGISTERED, 'ثبت‌نام اولیه'),
        (STATUS_ENROLLED, 'ثبت‌نام کامل'),
        (STATUS_LOST, 'از دست رفته'),
    ]

    SOURCE_CHOICES = [
        ('website', 'وب‌سایت'),
        ('instagram', 'اینستاگرام'),
        ('referral', 'معرفی دوست'),
        ('phone', 'تماس تلفنی'),
        ('walk_in', 'مراجعه حضوری'),
        ('other', 'سایر'),
    ]

    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    phone_number = models.CharField(max_length=11, verbose_name="شماره موبایل")
    email = models.EmailField(blank=True, null=True, verbose_name="ایمیل")
    interested_course = models.ForeignKey(
        'academy.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        verbose_name="دوره موردعلاقه",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="وضعیت"
    )
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default='other', verbose_name="منبع"
    )
    note = models.TextField(blank=True, null=True, verbose_name="یادداشت")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        verbose_name="مسئول پیگیری",
    )
    converted_student = models.OneToOneField(
        'academy.StudentEnrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead',
        verbose_name="تبدیل به هنرجو",
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='leads', verbose_name="آموزشگاه",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "سرنخ فروش"
        verbose_name_plural = "مدیریت سرنخ‌ها (CRM)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.get_status_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class LeadActivity(models.Model):
    ACTIVITY_CHOICES = [
        ('call', 'تماس تلفنی'),
        ('sms', 'پیامک'),
        ('meeting', 'جلسه حضوری'),
        ('email', 'ایمیل'),
        ('note', 'یادداشت'),
    ]

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name='activities', verbose_name="سرنخ"
    )
    activity_type = models.CharField(
        max_length=20, choices=ACTIVITY_CHOICES, verbose_name="نوع فعالیت"
    )
    description = models.TextField(verbose_name="شرح")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lead_activities',
        verbose_name="توسط",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ")

    class Meta:
        verbose_name = "فعالیت CRM"
        verbose_name_plural = "فعالیت‌های CRM"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead} — {self.get_activity_type_display()}"
