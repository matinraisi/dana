# Creates StudentAccount in Academy. Teacher was created in 0011.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0025_organizationmembership_detach_teacher_fk'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollment', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='user_account',
                    to='academy.studentenrollment',
                    verbose_name='پرونده هنرجو',
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_account',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='حساب کاربری',
                )),
            ],
            options={
                'verbose_name': 'حساب هنرجو',
                'verbose_name_plural': 'حساب‌های هنرجویان',
                'db_table': 'users_studentaccount',
            },
        ),
    ]
