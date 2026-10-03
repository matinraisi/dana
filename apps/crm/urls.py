from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/create/', views.LeadCreateView.as_view(), name='lead_create'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_update'),
    path('leads/<int:pk>/status/', views.LeadUpdateStatusView.as_view(), name='lead_update_status'),
    path('leads/<int:pk>/activity/', views.LeadAddActivityView.as_view(), name='lead_add_activity'),
    path('leads/<int:pk>/convert/', views.LeadConvertView.as_view(), name='lead_convert'),
]
