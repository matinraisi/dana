import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from apps.academy.mixins import AdminRequiredMixin

from ..models import CourseEnrollment, StudentEnrollment, PaymentRequest, PaymentGateway, AcademyInstallment
from ..services.payment_service import AqayePardakht
from ..services import gateway_client
from ..services.payment_flow import gateway_for, settle_failure, settle_success, start_online_payment

logger = logging.getLogger(__name__)


def get_callback_url(request):
    """ساخت آدرس callback پرداخت — از تنظیمات یا دامنه جاری"""
    if settings.PAYMENT_CALLBACK_URL:
        return settings.PAYMENT_CALLBACK_URL
    return request.build_absolute_uri(reverse('academy:payment_callback'))


class PaymentInitiateView(AdminRequiredMixin, View):
    """پرداخت از پنل ادمین"""
    def post(self, request):
        enrollment_id = request.POST.get('enrollment_id')
        amount = request.POST.get('amount')
        if not enrollment_id or not amount:
            messages.error(request, 'اطلاعات پرداخت ناقص است.')
            return redirect('academy:finance_management')

        enrollment = self.school_object_or_404(CourseEnrollment, id=enrollment_id)
        student = enrollment.student
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            messages.error(request, 'مبلغ پرداخت معتبر نیست.')
            return redirect('academy:finance_management')

        # The course's school decides whose merchant account is charged — not
        # the admin's: a superuser has no school and would otherwise get
        # whichever active gateway happened to come first.
        gateway = gateway_for(enrollment)
        if not gateway or not gateway.merchant_code:
            messages.error(request, 'درگاه پرداخت آنلاین فعال و دارای کد درگاه یافت نشد.')
            return redirect('academy:finance_management')

        pay_url, error = start_online_payment(
            request, enrollment=enrollment, student=student, amount=amount, gateway=gateway,
            description=f'پرداخت آنلاین {enrollment.course.title}',
            legacy_callback_url=get_callback_url(request),
        )
        if pay_url:
            return redirect(pay_url)
        messages.error(request, f'خطا: {error}')
        return redirect('academy:finance_management')


class PublicPaymentInitiateView(View):
    """پرداخت عمومی — از صفحه ثبت‌نام یا لینک SMS"""
    def post(self, request, enrollment_id, slug=None):
        # ``slug`` is present when mounted under /register/<slug>/pay/...
        enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)
        student = enrollment.student
        remaining = enrollment.remaining_amount
        reg_url = f'/register/{enrollment.course.registration_slug}/'

        if remaining <= 0:
            messages.info(request, 'شهریه این دوره قبلاً تسویه شده است.')
            return redirect(reg_url)

        # بررسی پرداخت pending تکراری
        existing_pending = PaymentRequest.objects.filter(
            enrollment=enrollment, status='pending'
        ).exists()
        if existing_pending:
            messages.warning(request, 'درخواست پرداخت قبلی هنوز فعال است. لطفاً صبر کنید.')
            return redirect(reg_url)

        gateway = gateway_for(enrollment)
        if not gateway or not gateway.merchant_code:
            messages.error(request, 'درگاه پرداخت فعال نیست. با مدیریت تماس بگیرید.')
            return redirect(reg_url)

        pay_url, error = start_online_payment(
            request, enrollment=enrollment, student=student, amount=remaining, gateway=gateway,
            description=f'پرداخت آنلاین {enrollment.course.title}',
            legacy_callback_url=get_callback_url(request),
        )
        if pay_url:
            return redirect(pay_url)
        messages.error(request, f'خطا: {error}')
        return redirect(reg_url)


