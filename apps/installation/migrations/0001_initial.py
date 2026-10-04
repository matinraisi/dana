from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InstallationConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_name', models.CharField(default='AI House EDU', max_length=200, verbose_name='نام مجموعه')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='installation/logos/', verbose_name='لوگو')),
                ('favicon', models.ImageField(blank=True, null=True, upload_to='installation/favicons/', verbose_name='فاوآیکون')),
                ('primary_color', models.CharField(default='#4f46e5', max_length=10, verbose_name='رنگ اصلی')),
                ('secondary_color', models.CharField(default='#06b6d4', max_length=10, verbose_name='رنگ فرعی')),
                ('contact_phone', models.CharField(blank=True, max_length=20, verbose_name='شماره تماس')),
                ('contact_address', models.TextField(blank=True, verbose_name='نشانی')),
                ('support_email', models.EmailField(blank=True, max_length=254, verbose_name='ایمیل پشتیبانی')),
                ('footer_text', models.CharField(blank=True, max_length=255, verbose_name='متن فوتر')),
            ],
            options={
                'verbose_name': 'تنظیمات و برندینگ سامانه',
                'verbose_name_plural': 'تنظیمات و برندینگ سامانه',
            },
        ),
    ]
