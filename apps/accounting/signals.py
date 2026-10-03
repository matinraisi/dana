from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice
from apps.core.models import Partner, PartnerRevenue

@receiver(post_save, sender=Invoice)
def calculate_partner_shares(sender, instance, created, **kwargs):
    # فقط زمانی عمل کن که تیک تسویه شده زده شده باشد
    if instance.is_paid:
        # جلوگیری از ایجاد سهم تکراری برای یک فاکتور
        if not PartnerRevenue.objects.filter(invoice=instance).exists():
            partners = Partner.objects.all()
            for partner in partners:
                share_amount = (instance.total_amount * partner.share_percentage) / 100
                PartnerRevenue.objects.create(
                    partner=partner,
                    invoice=instance,
                    amount=share_amount
                )