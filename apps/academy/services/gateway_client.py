"""کلاینت درگاه پرداخت سان‌تک (pay.sbsuntech.ir)

از زمانی که این تنظیمات پر باشد، پنل دیگر خودش با آقای پرداخت صحبت نمی‌کند:
پرداخت را درگاه می‌سازد، callback بانک را خودش وریفای می‌کند و نتیجه را با
webhook امضاشده به پنل خبر می‌دهد. طراحی و API: README مخزن payment-gateway.

The contract, in one place:

- Requests are signed: ``X-Signature = HMAC-SHA256(secret,
  "<ts>.<METHOD>.<path>.<body>")`` with ``X-Client-Id`` and ``X-Timestamp``.
- Webhooks to us are signed ``HMAC(secret, "<ts>.<body>")``.
- The browser's return carries ``sig = HMAC(secret, "<payment_id>.<status>.<ts>")``
  — a hint for the page, never grounds to credit anything on its own.
"""
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

#: How far a webhook's timestamp may be from our clock, as the gateway allows
#: for requests. Guards against a captured webhook being replayed much later.
WEBHOOK_MAX_SKEW = 300
#: How long a return link stays valid. A customer can sit on the bank's page;
#: this only decides whether the result page trusts the status it was handed.
RETURN_MAX_AGE = 3600


def is_configured() -> bool:
    return bool(
        settings.PAYMENT_GATEWAY_URL
        and settings.PAYMENT_GATEWAY_CLIENT_ID
        and settings.PAYMENT_GATEWAY_SECRET
    )


def _sign(message: str) -> str:
    return hmac.new(
        settings.PAYMENT_GATEWAY_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()


def _request(method: str, path: str, payload: dict | None = None) -> requests.Response:
    body = '' if payload is None else json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    ts = str(int(time.time()))
    headers = {
        'Content-Type': 'application/json',
        'X-Client-Id': settings.PAYMENT_GATEWAY_CLIENT_ID,
        'X-Timestamp': ts,
        'X-Signature': _sign(f'{ts}.{method}.{path}.{body}'),
    }
    url = settings.PAYMENT_GATEWAY_URL.rstrip('/') + path
    # 30 s: creating a payment waits on the provider (the gateway allows it 15).
    return requests.request(method, url, data=body.encode() or None, headers=headers, timeout=30)


@dataclass
class CreatedPayment:
    ok: bool
    payment_id: str = ''
    provider_ref: str = ''
    pay_url: str = ''
    error: str = ''


def create_payment(*, pin: str, amount: int, invoice_ref: str, return_url: str,
                   notify_url: str, mobile: str = '', description: str = '') -> CreatedPayment:
    payload = {
        'amount': int(amount),
        'invoice_ref': invoice_ref,
        'return_url': return_url,
        'notify_url': notify_url,
        'pin': pin,
    }
    if description:
        payload['description'] = description[:250]
    # The gateway accepts only 09xxxxxxxxx; anything else is left out rather
    # than failing the payment over an optional field.
    if mobile and len(mobile) == 11 and mobile.startswith('09') and mobile.isdigit():
        payload['mobile'] = mobile
    try:
        response = _request('POST', '/v1/payments', payload)
    except requests.RequestException as exc:
        logger.error('payment gateway unreachable: %s', exc)
        return CreatedPayment(ok=False, error='درگاه پرداخت در دسترس نیست. کمی بعد دوباره تلاش کنید.')
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code != 201:
        logger.warning('payment gateway refused: %s %s', response.status_code, data)
        return CreatedPayment(ok=False, error=data.get('error') or 'خطا در اتصال به درگاه پرداخت')
    payment = data.get('payment') or {}
    return CreatedPayment(
        ok=True,
        payment_id=payment.get('id', ''),
        provider_ref=payment.get('provider_ref') or '',
        pay_url=data.get('pay_url', ''),
    )


def get_payment(payment_id: str) -> dict | None:
    """The payment as the gateway sees it — the authority when in doubt."""
    try:
        response = _request('GET', f'/v1/payments/{payment_id}')
    except requests.RequestException as exc:
        logger.error('payment gateway unreachable: %s', exc)
        return None
    if response.status_code != 200:
        return None
    return (response.json() or {}).get('payment')


def verify_webhook(timestamp: str, signature: str, body: bytes) -> bool:
    if not timestamp.isdigit() or abs(time.time() - int(timestamp)) > WEBHOOK_MAX_SKEW:
        return False
    expected = _sign(f'{timestamp}.{body.decode("utf-8", errors="replace")}')
    return hmac.compare_digest(expected, signature or '')


def verify_return(payment_id: str, status: str, timestamp: str, signature: str) -> bool:
    if not timestamp.isdigit() or time.time() - int(timestamp) > RETURN_MAX_AGE:
        return False
    return hmac.compare_digest(_sign(f'{payment_id}.{status}.{timestamp}'), signature or '')
