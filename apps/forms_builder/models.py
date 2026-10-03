from django.db import models
from django.conf import settings
import uuid


class DynamicForm(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان فرم")
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, verbose_name="شناسه URL")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_forms',
        verbose_name="ایجادکننده",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_public = models.BooleanField(default=True, verbose_name="عمومی")
    requires_login = models.BooleanField(default=False, verbose_name="نیاز به ورود")
    one_response_per_user = models.BooleanField(default=False, verbose_name="یک پاسخ در هر کاربر")
    submit_message = models.TextField(
        default="پاسخ شما ثبت شد. ممنون از شما!",
        verbose_name="پیام پس از ارسال",
    )
    linked_course = models.ForeignKey(
        'academy.Course',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='forms',
        verbose_name="دوره مرتبط",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "فرم دینامیک"
        verbose_name_plural = "فرم‌های دینامیک"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def response_count(self):
        return self.submissions.count()


class FormField(models.Model):
    FIELD_TYPES = [
        ('text', 'متن کوتاه'),
        ('textarea', 'متن بلند'),
        ('number', 'عدد'),
        ('email', 'ایمیل'),
        ('phone', 'موبایل'),
        ('select', 'انتخاب از لیست'),
        ('radio', 'انتخاب تکی'),
        ('checkbox', 'چندانتخابی'),
        ('date', 'تاریخ'),
        ('file', 'بارگذاری فایل'),
        ('rating', 'امتیازدهی'),
        ('heading', 'عنوان / تیتر'),
        ('paragraph', 'متن توضیحی'),
    ]

    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='fields')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, verbose_name="نوع فیلد")
    label = models.CharField(max_length=200, verbose_name="برچسب")
    placeholder = models.CharField(max_length=200, blank=True, verbose_name="متن راهنما")
    help_text = models.CharField(max_length=300, blank=True, verbose_name="متن کمکی")
    is_required = models.BooleanField(default=False, verbose_name="اجباری")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    options = models.TextField(
        blank=True,
        help_text="گزینه‌ها را با خط جدید جدا کنید (برای select، radio، checkbox)",
        verbose_name="گزینه‌ها",
    )
    max_length = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر طول")
    min_value = models.FloatField(null=True, blank=True, verbose_name="حداقل مقدار")
    max_value = models.FloatField(null=True, blank=True, verbose_name="حداکثر مقدار")

    class Meta:
        verbose_name = "فیلد فرم"
        verbose_name_plural = "فیلدهای فرم"
        ordering = ['order']

    def __str__(self):
        return f"{self.form.title} — {self.label}"

    def get_options_list(self):
        return [opt.strip() for opt in self.options.splitlines() if opt.strip()]


class FormSubmission(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='form_submissions',
        verbose_name="کاربر",
    )
    submission_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پاسخ فرم"
        verbose_name_plural = "پاسخ‌های فرم"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.form.title} — {self.submission_id}"


class FieldResponse(models.Model):
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='responses')
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='responses')
    value = models.TextField(blank=True, verbose_name="پاسخ")
    file_upload = models.FileField(upload_to='form_uploads/', null=True, blank=True, verbose_name="فایل")

    class Meta:
        verbose_name = "پاسخ فیلد"
        verbose_name_plural = "پاسخ‌های فیلد"

    def __str__(self):
        return f"{self.field.label}: {self.value[:50]}"
