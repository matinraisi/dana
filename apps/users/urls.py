from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ورود استاد — حالت پیش‌فرض: رمز عبور
    path('teacher/login/', views.TeacherPasswordLoginView.as_view(), name='teacher_login'),
    path('teacher/login/otp/', views.TeacherOTPRequestView.as_view(), name='teacher_otp_login'),
    # ورود هنرجو — حالت پیش‌فرض: رمز عبور
    path('student/login/', views.StudentPasswordLoginView.as_view(), name='student_login'),
    path('student/login/otp/', views.StudentOTPRequestView.as_view(), name='student_otp_login'),
    # OTP
    path('verify/', views.OTPVerifyView.as_view(), name='otp_verify'),
    path('resend/', views.OTPResendView.as_view(), name='otp_resend'),
]
