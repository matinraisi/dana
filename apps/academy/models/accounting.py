from django.db import models
from django.conf import settings


class ExpenseCategory(models.Model):
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE,
        null=True, blank=True, related_name='expense_categories',
        verbose_name='آموزشگاه',
    )
    name = models.CharField(max_length=200, verbose_name="عنوان")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "دسته‌بندی هزینه"
        verbose_name_plural = "دسته‌بندی هزینه‌ها"

    def __str__(self):
        return self.name


class PaymentGateway(models.Model):
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE,
        null=True, blank=True, related_name='payment_gateways',
        verbose_name='آموزشگاه',
    )
    name = models.CharField(max_length=200, verbose_name="نام درگاه/کارت")
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name="شماره کارت")
    account_holder = models.CharField(max_length=200, blank=True, null=True, verbose_name="صاحب حساب")
    gateway_type = models.CharField(
        max_length=20,
        choices=[
            ('pos', 'کارت‌خوان'),
            ('gateway', 'درگاه پرداخت آنلاین'),
            ('card', 'کارت بانکی'),
            ('bank', 'حواله بانکی'),
            ('cash', 'وجه نقد'),
        ],
        default='pos',
        verbose_name="نوع",
    )
    merchant_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="کد درگاه (PIN)")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "درگاه/حساب مالی"
        verbose_name_plural = "درگاه‌ها و حساب‌های مالی"

    def __str__(self):
        return self.name


class PaymentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('success', 'پرداخت موفق'),
        ('failed', 'پرداخت ناموفق'),
    ]

    enrollment = models.ForeignKey(
        'academy.CourseEnrollment', on_delete=models.CASCADE,
        related_name='payment_requests', verbose_name='ثبت‌نام',
    )
    student = models.ForeignKey(
        'academy.StudentEnrollment', on_delete=models.CASCADE,
        related_name='payment_requests', verbose_name='هنرجو',
    )
    amount = models.PositiveIntegerField(verbose_name="مبلغ (تومان)")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="کد تراکنش درگاه")
    authority = models.CharField(max_length=200, blank=True, null=True, verbose_name="کد ارجاع درگاه")
    # شناسهٔ پرداخت در درگاه سان‌تک (pay.sbsuntech.ir). خالی برای پرداخت‌هایی
    # که مستقیم با آقای پرداخت ساخته شده‌اند.
    gateway_payment_id = models.CharField(
        max_length=40, blank=True, null=True, unique=True, verbose_name="شناسهٔ پرداخت در درگاه سان‌تک",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name="شماره کارت پرداخت‌کننده")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "درخواست پرداخت"
        verbose_name_plural = "درخواست‌های پرداخت"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.amount:,} تومان - {self.get_status_display()}"


class AccountingTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'درآمد'),
        ('expense', 'هزینه'),
        ('teacher_payout', 'پرداخت به مدرس'),
        ('refund', 'استرداد'),
        ('transfer', 'انتقال بین حساب'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'نقدی'),
        ('pos', 'کارت‌خوان'),
        ('gateway', 'درگاه آنلاین'),
        ('bank', 'حواله / پایا'),
        ('check', 'چک'),
        ('installment', 'قسط'),
    ]

    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPES, verbose_name="نوع تراکنش"
    )
    amount = models.PositiveIntegerField(verbose_name="مبلغ (تومان)")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name="روش پرداخت"
    )
    payment_gateway = models.ForeignKey(
        PaymentGateway, on_delete= models.SET_NULL, null=True, blank=True,
        verbose_name="درگاه / حساب", related_name="transactions"
    )
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name="شماره کارت (۴ رقم آخر)")

    # --- ارتباط با دوره و هنرجو ---
    course = models.ForeignKey(
        'academy.Course', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="دوره", related_name="transactions"
    )
    student = models.ForeignKey(
        'academy.StudentEnrollment', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="هنرجو", related_name="transactions"
    )
    enrollment = models.ForeignKey(
        'academy.CourseEnrollment', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="ثبت‌نام", related_name="transactions"
    )

    # --- دسته‌بندی هزینه ---
    expense_category = models.ForeignKey(
        ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="دسته هزینه", related_name="transactions"
    )

    # --- مدرس (برای پرداخت به مدرس) ---
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="مدرس", related_name="payout_transactions"
    )

    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    receipt_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="شماره رسید / فیش")
    receipt_image = models.ImageField(
        upload_to='accounting/receipts/', blank=True, null=True, verbose_name="تصویر رسید"
    )

    transaction_date = models.DateField(verbose_name="تاریخ تراکنش")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name="ثبت‌کننده", related_name="created_transactions"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "دفتر کل تراکنش‌های مالی"
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount:,} تومان - {self.created_at.date()}"
