from .dashboard import AcademyLoginView, AcademyLogoutView, DashboardHomeView
from .student import (
    StudentListView, StudentCreateView, StudentProfileView, StudentIdCardView,
    ImportExcelView, DownloadSampleExcelView,
    StudentEditView, StudentDeleteView,
)
from .course import CourseListView, CourseCreateView, CourseEditView, CourseDeleteView
from .finance import FinancialReportView, FinanceDashboardView, ToggleInstallmentStatusView, AddInstallmentView, RecordPaymentView
from .sms import SMSManagementView, SMSDashboardView, SendBulkSMSView, SMSAjaxSendView, SMSAjaxPreviewView
from .document import DocumentVerificationView, ApproveRejectDocumentView
from .users_mgmt import UserListView, UserCreateView, UserEditView, UserToggleActiveView
from .public_registration import PublicCourseRegistrationView
from . import exam
from .reports import (
    ReportDashboardView,
    CourseStudentsReportView,
    CourseStudentsExportView,
    AllStudentsReportView,
    AllStudentsExportView,
)
from .accounting import (
    AccountingDashboardView,
    AccountingTransactionListView,
    AccountingTransactionCreateView,
    AccountingTransactionDeleteView,
    CourseProfitReportView,
    TeacherPayoutListView,
)

from .meeting import MeetingHomeView, MeetingRoomView, MeetingCreateView, MeetingExternalView
from .payment import PaymentInitiateView, PaymentCallbackView, PublicPaymentInitiateView
from .timetable import TimetableView as timetableView, RoomTimetableView

__all__ = [
    'AcademyLoginView', 'AcademyLogoutView', 'DashboardHomeView',
    'StudentListView', 'StudentCreateView', 'StudentProfileView', 'StudentIdCardView',
    'ImportExcelView', 'DownloadSampleExcelView',
    'StudentEditView', 'StudentDeleteView',
    'CourseListView', 'CourseCreateView', 'CourseEditView', 'CourseDeleteView',
    'FinancialReportView', 'FinanceDashboardView',     'ToggleInstallmentStatusView', 'AddInstallmentView', 'RecordPaymentView',
    'SMSManagementView', 'SMSDashboardView', 'SendBulkSMSView', 'SMSAjaxSendView', 'SMSAjaxPreviewView',
    'DocumentVerificationView', 'ApproveRejectDocumentView',
    'UserListView', 'UserCreateView', 'UserEditView', 'UserToggleActiveView',
    'PublicCourseRegistrationView',
    'ReportDashboardView', 'CourseStudentsReportView',
    'CourseStudentsExportView', 'AllStudentsReportView', 'AllStudentsExportView',
    'AccountingDashboardView',
    'AccountingTransactionListView',
    'AccountingTransactionCreateView',
    'AccountingTransactionDeleteView',
    'CourseProfitReportView',
    'TeacherPayoutListView',
    'MeetingHomeView', 'MeetingRoomView', 'MeetingCreateView', 'MeetingExternalView',
    'PaymentInitiateView', 'PaymentCallbackView', 'PublicPaymentInitiateView',
]
