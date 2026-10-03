from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProvisioningRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("organization_name", models.CharField(max_length=255, verbose_name="نام مجموعه")),
                ("contact_name", models.CharField(max_length=150, verbose_name="نام مسئول")),
                ("phone_number", models.CharField(db_index=True, max_length=11, verbose_name="شماره تماس")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="ایمیل")),
                ("requested_product", models.CharField(choices=[("academy", "آموزشگاه"), ("school", "مدرسه")], max_length=20, verbose_name="محصول درخواستی")),
                ("message", models.TextField(blank=True, verbose_name="توضیحات درخواست")),
                ("status", models.CharField(choices=[("new", "جدید"), ("contacted", "تماس گرفته شد"), ("demo", "دمو"), ("provisioning", "در حال راه‌اندازی"), ("delivered", "تحویل شد"), ("rejected", "رد شد")], db_index=True, default="new", max_length=20, verbose_name="وضعیت")),
                ("internal_note", models.TextField(blank=True, verbose_name="یادداشت داخلی")),
                ("notified_at", models.DateTimeField(blank=True, null=True, verbose_name="زمان اطلاع‌رسانی")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")),
            ],
            options={
                "verbose_name": "درخواست راه‌اندازی",
                "verbose_name_plural": "درخواست‌های راه‌اندازی",
                "ordering": ["-created_at"],
            },
        ),
    ]
