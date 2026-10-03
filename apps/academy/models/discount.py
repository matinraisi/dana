import string
from django.db import models
from django.utils.crypto import get_random_string
from django.core.validators import MinValueValidator, MaxValueValidator


class DiscountCode(models.Model):
    TYPE_CHOICES = [
        ('percent', 'درصدی'),
        ('fixed', 'مبلغ ثابت'),
    ]

    code = models.CharField(
        max_length=20, unique=True, verbose_name="کد تخفیف",
        help_text="کد یکتا برای استفاده در فرم ثبت‌نام"
    )
    description = models.CharField(max_length=255, blank=True, verbose_name="توضیحات")
    discount_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default='percent', verbose_name="نوع تخفیف"
    )
    discount_value = models.PositiveIntegerField(
        verbose_name="مقدار تخفیف",
        help_text="درصد (۱ تا ۱۰۰) یا مبلغ ثابت به تومان"
    )
    max_uses = models.PositiveIntegerField(
        default=0, verbose_name="حداکثر دفعات استفاده",
        help_text="۰ = بدون محدودیت"
    )
    used_count = models.PositiveIntegerField(default=0, verbose_name="دفعات استفاده شده")
    min_amount = models.PositiveIntegerField(
        default=0, verbose_name="حداقل مبلغ سفارش",
        help_text="تخفیف فقط روی سفارش‌های بالاتر از این مبلغ اعمال می‌شود"
    )
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, null=True, blank=True,
        related_name='discount_codes', verbose_name="دوره خاص",
        help_text="اگر خالی باشد، روی همه دوره‌ها اعمال می‌شود"
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, null=True, blank=True,
        related_name='discount_codes', verbose_name="آموزشگاه"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ شروع")
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پایان")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True,
        related_name='created_discount_codes', verbose_name="ایجادکننده"
    )

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} — {self.get_discount_type_display()} {self.discount_value}"

    @property
    def is_valid(self):
        """بررسی اعتبار کد تخفیف"""
        from django.utils import timezone
        now = timezone.now()

        if not self.is_active:
            return False, "کد تخفیف غیرفعال است"

        if self.valid_from and now < self.valid_from:
            return False, "کد تخفیف هنوز فعال نشده"

        if self.valid_until and now > self.valid_until:
            return False, "کد تخفیف منقضی شده"

        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False, "حداکثر دفعات استفاده رسیده"

        return True, "کد معتبر"

    def calculate_discount(self, amount):
        """محاسبه مبلغ تخفیف"""
        if self.discount_type == 'percent':
            return int(amount * self.discount_value / 100)
        else:
            return min(self.discount_value, amount)

    def apply(self):
        """ثبت استفاده از کد"""
        self.used_count += 1
        self.save(update_fields=['used_count'])

    @staticmethod
    def generate_code(length=8):
        """تولید کد تصادفی"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = get_random_string(length, chars)
            if not DiscountCode.objects.filter(code=code).exists():
                return code
