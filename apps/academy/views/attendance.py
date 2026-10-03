from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin
from django.views import View

from ..models import Session, Course
from ..models.material import SessionMaterial
from ..services.attendance_service import AttendanceService
from ..utils.date_helper import to_gregorian


class SessionListView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, course_id):
        course = self.school_object_or_404(Course, id=course_id)
        sessions = course.sessions.order_by('session_number')
        return render(request, 'academy/attendance/session_list.html', {
            'course': course, 'sessions': sessions,
        })


class SessionCreateView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, course_id):
        course = self.school_object_or_404(Course, id=course_id)
        title = request.POST.get('title', f"جلسه {course.sessions.count() + 1}")
        start_date = to_gregorian(request.POST.get('date'))
        start_time = request.POST.get('start_time') or None
        end_time = request.POST.get('end_time') or None
        location = request.POST.get('location', '').strip() or None
        repeat_weeks = int(request.POST.get('repeat_weeks', 1) or 1)
        repeat_days = request.POST.getlist('repeat_days')

        if not start_date:
            messages.error(request, "تاریخ جلسه الزامی است.")
            return redirect('academy:session_list', course_id=course_id)

        session_number = course.sessions.count() + 1
        created_count = 0

        if repeat_weeks > 1 and repeat_days:
            for week in range(repeat_weeks):
                for day_str in repeat_days:
                    try:
                        day_num = int(day_str)
                    except (ValueError, TypeError):
                        continue
                    session_date = start_date + timedelta(weeks=week, days=(day_num - start_date.weekday()) % 7)
                    if session_date < start_date:
                        continue
                    Session.objects.create(
                        course=course, title=title, session_number=session_number,
                        date=session_date, start_time=start_time, end_time=end_time,
                        location=location,
                    )
                    session_number += 1
                    created_count += 1
        else:
            Session.objects.create(
                course=course, title=title, session_number=session_number,
                date=start_date, start_time=start_time, end_time=end_time,
                location=location,
            )
            created_count = 1

        messages.success(request, f"{created_count} جلسه با موفقیت ایجاد شد.")
        return redirect('academy:session_list', course_id=course_id)


class AttendanceSheetView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, session_id):
        data = AttendanceService.get_sheet(session_id)
        return render(request, 'academy/attendance/attendance_sheet.html', data)

    def post(self, request, session_id):
        attendance_data = {}
        for key, value in request.POST.items():
            if key.startswith('status_'):
                try:
                    student_id = int(key.replace('status_', ''))
                except (ValueError, TypeError):
                    continue
                attendance_data[student_id] = value
        count = AttendanceService.bulk_save(session_id, attendance_data)
        messages.success(request, f"حضور و غیاب {count} نفر با موفقیت ثبت شد.")
        return redirect('academy:attendance_sheet', session_id=session_id)


class StudentAttendanceReportView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, student_id, course_id):
        report = AttendanceService.get_student_report(student_id, course_id)
        return render(request, 'academy/attendance/student_report.html', report)


class CourseAttendanceSummaryView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, course_id):
        course = self.school_object_or_404(Course, id=course_id)
        students = AttendanceService.get_course_summary(course_id)
        total_sessions = course.sessions.count()
        return render(request, 'academy/attendance/course_summary.html', {
            'course': course, 'students': students, 'total_sessions': total_sessions,
        })

    def post(self, request, course_id):
        course = self.school_object_or_404(Course, id=course_id)
        action = request.POST.get('action')
        if action == 'add_material':
            title = request.POST.get('title')
            if not title:
                messages.error(request, "عنوان محتوا الزامی است.")
                return redirect('academy:course_attendance_summary', course_id=course_id)
            from django.db.models import Max
            max_order = SessionMaterial.objects.filter(course=course).aggregate(m=Max('order'))['m'] or 0
            SessionMaterial.objects.create(
                course=course, title=title,
                description=request.POST.get('description', ''),
                material_type=request.POST.get('material_type', 'file'),
                file=request.FILES.get('file'),
                link_url=request.POST.get('link_url', ''),
                order=max_order + 1,
            )
            messages.success(request, f"محتوا «{title}» اضافه شد.")
        elif action == 'delete_material':
            mid = request.POST.get('material_id')
            SessionMaterial.objects.filter(id=mid, course=course).delete()
            messages.success(request, "محتوا حذف شد.")
        return redirect('academy:course_attendance_summary', course_id=course_id)


class AdminMaterialListView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        import django.db.models as models
        materials = self.filter_by_school(
            SessionMaterial.objects.select_related('course', 'session').order_by('-created_at'),
            school_field='course__school'
        )
        courses = self.filter_by_school(Course.objects.all())
        t = request.GET.get('type', '')
        c = request.GET.get('course', '')
        if t:
            materials = materials.filter(material_type=t)
        if c:
            materials = materials.filter(models.Q(course_id=c) | models.Q(session__course_id=c))
        return render(request, 'academy/attendance/admin_materials.html', {
            'materials': materials, 'courses': courses,
            'filter_type': t, 'filter_course': c,
        })
