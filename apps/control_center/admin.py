from django.contrib import admin

from .models import Customer, InstallRecord, License, ProvisioningRequest


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


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("organization_name", "product_profile", "contact_name", "phone_number", "status", "created_at")
    list_filter = ("product_profile", "status")
    search_fields = ("organization_name", "contact_name", "phone_number", "email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("license_key", "customer", "plan_name", "status", "starts_at", "ends_at", "website_enabled")
    list_filter = ("status", "plan_name", "website_enabled")
    search_fields = ("license_key", "customer__organization_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(InstallRecord)
class InstallRecordAdmin(admin.ModelAdmin):
    list_display = ("domain", "customer", "product_mode", "app_version", "last_upgraded_at", "updated_at")
    list_filter = ("product_mode", "checklist_handover")
    search_fields = ("domain", "customer__organization_name", "server_host")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("customer", "domain", "panel_url", "server_host", "product_mode", "app_version", "database_note")}),
        ("چک‌لیست نصب دستی", {
            "fields": (
                "checklist_dns", "checklist_ssl", "checklist_env", "checklist_migrate",
                "checklist_admin", "checklist_sms", "checklist_payment", "checklist_handover",
            )
        }),
        ("یادداشت", {"fields": ("install_notes", "last_upgraded_at", "created_at", "updated_at")}),
    )
