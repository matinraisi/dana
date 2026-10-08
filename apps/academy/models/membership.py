from django.conf import settings
from django.db import models


class OrganizationMembership(models.Model):
    """Links a user to the Academy Organization of this instance.

    With one-org-per-instance, this marks which users belong to the academy
    rather than partitioning multiple tenants inside one database.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='academy_membership',
        verbose_name="کاربر",
    )
    organization = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="سازمان آموزشگاه",
    )

    class Meta:
        verbose_name = "عضویت سازمانی آموزشگاه"
        verbose_name_plural = "عضویت‌های سازمانی آموزشگاه"

    def __str__(self):
        return f"{self.user} → {self.organization}"
