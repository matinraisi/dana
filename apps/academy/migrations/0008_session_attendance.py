from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0007_studentenrollment_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='تاریخ پایان'),
        ),
        migrations.AddField(
            model_name='course',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='توضیحات دوره'),
        ),
        migrations.AddField(
            model_name='course',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='فعال'),
        ),
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ['-start_date'], 'verbose_name': 'دوره آموزشی', 'verbose_name_plural': 'دوره\u200cهای آموزشی'},
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='عنوان جلسه')),
                ('session_number', models.PositiveIntegerField(verbose_name='شماره جلسه')),
                ('date', models.DateField(verbose_name='تاریخ برگزاری')),
                ('start_time', models.TimeField(blank=True, null=True, verbose_name='ساعت شروع')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='ساعت پایان')),
                ('description', models.TextField(blank=True, null=True, verbose_name='توضیحات جلسه')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='academy.course', verbose_name='دوره')),
            ],
            options={
                'verbose_name': 'جلسه',
                'verbose_name_plural': 'جلسات دوره',
                'ordering': ['session_number'],
                'unique_together': {('course', 'session_number')},
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('present', 'حاضر'), ('absent', 'غایب'), ('excused', 'غیبت موجه'), ('late', 'تأخیر')], default='absent', max_length=10, verbose_name='وضعیت')),
                ('note', models.CharField(blank=True, max_length=255, null=True, verbose_name='یادداشت')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='academy.session', verbose_name='جلسه')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='academy.studentenrollment', verbose_name='هنرجو')),
            ],
            options={
                'verbose_name': 'حضور و غیاب',
                'verbose_name_plural': 'حضور و غیاب',
                'ordering': ['-session__date'],
                'unique_together': {('session', 'student')},
            },
        ),
        migrations.AlterField(
            model_name='smslog',
            name='sms_type',
            field=models.CharField(
                choices=[
                    ('profile_link', 'لینک پروفایل'),
                    ('bulk_plain', 'ارسال دسته\u200cجمعی'),
                    ('installment_reminder', 'یادآوری اقساط'),
                    ('attendance_absent', 'اطلاع\u200cرسانی غیبت'),
                    ('document_verified', 'تأیید مدارک'),
                    ('document_rejected', 'رد مدارک'),
                ],
                max_length=30,
                verbose_name='نوع پیامک'
            ),
        ),
    ]
