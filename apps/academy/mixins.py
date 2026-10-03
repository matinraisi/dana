from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.db.models import QuerySet


class AdminRequiredMixin(LoginRequiredMixin):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        if not request.user.is_admin_staff:
            return HttpResponseForbidden("دسترسی فقط برای مدیران سیستم.")
        return super().dispatch(request, *args, **kwargs)

    def get_school_id(self):
        """Return current user's school ID, or None if superuser."""
        if self.request.user.is_superuser:
            return None
        return getattr(self.request.user, 'school_id', None)

    def school_object_or_404(self, model, school_field='school', **kwargs):
        """Get an object filtered by school, or 404."""
        qs = model.objects.all()
        if not self.request.user.is_superuser:
            school_id = getattr(self.request.user, 'school_id', None)
            if school_id:
                qs = qs.filter(**{school_field + '_id': school_id})
            else:
                from django.http import Http404
                raise Http404
        return get_object_or_404(qs, **kwargs)


class SchoolFilterMixin:
    """Mixin for dashboard views to filter querysets by the user's school.

    Usage:
        class MyView(AdminRequiredMixin, SchoolFilterMixin, View):
            def get(self, request):
                qs = self.filter_by_school(Model.objects.all())
    """

    def filter_by_school(self, qs: QuerySet, school_field: str = 'school') -> QuerySet:
        """Filter a queryset by the current user's school."""
        user = self.request.user
        if user.is_superuser:
            return qs
        school_id = getattr(user, 'school_id', None)
        if school_id:
            return qs.filter(**{school_field + '_id': school_id})
        return qs.none()

    def school_filter_kwarg(self) -> dict:
        """Return a dict for use in filter(**kwarg) calls."""
        user = self.request.user
        if user.is_superuser:
            return {}
        school_id = getattr(user, 'school_id', None)
        if school_id:
            return {'school_id': school_id}
        return {'pk__in': []}