class PublicPaymentInstallmentView(View):
    """پرداخت اقساطی — ایجاد ۲ قسط و ارسال به درگاه برای قسط اول"""
    def post(self, request, enrollment_id, slug=None):
        # ``slug`` is present when mounted under /register/<slug>/pay/...
        enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)
        reg_url = f'/register/{enrollment.course.registration_slug}/'
        remaining = enrollment.remaining_amount

        if remaining <= 0:
            messages.info(request, 'شهریه قبلاً تسویه شده است.')
            return redirect(reg_url)

        # اگه قسط قبلاً ساخته شده، فقط همون رو بفرست
        existing = enrollment.installments.filter(status='pending').order_by('due_date')
        if existing.exists():
            first_installment = existing.first()
            installment_amount = first_installment.amount
        else:
            # ساخت ۲ قسط مساوی
            installment_amount = remaining // 2
            second_amount = remaining - installment_amount

            today = timezone.now().date()
            from datetime import timedelta
            AcademyInstallment.objects.create(
                enrollment=enrollment,
                amount=installment_amount,
                due_date=today,
                status='pending',
            )
            AcademyInstallment.objects.create(
                enrollment=enrollment,
                amount=second_amount,
                due_date=today + timedelta(days=30),
                status='pending',
            )

        # ارسال به درگاه با مبلغ قسط اول
        gateway = gateway_for(enrollment)
        if not gateway or not gateway.merchant_code:
            messages.error(request, 'درگاه پرداخت فعال نیست.')
            return redirect(reg_url)

        pay_url, error = start_online_payment(
            request, enrollment=enrollment, student=enrollment.student, amount=installment_amount,
            gateway=gateway, description=f'قسط اول — {enrollment.course.title}',
            legacy_callback_url=get_callback_url(request),
        )
        if pay_url:
            enrollment.payment_method = 'installment'
            enrollment.save()
            return redirect(pay_url)
        messages.error(request, f'خطا: {error}')
        return redirect(reg_url)


class PaymentCallbackView(View):
    """برگشت از درگاه پرداخت

    پارامترهای دریافتی از درگاه (مطابق مستندات):
    - transid: کد تراکنش
    - cardnumber: شماره کارت پرداخت‌کننده
    - tracking_number: شماره تراکنش بانکی
    - invoice_id: شماره فاکتور
    - bank: نام بانک
    - status: 1=موفق, 0=ناموفق
    """
    def get(self, request):
        trans_id = request.GET.get('transid')
        status = request.GET.get('status')
        card_number = request.GET.get('cardnumber')
        tracking_number = request.GET.get('tracking_number')
        bank = request.GET.get('bank')

        if not trans_id:
            return render(request, 'academy/payment_success.html', {
                'amount': 0,
                'error': 'کد تراکنش دریافت نشد.',
            })

        payment_req = PaymentRequest.objects.filter(
            transaction_id=trans_id, status='pending'
        ).select_related('enrollment', 'enrollment__course',
                         'enrollment__student', 'student').first()

        if not payment_req:
            return render(request, 'academy/payment_success.html', {
                'amount': 0,
                'error': 'درخواست پرداخت یافت نشد یا قبلاً پردازش شده است.',
            })

        # اگر status ناموفق بود، وریفای نکن
        if status != '1':
            settle_failure(payment_req)
            return render(request, 'academy/payment_success.html', {
                'amount': payment_req.amount,
                'course_title': payment_req.course.title if hasattr(payment_req, 'course') else payment_req.enrollment.course.title,
                'error': 'پرداخت توسط کاربر لغو شد یا ناموفق بود.',
            })

        # پیدا کردن درگاه فعال
        gateway = PaymentGateway.objects.filter(
            gateway_type='gateway', is_active=True,
            school_id=payment_req.enrollment.course.school_id,
        ).first()
        if not gateway:
            gateway = PaymentGateway.objects.filter(
                gateway_type='gateway', is_active=True,
            ).first()

        if not gateway or not gateway.merchant_code:
            payment_req.status = 'failed'
            payment_req.save()
            return render(request, 'academy/payment_success.html', {
                'amount': payment_req.amount,
                'course_title': payment_req.enrollment.course.title,
                'error': 'درگاه پرداخت پیکربندی نشده است.',
            })

        # وریفای تراکنش
        service = AqayePardakht(pin=gateway.merchant_code)
        verify_result = service.verify_payment(
            amount=payment_req.amount, transaction_id=trans_id,
        )

        if service.is_verified(verify_result):
            settle_success(
                payment_req, gateway=gateway, card_number=card_number,
                tracking_number=tracking_number, bank=bank,
                actor=request.user if request.user.is_authenticated else None,
            )
            return render(request, 'academy/payment_success.html', {
                'amount': payment_req.amount,
                'course_title': payment_req.enrollment.course.title,
                'tracking_number': tracking_number,
                'bank': bank,
            })
        else:
            settle_failure(payment_req)
            error_code = verify_result.get('code', 'نامشخص')
            return render(request, 'academy/payment_success.html', {
                'amount': payment_req.amount,
                'course_title': payment_req.enrollment.course.title,
                'error': f'پرداخت تأیید نشد (کد خطا: {error_code}).',
            })


