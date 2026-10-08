from django.shortcuts import redirect
from django.views.generic import TemplateView

from config.profile import get_profile


class HomeView(TemplateView):
    template_name = "website/cademy.html"

    def dispatch(self, request, *args, **kwargs):
        # Ask the active profile where an authenticated user should land.
        # Website must not hardcode Academy dashboard URLs.
        destination = get_profile().resolve_authenticated_home(request.user)
        if destination:
            return redirect(destination)
        return super().dispatch(request, *args, **kwargs)


class TrainingView(TemplateView):
    template_name = "website/training.html"


class AboutView(TemplateView):
    template_name = "website/about.html"


class ContactView(TemplateView):
    template_name = "website/contact.html"
