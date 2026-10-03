from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('users', '0005_teacher_card_number_teacher_shaba_number')]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('OWNER', 'صاحب کسب‌وکار / مدیر کل'),
                    ('PARTNER', 'شریک تجاری'),
                    ('MANAGER_ACADEMY', 'مدیر آکادمی'),
                    ('MANAGER_COMPANY', 'مدیر شرکت فنی'),
                    ('TEACHER', 'استاد / مدرس'),
                    ('STUDENT', 'هنرجو'),
                    ('SCHOOL_ADMIN', 'مدیر مدرسه'),
                    ('SCHOOL_TEACHER', 'دبیر مدرسه'),
                    ('SCHOOL_STUDENT', 'دانش‌آموز'),
                    ('SCHOOL_GUARDIAN', 'ولی دانش‌آموز'),
                ],
                default='OWNER', max_length=20, verbose_name='نقش کاربری',
            ),
        ),
    ]
