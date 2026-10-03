from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('register/', views.SchoolRegisterView.as_view(), name='register'),
    path('registered/', views.SchoolRegisteredView.as_view(), name='registered'),
]
