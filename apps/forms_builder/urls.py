from django.urls import path
from . import views

app_name = 'forms_builder'

urlpatterns = [
    path('', views.FormListView.as_view(), name='form_list'),
    path('create/', views.FormCreateView.as_view(), name='form_create'),
    path('<int:pk>/builder/', views.FormBuilderView.as_view(), name='form_builder'),
    path('<int:pk>/responses/', views.FormResponsesView.as_view(), name='form_responses'),
    path('<int:pk>/delete/', views.FormDeleteView.as_view(), name='form_delete'),
    path('f/<str:slug>/', views.FormPublicView.as_view(), name='form_public'),
]
