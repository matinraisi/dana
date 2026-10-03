from django.db import models


class SessionMaterial(models.Model):
    MATERIAL_TYPES = [
        ('assignment', 'تکلیف / تمرین'),
        ('video', 'فیلم آموزشی'),
        ('file', 'فایل ضمیمه'),
        ('link', 'لینک مفید'),
        ('source_code', 'سورس کد'),
        ('other', 'سایر'),
    ]

    course = models.ForeignKey(
        'academy.Course', on_delete=models.CASCADE,
        related_name='materials', verbose_name="دوره",
        null=True, blank=True,
    )
    session = models.ForeignKey(
        'academy.Session', on_delete=models.CASCADE,
        related_name='materials', verbose_name="جلسه",
        null=True, blank=True,
    )
    title = models.CharField(max_length=255, verbose_name="عنوان")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    material_type = models.CharField(
        max_length=20, choices=MATERIAL_TYPES, default='file', verbose_name="نوع"
    )
    file = models.FileField(
        upload_to='materials/', blank=True, null=True, verbose_name="فایل"
    )
    link_url = models.URLField(blank=True, null=True, verbose_name="لینک")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "محتوا / منبع آموزشی"
        verbose_name_plural = "محتوای آموزشی"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_material_type_display()})"
