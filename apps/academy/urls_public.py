from django.urls import path
from .views import public_registration, payment
from .views.idcard import VerifyIDCardView
from .views.student import StudentProfileView

urlpatterns = [
    path('', public_registration.PublicCourseRegistrationView.as_view(), name='public_registration'),
    path('profile/<str:slug>/', StudentProfileView.as_view(), name='student_profile'),
    path('pay/<int:enrollment_id>/', payment.PublicPaymentInitiateView.as_view(), name='public_payment'),
    path('pay/<int:enrollment_id>/installment/', payment.PublicPaymentInstallmentView.as_view(), name='public_payment_installment'),
    path('verify/<str:card_number>/', VerifyIDCardView.as_view(), name='verify_id_card'),
]
