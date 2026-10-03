from django.contrib import admin
from .models import DynamicForm, FormField, FormSubmission, FieldResponse


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ('order', 'field_type', 'label', 'is_required', 'options')


class FieldResponseInline(admin.TabularInline):
    model = FieldResponse
    extra = 0
    readonly_fields = ('field', 'value', 'file_upload')
    can_delete = False


@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'response_count', 'created_at')
    list_filter = ('is_active', 'requires_login')
    search_fields = ('title', 'slug')
    inlines = [FormFieldInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if school_id := getattr(request.user, 'school_id', None):
            return qs.filter(linked_course__school_id=school_id)
        return qs.none()


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('form', 'submitted_by', 'submitted_at', 'ip_address')
    list_filter = ('form',)
    readonly_fields = ('submission_id', 'submitted_at')
    inlines = [FieldResponseInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if school_id := getattr(request.user, 'school_id', None):
            return qs.filter(form__linked_course__school_id=school_id)
        return qs.none()
