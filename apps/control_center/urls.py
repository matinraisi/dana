from django.urls import path

from . import views


app_name = "control_center"

urlpatterns = [
    path("request/", views.ProvisioningRequestCreateView.as_view(), name="request_create"),
    path("requests/", views.ProvisioningRequestListView.as_view(), name="request_list"),
    path("requests/<int:pk>/update/", views.ProvisioningRequestUpdateView.as_view(), name="request_update"),
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/new/", views.CustomerFormView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerFormView.as_view(), name="customer_edit"),
    path("licenses/", views.LicenseListView.as_view(), name="license_list"),
    path("licenses/new/", views.LicenseFormView.as_view(), name="license_create"),
    path("licenses/<int:pk>/", views.LicenseFormView.as_view(), name="license_edit"),
    path("installs/", views.InstallListView.as_view(), name="install_list"),
    path("installs/new/", views.InstallFormView.as_view(), name="install_create"),
    path("installs/<int:pk>/", views.InstallFormView.as_view(), name="install_edit"),
]
