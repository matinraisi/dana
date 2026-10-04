from django.contrib import admin
from .models import InstallationConfig


@admin.register(InstallationConfig)
class InstallationConfigAdmin(admin.ModelAdmin):
    list_display = (
        'organization_name',
        'contact_phone',
        'support_email',
        'primary_color',
    )

    def has_add_permission(self, request):
        if InstallationConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
