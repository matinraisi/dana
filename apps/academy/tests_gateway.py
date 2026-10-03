"""پرداخت از طریق درگاه سان‌تک — تست‌ها

Run: ``python manage.py test apps.academy.tests_gateway``

What is pinned:
- with the gateway configured, a payment is created through it, and without it
  the old direct flow still runs (the switch is an env change);
- a signed webhook credits the enrollment **once**, however many times it
  arrives, and never on a bad signature or a mismatched amount;
- `paid` after `failed` still credits (the gateway's contract);
- the return page reads the payment back from the gateway rather than trusting
  the status in its own URL.
"""
import hashlib
import hmac
import json
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.schools.models import School

from .models import Course, CourseEnrollment, PaymentGateway, PaymentRequest, StudentEnrollment
from .models.accounting import AccountingTransaction
from .services import payment_flow

SECRET = 's' * 64
GATEWAY_SETTINGS = dict(
    PAYMENT_GATEWAY_URL='https://pay.sbsuntech.ir',
    PAYMENT_GATEWAY_CLIENT_ID='aihouse-panel',
    PAYMENT_GATEWAY_SECRET=SECRET,
    PANEL_PUBLIC_URL='https://panel.aihousesb.ir',
    # The result page renders `{% static %}`; the project's manifest storage
    # needs a collectstatic run that a test database never has.
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)


