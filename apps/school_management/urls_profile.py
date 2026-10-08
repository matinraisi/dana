"""School product URL tree — selected by ``config.profile``."""

from django.urls import include, path

from apps.school_management.admin import school_admin_site

urlpatterns = [
    path('admin/', school_admin_site.urls),
    path('school-panel/', include('apps.school_management.urls')),
]
