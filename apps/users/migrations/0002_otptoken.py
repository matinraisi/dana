from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OTPToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, verbose_name='شماره موبایل')),
                ('code', models.CharField(max_length=6, verbose_name='کد')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'کد یکبارمصرف',
                'verbose_name_plural': 'کدهای یکبارمصرف',
                'ordering': ['-created_at'],
            },
        ),
    ]