def _apply_gateway_payment(payment_req, payment: dict) -> None:
    """Record what the gateway says about a payment. Safe to call repeatedly."""
    status = payment.get('status')
    if status == 'paid':
        # The gateway verified this exact amount; a mismatch means the rows are
        # not the same payment, and money is never credited on a guess.
        if int(payment.get('amount') or 0) != payment_req.amount:
            logger.error('gateway amount mismatch: payment_request=%s', payment_req.pk)
            return
        settle_success(
            payment_req,
            gateway=gateway_for(payment_req.enrollment),
            card_number=payment.get('card_number'),
            tracking_number=payment.get('tracking_number'),
            bank=payment.get('bank'),
        )
    elif status == 'failed':
        settle_failure(payment_req)


@method_decorator(csrf_exempt, name='dispatch')
class GatewayWebhookView(View):
    """نتیجهٔ پرداخت از درگاه سان‌تک — امضاشده، سرور به سرور

    The authority for crediting an enrollment. Any 2xx tells the gateway to stop
    retrying, so a payment we do not know is acknowledged too (and logged): the
    gateway retrying it for two days would not make it ours.
    """
    def post(self, request):
        if not gateway_client.is_configured() or not gateway_client.verify_webhook(
            request.headers.get('X-Timestamp', ''), request.headers.get('X-Signature', ''), request.body,
        ):
            return HttpResponseForbidden('invalid signature')
        try:
            import json
            payment = json.loads(request.body).get('payment') or {}
        except ValueError:
            return HttpResponse(status=400)
        payment_req = PaymentRequest.objects.filter(gateway_payment_id=payment.get('id')).first()
        if payment_req is None:
            logger.warning('gateway webhook for unknown payment %s', payment.get('id'))
            return HttpResponse(status=204)
        _apply_gateway_payment(payment_req, payment)
        return HttpResponse(status=204)


class GatewayReturnView(View):
    """برگشت هنرجو از بانک، از طریق درگاه سان‌تک

    Shows the result. The status in the link is only a hint; before telling
    anyone they paid, the payment is read back from the gateway, and recorded
    here if the webhook has not arrived yet.
    """
    def get(self, request):
        payment_id = request.GET.get('payment_id', '')
        if not gateway_client.is_configured() or not gateway_client.verify_return(
            payment_id, request.GET.get('status', ''), request.GET.get('ts', ''), request.GET.get('sig', ''),
        ):
            return render(request, 'academy/payment_success.html', {
                'amount': 0, 'error': 'لینک بازگشت از درگاه معتبر نیست.',
            })
        payment_req = PaymentRequest.objects.filter(gateway_payment_id=payment_id).select_related(
            'enrollment__course',
        ).first()
        if payment_req is None:
            return render(request, 'academy/payment_success.html', {
                'amount': 0, 'error': 'درخواست پرداخت یافت نشد.',
            })

        if payment_req.status == 'pending':
            payment = gateway_client.get_payment(payment_id)
            if payment:
                _apply_gateway_payment(payment_req, payment)
                payment_req.refresh_from_db()

        context = {'amount': payment_req.amount, 'course_title': payment_req.enrollment.course.title}
        if payment_req.status == 'success':
            payment = gateway_client.get_payment(payment_id) or {}
            context.update(tracking_number=payment.get('tracking_number'), bank=payment.get('bank'))
        elif payment_req.status == 'failed':
            context['error'] = 'پرداخت انجام نشد یا لغو شد.'
        else:
            context['pending'] = True
            context['error'] = 'نتیجه تا چند دقیقهٔ دیگر ثبت و برایتان پیامک می‌شود.'
        return render(request, 'academy/payment_success.html', context)

