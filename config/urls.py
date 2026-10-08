from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from config.pwa import ManifestView
from config.profile import get_profile
from config.views import handler404, handler405

admin.site.site_header = 'پنل مدیریت'
admin.site.site_title = 'پنل مدیریت'
admin.site.index_title = 'پیشخوان مدیریتی'

handler403 = 'django.views.defaults.permission_denied'
handler404 = handler404
handler405 = handler405
handler500 = 'django.views.defaults.server_error'

profile = get_profile()

urlpatterns = [
    path('manifest.webmanifest', ManifestView.as_view(), name='pwa_manifest'),
]

# Public website is optional per instance (panel/PWA remain available).
if getattr(settings, 'WEBSITE_ENABLED', True):
    urlpatterns += [
        path('', include('website.urls')),
    ]
else:
    root = profile.root_redirect
    if str(root).startswith('/'):
        urlpatterns += [path('', RedirectView.as_view(url=root, permanent=False))]
    else:
        urlpatterns += [path('', RedirectView.as_view(pattern_name=root, permanent=False))]

# Profile URL tree — composition lives in each profile's urls_profile module.
urlpatterns += [path('', include(profile.urls_module))]

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
