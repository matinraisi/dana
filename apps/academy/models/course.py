import string
from django.db import models
from django.utils.crypto import get_random_string


def _default_reg_slug():
    return get_random_string(8, string.ascii_lowercase + string.digits)


class Course(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_UPCOMING = 'upcoming'
    STATUS_OPEN = 'open'
    STATUS_FULL = 'full'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'پیش‌نویس'),
        (STATUS_UPCOMING, 'به‌زودی'),
        (STATUS_OPEN, 'ثبت‌نام باز'),
        (STATUS_FULL, 'تکمیل ظرفیت'),
        (STATUS_ACTIVE, 'در حال برگزاری'),
        (STATUS_COMPLETED, 'پایان یافته'),
    ]

    LEVEL_CHOICES = [
        ('beginner', 'مبتدی'),
        ('intermediate', 'متوسط'),
        ('advanced', 'پیشرفته'),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان دوره")
    code = models.CharField(max_length=50, unique=True, verbose_name="کد دوره")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات دوره")
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, default='beginner', verbose_name="سطح دوره"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name="وضعیت"
    )
    teacher = models.ForeignKey(
        'academy.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="استاد دوره",
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE,
        null=True, blank=True, related_name='courses',
        verbose_name="آموزشگاه",
    )
    cover_image = models.ImageField(
        upload_to='courses/covers/', blank=True, null=True, verbose_name="تصویر دوره"
    )
    max_students = models.PositiveIntegerField(
        default=20, verbose_name="حداکثر ظرفیت"
    )
    fee = models.PositiveIntegerField(default=0, verbose_name="شهریه (تومان)")
    start_date = models.DateField(blank=True, null=True, verbose_name="تاریخ شروع")
    end_date = models.DateField(blank=True, null=True, verbose_name="تاریخ پایان")
    prerequisite = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_courses',
        verbose_name="پیش‌نیاز",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    registration_slug = models.CharField(
        unique=True,
        max_length=12,
        default=_default_reg_slug,
        verbose_name="لینک ثبت‌نام عمومی",
        help_text="این کد در URL ثبت‌نام آنلاین استفاده می‌شود",
    )
    allow_public_registration = models.BooleanField(default=False, verbose_name="ثبت‌نام آنلاین")

    class Meta:
        verbose_name = "دوره آموزشی"
        verbose_name_plural = "دوره‌های آموزشی"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} ({self.code})"

    @property
    def total_sessions(self):
        return self.sessions.count()

    @property
    def student_count(self):
        return self.active_enrollments.count()

    @property
    def is_full(self):
        return self.student_count >= self.max_students

    def save(self, *args, **kwargs):
        if self.pk is not None and self.is_full and self.status == self.STATUS_OPEN:
            self.status = self.STATUS_FULL
        super().save(*args, **kwargs)


class Session(models.Model):

    class MeetingType(models.TextChoices):
        NONE = 'none', 'بدون کلاس آنلاین'
        JITSI = 'jitsi', 'جیتسی (Jitsi Meet)'
        GOOGLE_MEET = 'google_meet', 'گوگل میت (Google Meet)'
        ZOOM = 'zoom', 'زوم (Zoom)'
        BBB = 'bigbluebutton', 'بیگ‌بلوباتن (BigBlueButton)'
        CUSTOM = 'custom', 'سایر (لینک دلخواه)'

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="دوره",
    )
    title = models.CharField(max_length=255, verbose_name="عنوان جلسه")
    session_number = models.PositiveIntegerField(verbose_name="شماره جلسه")
    date = models.DateField(verbose_name="تاریخ برگزاری")
    start_time = models.TimeField(blank=True, null=True, verbose_name="ساعت شروع")
    end_time = models.TimeField(blank=True, null=True, verbose_name="ساعت پایان")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="محل برگزاری")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات جلسه")

    meeting_type = models.CharField(
        max_length=20, choices=MeetingType.choices, default=MeetingType.NONE,
        verbose_name="نوع کلاس آنلاین",
    )
    meeting_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="لینک کلاس آنلاین")
    meeting_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه جلسه (اختیاری)")
    meeting_password = models.CharField(max_length=100, blank=True, null=True, verbose_name="رمز جلسه (اختیاری)")

    class Meta:
        verbose_name = "جلسه"
        verbose_name_plural = "جلسات دوره"
        ordering = ['session_number']
        unique_together = ('course', 'session_number')

    def __str__(self):
        return f"جلسه {self.session_number} — {self.course.title}"

    def generate_jitsi_link(self):
        import hashlib
        raw = f"{self.course.school_id}-{self.course.code}-{self.session_number}"
        slug = hashlib.md5(raw.encode()).hexdigest()[:12]
        return f"https://meet.jit.si/academy-{slug}"

    def get_meeting_link(self):
        if self.meeting_link:
            return self.meeting_link
        if self.meeting_type == self.MeetingType.JITSI:
            return self.generate_jitsi_link()
        return None

    def has_online_meeting(self):
        return self.meeting_type != self.MeetingType.NONE
