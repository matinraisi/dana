"""URLs owned exclusively by the school product."""

from django.urls import path

from . import views

app_name = "school_management"

urlpatterns = [
    path("", views.SchoolDashboardView.as_view(), name="home"),
    path("profile/", views.SchoolProfileEditView.as_view(), name="profile"),
    path("years/", views.AcademicYearListView.as_view(), name="years"),
    path("structure/", views.StructureListView.as_view(), name="structure"),
    path("students/", views.StudentListView.as_view(), name="students"),
    path("students/new/", views.StudentCreateView.as_view(), name="student_create"),
    path("students/<int:pk>/", views.StudentDetailView.as_view(), name="student_detail"),
    path("guardians/", views.GuardianListView.as_view(), name="guardians"),
    path("enrollments/", views.EnrollmentListView.as_view(), name="enrollments"),
]
