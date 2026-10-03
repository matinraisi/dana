from django.shortcuts import render, redirect
from django.views import View
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
import time

from ..models import Course, StudentEnrollment, AcademyInstallment, AccountingTransaction, Session, CourseEnrollment

# Admin login lockout constants
ADMIN_MAX_ATTEMPTS = 5
ADMIN_LOCKOUT_SECONDS = 300  # 5 minutes


class AcademyLoginView(LoginView):
    template_name = 'academy/dashboard/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        # Rate limiting برای لاگین مدیر
        request = self.request
        now = time.time()
        attempts = request.session.get('login_attempts', 0)
        last_attempt = request.session.get('last_login_attempt', 0)

        # اگر قفل باشد
        if attempts >= ADMIN_MAX_ATTEMPTS:
            elapsed = now - last_attempt
            if elapsed < ADMIN_LOCKOUT_SECONDS:
                remaining = int(ADMIN_LOCKOUT_SECONDS - elapsed)
                messages.error(
                    request,
                    f'تعداد تلاش‌های ناموفق بیش از حد مجاز است. لطفاً {remaining} ثانیه صبر کنید.'
                )
                return super().form_invalid(form)
            else:
                # قفل تمام شد — ریست
                request.session['login_attempts'] = 0

        request.session['login_attempts'] = attempts + 1
        request.session['last_login_attempt'] = now

        return super().form_invalid(form)


class AcademyLogoutView(LogoutView):
    next_page = 'academy:login'


class DashboardHomeView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        school_id = self.get_school_id()
        is_super = request.user.is_superuser

        courses = self.filter_by_school(Course.objects.all())
        base_kw = {} if is_super else {'student__school_id': school_id}
        base_kw2 = {} if is_super else {'course__school_id': school_id}

        total_students = self.filter_by_school(StudentEnrollment.objects.all()).count()
        total_courses = courses.count()
        active_courses = courses.filter(status__in=['open', 'active']).count()
        pending_docs = self.filter_by_school(
            StudentEnrollment.objects.filter(document_status='pending')
        ).count()
        overdue_count = self.filter_by_school(
            AcademyInstallment.objects.filter(status='overdue'),
            school_field='enrollment__student__school'
        ).count()
        income_total = AccountingTransaction.objects.filter(
            transaction_type='income', **base_kw2
        ).aggregate(s=Sum('amount'))['s'] or 0
        expense_total = AccountingTransaction.objects.filter(
            transaction_type='expense', **base_kw2
        ).aggregate(s=Sum('amount'))['s'] or 0
        enrollments_qs = CourseEnrollment.objects.filter(**base_kw).select_related(
            'student', 'course'
        ).order_by('-enrolled_at')[:5]
        today = timezone.now().date()
        upcoming_sessions = Session.objects.filter(
            date__gte=today, **base_kw2
        ).select_related('course').order_by('date', 'start_time')[:5]

        context = {
            'total_students': total_students,
            'total_courses': total_courses,
            'active_courses': active_courses,
            'pending_docs_count': pending_docs,
            'overdue_count': overdue_count,
            'income_total': income_total,
            'expense_total': expense_total,
            'net_profit': income_total - expense_total,
            'recent_enrollments': enrollments_qs,
            'upcoming_sessions': upcoming_sessions,
        }
        return render(request, 'academy/dashboard/home.html', context)
