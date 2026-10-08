from django.conf import settings
from django.db import models


class StudentAccount(models.Model):
    """Academy student login link to a StudentEnrollment dossier."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_account',
        verbose_name="حساب کاربری",
    )
    enrollment = models.OneToOneField(
        'academy.StudentEnrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        verbose_name="پرونده هنرجو",
    )

    class Meta:
        verbose_name = "حساب هنرجو"
        verbose_name_plural = "حساب‌های هنرجویان"
        # Preserve existing physical table from users.StudentAccount
        db_table = 'users_studentaccount'

    def __str__(self):
        return f"حساب: {self.user.username}"
