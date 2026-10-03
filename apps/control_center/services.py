import logging

from django.conf import settings

from apps.notifications.sms import send_sms

logger = logging.getLogger(__name__)


def notify_admins_of_provisioning_request(provisioning_request) -> bool:
    """Notify Dana operators without coupling the request to academy SMS logs."""
    recipients = settings.SMS_ADMIN_PHONES
    if not recipients:
        logger.warning("No SMS_ADMIN_PHONES configured for control requests.")
        return False

    message = (
        "درخواست جدید دانا\n"
        f"مجموعه: {provisioning_request.organization_name}\n"
        f"مسئول: {provisioning_request.contact_name}\n"
        f"تماس: {provisioning_request.phone_number}\n"
        f"محصول: {provisioning_request.get_requested_product_display()}"
    )
    return any(send_sms(phone, message) for phone in recipients)
