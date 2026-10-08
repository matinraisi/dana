from django.contrib import admin
from .models import Lead, LeadActivity
from apps.academy.admin_mixins import SchoolAdminMixin


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 1
    fields = ('activity_type', 'description', 'created_by')


@admin.register(Lead)
class LeadAdmin(SchoolAdminMixin, admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'interested_course', 'status', 'source', 'created_at')
    list_filter = ('status', 'source', 'interested_course')
    search_fields = ('first_name', 'last_name', 'phone_number')
    inlines = [LeadActivityInline]
    list_editable = ('status',)
