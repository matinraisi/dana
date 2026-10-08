"""Academy-only Django admin helpers (not part of the kernel)."""

from apps.academy.org import get_instance_organization


class SchoolAdminMixin:
    """Auto-stamp the singleton Academy Organization on save."""

    school_field = 'school'

    def save_model(self, request, obj, form, change):
        if hasattr(obj, 'school_id') and not obj.school_id:
            org = get_instance_organization()
            if org is not None:
                obj.school = org
        super().save_model(request, obj, form, change)
