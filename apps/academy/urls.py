from django.urls import path
from . import views
from .views import attendance as views_attendance
from .views.idcard import IssueIDCardView, StudentIdCardView, VerifyIDCardView, IDCardListView, RevokeIDCardView
from .views.users_mgmt import UserListView, UserCreateView, UserEditView, UserToggleActiveView
from .views.discount import (
    DiscountCodeListView, DiscountCodeCreateView, DiscountCodeDeleteView,
    DiscountCodeToggleView, ValidateDiscountAjaxView,
)

app_name = 'academy'

urlpatterns = [
    # --- احراز هویت ---
    path('login/', views.AcademyLoginView.as_view(), name='login'),
    path('logout/', views.AcademyLogoutView.as_view(), name='logout'),

    # --- داشبورد ---
    path('', views.DashboardHomeView.as_view(), name='dashboard_home'),

    # --- هنرجویان ---
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/create/', views.StudentCreateView.as_view(), name='student_create'),
    path('import-excel/', views.ImportExcelView.as_view(), name='import_excel'),
    path('download-sample/', views.DownloadSampleExcelView.as_view(), name='download_sample_excel'),

    # --- دوره‌ها ---
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/edit/', views.CourseEditView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    # --- مالی ---
    path('financial-reports/', views.FinancialReportView.as_view(), name='financial_reports'),
    path('finance/', views.FinanceDashboardView.as_view(), name='finance_management'),
    path('finance/installment/<int:installment_id>/toggle/', views.ToggleInstallmentStatusView.as_view(), name='toggle_installment'),
    path('finance/installment/add/', views.AddInstallmentView.as_view(), name='add_installment'),
    path('finance/record-payment/', views.RecordPaymentView.as_view(), name='record_payment'),
    path('finance/payment-initiate/', views.PaymentInitiateView.as_view(), name='payment_initiate'),
    path('payment/callback/', views.PaymentCallbackView.as_view(), name='payment_callback'),
    path('pay/<int:enrollment_id>/', views.PublicPaymentInitiateView.as_view(), name='public_payment'),

    # --- مدارک ---
    path('documents/', views.DocumentVerificationView.as_view(), name='document_verification'),
    path('documents/<int:student_id>/verify/', views.ApproveRejectDocumentView.as_view(), name='approve_reject_doc'),

    # --- پیامک ---
    path('sms/', views.SMSDashboardView.as_view(), name='sms_dashboard'),
    path('sms/send/', views.SendBulkSMSView.as_view(), name='send_bulk_sms'),
    path('sms/ajax/send/', views.SMSAjaxSendView.as_view(), name='sms_ajax_send'),
    path('sms/ajax/preview/', views.SMSAjaxPreviewView.as_view(), name='sms_ajax_preview'),
    path('sms-management/', views.SMSManagementView.as_view(), name='sms_management'),

    # --- حضور و غیاب ---
    path('courses/<int:course_id>/sessions/', views_attendance.SessionListView.as_view(), name='session_list'),
    path('courses/<int:course_id>/sessions/create/', views_attendance.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:session_id>/attendance/', views_attendance.AttendanceSheetView.as_view(), name='attendance_sheet'),
    path('students/<int:student_id>/attendance/<int:course_id>/', views_attendance.StudentAttendanceReportView.as_view(), name='student_attendance_report'),
    path('courses/<int:course_id>/attendance/', views_attendance.CourseAttendanceSummaryView.as_view(), name='course_attendance_summary'),
    path('materials/', views_attendance.AdminMaterialListView.as_view(), name='admin_materials'),

    # --- مدیریت کاربران ---
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/toggle/', UserToggleActiveView.as_view(), name='user_toggle'),

    # --- کارت شناسایی ---
    path('id-cards/', IDCardListView.as_view(), name='idcard_list'),
    path('students/<int:student_id>/issue-card/', IssueIDCardView.as_view(), name='issue_id_card'),
    path('id-cards/<int:card_id>/revoke/', RevokeIDCardView.as_view(), name='revoke_id_card'),
    path('verify/<str:card_number>/', VerifyIDCardView.as_view(), name='verify_id_card'),

    # --- ثبت‌نام عمومی در دوره ---
    path('register/<str:slug>/', views.PublicCourseRegistrationView.as_view(), name='public_registration'),

    # --- ویرایش / حذف هنرجو ---
    path('students/<slug:slug>/edit/', views.StudentEditView.as_view(), name='student_edit'),
    path('students/<slug:slug>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),

    # --- پروفایل عمومی هنرجو ---
    path('p/<str:slug>/', views.StudentProfileView.as_view(), name='student_profile'),
    path('id-card/<str:slug>/', StudentIdCardView.as_view(), name='student_id_card'),

    # --- گزارشات ---
    path('reports/', views.ReportDashboardView.as_view(), name='reports_dashboard'),
    path('reports/course-students/', views.CourseStudentsReportView.as_view(), name='course_students_report'),
    path('reports/course-students/<int:course_id>/export/', views.CourseStudentsExportView.as_view(), name='course_students_export'),
    path('reports/all-students/', views.AllStudentsReportView.as_view(), name='all_students_report'),
    path('reports/all-students/export/', views.AllStudentsExportView.as_view(), name='all_students_export'),

    # --- آزمون‌ها (مدیریت) ---
    path('exams/', views.exam.ExamListView.as_view(), name='exam_list'),
    path('exams/create/', views.exam.ExamCreateView.as_view(), name='exam_create'),
    path('exams/<int:exam_id>/edit/', views.exam.ExamEditView.as_view(), name='exam_edit'),
    path('exams/<int:exam_id>/delete/', views.exam.ExamDeleteView.as_view(), name='exam_delete'),
    path('exams/<int:exam_id>/questions/', views.exam.ExamQuestionsView.as_view(), name='exam_questions'),
    path('exams/<int:exam_id>/results/', views.exam.ExamResultsView.as_view(), name='exam_results'),
    path('exams/<int:exam_id>/take/', views.exam.TakeExamView.as_view(), name='take_exam'),
    path('attempts/<int:attempt_id>/', views.exam.AttemptDetailView.as_view(), name='attempt_detail'),
    path('attempts/<int:attempt_id>/result/', views.exam.ExamResultView.as_view(), name='exam_result'),

    # --- گزینه‌های سوال ---
    path('questions/<int:question_id>/choices/', views.exam.QuestionChoicesView.as_view(), name='question_choices'),

    # --- حسابداری پیشرفته ---
    path('accounting/', views.AccountingDashboardView.as_view(), name='accounting_dashboard'),
    path('accounting/transactions/', views.AccountingTransactionListView.as_view(), name='accounting_transactions'),
    path('accounting/create/', views.AccountingTransactionCreateView.as_view(), name='accounting_create'),
    path('accounting/<int:pk>/delete/', views.AccountingTransactionDeleteView.as_view(), name='accounting_delete'),
    path('accounting/course-profits/', views.CourseProfitReportView.as_view(), name='course_profit_report'),
    path('accounting/teacher-payouts/', views.TeacherPayoutListView.as_view(), name='teacher_payouts'),

    # --- آزمون‌ها (هنرجو) ---
    path('my/exams/', views.exam.StudentExamListView.as_view(), name='student_exams'),

    # --- تقویم و برنامه کلاس‌ها ---
    path('timetable/', views.timetableView.as_view(), name='timetable'),
    path('rooms/', views.RoomTimetableView.as_view(), name='room_timetable'),

    # --- کلاس آنلاین (عمومی) ---
    path('meet/', views.MeetingHomeView.as_view(), name='meeting_home'),
    path('meet/new/', views.MeetingCreateView.as_view(), name='meeting_create'),
    path('meet/<str:room_id>/', views.MeetingRoomView.as_view(), name='meeting_room'),
    path('meet/external/', views.MeetingExternalView.as_view(), name='meeting_external'),

    # --- کدهای تخفیف ---
    path('discounts/', DiscountCodeListView.as_view(), name='discount_list'),
    path('discounts/create/', DiscountCodeCreateView.as_view(), name='discount_create'),
    path('discounts/<int:pk>/delete/', DiscountCodeDeleteView.as_view(), name='discount_delete'),
    path('discounts/<int:pk>/toggle/', DiscountCodeToggleView.as_view(), name='discount_toggle'),
    path('discounts/ajax/validate/', ValidateDiscountAjaxView.as_view(), name='discount_validate'),
]
