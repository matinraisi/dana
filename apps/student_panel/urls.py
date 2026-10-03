from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('', views.StudentDashboardView.as_view(), name='dashboard'),
    path('courses/', views.StudentCoursesView.as_view(), name='courses'),
    path('attendance/', views.StudentAttendanceView.as_view(), name='attendance'),
    path('payments/', views.StudentPaymentsView.as_view(), name='payments'),
    path('id-card/', views.StudentIDCardView.as_view(), name='id_card'),
    path('roadmap/', views.StudentRoadmapView.as_view(), name='roadmap'),
    path('profile/', views.StudentProfileView.as_view(), name='profile'),
    path('materials/', views.StudentMaterialListView.as_view(), name='materials'),
    path('sessions/', views.StudentSessionsView.as_view(), name='sessions'),
    path('payment/initiate/', views.StudentPaymentInitiateView.as_view(), name='payment_initiate'),
]
