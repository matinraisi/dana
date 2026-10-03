import logging

logger = logging.getLogger(__name__)


class SMSService:
    @staticmethod
    def send_welcome_sms(lead):
        """پیامک خوش‌آمدگویی لیدهای جدید"""
        if not lead.phone_number:
            return False
        try:
            from apps.academy.services.sms_service import SmsService
            message = f"{lead.full_name} عزیز، خوش آمدید!"
            SmsService.send(lead.phone_number, message, sms_type='crm_welcome')
            return True
        except Exception as e:
            logger.error(f"خطا در ارسال پیامک خوش‌آمد لید {lead.full_name}: {e}")
            return False
