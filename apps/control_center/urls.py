from django.urls import path

from . import views


app_name = "control_center"

urlpatterns = [
    path("request/", views.ProvisioningRequestCreateView.as_view(), name="request_create"),
    path("requests/", views.ProvisioningRequestListView.as_view(), name="request_list"),
    path("requests/<int:pk>/update/", views.ProvisioningRequestUpdateView.as_view(), name="request_update"),
]
