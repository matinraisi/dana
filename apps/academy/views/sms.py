import logging
import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from apps.academy.mixins import AdminRequiredMixin

from ..models import Course, StudentEnrollment, SMSLog
from ..admin import send_plain_sms

logger = logging.getLogger(__name__)


def _get_receivers(request, target_type, message_text):
    """Get list of phone numbers based on target type."""
    from apps.crm.models import Lead
    from apps.users.models import User
    from apps.academy.models import Teacher

    recep_numbers = []
    if target_type == 'all':
        recep_numbers = list(StudentEnrollment.objects.all().values_list('phone_number', flat=True))
    elif target_type == 'course':
        course_id = request.POST.get('course_id') or request.GET.get('course_id')
        if course_id:
            recep_numbers = list(StudentEnrollment.objects.filter(
                active_enrollments__course_id=course_id
            ).values_list('phone_number', flat=True).distinct())
    elif target_type == 'selective':
        student_ids = request.POST.getlist('student_ids') or request.GET.getlist('student_ids')
        if student_ids:
            recep_numbers = list(StudentEnrollment.objects.filter(
                id__in=student_ids
            ).values_list('phone_number', flat=True))
    elif target_type == 'teachers':
        recep_numbers = list(
            Teacher.objects.filter(is_active=True).values_list('phone_number', flat=True)
        )
    elif target_type == 'teacher_selective':
        teacher_ids = request.POST.getlist('teacher_ids') or request.GET.getlist('teacher_ids')
        if teacher_ids:
            recep_numbers = list(Teacher.objects.filter(
                id__in=teacher_ids, is_active=True
            ).values_list('phone_number', flat=True))
    elif target_type == 'users':
        user_role = request.POST.get('user_role') or request.GET.get('user_role', '')
        qs = User.objects.filter(is_active=True).exclude(phone_number='')
        if user_role:
            qs = qs.filter(role=user_role)
        recep_numbers = list(qs.values_list('phone_number', flat=True))
    elif target_type == 'user_selective':
        user_ids = request.POST.getlist('user_ids') or request.GET.getlist('user_ids')
        if user_ids:
            recep_numbers = list(User.objects.filter(
                id__in=user_ids, is_active=True
            ).values_list('phone_number', flat=True))
    elif target_type == 'leads':
        lead_ids = request.POST.getlist('lead_ids') or request.GET.getlist('lead_ids')
        if lead_ids:
            recep_numbers = list(Lead.objects.filter(
                id__in=lead_ids
            ).values_list('phone_number', flat=True))
        else:
            recep_numbers = list(
                Lead.objects.exclude(phone_number='')
            .values_list('phone_number', flat=True))
    elif target_type == 'lead_status':
        status = request.POST.get('lead_status') or request.GET.get('lead_status')
        if status:
            recep_numbers = list(
                Lead.objects.filter(status=status).exclude(phone_number='')
            .values_list('phone_number', flat=True))

    return list(set([n.strip() for n in recep_numbers if n and n.strip()]))


class SMSDashboardView(AdminRequiredMixin, View):
    def get(self, request):
        from apps.users.models import User
        from apps.academy.models import Teacher
        courses = Course.objects.all()
        students = StudentEnrollment.objects.all()
        teachers = Teacher.objects.filter(is_active=True).select_related('user')
        users = User.objects.filter(is_active=True).exclude(phone_number='')
        from apps.crm.models import Lead
        leads = Lead.objects.exclude(phone_number='')

        # جستجو در لاگ‌ها
        search = request.GET.get('search', '').strip()
        sms_logs = SMSLog.objects.all()

        if search:
            sms_logs = sms_logs.filter(
                Q(receptor__icontains=search) | Q(message__icontains=search)
            )

        # صفحه‌بندی
        from django.core.paginator import Paginator
        page_number = request.GET.get('page', 1)
        paginator = Paginator(sms_logs, 15)
        page_obj = paginator.get_page(page_number)

        total_sms = SMSLog.objects.all().count()
        success_sms = SMSLog.objects.filter(is_sent=True).count()

        return render(request, 'academy/dashboard/sms_management.html', {
            'courses': courses,
            'students': students,
            'teachers': teachers,
            'users': users,
            'leads': leads,
            'sms_logs': page_obj,
            'page_obj': page_obj,
            'total_sms': total_sms,
            'success_sms': success_sms,
            'failed_sms': total_sms - success_sms,
            'search_query': search,
        })


