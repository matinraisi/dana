from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from apps.academy.mixins import AdminRequiredMixin, SchoolFilterMixin
from django.db.models import Sum, Q
from django.utils import timezone

from ..models import CourseEnrollment, AcademyInstallment, StudentEnrollment
from ..models.accounting import AccountingTransaction, PaymentGateway
from ..services.sms_service import SmsService


class FinancialReportView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        now = timezone.now().date()
        next_30_days = now + timedelta(days=30)

        self.filter_by_school(AcademyInstallment.objects.filter(status='pending', due_date__lt=now), school_field='enrollment__student__school').update(status='overdue')

        total_revenue = self.filter_by_school(CourseEnrollment.objects.all(), school_field='course__school').aggregate(total=Sum('paid_amount'))['total'] or 0
        overdue_payments = self.filter_by_school(AcademyInstallment.objects.filter(status='overdue'), school_field='enrollment__student__school').aggregate(total=Sum('amount'))['total'] or 0
        upcoming_cashflow = self.filter_by_school(AcademyInstallment.objects.filter(
            status='pending', due_date__range=[now, next_30_days]
        ), school_field='enrollment__student__school').aggregate(total=Sum('amount'))['total'] or 0
        recent_installments = self.filter_by_school(AcademyInstallment.objects.select_related(
            'enrollment__student', 'enrollment__course'
        ), school_field='enrollment__student__school').order_by('-due_date')[:10]

        return render(request, 'academy/dashboard/financial_report.html', {
            'total_revenue': total_revenue,
            'overdue_payments': overdue_payments,
            'upcoming_cashflow': upcoming_cashflow,
            'recent_installments': recent_installments,
        })


class FinanceDashboardView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        today = timezone.now().date()
        self.filter_by_school(AcademyInstallment.objects.filter(status='pending', due_date__lt=today), school_field='enrollment__student__school').update(status='overdue')

        enrollments = self.filter_by_school(CourseEnrollment.objects.select_related('student', 'course').prefetch_related('installments').all(), school_field='course__school')

        # جستجو
        search = request.GET.get('q', '').strip()
        if search:
            enrollments = enrollments.filter(
                Q(student__first_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__phone_number__icontains=search)
                | Q(course__title__icontains=search)
            )

        # صفحه‌بندی
        from django.core.paginator import Paginator
        page_number = request.GET.get('page', 1)
        paginator = Paginator(enrollments, 15)  # ۱۳ هنرجو در هر صفحه
        page_obj = paginator.get_page(page_number)

        total_students = self.filter_by_school(StudentEnrollment.objects.all()).count()
        total_revenue = self.filter_by_school(CourseEnrollment.objects.all(), school_field='course__school').aggregate(t=Sum('paid_amount'))['t'] or 0
        total_debt = self.filter_by_school(CourseEnrollment.objects.all(), school_field='course__school').aggregate(t=Sum('total_amount'))['t'] or 0
        total_remaining = total_debt - total_revenue
        overdue_count = self.filter_by_school(AcademyInstallment.objects.filter(status='overdue'), school_field='enrollment__student__school').count()

        return render(request, 'academy/dashboard/finance_management.html', {
            'enrollments': page_obj,
            'page_obj': page_obj,
            'total_students': total_students,
            'total_revenue': total_revenue,
            'total_debt': total_debt,
            'total_remaining': total_remaining,
            'overdue_count': overdue_count,
            'search_query': search,
        })


class AddInstallmentView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request):
        enroll_id = request.POST.get('enrollment_id')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        if enroll_id and amount and due_date:
            try:
                enroll = self.filter_by_school(CourseEnrollment.objects.all(), school_field='course__school').get(id=enroll_id)
                if int(amount) > 0:
                    AcademyInstallment.objects.create(
                        enrollment=enroll,
                        amount=int(amount),
                        due_date=due_date,
                        status='pending',
                    )
                    messages.success(request, f"قسط {int(amount):,} تومانی با سررسید {due_date} اضافه شد.")
            except (CourseEnrollment.DoesNotExist, ValueError, TypeError):
                messages.error(request, "خطا در افزودن قسط.")
        else:
            messages.error(request, "مبلغ و تاریخ سررسید را وارد کنید.")
        referer = request.META.get('HTTP_REFERER', '/')
        return redirect(referer)


