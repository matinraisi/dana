from django.db import models
from apps.core.models import BusinessUnit, User
from apps.crm.models import Lead
import uuid

class Transaction(models.Model):
    TRANSACTION_TYPE = (('INCOME', 'درآمد'), ('EXPENSE', 'هزینه'))
    STATUS_CHOICES = (
        ('DRAFT', 'پیش‌نویس'), ('PENDING', 'در انتظار پرداخت'),
        ('PAID', 'پرداخت شده'), ('CANCELLED', 'لغو شده'),
    )

    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.CASCADE, verbose_name="مربوط به کسب‌وکار")
    title = models.CharField(max_length=255, verbose_name="عنوان تراکنش")
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE, verbose_name="نوع")
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="مبلغ (تومان)")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT', verbose_name="وضعیت")
    due_date = models.DateField(null=True, blank=True, verbose_name="تاریخ سررسید")
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to="transactions/", null=True, blank=True, verbose_name="پیوست")

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"

    def __str__(self):
        return f"{self.title} - {self.amount}"

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'پیش‌نویس'), ('SENT', 'ارسال شده'),
        ('PAID', 'پرداخت شده'), ('CANCELLED', 'لغو شده'),
    )
    
    client = models.ForeignKey('crm.Lead', on_delete=models.CASCADE, verbose_name="مشتری")
    business_unit = models.ForeignKey(
            "core.BusinessUnit", 
            on_delete=models.CASCADE, 
            verbose_name="واحد صادرکننده"
        )
    title = models.CharField(max_length=255, verbose_name="عنوان فاکتور")
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="شماره فاکتور", blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="مبلغ کل (تومان)")
    is_paid = models.BooleanField(default=False, verbose_name="تسویه شده")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True, verbose_name="مهلت پرداخت")
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # ایجاد شماره فاکتور بر اساس نام واحد تجاری و یک کد رندوم
            prefix = self.business_unit.name[:3].upper() if self.business_unit else "INV"
            self.invoice_number = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        
        # حتما args و kwargs را به این شکل پاس دهید
        super(Invoice, self).save(*args, **kwargs)
    def update_total(self):
        """محاسبه مجموع ردیف‌های فاکتور"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    description = models.CharField(max_length=255, verbose_name="شرح خدمات/کالا")
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد/مقدار")
    unit_price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="قیمت واحد")

    @property
    def total_price(self):
        return self.quantity * self.unit_price