import logging
import time

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, authenticate
from django.contrib import messages

from .models import OTPToken, User
from apps.notifications.sms import send_sms

logger = logging.getLogger(__name__)

# Rate limiting constants
OTP_MIN_INTERVAL_SECONDS = 60   # حداقل فاصله بین دو درخواست OTP
OTP_MAX_ATTEMPTS_PER_HOUR = 10  # حداکثر ۱۰ درخواست OTP در ساعت
DEFAULT_PASSWORD = '123456789'  # رمز عبور اولیه استاد/هنرجو

# Rate limiting for password login
PW_MAX_ATTEMPTS = 5
PW_LOCKOUT_SECONDS = 300  # 5 minutes


class PasswordLoginView(View):
    """ورود با رمز عبور (شماره موبایل + رمز)"""
    panel = 'teacher'

    def get(self, request):
        role = 'TEACHER' if self.panel == 'teacher' else 'STUDENT'
        if request.user.is_authenticated and request.user.role == role:
            return self._redirect_home()
        return render(request, 'users/password_login.html', {'panel': self.panel})

    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')

        if not phone or not password:
            messages.error(request, 'شماره موبایل و رمز عبور را وارد کنید.')
            return render(request, 'users/password_login.html', {'panel': self.panel})

        # Rate limiting
        now = time.time()
        attempts = request.session.get('pw_login_attempts', 0)
        last_attempt = request.session.get('pw_last_attempt', 0)

        if attempts >= PW_MAX_ATTEMPTS:
            elapsed = now - last_attempt
            if elapsed < PW_LOCKOUT_SECONDS:
                remaining = int(PW_LOCKOUT_SECONDS - elapsed)
                messages.error(request, f'تعداد تلاش‌های ناموفق بیش از حد مجاز است. لطفاً {remaining} ثانیه صبر کنید.')
                return render(request, 'users/password_login.html', {'panel': self.panel})
            else:
                request.session['pw_login_attempts'] = 0
                attempts = 0

        role = 'TEACHER' if self.panel == 'teacher' else 'STUDENT'
        user = authenticate(request, username=phone, password=password)

        if user is None or user.role != role:
            request.session['pw_login_attempts'] = attempts + 1
            request.session['pw_last_attempt'] = now
            messages.error(request, 'شماره موبایل یا رمز عبور اشتباه است.')
            return render(request, 'users/password_login.html', {'panel': self.panel})

        # Login موفق
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session.pop('pw_login_attempts', None)
        request.session.pop('pw_last_attempt', None)
        return self._redirect_home()

    def _redirect_home(self):
        if self.panel == 'teacher':
            return redirect('teacher:dashboard')
        return redirect('student:dashboard')


class TeacherPasswordLoginView(PasswordLoginView):
    panel = 'teacher'


class StudentPasswordLoginView(PasswordLoginView):
    panel = 'student'


def _send_otp_sms(phone: str, code: str):
    if not send_sms(phone, f'کد ورود دانا: {code}\nمعتبر تا ۵ دقیقه'):
        logger.error("OTP SMS failed for %s.", phone)


class OTPRequestView(View):
    """مرحله اول: وارد کردن شماره موبایل"""
    panel = 'teacher'  # یا 'student'

    def get(self, request):
        role = 'TEACHER' if self.panel == 'teacher' else 'STUDENT'
        if request.user.is_authenticated and request.user.role == role:
            return redirect(self._home())
        return render(request, 'users/otp_request.html', {'panel': self.panel})

    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        if not phone or len(phone) != 11 or not phone.startswith('09'):
            messages.error(request, 'شماره موبایل معتبر وارد کنید (مثلاً ۰۹۱۲۳۴۵۶۷۸۹).')
            return render(request, 'users/otp_request.html', {'panel': self.panel})

        # --- Rate Limiting ---
        now = time.time()
        last_otp_time = request.session.get('otp_last_request_time', 0)
        otp_attempts = request.session.get('otp_hour_attempts', 0)

        # فاصله زمانی بین درخواست‌ها
        if now - last_otp_time < OTP_MIN_INTERVAL_SECONDS:
            remaining = int(OTP_MIN_INTERVAL_SECONDS - (now - last_otp_time))
            messages.error(request, f'لطفاً {remaining} ثانیه صبر کنید و دوباره تلاش کنید.')
            return render(request, 'users/otp_request.html', {'panel': self.panel})

        # محدودیت تعداد درخواست در ساعت
        if otp_attempts >= OTP_MAX_ATTEMPTS_PER_HOUR:
            messages.error(request, 'تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً بعداً تلاش کنید.')
            return render(request, 'users/otp_request.html', {'panel': self.panel})

        # بررسی وجود کاربر با این موبایل + نقش صحیح
        role = 'TEACHER' if self.panel == 'teacher' else 'STUDENT'
        user = User.objects.filter(phone_number=phone, role=role).first()
        if not user:
            messages.error(request, 'این شماره موبایل در سیستم ثبت نشده.')
            return render(request, 'users/otp_request.html', {'panel': self.panel})

        otp = OTPToken.generate(phone)
        _send_otp_sms(phone, otp.code)
        request.session['otp_phone'] = phone
        request.session['otp_panel'] = self.panel
        request.session['otp_last_request_time'] = now
        request.session['otp_hour_attempts'] = otp_attempts + 1
        messages.success(request, f'کد تأیید به {phone} ارسال شد.')
        return redirect('users:otp_verify')

    def _home(self):
        return 'teacher:dashboard' if self.panel == 'teacher' else 'student:dashboard'


