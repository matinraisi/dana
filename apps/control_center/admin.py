from django.contrib import admin

from .models import ProvisioningRequest


@admin.register(ProvisioningRequest)
class ProvisioningRequestAdmin(admin.ModelAdmin):
    list_display = (
        "organization_name",
        "requested_product",
        "contact_name",
        "phone_number",
        "status",
        "notified_at",
        "created_at",
    )
    list_filter = ("requested_product", "status")
    search_fields = ("organization_name", "contact_name", "phone_number", "email")
    readonly_fields = ("notified_at", "created_at", "updated_at")