class SMSManagementView(AdminRequiredMixin, View):
    def get(self, request):
        sms_logs = SMSLog.objects.all()[:100]
        total_sms = SMSLog.objects.all().count()
        success_sms = SMSLog.objects.filter(is_sent=True).count()
        return render(request, 'academy/dashboard/sms_management.html', {
            'sms_logs': sms_logs,
            'total_sms': total_sms,
            'success_sms': success_sms,
            'failed_sms': total_sms - success_sms,
        })


class SendBulkSMSView(AdminRequiredMixin, View):
    def post(self, request):
        target_type = request.POST.get('target_type')
        message_text = request.POST.get('message', '').strip()

        if not message_text:
            messages.error(request, "متن پیامک نمی‌تواند خالی باشد.")
            return redirect('academy:sms_dashboard')

        recep_numbers = _get_receivers(request, target_type, message_text)

        if not recep_numbers:
            messages.warning(request, "هیچ موبایلی با این فیلترها پیدا نشد.")
            return redirect('academy:sms_dashboard')

        success_count = 0
        for num in recep_numbers:
            is_sent = send_plain_sms(num, message_text)
            if is_sent:
                success_count += 1

        messages.success(request, f"پیامک به {success_count} از {len(recep_numbers)} نفر ارسال شد.")
        return redirect('academy:sms_dashboard')


class SMSAjaxSendView(AdminRequiredMixin, View):
    """AJAX endpoint: send SMS to one number at a time with progress."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': '.invalid JSON'}, status=400)

        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()

        if not phone or not message:
            return JsonResponse({'error': 'شماره یا متن خالی است'}, status=400)

        is_sent = send_plain_sms(phone, message)
        return JsonResponse({
            'success': is_sent,
            'phone': phone,
        })


class SMSAjaxPreviewView(AdminRequiredMixin, View):
    """AJAX endpoint: get receiver count before sending."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid JSON'}, status=400)

        target_type = data.get('target_type', '')
        message_text = data.get('message', '')

        # We need to fake request.POST/GET for _get_receivers
        from django.test import RequestFactory
        factory = RequestFactory()
        fake_request = factory.post('/', data={
            'target_type': target_type,
            'course_id': data.get('course_id', ''),
            'lead_status': data.get('lead_status', ''),
        })
        # Copy session and user from real request
        fake_request.session = request.session
        fake_request.user = request.user
        # For list data, pass via body
        if data.get('student_ids'):
            fake_request.POST = fake_request.POST.copy()
            fake_request.POST.setlist('student_ids', data['student_ids'])
        if data.get('teacher_ids'):
            fake_request.POST = fake_request.POST.copy()
            fake_request.POST.setlist('teacher_ids', data['teacher_ids'])
        if data.get('user_ids'):
            fake_request.POST = fake_request.POST.copy()
            fake_request.POST.setlist('user_ids', data['user_ids'])
        if data.get('user_role'):
            fake_request.POST = fake_request.POST.copy()
            fake_request.POST['user_role'] = data['user_role']
        if data.get('lead_ids'):
            fake_request.POST = fake_request.POST.copy()
            fake_request.POST.setlist('lead_ids', data['lead_ids'])

        receivers = _get_receivers(fake_request, target_type, message_text)

        return JsonResponse({
            'count': len(receivers),
            'phones': receivers,
        })
