import logging
import requests
from django.urls import reverse

logger = logging.getLogger(__name__)


class AqayePardakht:
    """آقای پرداخت — درگاه پرداخت آنلاین

    مستندات: https://panel.aqayepardakht.ir/docs
    """

    CREATE_URL = 'https://panel.aqayepardakht.ir/api/v2/create'
    VERIFY_URL = 'https://panel.aqayepardakht.ir/api/v2/verify'
    GATEWAY_URL = 'https://panel.aqayepardakht.ir/startpay/'

    def __init__(self, pin: str):
        self.pin = pin

    def create_payment(self, amount: int, callback_url: str, invoice_id: str = None,
                       mobile: str = None, email: str = None,
                       card_number: str = None, description: str = None,
                       callback_method: str = 'GET') -> dict:
        """ایجاد تراکنش جدید

        Args:
            amount: مبلغ به تومان (۱,۰۰۰ تا ۴۰۰,۰۰۰,۰۰۰)
            callback_url: آدرس برگشت پس از پرداخت
            callback_method: GET یا POST (توصیه: GET)
            invoice_id: شماره فاکتور
            mobile: شماره موبایل پرداخت‌کننده
            email: ایمیل پرداخت‌کننده
            card_number: شماره کارت ۱۶ رقمی (بدون خط تیره)
            description: توضیحات تراکنش
        """
        data = {
            'pin': self.pin,
            'amount': amount,
            'callback': callback_url,
            'callback_method': callback_method,
        }
        if invoice_id:
            data['invoice_id'] = invoice_id
        if mobile:
            data['mobile'] = mobile
        if email:
            data['email'] = email
        if card_number:
            data['card_number'] = card_number.replace('-', '').replace(' ', '')
        if description:
            data['description'] = description

        try:
            response = requests.post(self.CREATE_URL, data=data, timeout=30)
            result = response.json()
            logger.info(f"AqayePardakht create: status={result.get('status')}, transid={result.get('transid')}")
            return result
        except requests.RequestException as e:
            logger.error(f"AqayePardakht create error: {e}")
            return {'status': 'error', 'message': str(e)}

    def verify_payment(self, amount: int, transaction_id: str) -> dict:
        """وریفای تراکنش

        Args:
            amount: مبلغ دقیق تراکنش (باید با مبلغ ارسالی یکسان باشد)
            transaction_id: کد تراکنش دریافتی از create
        """
        data = {
            'pin': self.pin,
            'amount': amount,
            'transid': transaction_id,
        }
        try:
            response = requests.post(self.VERIFY_URL, data=data, timeout=30)
            result = response.json()
            logger.info(f"AqayePardakht verify: status={result.get('status')}, code={result.get('code')}")
            return result
        except requests.RequestException as e:
            logger.error(f"AqayePardakht verify error: {e}")
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def get_gateway_url(transaction_id: str) -> str:
        """آدرس صفحه پرداخت — مستقیم به درگاه"""
        return f'{AqayePardakht.GATEWAY_URL}{transaction_id}'

    @staticmethod
    def get_redirect_url(transaction_id: str) -> str:
        """آدرس redirect از طریق دامنه اصلی (برای حل مشکل Referrer)"""
        base = 'https://aihousesb.ir/dashboard/payment/callback/'
        return f'{base}?transid={transaction_id}'

    @staticmethod
    def is_payment_successful(api_response: dict) -> bool:
        """بررسی موفقیت ایجاد تراکنش"""
        return api_response.get('status') == 'success'

    @staticmethod
    def is_verified(api_response: dict) -> bool:
        """بررسی موفقیت وریفای — code=1 یعنی پرداخت موفق"""
        return api_response.get('status') == 'success' and api_response.get('code') == '1'
