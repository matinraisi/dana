from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.urls import reverse

from apps.academy.models import StudentEnrollment, CourseEnrollment, Course, Attendance, Session
from apps.academy.models.material import SessionMaterial
from apps.academy.models.accounting import PaymentGateway, PaymentRequest, AccountingTransaction
from apps.academy.views.student import validate_image_file
from apps.academy.services.idcard_service import IDCardService
from apps.academy.services.payment_flow import gateway_for, start_online_payment
from apps.academy.views.payment import get_callback_url

from apps.users.mixins import RoleRequiredMixin


class StudentRequiredMixin(RoleRequiredMixin):
    role = 'STUDENT'
    panel = 'student'
    login_url = '/auth/student/login/'

    def get_student_enrollment(self, request):
        try:
            return request.user.student_account.enrollment
        except Exception:
            return None


class StudentDashboardView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return render(request, 'student/no_enrollment.html')

        course_enrollments = enrollment.active_enrollments.select_related('course').all()
        card = getattr(enrollment, 'id_card', None)

        course_ids = enrollment.active_enrollments.values_list('course_id', flat=True)
        upcoming_meetings = Session.objects.filter(
            course_id__in=course_ids, meeting_type__in=['jitsi', 'google_meet', 'zoom', 'bigbluebutton', 'custom']
        ).exclude(meeting_link__isnull=True).exclude(meeting_link=''
        ).select_related('course').order_by('date', 'start_time')[:10]

        return render(request, 'student/dashboard.html', {
            'student': enrollment,
            'course_enrollments': course_enrollments,
            'card': card,
            'total_courses': course_enrollments.count(),
            'total_paid': sum(e.paid_amount for e in course_enrollments),
            'total_remaining': sum(e.remaining_amount for e in course_enrollments),
            'upcoming_meetings': upcoming_meetings,
        })


class StudentCoursesView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        course_enrollments = enrollment.active_enrollments.select_related(
            'course', 'course__teacher'
        ).prefetch_related('installments')

        return render(request, 'student/courses.html', {
            'student': enrollment,
            'course_enrollments': course_enrollments,
        })


class StudentAttendanceView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        attendances = Attendance.objects.filter(
            student=enrollment
        ).select_related('session__course').order_by('-session__date')

        by_course = {}
        for att in attendances:
            c = att.session.course
            if c.id not in by_course:
                by_course[c.id] = {'course': c, 'records': [], 'present': 0, 'absent': 0}
            by_course[c.id]['records'].append(att)
            if att.status in ('present', 'late'):
                by_course[c.id]['present'] += 1
            elif att.status == 'absent':
                by_course[c.id]['absent'] += 1

        return render(request, 'student/attendance.html', {
            'student': enrollment,
            'by_course': by_course.values(),
        })


class StudentPaymentsView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        course_enrollments = enrollment.active_enrollments.select_related('course').prefetch_related(
            'installments'
        )

        return render(request, 'student/payments.html', {
            'student': enrollment,
            'course_enrollments': course_enrollments,
        })


