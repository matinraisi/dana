import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin
from django.contrib import messages

from django.db.models import Count
from apps.users.models import User, Teacher, StudentAccount
from apps.academy.models import StudentEnrollment

logger = logging.getLogger(__name__)


class UserListView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        role_filter = request.GET.get('role', '')
        users = self.filter_by_school(User.objects.all(), school_field='school').order_by('role', 'first_name')
        if role_filter:
            users = users.filter(role=role_filter)
        role_counts = dict(self.filter_by_school(User.objects.all(), school_field='school').values_list('role').annotate(count=Count('id')))
        role_choices_with_count = [(val, label, role_counts.get(val, 0)) for val, label in User.ROLE_CHOICES]
        return render(request, 'academy/dashboard/user_list.html', {
            'users': users,
            'role_filter': role_filter,
            'role_choices': User.ROLE_CHOICES,
            'role_choices_with_count': role_choices_with_count,
        })


class UserCreateView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        students_without_account = self.filter_by_school(StudentEnrollment.objects.filter(
            user_account__isnull=True
        )).order_by('first_name')
        return render(request, 'academy/dashboard/user_create.html', {
            'role_choices': User.ROLE_CHOICES,
            'students_without_account': students_without_account,
        })

    def post(self, request):
        role = request.POST.get('role', 'STUDENT')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        username = request.POST.get('username', '').strip() or f"u_{phone}"

        if not phone:
            messages.error(request, 'شماره موبایل الزامی است.')
            return redirect('academy:user_create')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'نام کاربری «{username}» قبلاً استفاده شده.')
            return redirect('academy:user_create')

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            role=role,
            school=getattr(request.user, 'school', None),
        )

        # اگر نقش استاد است → Teacher profile بساز + پیامک بفرست
        if role == 'TEACHER':
            try:
                salary_per_session = int(request.POST.get('salary_per_session') or 0)
            except (ValueError, TypeError):
                salary_per_session = 0
            teacher, _ = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': phone,
                    'specialization': request.POST.get('specialization', ''),
                    'salary_per_session': salary_per_session,
                    'card_number': request.POST.get('card_number', '').strip() or None,
                    'shaba_number': request.POST.get('shaba_number', '').strip() or None,
                }
            )
            # ارسال پیامک خوش‌آمدگویی استاد
            try:
                from apps.academy.services.sms_service import SmsService
                SmsService.send(
                    phone,
                    f"{first_name} {last_name} عزیز، حساب کاربری شما در سیستم ایجاد شد.\nنام کاربری: {username}\nبرای ورود به پنل استاد از شماره موبایل خود استفاده کنید.",
                    sms_type='teacher_welcome'
                )
            except Exception as e:
                logger.error(f"SMS failed for teacher {phone}: {e}")

        # اگر نقش هنرجو است
        if role == 'STUDENT':
            enrollment_id = request.POST.get('enrollment_id')
            if enrollment_id:
                try:
                    enrollment = StudentEnrollment.objects.get(id=enrollment_id)
                    StudentAccount.objects.get_or_create(user=user, defaults={'enrollment': enrollment})
                except StudentEnrollment.DoesNotExist:
                    pass

        messages.success(request, f'کاربر «{user.get_full_name() or username}» با نقش {user.get_role_display()} ساخته شد.')
        return redirect('academy:user_list')


class UserEditView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        teacher = getattr(user, 'teacher_profile', None)
        students_without_account = self.filter_by_school(StudentEnrollment.objects.filter(
            user_account__isnull=True
        )).order_by('first_name')
        return render(request, 'academy/dashboard/user_edit.html', {
            'edit_user': user,
            'teacher': teacher,
            'role_choices': User.ROLE_CHOICES,
            'students_without_account': students_without_account,
        })

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.phone_number = request.POST.get('phone_number', user.phone_number).strip()
        user.role = request.POST.get('role', user.role)
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()

        # بروزرسانی Teacher profile
        if user.role == 'TEACHER':
            teacher, _ = Teacher.objects.get_or_create(user=user)
            teacher.phone_number = user.phone_number
            teacher.specialization = request.POST.get('specialization', teacher.specialization or '')
            teacher.card_number = request.POST.get('card_number', '').strip() or None
            teacher.shaba_number = request.POST.get('shaba_number', '').strip() or None
            sal = request.POST.get('salary_per_session')
            if sal:
                try:
                    teacher.salary_per_session = int(sal)
                except (ValueError, TypeError):
                    pass
            teacher.save()

        messages.success(request, 'اطلاعات کاربر بروزرسانی شد.')
        return redirect('academy:user_list')


class UserToggleActiveView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'نمی‌توانید حساب خودتان را غیرفعال کنید.')
            return redirect('academy:user_list')
        user.is_active = not user.is_active
        user.save()
        status = 'فعال' if user.is_active else 'غیرفعال'
        messages.success(request, f'حساب «{user.get_full_name() or user.username}» {status} شد.')
        return redirect('academy:user_list')
