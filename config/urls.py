from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import handler404, handler405
from .product_mode import ACADEMY, CONTROL, SCHOOL

admin.site.site_header = 'پنل مدیریت'
admin.site.site_title = 'پنل مدیریت'
admin.site.index_title = 'پیشخوان مدیریتی'

handler403 = 'django.views.defaults.permission_denied'
handler404 = handler404
handler405 = handler405
handler500 = 'django.views.defaults.server_error'

urlpatterns = [
    # Landing page (صفحه اصلی سایت)
    path('', include('website.urls')),
]


if settings.PRODUCT_MODE == ACADEMY:
    from apps.academy.views.idcard import VerifyIDCardView
    from apps.academy.views.payment import (
        GatewayReturnView,
        GatewayWebhookView,
        PublicPaymentInitiateView,
        PublicPaymentInstallmentView,
    )

    urlpatterns += [
        # ─── پنل مدیریت (زیرمجموعه dashboard) ───
        path('dashboard/', include('apps.academy.urls')),

        # ─── پنل استاد ───
        path('teacher/', include('apps.teacher_panel.urls')),

        # ─── پنل هنرجو ───
        path('my/', include('apps.student_panel.urls')),

        # ─── CRM ───
        path('crm/', include('apps.crm.urls')),

        # ─── فرم‌ساز ───
        path('forms/', include('apps.forms_builder.urls')),

        # ─── احراز هویت ───
        path('auth/', include('apps.users.urls')),

        # ─── ثبت‌نام مدرسه ───
        path('school/', include('apps.schools.urls')),

        # ─── URLهای عمومی (سطح روت) ───
        # ثبت‌نام عمومی دوره
        path('register/<str:slug>/', include('apps.academy.urls_public')),
        # پرداخت عمومی (مستقیم به ویو، نه include)
        path('pay/<int:enrollment_id>/', PublicPaymentInitiateView.as_view(), name='public_payment'),
        path('pay/<int:enrollment_id>/installment/', PublicPaymentInstallmentView.as_view(), name='public_payment_installment'),
        # درگاه پرداخت سان‌تک: webhook سرور به سرور و صفحهٔ بازگشت هنرجو
        path('payment/gateway/webhook/', GatewayWebhookView.as_view(), name='gateway_payment_webhook'),
        path('payment/gateway/return/', GatewayReturnView.as_view(), name='gateway_payment_return'),
        # تأیید کارت شناسایی (مستقیم به ویو)
        path('verify/<str:card_number>/', VerifyIDCardView.as_view(), name='verify_id_card'),
    ]

elif settings.PRODUCT_MODE == SCHOOL:
    from apps.school_management.admin import school_admin_site

    urlpatterns += [
        path('admin/', school_admin_site.urls),
        path('school-panel/', include('apps.school_management.urls')),
    ]

elif settings.PRODUCT_MODE == CONTROL:
    urlpatterns += [
        path('admin/', admin.site.urls),
        path('control/', include('apps.control_center.urls')),
    ]

else:
    urlpatterns += [path('admin/', admin.site.urls)]

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
