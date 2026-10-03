from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project

@receiver(post_save, sender=Project)
def handle_project_completion(sender, instance, created, **kwargs):
    # چک می‌کنیم که اگر وضعیت به "تکمیل شده" تغییر کرد، متد توزیع سود اجرا شود
    if instance.status == 'COMPLETED':
        instance.distribute_profit()