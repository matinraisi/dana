from django.contrib import admin


class SchoolAdminMixin(admin.ModelAdmin):
    """Filter queryset based on user's school. Superusers see all."""

    school_field = 'school'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if school_id := getattr(request.user, 'school_id', None):
            return qs.filter(**{self.school_field + '_id': school_id})
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            if hasattr(obj, 'school_id') and not obj.school_id:
                obj.school = request.user.school
        super().save_model(request, obj, form, change)

    def _has_direct_school_field(self):
        return self.school_field == 'school'

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request) or [])
        if self._has_direct_school_field() and request.user.is_superuser and 'school' not in filters:
            filters = ['school'] + filters
        return filters

    def get_list_display(self, request):
        fields = list(super().get_list_display(request) or [])
        if self._has_direct_school_field() and request.user.is_superuser and 'school' not in fields:
            fields = ['school'] + fields
        return fields

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj) or [])
        if self._has_direct_school_field() and not request.user.is_superuser and 'school' not in ro:
            ro = ['school'] + ro
        return ro
