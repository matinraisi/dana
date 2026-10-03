import string
from django.db import models
from django.utils.crypto import get_random_string
from .course import Course


class StudentEnrollment(models.Model):
    DOCUMENT_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('verified', 'تأیید شده'),
        ('rejected', 'نقص مدارک'),
    ]
    EDUCATION_CHOICES = [
        ('under_diploma', 'زیر دیپلم'),
        ('diploma', 'دیپلم'),
        ('associate', 'فوق دیپلم'),
        ('bachelor', 'کارشناسی'),
        ('master', 'کارشناسی ارشد'),
        ('phd', 'دکتری'),
    ]

    # --- هویت ---
    first_name = models.CharField(max_length=150, verbose_name="نام")
    last_name = models.CharField(max_length=150, verbose_name="نام خانوادگی")
    national_code = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="شماره موبایل")
    emergency_phone = models.CharField(
        max_length=11, blank=True, null=True, verbose_name="شماره اضطراری"
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="تاریخ تولد")
    address = models.TextField(blank=True, null=True, verbose_name="آدرس")

    # --- تحصیلی ---
    field_of_study = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="رشته تحصیلی"
    )
    education_level = models.CharField(
        max_length=30, choices=EDUCATION_CHOICES, blank=True, null=True, verbose_name="مقطع تحصیلی"
    )

    # --- مدارک ---
    avatar_3x4 = models.ImageField(
        upload_to='students/avatars/', blank=True, null=True, verbose_name="عکس ۳×۴"
    )
    national_card_img = models.ImageField(
        upload_to='students/documents/', blank=True, null=True, verbose_name="کارت ملی"
    )
    identity_img = models.ImageField(
        upload_to='students/documents/', blank=True, null=True, verbose_name="شناسنامه"
    )
    document_status = models.CharField(
        max_length=20, choices=DOCUMENT_CHOICES, default='pending', verbose_name="وضعیت مدارک"
    )
    document_rejection_reason = models.TextField(
        blank=True, null=True, verbose_name="علت رد مدارک"
    )
    is_documents_approved = models.BooleanField(
        default=False, verbose_name="تأیید مدارک"
    )

    # --- آموزشگاه ---
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE,
        null=True, blank=True, related_name='students',
        verbose_name="آموزشگاه",
    )
    # --- دوره‌ها ---
    courses = models.ManyToManyField(
        Course, through='CourseEnrollment', related_name="students", verbose_name="دوره‌ها"
    )

    # --- شناسه یکتا ---
    short_slug = models.SlugField(
        max_length=10, unique=True, blank=True, verbose_name="لینک کوتاه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "هنرجو"
        verbose_name_plural = "مدیریت هنرجویان"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        self.is_documents_approved = (self.document_status == 'verified')
        if not self.short_slug:
            while True:
                code = get_random_string(
                    length=6, allowed_chars=string.ascii_lowercase + string.digits
                )
                if not StudentEnrollment.objects.filter(short_slug=code).exists():
                    self.short_slug = code
                    break
        super().save(*args, **kwargs)


class CourseEnrollment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقدی / یکجا'),
        ('installment', 'اقساطی'),
        ('unpaid', 'بدهکار / بدون پرداخت'),
    ]

    student = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="active_enrollments",
        verbose_name="هنرجو",
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="active_enrollments", verbose_name="دوره"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='unpaid',
        verbose_name="نوع پرداخت",
    )
    total_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ کل (تومان)")
    paid_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ پرداختی (تومان)")
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت‌نام")

    class Meta:
        verbose_name = "ثبت‌نام دوره"
        verbose_name_plural = "جزئیات ثبت‌نام دوره‌ها"
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} — {self.course.title}"

    @property
    def remaining_amount(self):
        return max(0, self.total_amount - self.paid_amount)

    @property
    def is_fully_paid(self):
        return self.total_amount > 0 and self.remaining_amount == 0

    def update_paid_amount(self):
        total_paid = sum(inst.amount for inst in self.installments.filter(status='paid'))
        self.paid_amount = total_paid
        if self.remaining_amount == 0 and self.total_amount > 0:
            self.payment_method = 'cash'
        elif self.paid_amount > 0:
            self.payment_method = 'installment'
        self.save()
