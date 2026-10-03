from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """Base mixin for role-based access (teacher / student).

    Subclasses must set:
        role   — 'TEACHER' or 'STUDENT'
        panel  — 'teacher' or 'student' (for template context)
        login_url — fallback login path
    """
    role = None
    panel = None
    login_url = '/auth/teacher/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        if not request.user.role == self.role:
            display = 'اساتید' if self.role == 'TEACHER' else 'هنرجویان'
            return HttpResponseForbidden(f"دسترسی فقط برای {display}.")
        return super().dispatch(request, *args, **kwargs)
