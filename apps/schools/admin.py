from django.contrib import admin
from django.core.exceptions import ValidationError

from apps.academy.org import set_organization
from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'is_active', 'created_at')
    search_fields = ('title', 'owner__username', 'phone', 'email')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'is_active')
    fieldsets = (
        ('سازمان آموزشگاه', {
            'fields': ('title', 'slug', 'is_active'),
            'description': 'هر Instance آموزشگاه فقط یک سازمان دارد.',
        }),
        ('برندینگ', {
            'fields': ('logo', 'favicon', 'primary_color'),
            'description': 'برندینگ سطح Instance همچنان از InstallationConfig هم پشتیبانی می‌شود.',
        }),
        ('اطلاعات تماس', {
            'fields': ('phone', 'email', 'address', 'description'),
        }),
        ('مدیریت', {
            'fields': ('owner',),
        }),
        ('زمان', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def has_add_permission(self, request):
        if School.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Keep the singleton; do not allow deleting the only org from admin.
        return False

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as exc:
            form.add_error(None, exc)
            raise
        if obj.owner_id:
            set_organization(obj.owner, obj)
