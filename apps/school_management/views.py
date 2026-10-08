from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))

from .models import (
    AcademicYear,
    Classroom,
    GradeLevel,
    Guardian,
    SchoolEnrollment,
    SchoolProfile,
    Student,
    StudentGuardian,
    StudyField,
)


class SchoolStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "school_admin:login"

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_superuser or user.is_staff or getattr(user, "is_school_user", False)
        )


class SchoolDashboardView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        profile = SchoolProfile.objects.first()
        context = {
            "profile": profile,
            "nav": "home",
            "stats": {
                "students": Student.objects.filter(is_active=True).count(),
                "classrooms": Classroom.objects.filter(is_active=True).count(),
                "guardians": Guardian.objects.count(),
                "enrollments": SchoolEnrollment.objects.filter(status=SchoolEnrollment.Status.ACTIVE).count(),
                "years": AcademicYear.objects.count(),
            },
            "active_year": AcademicYear.objects.filter(is_active=True).first(),
            "recent_students": Student.objects.order_by("-created_at")[:8],
        }
        return render(request, "school_management/dashboard.html", context)


class AcademicYearListView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        return render(request, "school_management/year_list.html", {
            "nav": "years",
            "years": AcademicYear.objects.annotate(classroom_count=Count("classrooms")),
        })

    def post(self, request):
        title = request.POST.get("title", "").strip()
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        is_active = request.POST.get("is_active") == "on"
        if not title or not start_date or not end_date:
            messages.error(request, "عنوان و تاریخ‌ها الزامی هستند.")
            return redirect("school_management:years")
        year = AcademicYear(
            title=title,
            start_date=_parse_date(start_date),
            end_date=_parse_date(end_date),
            is_active=is_active,
        )
        try:
            year.full_clean()
            if is_active:
                AcademicYear.objects.filter(is_active=True).update(is_active=False)
            year.save()
            messages.success(request, "سال تحصیلی ذخیره شد.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("school_management:years")


class StructureListView(SchoolStaffRequiredMixin, View):
    """Grades, fields, classrooms — first structural slice."""

    def get(self, request):
        return render(request, "school_management/structure.html", {
            "nav": "structure",
            "grades": GradeLevel.objects.all(),
            "fields": StudyField.objects.all(),
            "classrooms": Classroom.objects.select_related("academic_year", "grade_level", "study_field"),
            "years": AcademicYear.objects.all(),
        })

    def post(self, request):
        action = request.POST.get("action")
        try:
            if action == "add_grade":
                GradeLevel.objects.create(
                    title=request.POST.get("title", "").strip(),
                    order=int(request.POST.get("order") or 0),
                )
            elif action == "add_field":
                StudyField.objects.create(
                    title=request.POST.get("title", "").strip(),
                    code=request.POST.get("code", "").strip(),
                )
            elif action == "add_classroom":
                Classroom.objects.create(
                    academic_year_id=request.POST.get("academic_year_id"),
                    grade_level_id=request.POST.get("grade_level_id"),
                    study_field_id=request.POST.get("study_field_id") or None,
                    title=request.POST.get("title", "").strip(),
                    code=request.POST.get("code", "").strip(),
                    capacity=int(request.POST.get("capacity") or 30),
                    gender=request.POST.get("gender") or Classroom.Gender.COED,
                )
            messages.success(request, "ذخیره شد.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("school_management:structure")


class StudentListView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        q = request.GET.get("q", "").strip()
        qs = Student.objects.all()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(national_code__icontains=q)
                | Q(mobile_number__icontains=q)
            )
        return render(request, "school_management/student_list.html", {
            "nav": "students",
            "page_obj": Paginator(qs, 25).get_page(request.GET.get("page", 1)),
            "query": q,
        })


class StudentCreateView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        return render(request, "school_management/student_form.html", {
            "nav": "students",
            "title": "ثبت دانش‌آموز",
            "genders": Student.Gender.choices,
        })

    def post(self, request):
        student = Student(
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            national_code=request.POST.get("national_code", "").strip(),
            gender=request.POST.get("gender") or Student.Gender.BOY,
            mobile_number=request.POST.get("mobile_number", "").strip(),
            address=request.POST.get("address", "").strip(),
            birth_date=_parse_date(request.POST.get("birth_date")),
        )
        try:
            student.full_clean()
            student.save()
            messages.success(request, "دانش‌آموز ثبت شد.")
            return redirect("school_management:student_detail", pk=student.pk)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("school_management:student_create")


class StudentDetailView(SchoolStaffRequiredMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        return render(request, "school_management/student_detail.html", {
            "nav": "students",
            "student": student,
            "links": student.guardian_links.select_related("guardian"),
            "enrollments": student.school_enrollments.select_related("academic_year", "classroom"),
            "guardians": Guardian.objects.all()[:100],
            "years": AcademicYear.objects.all(),
            "classrooms": Classroom.objects.select_related("academic_year", "grade_level"),
            "relationships": StudentGuardian.Relationship.choices,
            "statuses": SchoolEnrollment.Status.choices,
        })

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        action = request.POST.get("action")
        try:
            if action == "link_guardian":
                guardian_id = request.POST.get("guardian_id")
                if request.POST.get("new_guardian") == "1":
                    guardian = Guardian.objects.create(
                        first_name=request.POST.get("g_first_name", "").strip(),
                        last_name=request.POST.get("g_last_name", "").strip(),
                        mobile_number=request.POST.get("g_mobile", "").strip(),
                        national_code=request.POST.get("g_national_code") or None,
                    )
                else:
                    guardian = get_object_or_404(Guardian, pk=guardian_id)
                link = StudentGuardian(
                    student=student,
                    guardian=guardian,
                    relationship=request.POST.get("relationship") or StudentGuardian.Relationship.FATHER,
                    is_primary=request.POST.get("is_primary") == "on",
                    receives_notifications=request.POST.get("receives_notifications") == "on",
                )
                link.full_clean()
                link.save()
                messages.success(request, "ولی متصل شد.")
            elif action == "enroll":
                enrollment = SchoolEnrollment(
                    student=student,
                    academic_year_id=request.POST.get("academic_year_id"),
                    classroom_id=request.POST.get("classroom_id"),
                    student_number=request.POST.get("student_number") or None,
                    status=request.POST.get("status") or SchoolEnrollment.Status.ACTIVE,
                    enrolled_at=_parse_date(request.POST.get("enrolled_at")),
                    note=request.POST.get("note", "").strip(),
                )
                enrollment.full_clean()
                enrollment.save()
                messages.success(request, "ثبت‌نام تحصیلی ذخیره شد.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("school_management:student_detail", pk=pk)


class GuardianListView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        q = request.GET.get("q", "").strip()
        qs = Guardian.objects.all()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(mobile_number__icontains=q)
                | Q(national_code__icontains=q)
            )
        return render(request, "school_management/guardian_list.html", {
            "nav": "guardians",
            "page_obj": Paginator(qs, 25).get_page(request.GET.get("page", 1)),
            "query": q,
        })

    def post(self, request):
        try:
            Guardian.objects.create(
                first_name=request.POST.get("first_name", "").strip(),
                last_name=request.POST.get("last_name", "").strip(),
                mobile_number=request.POST.get("mobile_number", "").strip(),
                national_code=request.POST.get("national_code") or None,
                address=request.POST.get("address", "").strip(),
            )
            messages.success(request, "ولی ثبت شد.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("school_management:guardians")


class EnrollmentListView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        year_raw = request.GET.get("year", "").strip()
        try:
            year_id = int(year_raw) if year_raw else None
        except (TypeError, ValueError):
            year_id = None
        qs = SchoolEnrollment.objects.select_related("student", "academic_year", "classroom")
        if year_id is not None:
            qs = qs.filter(academic_year_id=year_id)
        return render(request, "school_management/enrollment_list.html", {
            "nav": "enrollments",
            "page_obj": Paginator(qs, 25).get_page(request.GET.get("page", 1)),
            "years": AcademicYear.objects.all(),
            "active_year": str(year_id) if year_id is not None else "",
        })


class SchoolProfileEditView(SchoolStaffRequiredMixin, View):
    def get(self, request):
        profile = SchoolProfile.objects.first()
        return render(request, "school_management/profile_form.html", {
            "nav": "profile",
            "profile": profile,
        })

    def post(self, request):
        profile = SchoolProfile.objects.first() or SchoolProfile()
        profile.name = request.POST.get("name", "").strip()
        profile.education_code = request.POST.get("education_code", "").strip()
        profile.phone_number = request.POST.get("phone_number", "").strip()
        profile.address = request.POST.get("address", "").strip()
        if request.FILES.get("logo"):
            profile.logo = request.FILES["logo"]
        try:
            profile.full_clean()
            profile.save()
            messages.success(request, "مشخصات مدرسه ذخیره شد.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect("school_management:profile")
