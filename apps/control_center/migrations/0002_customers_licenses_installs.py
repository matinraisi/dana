from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('control_center', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_name', models.CharField(max_length=255, verbose_name='نام مجموعه')),
                ('product_profile', models.CharField(choices=[('academy', 'آموزشگاه'), ('school', 'مدرسه')], max_length=20, verbose_name='پروفایل محصول')),
                ('contact_name', models.CharField(max_length=150, verbose_name='نام مسئول')),
                ('phone_number', models.CharField(db_index=True, max_length=11, verbose_name='شماره تماس')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='ایمیل')),
                ('status', models.CharField(choices=[('active', 'فعال'), ('trial', 'آزمایشی'), ('suspended', 'معلق'), ('churned', 'قطع همکاری')], db_index=True, default='trial', max_length=20, verbose_name='وضعیت')),
                ('notes', models.TextField(blank=True, verbose_name='یادداشت')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین تغییر')),
                ('source_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customers', to='control_center.provisioningrequest', verbose_name='درخواست مبدأ')),
            ],
            options={
                'verbose_name': 'مشتری',
                'verbose_name_plural': 'مشتریان',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_key', models.CharField(max_length=64, unique=True, verbose_name='کلید لایسنس')),
                ('plan_name', models.CharField(default='standard', max_length=100, verbose_name='پلن')),
                ('status', models.CharField(choices=[('active', 'فعال'), ('expired', 'منقضی'), ('grace', 'مهلت'), ('revoked', 'باطل')], db_index=True, default='active', max_length=20, verbose_name='وضعیت')),
                ('starts_at', models.DateField(verbose_name='شروع')),
                ('ends_at', models.DateField(blank=True, null=True, verbose_name='پایان')),
                ('max_users', models.PositiveIntegerField(default=0, help_text='۰ = نامحدود', verbose_name='سقف کاربر')),
                ('website_enabled', models.BooleanField(default=True, verbose_name='وب‌سایت فعال')),
                ('notes', models.TextField(blank=True, verbose_name='یادداشت')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='licenses', to='control_center.customer', verbose_name='مشتری')),
            ],
            options={
                'verbose_name': 'لایسنس',
                'verbose_name_plural': 'لایسنس‌ها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InstallRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255, verbose_name='دامنه')),
                ('panel_url', models.URLField(blank=True, verbose_name='آدرس پنل')),
                ('server_host', models.CharField(blank=True, max_length=255, verbose_name='سرور / هاست')),
                ('product_mode', models.CharField(max_length=20, verbose_name='PRODUCT_MODE')),
                ('app_version', models.CharField(blank=True, max_length=64, verbose_name='نسخه نصب‌شده')),
                ('database_note', models.CharField(blank=True, max_length=255, verbose_name='یادداشت دیتابیس')),
                ('checklist_dns', models.BooleanField(default=False, verbose_name='DNS تنظیم شد')),
                ('checklist_ssl', models.BooleanField(default=False, verbose_name='SSL فعال شد')),
                ('checklist_env', models.BooleanField(default=False, verbose_name='.env پیکربندی شد')),
                ('checklist_migrate', models.BooleanField(default=False, verbose_name='migrate اجرا شد')),
                ('checklist_admin', models.BooleanField(default=False, verbose_name='ادمین اولیه ساخته شد')),
                ('checklist_sms', models.BooleanField(default=False, verbose_name='پیامک تست شد')),
                ('checklist_payment', models.BooleanField(default=False, verbose_name='پرداخت تست شد')),
                ('checklist_handover', models.BooleanField(default=False, verbose_name='تحویل به مشتری')),
                ('install_notes', models.TextField(blank=True, verbose_name='یادداشت نصب')),
                ('last_upgraded_at', models.DateField(blank=True, null=True, verbose_name='آخرین ارتقا')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installs', to='control_center.customer', verbose_name='مشتری')),
            ],
            options={
                'verbose_name': 'نصب Instance',
                'verbose_name_plural': 'نصب‌های Instance',
                'ordering': ['-created_at'],
            },
        ),
    ]