def sign(message: str) -> str:
    return hmac.new(SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()


class FakeResponse:
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class GatewayPaymentTests(TestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user(username='owner', password='x')
        self.school = School.objects.create(title='آموزشگاه', slug='school', owner=owner, is_active=True)
        self.course = Course.objects.create(title='پایتون', code='PY1', school=self.school)
        self.student = StudentEnrollment.objects.create(
            first_name='مریم', last_name='احمدی', national_code='0012345678', phone_number='09123456789',
        )
        self.enrollment = CourseEnrollment.objects.create(
            student=self.student, course=self.course, total_amount=500_000,
        )
        self.gateway = PaymentGateway.objects.create(
            school=self.school, name='آقای پرداخت', gateway_type='gateway', merchant_code='SCHOOL-PIN',
        )

    # ── creating ──────────────────────────────────────────────────────────

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_payment_is_created_through_the_gateway(self):
        created = FakeResponse(201, {
            'payment': {'id': 'pay_abc', 'provider_ref': 'T1'},
            'pay_url': 'https://aihousesb.ir/dashboard/payment/callback/?transid=T1',
        })
        with mock.patch('apps.academy.services.gateway_client.requests.request', return_value=created) as req:
            url, error = payment_flow.start_online_payment(
                None, enrollment=self.enrollment, student=self.student, amount=250_000,
                gateway=self.gateway, description='شهریه', legacy_callback_url='',
            )

        self.assertEqual(url, 'https://aihousesb.ir/dashboard/payment/callback/?transid=T1')
        self.assertEqual(error, '')
        method, sent_url = req.call_args.args
        self.assertEqual((method, sent_url), ('POST', 'https://pay.sbsuntech.ir/v1/payments'))
        body = json.loads(req.call_args.kwargs['data'])
        self.assertEqual(body['pin'], 'SCHOOL-PIN')
        self.assertEqual(body['amount'], 250_000)
        self.assertEqual(body['notify_url'], 'https://panel.aihousesb.ir/payment/gateway/webhook/')
        headers = req.call_args.kwargs['headers']
        self.assertEqual(
            headers['X-Signature'],
            sign(f"{headers['X-Timestamp']}.POST./v1/payments.{req.call_args.kwargs['data'].decode()}"),
        )
        payment = PaymentRequest.objects.get()
        self.assertEqual((payment.gateway_payment_id, payment.transaction_id), ('pay_abc', 'T1'))
        self.assertEqual(body['invoice_ref'], f'payment-request-{payment.id}')

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_refused_payment_is_not_left_pending(self):
        refused = FakeResponse(502, {'error': 'کد پین درگاه اشتباه است'})
        with mock.patch('apps.academy.services.gateway_client.requests.request', return_value=refused):
            url, error = payment_flow.start_online_payment(
                None, enrollment=self.enrollment, student=self.student, amount=250_000,
                gateway=self.gateway, description='شهریه', legacy_callback_url='',
            )
        self.assertIsNone(url)
        self.assertEqual(error, 'کد پین درگاه اشتباه است')
        self.assertEqual(PaymentRequest.objects.get().status, 'failed')

    @override_settings(PAYMENT_GATEWAY_URL='', PAYMENT_GATEWAY_CLIENT_ID='', PAYMENT_GATEWAY_SECRET='')
    def test_without_the_gateway_the_direct_flow_still_runs(self):
        with mock.patch(
            'apps.academy.services.payment_flow.AqayePardakht.create_payment',
            return_value={'status': 'success', 'transid': 'D9'},
        ):
            url, _ = payment_flow.start_online_payment(
                None, enrollment=self.enrollment, student=self.student, amount=250_000,
                gateway=self.gateway, description='شهریه', legacy_callback_url='https://x/cb/',
            )
        self.assertEqual(url, 'https://aihousesb.ir/dashboard/payment/callback/?transid=D9')
        self.assertIsNone(PaymentRequest.objects.get().gateway_payment_id)

    @override_settings(**GATEWAY_SETTINGS)
    def test_the_admin_button_charges_the_course_schools_account(self):
        """A superuser has no school; the enrollment's school picks the PIN,
        not whichever active gateway comes first."""
        owner = get_user_model().objects.get(username='owner')
        other = School.objects.create(title='دیگری', slug='other', owner=owner, is_active=True)
        PaymentGateway.objects.create(
            school=other, name='درگاه دیگر', gateway_type='gateway', merchant_code='OTHER-PIN',
        )
        enrollment = CourseEnrollment.objects.create(
            student=self.student, course=Course.objects.create(title='هوش', code='AI1', school=other),
            total_amount=1_000,
        )
        admin = get_user_model().objects.create_superuser(username='root', password='x')
        self.client.force_login(admin)
        created = FakeResponse(201, {'payment': {'id': 'pay_x', 'provider_ref': 'T2'}, 'pay_url': 'https://x/'})
        with mock.patch('apps.academy.services.gateway_client.requests.request', return_value=created) as req:
            self.client.post('/dashboard/finance/payment-initiate/', {
                'enrollment_id': enrollment.id, 'amount': 1_000,
            })
        self.assertEqual(json.loads(req.call_args.kwargs['data'])['pin'], 'OTHER-PIN')

    # ── webhook ───────────────────────────────────────────────────────────

    def _pending(self, amount=250_000):
        return PaymentRequest.objects.create(
            enrollment=self.enrollment, student=self.student, amount=amount,
            gateway_payment_id='pay_abc', description='شهریه',
        )

    def _webhook(self, status='paid', amount=250_000, secret_ok=True, ts=None):
        body = json.dumps({
            'event': f'payment.{status}',
            'payment': {'id': 'pay_abc', 'status': status, 'amount': amount, 'tracking_number': '777', 'bank': 'ملت'},
        })
        ts = str(ts or int(time.time()))
        sig = sign(f'{ts}.{body}') if secret_ok else 'f' * 64
        return self.client.post(
            '/payment/gateway/webhook/', data=body, content_type='application/json',
            HTTP_X_TIMESTAMP=ts, HTTP_X_SIGNATURE=sig,
        )

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_paid_webhook_credits_the_enrollment_once(self):
        payment = self._pending()
        with mock.patch('apps.academy.services.payment_flow._send_success_sms') as sms:
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self._webhook().status_code, 204)
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self._webhook().status_code, 204)

        payment.refresh_from_db()
        self.enrollment.refresh_from_db()
        self.assertEqual(payment.status, 'success')
        self.assertEqual(self.enrollment.paid_amount, 250_000)
        self.assertEqual(AccountingTransaction.objects.count(), 1)
        self.assertEqual(sms.call_count, 1)

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_badly_signed_webhook_changes_nothing(self):
        payment = self._pending()
        self.assertEqual(self._webhook(secret_ok=False).status_code, 403)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_replayed_old_webhook_is_refused(self):
        self._pending()
        self.assertEqual(self._webhook(ts=int(time.time()) - 3600).status_code, 403)

    @override_settings(**GATEWAY_SETTINGS)
    def test_an_amount_mismatch_is_never_credited(self):
        payment = self._pending(amount=250_000)
        self._webhook(amount=1_000)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(AccountingTransaction.objects.count(), 0)

    @override_settings(**GATEWAY_SETTINGS)
    def test_paid_after_failed_is_still_credited(self):
        payment = self._pending()
        self._webhook(status='failed')
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        with mock.patch('apps.academy.services.payment_flow._send_success_sms'):
            self._webhook(status='paid')
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'success')

    @override_settings(**GATEWAY_SETTINGS)
    def test_failed_after_paid_changes_nothing(self):
        payment = self._pending()
        with mock.patch('apps.academy.services.payment_flow._send_success_sms'):
            self._webhook(status='paid')
        self._webhook(status='failed')
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'success')

    # ── return page ───────────────────────────────────────────────────────

    @override_settings(**GATEWAY_SETTINGS)
    def test_the_return_page_confirms_with_the_gateway_before_crediting(self):
        payment = self._pending()
        ts = str(int(time.time()))
        from_gateway = FakeResponse(200, {'payment': {
            'id': 'pay_abc', 'status': 'paid', 'amount': 250_000, 'tracking_number': '777', 'bank': 'ملت',
        }})
        with mock.patch('apps.academy.services.gateway_client.requests.request', return_value=from_gateway), \
                mock.patch('apps.academy.services.payment_flow._send_success_sms'):
            res = self.client.get('/payment/gateway/return/', {
                'payment_id': 'pay_abc', 'status': 'paid', 'ts': ts, 'sig': sign(f'pay_abc.paid.{ts}'),
            })
        self.assertEqual(res.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'success')

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_return_link_saying_paid_is_not_believed_on_its_own(self):
        payment = self._pending()
        ts = str(int(time.time()))
        still_pending = FakeResponse(200, {'payment': {'id': 'pay_abc', 'status': 'pending', 'amount': 250_000}})
        with mock.patch('apps.academy.services.gateway_client.requests.request', return_value=still_pending):
            self.client.get('/payment/gateway/return/', {
                'payment_id': 'pay_abc', 'status': 'paid', 'ts': ts, 'sig': sign(f'pay_abc.paid.{ts}'),
            })
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')

    @override_settings(**GATEWAY_SETTINGS)
    def test_a_forged_return_link_is_refused(self):
        self._pending()
        with mock.patch('apps.academy.services.gateway_client.requests.request') as req:
            res = self.client.get('/payment/gateway/return/', {
                'payment_id': 'pay_abc', 'status': 'paid', 'ts': str(int(time.time())), 'sig': 'f' * 64,
            })
        self.assertContains(res, 'معتبر نیست')
        req.assert_not_called()


