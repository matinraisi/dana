"""PWA manifest for the current instance branding."""

from django.http import JsonResponse
from django.views import View

from apps.installation.utils import get_installation_config


class ManifestView(View):
    def get(self, request):
        installation = get_installation_config()
        # Instance branding from InstallationConfig (profile context may add more in templates).
        name = installation.organization_name or 'دانا'
        color = installation.primary_color or '#4f46e5'
        icons = []
        if installation.logo:
            icons.append({'src': installation.logo.url, 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'})
        else:
            icons = [
                {'src': '/static/pwa/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any maskable'},
                {'src': '/static/pwa/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
            ]
        return JsonResponse(
            {
                'name': name,
                'short_name': name[:12],
                'start_url': '/',
                'display': 'standalone',
                'dir': 'rtl',
                'lang': 'fa',
                'background_color': '#ffffff',
                'theme_color': color,
                'icons': icons,
            },
            json_dumps_params={'ensure_ascii': False},
        )