class StudentPaymentInitiateView(StudentRequiredMixin, View):
    def post(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            messages.error(request, 'هنرجو یافت نشد.')
            return redirect('student:payments')

        course_enrollment_id = request.POST.get('enrollment_id')
        amount = request.POST.get('amount')
        if not course_enrollment_id or not amount:
            messages.error(request, 'اطلاعات پرداخت ناقص است.')
            return redirect('student:payments')

        course_enrollment = get_object_or_404(CourseEnrollment, id=course_enrollment_id)

        if course_enrollment.student_id != enrollment.id:
            messages.error(request, 'این ثبت‌نامه متعلق به شما نیست.')
            return redirect('student:payments')

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            messages.error(request, 'مبلغ پرداخت معتبر نیست.')
            return redirect('student:payments')
        if amount <= 0 or amount > course_enrollment.remaining_amount:
            messages.error(request, 'مبلغ نامعتبر است.')
            return redirect('student:payments')

        # The school's gateway first, as every other payment view does. This view
        # used to take any active gateway — another school's PIN, on a
        # multi-school install.
        gateway = gateway_for(course_enrollment)
        if not gateway or not gateway.merchant_code:
            messages.error(request, 'درگاه پرداخت آنلاین فعال یافت نشد. با مدیریت تماس بگیرید.')
            return redirect('student:payments')

        pay_url, error = start_online_payment(
            request, enrollment=course_enrollment, student=enrollment, amount=amount, gateway=gateway,
            description=f'پرداخت آنلاین {course_enrollment.course.title}',
            legacy_callback_url=get_callback_url(request),
        )
        if pay_url:
            return redirect(pay_url)
        messages.error(request, f'خطا: {error}')
        return redirect('student:payments')


class StudentIDCardView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        card = getattr(enrollment, 'id_card', None)
        return render(request, 'student/id_card.html', {
            'student': enrollment,
            'card': card,
        })


class StudentRoadmapView(StudentRequiredMixin, View):
    """مسیر یادگیری هنرجو بر اساس پیش‌نیازها"""

    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        completed_course_ids = list(
            enrollment.active_enrollments.filter(
                course__status='completed'
            ).values_list('course_id', flat=True)
        )

        next_courses = Course.objects.filter(
            prerequisite_id__in=completed_course_ids,
            status__in=['upcoming', 'open'],
        ).select_related('teacher', 'prerequisite')

        open_courses = Course.objects.filter(
            status__in=['upcoming', 'open'],
            prerequisite__isnull=True,
        ).exclude(
            id__in=enrollment.active_enrollments.values_list('course_id', flat=True)
        )

        return render(request, 'student/roadmap.html', {
            'student': enrollment,
            'completed_ids': completed_course_ids,
            'next_courses': next_courses,
            'open_courses': open_courses,
        })


class StudentProfileView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        return render(request, 'student/profile.html', {'student': enrollment})

    def post(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        if request.FILES.get('avatar_3x4'):
            valid, err = validate_image_file(request.FILES['avatar_3x4'])
            if not valid:
                messages.error(request, err)
                return redirect('student:profile')
            enrollment.avatar_3x4 = request.FILES['avatar_3x4']
        if request.FILES.get('national_card_img'):
            valid, err = validate_image_file(request.FILES['national_card_img'])
            if not valid:
                messages.error(request, err)
                return redirect('student:profile')
            enrollment.national_card_img = request.FILES['national_card_img']
        if request.FILES.get('identity_img'):
            valid, err = validate_image_file(request.FILES['identity_img'])
            if not valid:
                messages.error(request, err)
                return redirect('student:profile')
            enrollment.identity_img = request.FILES['identity_img']
        enrollment.save()
        messages.success(request, 'مدارک با موفقیت بروزرسانی شد.')
        return redirect('student:profile')


class StudentSessionsView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        course_ids = enrollment.active_enrollments.values_list('course_id', flat=True)
        sessions = Session.objects.filter(
            course_id__in=course_ids
        ).select_related('course').order_by('-date', '-start_time')

        return render(request, 'student/sessions.html', {
            'student': enrollment,
            'sessions': sessions,
        })


class StudentMaterialListView(StudentRequiredMixin, View):
    def get(self, request):
        enrollment = self.get_student_enrollment(request)
        if not enrollment:
            return redirect('student:dashboard')

        course_ids = enrollment.active_enrollments.values_list('course_id', flat=True)
        materials = SessionMaterial.objects.filter(
            course_id__in=course_ids, is_active=True
        ).select_related('session__course').order_by('-created_at')

        cid = request.GET.get('course')
        if cid:
            materials = materials.filter(course_id=cid)

        return render(request, 'student/materials.html', {
            'student': enrollment,
            'materials': materials,
            'courses': enrollment.active_enrollments.select_related('course').all(),
        })
