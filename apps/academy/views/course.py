from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin

from ..models import Course
from ..utils.date_helper import to_gregorian
from apps.users.models import Teacher
from apps.schools.models import School


class CourseListView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        courses = self.filter_by_school(Course.objects.all()).order_by('-start_date')
        context = {
            'courses': courses,
            'active_count': courses.filter(status__in=['open', 'active']).count(),
            'open_count': courses.filter(status='open').count(),
            'completed_count': courses.filter(status='completed').count(),
        }
        return render(request, 'academy/dashboard/course_list.html', context)


class CourseCreateView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        teachers = self.filter_by_school(Teacher.objects.filter(is_active=True), school_field='user__school')
        all_courses = self.filter_by_school(Course.objects.all())
        schools = School.objects.filter(is_active=True) if request.user.is_superuser else None
        return render(request, 'academy/dashboard/course_create.html', {
            'teachers': teachers,
            'all_courses': all_courses,
            'schools': schools,
        })

    def post(self, request):
        title = request.POST.get('title')
        code = request.POST.get('code')
        if not title or not code:
            messages.error(request, "عنوان و کد دوره الزامی هستند.")
            return redirect('academy:course_create')

        if Course.objects.filter(code=code).exists():
            messages.error(request, f"دوره‌ای با کد {code} از قبل موجود است.")
            return redirect('academy:course_create')

        teacher_id = request.POST.get('teacher_id') or None
        prerequisite_id = request.POST.get('prerequisite_id') or None

        try:
            fee = int(request.POST.get('fee') or 0)
            max_students = int(request.POST.get('max_students') or 20)
        except ValueError:
            fee = 0
            max_students = 20

        is_active = request.POST.get('is_active') == 'on'
        allow_public_registration = request.POST.get('allow_public_registration') == 'on'
        start_date = to_gregorian(request.POST.get('start_date'))
        end_date = to_gregorian(request.POST.get('end_date'))
        description = request.POST.get('description') or ''
        level = request.POST.get('level') or 'beginner'
        status = request.POST.get('status') or 'draft'

        teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id else None
        prerequisite = Course.objects.filter(id=prerequisite_id).first() if prerequisite_id else None
        cover_image = request.FILES.get('cover_image')

        # تعیین مدرسه
        if request.user.is_superuser:
            school_id = request.POST.get('school_id')
            school = School.objects.filter(id=school_id).first() if school_id else None
        else:
            school = getattr(request.user, 'school', None)

        course = Course(
            title=title, code=code, description=description,
            level=level, status=status,
            teacher=teacher, prerequisite=prerequisite,
            max_students=max_students, fee=fee,
            start_date=start_date, end_date=end_date,
            is_active=is_active,
            allow_public_registration=allow_public_registration,
            school=school,
        )
        if cover_image:
            course.cover_image = cover_image
        course.save()

        # ارسال پیامک به استاد
        if teacher and teacher.user.phone_number:
            try:
                from apps.academy.services.sms_service import SmsService
                SmsService.send(
                    teacher.user.phone_number,
                    f"{teacher.user.get_full_name()} عزیز، دوره «{title}» به شما تخصیص داده شد.\nتاریخ شروع: {start_date or 'نامشخص'}\nبرای مشاهده جلسات وارد پنل استاد شوید.",
                    sms_type='course_assigned'
                )
            except Exception:
                pass

        messages.success(request, f"دوره «{title}» با موفقیت ثبت شد.")
        return redirect('academy:course_list')


class CourseEditView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request, pk):
        course = self.school_object_or_404(Course, pk=pk)
        teachers = self.filter_by_school(Teacher.objects.filter(is_active=True), school_field='user__school')
        all_courses = self.filter_by_school(Course.objects.exclude(pk=pk))
        return render(request, 'academy/dashboard/course_edit.html', {
            'course': course,
            'teachers': teachers,
            'all_courses': all_courses,
        })

    def post(self, request, pk):
        course = self.school_object_or_404(Course, pk=pk)
        title = request.POST.get('title', course.title)
        code = request.POST.get('code', course.code)

        if not title or not code:
            messages.error(request, "عنوان و کد دوره الزامی هستند.")
            return redirect('academy:course_edit', pk=pk)

        if Course.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, f"دوره‌ای با کد {code} از قبل موجود است.")
            return redirect('academy:course_edit', pk=pk)

        teacher_id = request.POST.get('teacher_id') or None
        prerequisite_id = request.POST.get('prerequisite_id') or None

        try:
            fee = int(request.POST.get('fee') or 0)
            max_students = int(request.POST.get('max_students') or 20)
        except ValueError:
            fee = course.fee
            max_students = course.max_students

        is_active = request.POST.get('is_active') == 'on'
        allow_public_registration = request.POST.get('allow_public_registration') == 'on'
        start_date = to_gregorian(request.POST.get('start_date'))
        end_date = to_gregorian(request.POST.get('end_date'))
        description = request.POST.get('description') or ''
        level = request.POST.get('level') or course.level
        status = request.POST.get('status') or course.status

        teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id else None
        prerequisite = Course.objects.filter(id=prerequisite_id).first() if prerequisite_id else None
        cover_image = request.FILES.get('cover_image')

        course.title = title
        course.code = code
        course.description = description
        course.level = level
        course.status = status
        course.teacher = teacher
        course.prerequisite = prerequisite
        course.max_students = max_students
        course.fee = fee
        course.start_date = start_date
        course.end_date = end_date
        course.is_active = is_active
        course.allow_public_registration = allow_public_registration
        if cover_image:
            course.cover_image = cover_image
        course.save()

        messages.success(request, f"دوره «{title}» با موفقیت بروزرسانی شد.")
        return redirect('academy:course_list')


class CourseDeleteView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, pk):
        course = self.school_object_or_404(Course, pk=pk)
        title = course.title
        course.delete()
        messages.success(request, f"دوره «{title}» با موفقیت حذف شد.")
        return redirect('academy:course_list')
