"""شروع پرداخت آنلاین و ثبت نتیجهٔ آن — یک مسیر برای همهٔ ویوها

Before this module, four views each created a payment their own way, and the
callback held the only copy of "what a successful payment does". Now:

- ``start_online_payment`` is the one way to send a customer to the bank. It
  goes through the Suntech payment gateway when ``PAYMENT_GATEWAY_*`` is set,
  and falls back to talking to Aqaye Pardakht directly when it is not — so the
  switch is an env change, and undoing it is too.
- ``settle_success`` / ``settle_failure`` are the one way to record a result,
  called from the old callback, the gateway webhook and the return page alike.
  ``settle_success`` credits a payment **once**: it locks the row and returns
  early if it is already successful, because the webhook and the return page
  can both arrive for the same payment, in either order.
"""
import logging

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from ..models import PaymentGateway, PaymentRequest
from ..models.accounting import AccountingTransaction
from . import gateway_client
from .payment_service import AqayePardakht

logger = logging.getLogger(__name__)


def gateway_for(enrollment) -> PaymentGateway | None:
    """The school's active online gateway, else any active one — the lookup
    every payment view already made."""
    gateway = PaymentGateway.objects.filter(
        gateway_type='gateway', is_active=True, school_id=enrollment.course.school_id,
    ).first()
    return gateway or PaymentGateway.objects.filter(gateway_type='gateway', is_active=True).first()


def _panel_url(name: str) -> str:
    from django.conf import settings
    return settings.PANEL_PUBLIC_URL.rstrip('/') + reverse(name)


def start_online_payment(request, *, enrollment, student, amount: int, gateway: PaymentGateway,
                         description: str, legacy_callback_url: str) -> tuple[str | None, str]:
    """Create the payment and return ``(url to send the browser to, error)``.

    The ``PaymentRequest`` exists before the gateway is asked, so its id can be
    the invoice reference; it is marked failed if the gateway refuses.
    """
    if gateway_client.is_configured():
        payment_req = PaymentRequest.objects.create(
            enrollment=enrollment, student=student, amount=amount, description=description,
        )
        created = gateway_client.create_payment(
            pin=gateway.merchant_code,
            amount=amount,
            invoice_ref=f'payment-request-{payment_req.id}',
            return_url=_panel_url('gateway_payment_return'),
            notify_url=_panel_url('gateway_payment_webhook'),
            mobile=student.phone_number or '',
            description=description,
        )
        if not created.ok:
            payment_req.status = 'failed'
            payment_req.save(update_fields=['status', 'updated_at'])
            return None, created.error
        payment_req.gateway_payment_id = created.payment_id
        payment_req.transaction_id = created.provider_ref
        payment_req.authority = created.provider_ref
        payment_req.save(update_fields=['gateway_payment_id', 'transaction_id', 'authority', 'updated_at'])
        return created.pay_url, ''

    # Direct to Aqaye Pardakht — the behaviour before the gateway existed.
    service = AqayePardakht(pin=gateway.merchant_code)
    result = service.create_payment(
        amount=amount,
        callback_url=legacy_callback_url,
        invoice_id=str(enrollment.id),
        mobile=student.phone_number,
        description=description,
    )
    trans_id = result.get('transid')
    if not trans_id:
        return None, result.get('message', 'خطا در اتصال به درگاه پرداخت')
    PaymentRequest.objects.create(
        enrollment=enrollment, student=student, amount=amount,
        transaction_id=str(trans_id), authority=trans_id, description=description,
    )
    return AqayePardakht.get_redirect_url(trans_id), ''


def settle_success(payment_req: PaymentRequest, *, gateway: PaymentGateway | None,
                   card_number=None, tracking_number=None, bank=None, actor=None) -> bool:
    """Record a verified payment. Returns False if it had already been recorded.

    Everything a successful payment does happens here, inside one transaction:
    the enrollment's paid amount, its installments, the accounting entry. The
    SMS goes out after the commit, so a rolled-back credit never texts anyone.
    """
    with transaction.atomic():
        locked = PaymentRequest.objects.select_for_update().get(pk=payment_req.pk)
        if locked.status == 'success':
            return False
        locked.status = 'success'
        if card_number:
            locked.card_number = card_number[:16]
        locked.save()

        enrollment = locked.enrollment
        enrollment.paid_amount += locked.amount
        if enrollment.paid_amount >= enrollment.total_amount:
            enrollment.payment_method = 'cash'
        elif enrollment.paid_amount > 0:
            enrollment.payment_method = 'installment'
        enrollment.save()

        paid_remaining = locked.amount
        for inst in enrollment.installments.filter(status='pending').order_by('due_date'):
            if paid_remaining <= 0:
                break
            inst.status = 'paid'
            inst.paid_at = timezone.now().date()
            inst.save()
            paid_remaining -= inst.amount

        AccountingTransaction.objects.create(
            transaction_type='income',
            amount=locked.amount,
            payment_method='gateway',
            payment_gateway=gateway,
            course=enrollment.course,
            student=locked.student,
            enrollment=enrollment,
            description=f'پرداخت آنلاین — {locked.description} — بانک: {bank or "-"}',
            transaction_date=timezone.now().date(),
            created_by=actor,
        )
        transaction.on_commit(lambda: _send_success_sms(locked, enrollment, tracking_number, bank))
    payment_req.refresh_from_db()
    return True


def settle_failure(payment_req: PaymentRequest) -> bool:
    """Mark a payment failed — only while it is still pending. A payment that
    succeeded stays succeeded whatever arrives after it."""
    updated = PaymentRequest.objects.filter(pk=payment_req.pk, status='pending').update(
        status='failed', updated_at=timezone.now(),
    )
    payment_req.refresh_from_db()
    return updated == 1


def _send_success_sms(payment_req, enrollment, tracking_number, bank) -> None:
    student = payment_req.student
    user = student.user if hasattr(student, 'user') else None
    if user:
        sms_text = (
            f'پرداخت شما به مبلغ {payment_req.amount:,} تومان برای دوره «{enrollment.course.title}» با موفقیت انجام شد.\n'
            f'شماره تراکنش: {tracking_number or "-"}\n'
            f'بانک: {bank or "-"}\n\n'
            f'ورود به پنل هنرجو:\n'
            f'آدرس: https://panel.aihousesb.ir/my/\n'
            f'نام کاربری: {user.username}\n'
            f'رمز عبور: 123456789'
        )
    else:
        sms_text = (
            f'پرداخت شما به مبلغ {payment_req.amount:,} تومان برای دوره «{enrollment.course.title}» با موفقیت انجام شد.\n'
            f'شماره تراکنش: {tracking_number or "-"}'
        )
    try:
        from .sms_service import SmsService
        SmsService.send(student.phone_number, sms_text, sms_type='payment_success')
    except Exception:
        logger.exception('payment success SMS not sent: payment_request=%s', payment_req.pk)
