import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from apps.academy.mixins import AdminRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone

from ..models import StudentEnrollment, StudentIDCard
from ..services.idcard_service import IDCardService

logger = logging.getLogger(__name__)


class IssueIDCardView(AdminRequiredMixin, View):
    """صدور / بازصدور کارت شناسایی هنرجو"""

    def post(self, request, student_id):
        student = self.school_object_or_404(StudentEnrollment, id=student_id)

        # تولید شماره کارت
        card_number = IDCardService.generate_card_number(student.id)

        # ایجاد یا بازیابی کارت
        card, created = StudentIDCard.objects.get_or_create(
            student=student,
            defaults={'card_number': card_number, 'is_valid': True},
        )

        # بروزرسانی کارت
        card.card_number = card_number
        card.is_valid = True
        card.issued_at = timezone.now()
        card.save()

        # تولید QR با شماره واقعی
        real_url = request.build_absolute_uri(
            reverse('academy:verify_id_card', kwargs={'card_number': card.card_number})
        )
        qr_image = IDCardService.generate_qr(real_url)
        card.qr_code.save(f"idcards/qr_{student.id}.png", qr_image, save=True)

        # ارسال پیامک با لینک کارت به نگهبانی
        try:
            from apps.academy.services.sms_service import SmsService
            SmsService.send(
                student.phone_number,
                f"کارت شناسایی صادر شد\n"
                f"مدرسه هوش مصنوعی\n"
                f"{real_url}\n"
                f"این کارت برای شناسایی افراد در ورود و خروج مدرسه استفاده می‌شود.",
                sms_type='id_card_issued'
            )
        except Exception as e:
            logger.error(f"SMS failed for card issuance: {e}")

        messages.success(request, f"کارت شناسایی «{student.full_name}» با شماره {card.card_number} صادر شد.")
        return redirect('academy:student_id_card', slug=student.short_slug)


class StudentIdCardView(AdminRequiredMixin, View):
    """نمایش کارت شناسایی هنرجو — قابل چاپ"""

    def get(self, request, slug):
        student = self.school_object_or_404(StudentEnrollment, short_slug=slug)
        card = getattr(student, 'id_card', None)
        return render(request, 'academy/id_card.html', {
            'student': student,
            'card': card,
        })


class VerifyIDCardView(View):
    """نقطه تأیید QR — عمومی (بدون نیاز به ورود)"""

    def get(self, request, card_number):
        try:
            card = StudentIDCard.objects.select_related('student').get(
                card_number=card_number
            )
            student = card.student
            enrollments = student.active_enrollments.select_related('course').all()
            return render(request, 'academy/id_card_verify.html', {
                'card': card,
                'student': student,
                'enrollments': enrollments,
                'is_valid': card.is_valid,
            })
        except StudentIDCard.DoesNotExist:
            return render(request, 'academy/id_card_verify.html', {
                'is_valid': False,
                'error': 'کارت شناسایی یافت نشد یا منقضی شده است.',
            })


class IDCardListView(AdminRequiredMixin, View):
    """لیست کارت‌های صادرشده برای مدیر"""

    def get(self, request):
        cards = StudentIDCard.objects.select_related('student').order_by('-issued_at')

        # صفحه‌بندی
        from django.core.paginator import Paginator
        page_number = request.GET.get('page', 1)
        paginator = Paginator(cards, 20)
        page_obj = paginator.get_page(page_number)

        # آمار
        valid_count = cards.filter(is_valid=True).count()
        invalid_count = cards.filter(is_valid=False).count()
        unpaid_count = cards.filter(student__active_enrollments__isnull=False).exclude(
            student__active_enrollments__paid_amount__gt=0
        ).distinct().count()

        return render(request, 'academy/dashboard/idcard_list.html', {
            'cards': page_obj,
            'page_obj': page_obj,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'unpaid_count': unpaid_count,
        })


class RevokeIDCardView(AdminRequiredMixin, View):
    """باطل کردن / فعال کردن کارت شناسایی"""

    def post(self, request, card_id):
        card = self.school_object_or_404(StudentIDCard, id=card_id)
        card.is_valid = not card.is_valid
        card.save(update_fields=['is_valid'])
        status = "فعال" if card.is_valid else "باطل"
        messages.success(request, f"کارت شناسایی «{card.student.full_name}» {status} شد.")
        return redirect('academy:idcard_list')