class ToggleInstallmentStatusView(AdminRequiredMixin, SchoolFilterMixin, View):
    def post(self, request, installment_id):
        installment = get_object_or_404(self.filter_by_school(AcademyInstallment.objects.all(), school_field='enrollment__student__school'), id=installment_id)
        enrollment = installment.enrollment

        if installment.status in ['pending', 'overdue']:
            installment.status = 'paid'
            installment.paid_at = timezone.now()
            messages.success(request, f"قسط {installment.amount:,} تومان پرداخت شده ثبت شد.")

            # Auto-create AccountingTransaction
            default_gateway = PaymentGateway.objects.filter(
                gateway_type__in=['pos', 'gateway', 'card', 'cash'], is_active=True
            ).first()
            AccountingTransaction.objects.create(
                transaction_type='income',
                amount=installment.amount,
                payment_method='installment',
                payment_gateway=default_gateway,
                course=enrollment.course,
                student=enrollment.student,
                enrollment=enrollment,
                description=f"پرداخت قسط {installment.due_date} — {enrollment.student}",
                transaction_date=timezone.now().date(),
                created_by=request.user,
            )

            try:
                SmsService.notify_payment(enrollment.student, installment.amount)
            except Exception:
                pass
        else:
            installment.status = 'pending'
            installment.paid_at = None
            messages.warning(request, "وضعیت قسط به در انتظار پرداخت بازگشت.")
        installment.save()
        enrollment.update_paid_amount()
        return redirect('academy:finance_management')


class RecordPaymentView(AdminRequiredMixin, SchoolFilterMixin, View):
    def get(self, request):
        return redirect('academy:finance_management')

    def post(self, request):
        enroll_id = request.POST.get('enrollment_id')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'cash')
        card_number = request.POST.get('card_number', '')
        description = request.POST.get('description', '')

        if not enroll_id or not amount:
            messages.error(request, 'هنرجو و مبلغ را وارد کنید.')
            return redirect('academy:finance_management')

        try:
            enroll = self.filter_by_school(CourseEnrollment.objects.select_related('student', 'course').all(), school_field='course__school').get(id=enroll_id)
            amount_val = int(amount)
            if amount_val <= 0:
                messages.error(request, 'مبلغ باید بیشتر از صفر باشد.')
                return redirect('academy:finance_management')

            default_gateway = PaymentGateway.objects.filter(
                gateway_type__in=['pos', 'gateway', 'card', 'cash'], is_active=True
            ).first()

            tx = AccountingTransaction.objects.create(
                transaction_type='income',
                amount=amount_val,
                payment_method=payment_method,
                payment_gateway=default_gateway,
                card_number=card_number,
                course=enroll.course,
                student=enroll.student,
                enrollment=enroll,
                description=description or f"پرداخت شهریه {enroll.course.title} — {enroll.student}",
                transaction_date=timezone.now().date(),
                created_by=request.user,
            )

            enroll.paid_amount = (enroll.paid_amount or 0) + amount_val
            if enroll.remaining_amount == 0 and enroll.total_amount > 0:
                enroll.payment_method = 'cash'
            elif enroll.paid_amount > 0:
                enroll.payment_method = 'installment'
            enroll.save()

            try:
                SmsService.notify_payment(enroll.student, amount_val)
            except Exception:
                pass

            messages.success(request, f'پرداخت {amount_val:,} تومان برای {enroll.student} ثبت شد.')

        except (CourseEnrollment.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'خطا در ثبت پرداخت.')

        return redirect('academy:finance_management')
