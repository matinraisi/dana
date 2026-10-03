from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View


class SchoolPanelRedirectView(LoginRequiredMixin, View):
    login_url = 'school_admin:login'

    def get(self, request, *args, **kwargs):
        return redirect('school_admin:index')
