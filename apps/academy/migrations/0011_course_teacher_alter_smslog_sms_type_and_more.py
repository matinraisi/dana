# Teacher is created in Academy (not users). Fresh installs own the table here.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0010_studentidcard_course_cover_image_course_fee_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True, null=True, verbose_name='بیوگرافی')),
                ('specialization', models.CharField(blank=True, max_length=200, null=True, verbose_name='تخصص')),
                ('national_code', models.CharField(blank=True, max_length=10, null=True, unique=True, verbose_name='کد ملی')),
                ('phone_number', models.CharField(blank=True, max_length=11, null=True, verbose_name='شماره تماس')),
                ('card_number', models.CharField(blank=True, max_length=16, null=True, verbose_name='شماره کارت بانکی')),
                ('shaba_number', models.CharField(blank=True, max_length=24, null=True, verbose_name='شماره شبا')),
                ('hire_date', models.DateField(blank=True, null=True, verbose_name='تاریخ استخدام')),
                ('salary_per_session', models.PositiveIntegerField(default=0, verbose_name='دستمزد هر جلسه (تومان)')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='teacher_profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='حساب کاربری',
                )),
            ],
            options={
                'verbose_name': 'استاد',
                'verbose_name_plural': 'مدیریت اساتید',
                'db_table': 'users_teacher',
            },
        ),
        migrations.AddField(
            model_name='course',
            name='teacher',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses',
                to='academy.teacher',
                verbose_name='استاد دوره',
            ),
        ),
        migrations.AlterField(
            model_name='smslog',
            name='sms_type',
            field=models.CharField(
                choices=[
                    ('registration', 'تأیید ثبت\u200cنام'),
                    ('payment', 'تأیید پرداخت'),
                    ('document_approved', 'تأیید مدارک'),
                    ('document_rejected', 'رد مدارک'),
                    ('attendance_absent', 'اطلاع غیبت'),
                    ('installment_reminder', 'یادآوری قسط'),
                    ('course_start', 'شروع دوره'),
                    ('bulk_plain', 'ارسال دسته\u200cجمعی'),
                    ('template', 'پیامک الگو'),
                    ('profile_link', 'لینک پروفایل'),
                ],
                max_length=30,
                verbose_name='نوع پیامک',
            ),
        ),
        migrations.AddField(
            model_name='studentidcard',
            name='student',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='id_card',
                to='academy.studentenrollment',
                verbose_name='هنرجو',
            ),
        ),
    ]
