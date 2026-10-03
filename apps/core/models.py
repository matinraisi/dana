from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class BusinessUnit(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام واحد تجاری")
    logo = models.ImageField(upload_to="branding/logos/", verbose_name="لوگو")
    signature = models.ImageField(upload_to="branding/signatures/", verbose_name="تصویر امضا/مهر")
    primary_color = models.CharField(max_length=7, default="#a855f7", verbose_name="رنگ اصلی (HEX)")
    invoice_header = models.ImageField(upload_to="branding/headers/", null=True, blank=True, verbose_name="تصویر سربرگ فاکتور")
    # سایر فیلدها مثل آدرس و تلفن مخصوص هر واحد
    address = models.TextField(verbose_name="آدرس واحد", blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    businesses = models.ManyToManyField(BusinessUnit, related_name="users", blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

class Partner(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کاربر")
    share_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="درصد سهم (مثلا ۳۳.۳)",
        verbose_name="درصد شراکت"
    )

    class Meta:
        verbose_name = "شریک"
        verbose_name_plural = "شرکا"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.share_percentage}%)"

class Project(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'در حال برنامه‌ریزی'),
        ('ACTIVE', 'فعال'),
        ('COMPLETED', 'تکمیل شده'),
    ]
    
    title = models.CharField(max_length=255, verbose_name="نام پروژه")
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, verbose_name="واحد تجاری")
    client = models.ForeignKey('crm.Lead', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مشتری مرتبط")    
    description = models.TextField(verbose_name="توضیحات پروژه")
    start_date = models.DateField(verbose_name="تاریخ شروع")
    deadline = models.DateField(verbose_name="مهلت نهایی")
    total_budget = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="بودجه کل (درآمد)")
    total_expenses = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="مجموع هزینه‌ها")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING', verbose_name="وضعیت")
    is_active = models.BooleanField(default=True, verbose_name="نمایش در نمونه‌کارها")
    image = models.ImageField(upload_to="projects/", null=True, blank=True, verbose_name="تصویر اصلی نمونه‌کار")

    class Meta:
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"

    def __str__(self):
        return self.title

    @property
    def net_profit(self):
        return self.total_budget - self.total_expenses

    def distribute_profit(self):
        if self.status == 'COMPLETED' and self.total_budget > 0:
            profit = self.net_profit 
            partners = Partner.objects.all()
            for partner in partners:
                share_amount = (profit * partner.share_percentage) / 100
                PartnerRevenue.objects.update_or_create(
                    project=self,
                    partner=partner,
                    defaults={'amount': share_amount}
                )

class PartnerRevenue(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, verbose_name="شریک")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, verbose_name="پروژه")
    invoice = models.ForeignKey(
        "accounting.Invoice", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="فاکتور"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="مبلغ سهم")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "سهم سود شریک"
        verbose_name_plural = "سهم سود شرکا"
        
    def save(self, *args, **kwargs):
        # حذف کدهای مربوط به Invoice و اصلاح super
        super(PartnerRevenue, self).save(*args, **kwargs)

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'کم'),
        ('MEDIUM', 'متوسط'),
        ('HIGH', 'فوری'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="پروژه")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="مسئول تسک")
    title = models.CharField(max_length=255, verbose_name="عنوان وظیفه")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name="اولویت")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    due_date = models.DateField(verbose_name="فرصت انجام")

    class Meta:
        verbose_name = "وظیفه"
        verbose_name_plural = "وظایف"

class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="files", verbose_name="پروژه")
    title = models.CharField(max_length=255, verbose_name="عنوان فایل")
    file = models.FileField(upload_to="project_assets/%Y/%m/", verbose_name="فایل")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "فایل پروژه"
        verbose_name_plural = "فایل‌های پروژه"