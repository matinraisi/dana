import logging

from django.conf import settings

from apps.notifications.sms import send_sms

logger = logging.getLogger(__name__)

def send_registration_sms(student_phone, student_name, course_title, card_link):
    """
    ارسال پیامک تایید ثبت نام به هنرجو و مدیران با متن معمولی
    """
    student_message = (
        f"{student_name} عزیز، ثبت‌نام شما در دوره «{course_title}» تأیید شد.\n"
        f"مشاهده پروفایل و مدارک: {card_link}"
    )
    student_sent = send_sms(student_phone, student_message)
    for admin_phone in settings.SMS_ADMIN_PHONES:
        send_sms(admin_phone, f"مدیریت محترم؛\nهنرجو {student_name} در دوره {course_title} ثبت‌نام کرد.")
    return student_sent