class LegacyCallbackTests(TestCase):
    """The direct Aqaye Pardakht callback, still used while the gateway is off
    and for payments Django created before the switch."""

    setUp = GatewayPaymentTests.setUp

    def _legacy_pending(self):
        return PaymentRequest.objects.create(
            enrollment=self.enrollment, student=self.student, amount=250_000,
            transaction_id='D9', authority='D9', description='شهریه',
        )

    @override_settings(STORAGES=GATEWAY_SETTINGS['STORAGES'])
    def test_a_cancelled_payment_shows_as_failed_not_successful(self):
        self._legacy_pending()
        res = self.client.get('/dashboard/payment/callback/', {'transid': 'D9', 'status': '0'})
        self.assertContains(res, 'پرداخت انجام نشد')
        self.assertNotContains(res, 'پرداخت با موفقیت انجام شد')
        self.assertEqual(PaymentRequest.objects.get().status, 'failed')

    @override_settings(STORAGES=GATEWAY_SETTINGS['STORAGES'])
    def test_a_verified_payment_is_credited_as_before(self):
        self._legacy_pending()
        with mock.patch(
            'apps.academy.views.payment.AqayePardakht.verify_payment',
            return_value={'status': 'success', 'code': '1'},
        ), mock.patch('apps.academy.services.payment_flow._send_success_sms'):
            res = self.client.get('/dashboard/payment/callback/', {
                'transid': 'D9', 'status': '1', 'tracking_number': '555', 'bank': 'ملت',
            })
        self.assertContains(res, 'پرداخت با موفقیت انجام شد')
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.paid_amount, 250_000)
        self.assertEqual(AccountingTransaction.objects.count(), 1)
