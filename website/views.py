from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.conf import settings

from config.product_mode import ACADEMY, CONTROL, SCHOOL


class HomeView(TemplateView):
    template_name = "website/cademy.html"

    def dispatch(self, request, *args, **kwargs):
        # Redirects below belong only to the academy product. A school or
        # control installation must never resolve an academy dashboard URL.
        if request.user.is_authenticated and settings.PRODUCT_MODE == ACADEMY:
            if request.user.is_superuser or request.user.is_admin_staff:
                return redirect('academy:dashboard_home')
            elif request.user.role == 'TEACHER':
                return redirect('teacher:dashboard')
            elif request.user.role == 'STUDENT':
                return redirect('student:dashboard')
        if request.user.is_authenticated and settings.PRODUCT_MODE == CONTROL and request.user.is_superuser:
            return redirect('control_center:request_list')
        if request.user.is_authenticated and settings.PRODUCT_MODE == SCHOOL and request.user.is_staff:
            return redirect('/admin/')
        return super().dispatch(request, *args, **kwargs)


class TrainingView(TemplateView):
    template_name = "website/training.html"
