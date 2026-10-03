from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
import django_jalali.admin as jadmin  # Registers the Jalali admin date widget.

from apps.users.models import User

from .models import AcademicYear, Classroom, GradeLevel, Guardian, SchoolEnrollment, SchoolProfile, Student, StudentGuardian, StudyField


class SchoolAdminSite(admin.AdminSite):
    site_header = 'پنل مدیریت مدرسه'
    site_title = 'مدیریت مدرسه'
    index_title = 'مدیریت مدرسه'


school_admin_site = SchoolAdminSite(name='school_admin')


@admin.register(User, site=school_admin_site)
class SchoolUserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'phone_number', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'phone_number')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_image')}),
        ('دسترسی‌ها', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'first_name', 'last_name', 'role', 'phone_number', 'password1', 'password2', 'is_staff', 'is_superuser')}),
    )


@admin.register(SchoolProfile, site=school_admin_site)
class SchoolProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'education_code', 'phone_number', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        return not SchoolProfile.objects.exists()


@admin.register(AcademicYear, site=school_admin_site)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)


@admin.register(GradeLevel, site=school_admin_site)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(StudyField, site=school_admin_site)
class StudyFieldAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'code')


@admin.register(Classroom, site=school_admin_site)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'academic_year', 'grade_level', 'study_field', 'capacity', 'gender', 'is_active')
    list_filter = ('academic_year', 'grade_level', 'gender', 'is_active')
    search_fields = ('title', 'code')


@admin.register(Guardian, site=school_admin_site)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'mobile_number', 'national_code')
    search_fields = ('first_name', 'last_name', 'mobile_number', 'national_code')


@admin.register(Student, site=school_admin_site)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'national_code', 'gender', 'mobile_number', 'is_active')
    list_filter = ('gender', 'is_active')
    search_fields = ('first_name', 'last_name', 'national_code', 'mobile_number')


@admin.register(StudentGuardian, site=school_admin_site)
class StudentGuardianAdmin(admin.ModelAdmin):
    list_display = ('student', 'guardian', 'relationship', 'is_primary', 'receives_notifications')
    list_filter = ('relationship', 'is_primary', 'receives_notifications')


@admin.register(SchoolEnrollment, site=school_admin_site)
class SchoolEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'classroom', 'student_number', 'status', 'enrolled_at')
    list_filter = ('academic_year', 'classroom', 'status')
    search_fields = ('student__first_name', 'student__last_name', 'student__national_code', 'student_number')
