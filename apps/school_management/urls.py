"""URLs owned exclusively by the school product.

The school dashboard will be introduced with its first approved domain slice.
Keeping this namespace separate from ``apps.academy`` is an architectural
boundary, not a compatibility layer.
"""

from django.urls import path

from .views import SchoolPanelRedirectView

app_name = "school_management"

urlpatterns = [
    path('', SchoolPanelRedirectView.as_view(), name='home'),
]
