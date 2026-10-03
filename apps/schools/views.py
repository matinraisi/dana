import logging

from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.conf import settings
from apps.users.models import User
from apps.notifications.sms import send_sms
from .models import School

logger = logging.getLogger(__name__)

def _notify_admin_new_school(title, admin_name, admin_phone):
    """ارسال پیامک به مدیر سیستم هنگام ثبت‌نام آموزشگاه جدید"""
    msg = (
        f"آموزشگاه جدید ثبت‌نام کرد:\n"
        f"نام آموزشگاه: {title}\n"
        f"نام مدیر: {admin_name}\n"
        f"شماره تماس: {admin_phone}\n"
        f"وضعیت: در انتظار تأیید"
    )
    for phone in settings.SMS_ADMIN_PHONES:
        send_sms(phone, msg)


class SchoolRegisterView(View):
    template_name = 'schools/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('academy:dashboard_home')
        return render(request, self.template_name)

    def post(self, request):
        title = request.POST.get('title', '').strip()
        admin_name = request.POST.get('admin_name', '').strip()
        admin_phone = request.POST.get('admin_phone', '').strip()
        admin_email = request.POST.get('admin_email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not all([title, admin_name, admin_phone, password, password2]):
            messages.error(request, "همه فیلدهای الزامی را پر کنید.")
            return render(request, self.template_name, {'post': request.POST})

        if password != password2:
            messages.error(request, "رمز عبور با تکرار آن مطابقت ندارد.")
            return render(request, self.template_name, {'post': request.POST})

        if len(password) < 6:
            messages.error(request, "رمز عبور باید حداقل ۶ کاراکتر باشد.")
            return render(request, self.template_name, {'post': request.POST})

        if User.objects.filter(phone_number=admin_phone).exists():
            messages.error(request, "این شماره موبایل قبلاً ثبت شده است.")
            return render(request, self.template_name, {'post': request.POST})

        username = admin_phone
        base = username
        i = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}_{i}"
            i += 1

        user = User.objects.create_user(
            username=username,
            password=password,
            phone_number=admin_phone,
            email=admin_email or '',
            first_name=admin_name,
            role='MANAGER_ACADEMY',
            is_active=True,
        )

        school = School.objects.create(
            title=title,
            owner=user,
            is_active=False,
        )

        user.school = school
        user.save(update_fields=['school'])

        # ارسال پیامک اطلاع‌رسانی به مدیر سیستم
        _notify_admin_new_school(title, admin_name, admin_phone)

        messages.success(
            request,
            f"آموزشگاه شما با موفقیت ثبت شد. نام کاربری شما: {username} — پس از تأیید ادمین اصلی، می‌توانید وارد شوید."
        )
        return redirect('schools:registered')


class SchoolRegisteredView(View):
    template_name = 'schools/registered.html'

    def get(self, request):
        return render(request, self.template_name)