class TeacherOTPRequestView(OTPRequestView):
    panel = 'teacher'


class StudentOTPRequestView(OTPRequestView):
    panel = 'student'


class OTPVerifyView(View):
    """مرحله دوم: وارد کردن کد"""

    def _login_url(self, panel):
        if panel == 'student':
            return 'users:student_login'
        return 'users:teacher_login'

    def get(self, request):
        phone = request.session.get('otp_phone')
        panel = request.session.get('otp_panel', 'teacher')
        if not phone:
            return redirect(self._login_url(panel))
        return render(request, 'users/otp_verify.html', {'phone': phone, 'panel': panel})

    def post(self, request):
        phone = request.session.get('otp_phone')
        panel = request.session.get('otp_panel', 'teacher')
        code = request.POST.get('code', '').strip()

        if not phone:
            return redirect(self._login_url(panel))

        token = OTPToken.objects.filter(phone_number=phone, code=code, is_used=False).order_by('-created_at').first()

        if not token or not token.is_valid():
            messages.error(request, 'کد وارد شده نادرست یا منقضی شده است.')
            return render(request, 'users/otp_verify.html', {'phone': phone, 'panel': panel})

        token.is_used = True
        token.save()

        role = 'TEACHER' if panel == 'teacher' else 'STUDENT'
        user = User.objects.filter(phone_number=phone, role=role).first()
        if not user:
            messages.error(request, 'کاربری با این مشخصات یافت نشد.')
            return redirect('users:teacher_login')

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # پاکسازی کامل session OTP
        for key in ('otp_phone', 'otp_panel', 'otp_last_request_time', 'otp_hour_attempts'):
            request.session.pop(key, None)

        if panel == 'teacher':
            return redirect('teacher:dashboard')
        else:
            return redirect('student:dashboard')


class OTPResendView(View):
    """ارسال مجدد کد"""

    def _login_url(self, panel):
        if panel == 'student':
            return 'users:student_login'
        return 'users:teacher_login'

    def post(self, request):
        phone = request.session.get('otp_phone')
        panel = request.session.get('otp_panel', 'teacher')
        if not phone:
            return redirect(self._login_url(panel))

        # --- Rate Limiting ---
        now = time.time()
        last_otp_time = request.session.get('otp_last_request_time', 0)
        otp_attempts = request.session.get('otp_hour_attempts', 0)

        if now - last_otp_time < OTP_MIN_INTERVAL_SECONDS:
            remaining = int(OTP_MIN_INTERVAL_SECONDS - (now - last_otp_time))
            messages.error(request, f'لطفاً {remaining} ثانیه صبر کنید و دوباره تلاش کنید.')
            return redirect('users:otp_verify')

        if otp_attempts >= OTP_MAX_ATTEMPTS_PER_HOUR:
            messages.error(request, 'تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً بعداً تلاش کنید.')
            return redirect('users:otp_verify')

        otp = OTPToken.generate(phone)
        _send_otp_sms(phone, otp.code)
        request.session['otp_last_request_time'] = now
        request.session['otp_hour_attempts'] = otp_attempts + 1
        messages.success(request, 'کد جدید ارسال شد.')
        return redirect('users:otp_verify')
