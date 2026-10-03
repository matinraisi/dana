from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academy', '0021_session_location'),
        ('schools', '0002_school_add_is_default'),
        ('users', '0005_teacher_card_number_teacher_shaba_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='کد تخفیف', help_text='کد یکتا برای استفاده در فرم ثبت‌نام')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='توضیحات')),
                ('discount_type', models.CharField(choices=[('percent', 'درصدی'), ('fixed', 'مبلغ ثابت')], default='percent', max_length=10, verbose_name='نوع تخفیف')),
                ('discount_value', models.PositiveIntegerField(verbose_name='مقدار تخفیف', help_text='درصد (۱ تا ۱۰۰) یا مبلغ ثابت به تومان')),
                ('max_uses', models.PositiveIntegerField(default=0, verbose_name='حداکثر دفعات استفاده', help_text='۰ = بدون محدودیت')),
                ('used_count', models.PositiveIntegerField(default=0, verbose_name='دفعات استفاده شده')),
                ('min_amount', models.PositiveIntegerField(default=0, verbose_name='حداقل مبلغ سفارش', help_text='تخفیف فقط روی سفارش‌های بالاتر از این مبلغ اعمال می‌شود')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('valid_from', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ شروع')),
                ('valid_until', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ پایان')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='discount_codes', to='academy.course', verbose_name='دوره خاص', help_text='اگر خالی باشد، روی همه دوره‌ها اعمال می‌شود')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_discount_codes', to=settings.AUTH_USER_MODEL, verbose_name='ایجادکننده')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='discount_codes', to='schools.school', verbose_name='آموزشگاه')),
            ],
            options={
                'verbose_name': 'کد تخفیف',
                'verbose_name_plural': 'کدهای تخفیف',
                'ordering': ['-created_at'],
            },
        ),
    ]
