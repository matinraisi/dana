import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Lead)
def notify_admin_new_lead(sender, instance, created, **kwargs):
    if created:
        logger.info(f"سرنخ جدید ثبت شد: {instance.full_name}")
