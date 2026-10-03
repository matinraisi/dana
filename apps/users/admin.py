from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Teacher, StudentAccount, OTPToken
from apps.admin_base import SchoolAdminMixin


@admin.register(User)
class UserAdmin(SchoolAdminMixin, BaseUserAdmin):
    school_field = 'school'
    list_display = ('username', 'email', 'role', 'school', 'phone_number', 'is_active')
    list_filter = ('role', 'is_active', 'school')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_image')}),
        ('دسترسی‌ها', {'fields': ('role', 'school', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            if not obj.school_id:
                obj.school = request.user.school
        super().save_model(request, obj, form, change)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'phone_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if school_id := getattr(request.user, 'school_id', None):
            return qs.filter(user__school_id=school_id)
        return qs.none()


@admin.register(StudentAccount)
class StudentAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'enrollment')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if school_id := getattr(request.user, 'school_id', None):
            return qs.filter(user__school_id=school_id)
        return qs.none()


@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'is_used', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('phone_number',)
    readonly_fields = ('phone_number', 'code', 'created_at')
