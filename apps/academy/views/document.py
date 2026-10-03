from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin

from ..models import StudentEnrollment
from ..services.sms_service import SmsService


class DocumentVerificationView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        from django.db.models import Q
        students = self.filter_by_school(StudentEnrollment.objects.filter(
            Q(avatar_3x4__isnull=False) | Q(national_card_img__isnull=False) | Q(identity_img__isnull=False)
        ).distinct().order_by('-created_at'))
        paginator = Paginator(students, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        return render(request, 'academy/dashboard/document_verification.html', {'page_obj': page_obj})


class ApproveRejectDocumentView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, student_id):
        student = self.school_object_or_404(StudentEnrollment, id=student_id)
        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        if action == 'verify':
            student.document_status = 'verified'
            student.document_rejection_reason = ''
            student.save()
            messages.success(request, f"مدارک {student.full_name} تأیید شد.")
            try:
                SmsService.notify_document_approved(student)
            except Exception:
                pass

        elif action == 'reject':
            if not rejection_reason:
                messages.error(request, "علت رد مدارک الزامی است.")
                return redirect('academy:document_verification')
            student.document_status = 'rejected'
            student.document_rejection_reason = rejection_reason
            student.save()
            messages.warning(request, f"مدارک {student.full_name} رد شد.")
            try:
                SmsService.notify_document_rejected(student, rejection_reason)
            except Exception:
                pass

        return redirect('academy:document_verification')
