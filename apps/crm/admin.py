from django.contrib import admin
from .models import Lead, LeadActivity
from apps.admin_base import SchoolAdminMixin


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 1
    fields = ('activity_type', 'description', 'created_by')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if school_id := getattr(request.user, 'school_id', None):
            return qs.filter(lead__school_id=school_id)
        return qs.none()


@admin.register(Lead)
class LeadAdmin(SchoolAdminMixin, admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'interested_course', 'status', 'source', 'created_at')
    list_filter = ('status', 'source', 'interested_course')
    search_fields = ('first_name', 'last_name', 'phone_number')
    inlines = [LeadActivityInline]
    list_editable = ('status',)
