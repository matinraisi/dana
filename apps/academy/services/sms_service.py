import logging

from apps.notifications.sms import send_sms
from ..models import SMSLog

logger = logging.getLogger(__name__)

class SmsService:

    @staticmethod
    def send(phone: str, message: str, sms_type: str = 'bulk_plain') -> bool:
        is_sent = send_sms(phone, message)

        SMSLog.objects.create(receptor=phone, message=message, sms_type=sms_type, is_sent=is_sent)
        return is_sent

    @staticmethod
    def send_template(phone: str, template: str, tokens: dict) -> bool:
        logger.warning("Template SMS is disabled; use SmsService.send with final text instead.")
        is_sent = False

        SMSLog.objects.create(
            receptor=phone,
            message=f"[Template:{template}]",
            sms_type='template',
            is_sent=is_sent,
        )
        return is_sent

    @staticmethod
    def bulk_send(phones: list, message: str, sms_type: str = 'bulk_plain') -> int:
        return sum(1 for phone in phones if SmsService.send(phone, message, sms_type))

    # --- predefined trigger messages ---

    @staticmethod
    def notify_welcome(student, login_url: str):
        msg = (
            f"{student.first_name} عزیز، خوش آمدید!\n"
            f"ثبت‌نام شما با موفقیت انجام شد.\n\n"
            f"نام کاربری: {student.phone_number}\n"
            f"رمز عبور: 123456789\n"
            f"ورود: {login_url}\n\n"
            f"پس از ورود، رمز عبور خود را تغییر دهید."
        )
        return SmsService.send(student.phone_number, msg, sms_type='welcome')

    @staticmethod
    def notify_registration(student, course, profile_url: str):
        msg = (
            f"{student.first_name} عزیز،\n"
            f"ثبت‌نام شما در دوره «{course.title}» با موفقیت انجام شد.\n"
            f"پروفایل شما: {profile_url}\n"
            f"آکادمی هوش مصنوعی سانتک"
        )
        return SmsService.send(student.phone_number, msg, sms_type='registration')

    @staticmethod
    def notify_payment(student, amount: int):
        msg = (
            f"{student.first_name} عزیز،\n"
            f"مبلغ {amount:,} تومان پرداخت شما ثبت شد.\n"
            f"آکادمی هوش مصنوعی سانتک"
        )
        return SmsService.send(student.phone_number, msg, sms_type='payment')

    @staticmethod
    def notify_document_approved(student):
        msg = f"{student.first_name} عزیز، مدارک شناسایی شما تأیید شد. آکادمی سانتک"
        return SmsService.send(student.phone_number, msg, sms_type='document_approved')

    @staticmethod
    def notify_document_rejected(student, reason: str):
        msg = f"{student.first_name} عزیز، مدارک شما رد شد.\nعلت: {reason}\nلطفاً اصلاح کنید."
        return SmsService.send(student.phone_number, msg, sms_type='document_rejected')

    @staticmethod
    def notify_absence(student, session):
        msg = (
            f"{student.first_name} عزیز،\n"
            f"غیبت شما در جلسه {session.session_number} دوره «{session.course.title}» ثبت شد."
        )
        return SmsService.send(student.phone_number, msg, sms_type='attendance_absent')

    @staticmethod
    def notify_installment_due(student, installment):
        msg = (
            f"{student.first_name} عزیز،\n"
            f"قسط {installment.amount:,} تومان شما سررسید شده است.\n"
            f"لطفاً هرچه زودتر پرداخت فرمایید."
        )
        return SmsService.send(student.phone_number, msg, sms_type='installment_reminder')
