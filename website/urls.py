from django.urls import path

from .views import AboutView, ContactView, HomeView, TrainingView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('training/', TrainingView.as_view(), name='training'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
]
