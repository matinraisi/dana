from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect


class AdminRequiredMixin(LoginRequiredMixin):
    login_url = '/dashboard/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.get_login_url())
        if not request.user.is_admin_staff:
            return HttpResponseForbidden("دسترسی فقط برای مدیران سیستم.")
        return super().dispatch(request, *args, **kwargs)

    def school_object_or_404(self, model, **kwargs):
        """Object lookup helper used by Academy admin views."""
        return get_object_or_404(model, **kwargs)
