"""Academy product URL tree — selected by ``config.profile``."""

from django.urls import include, path

from apps.academy.views.idcard import VerifyIDCardView
from apps.academy.views.payment import (
    GatewayReturnView,
    GatewayWebhookView,
    PublicPaymentInitiateView,
    PublicPaymentInstallmentView,
)

urlpatterns = [
    path('dashboard/', include('apps.academy.urls')),
    path('teacher/', include('apps.teacher_panel.urls')),
    path('my/', include('apps.student_panel.urls')),
    path('crm/', include('apps.crm.urls')),
    path('forms/', include('apps.forms_builder.urls')),
    path('auth/', include('apps.users.urls')),
    path('register/<str:slug>/', include('apps.academy.urls_public')),
    path('pay/<int:enrollment_id>/', PublicPaymentInitiateView.as_view(), name='public_payment'),
    path(
        'pay/<int:enrollment_id>/installment/',
        PublicPaymentInstallmentView.as_view(),
        name='public_payment_installment',
    ),
    path('payment/gateway/webhook/', GatewayWebhookView.as_view(), name='gateway_payment_webhook'),
    path('payment/gateway/return/', GatewayReturnView.as_view(), name='gateway_payment_return'),
    path('verify/<str:card_number>/', VerifyIDCardView.as_view(), name='verify_id_card'),
]
