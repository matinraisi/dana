from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
import calendar
from apps.academy.mixins import AdminRequiredMixin
from apps.academy.utils.date_helper import to_jalali, to_gregorian
from django.contrib.auth import get_user_model

User = get_user_model()

from ..models import Course, CourseEnrollment, StudentEnrollment
from ..models.accounting import AccountingTransaction, ExpenseCategory, PaymentGateway
from ..models.course import Session


class AccountingDashboardView(AdminRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        # ─── KPI اصلی ───
        # درآمد واقعی: مجموع پرداختی هنرجویان
        total_revenue = CourseEnrollment.objects.all().aggregate(t=Sum('paid_amount'))['t'] or 0

        # هزینه‌ها: تراکنش‌های هزینه + پرداخت مدرسین
        total_expenses = AccountingTransaction.objects.filter(transaction_type__in=['expense', 'teacher_payout']).aggregate(t=Sum('amount'))['t'] or 0

        net_profit = total_revenue - total_expenses

        # شهریه کل: مجموع شهریه تمام دوره‌ها
        enrollment_revenue = CourseEnrollment.objects.all().aggregate(total=Sum('total_amount'))['total'] or 0

        total_debt = enrollment_revenue - total_revenue

        # ─── آمار ماه جاری ───
        month_revenue = AccountingTransaction.objects.filter(transaction_type='income', transaction_date__gte=month_start).aggregate(t=Sum('amount'))['t'] or 0

        month_expenses = AccountingTransaction.objects.filter(transaction_type__in=['expense', 'teacher_payout'],transaction_date__gte=month_start).aggregate(t=Sum('amount'))['t'] or 0

        month_net = month_revenue - month_expenses

        # ─── داده‌های نمودار ماهانه (۶ ماه اخیر) ───
        monthly_data = []
        for i in range(5, -1, -1):
            m_start = today.replace(day=1)
            for _ in range(i):
                m_start = (m_start - timedelta(days=1)).replace(day=1)
            m_end_date = m_start.replace(day=calendar.monthrange(m_start.year, m_start.month)[1])

            inc = AccountingTransaction.objects.filter(transaction_type='income',transaction_date__gte=m_start,transaction_date__lte=m_end_date).aggregate(t=Sum('amount'))['t'] or 0

            exp = AccountingTransaction.objects.filter(transaction_type__in=['expense', 'teacher_payout'],transaction_date__gte=m_start,transaction_date__lte=m_end_date).aggregate(t=Sum('amount'))['t'] or 0

            # برچسب شمسی
            jalali_label = to_jalali(m_start).split('/')[1] + '/' + to_jalali(m_start).split('/')[0]

            monthly_data.append({
                'label': jalali_label,
                'income': inc,
                'expense': exp,
                'net': inc - exp,
            })

        # ─── داده‌های نمودار هفتگی (۴ هفته اخیر) ───
        weekly_data = []
        for i in range(3, -1, -1):
            w_end = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
            w_start = w_end - timedelta(days=6)

            inc = AccountingTransaction.objects.filter(transaction_type='income',transaction_date__gte=w_start,transaction_date__lte=w_end).aggregate(t=Sum('amount'))['t'] or 0

            exp = AccountingTransaction.objects.filter(transaction_type__in=['expense', 'teacher_payout'],transaction_date__gte=w_start,transaction_date__lte=w_end).aggregate(t=Sum('amount'))['t'] or 0

            # برچسب شمسی
            j_start = to_jalali(w_start)
            j_end = to_jalali(w_end)
            weekly_data.append({
                'label': f'{j_start}-{j_end}',
                'income': inc,
                'expense': exp,
            })

        # ─── آخرین تراکنش‌ها ───
        recent_transactions = AccountingTransaction.objects.select_related('course', 'student', 'expense_category', 'payment_gateway').order_by('-transaction_date', '-created_at')[:10]

        # ─── درآمد به تفکیک دوره ───
        revenue_by_course = CourseEnrollment.objects.all().values('course__title').annotate(total=Sum('paid_amount'),count=Count('id')
        ).order_by('-total')

        # ─── هزینه به تفکیک دسته ───
        expense_by_category = AccountingTransaction.objects.filter(transaction_type='expense').values('expense_category__name').annotate(total=Sum('amount'),count=Count('id')
        ).order_by('-total')

        return render(request, 'academy/dashboard/accounting_dashboard.html', {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'month_revenue': month_revenue,
            'month_expenses': month_expenses,
            'month_net': month_net,
            'recent_transactions': recent_transactions,
            'revenue_by_course': revenue_by_course,
            'expense_by_category': expense_by_category,
            'enrollment_revenue': enrollment_revenue,
            'total_debt': total_debt,
            'monthly_data': monthly_data,
            'weekly_data': weekly_data,
        })


class AccountingTransactionListView(AdminRequiredMixin, View):
    def get(self, request):
        tx_type = request.GET.get('type', '')
        course_id = request.GET.get('course', '')
        gateway_id = request.GET.get('gateway', '')
        payment_method = request.GET.get('method', '')
        date_from = request.GET.get('from', '')
        date_to = request.GET.get('to', '')

        transactions = AccountingTransaction.objects.select_related(
            'course', 'student', 'expense_category', 'payment_gateway', 'created_by'
        )

        if tx_type:
            transactions = transactions.filter(transaction_type=tx_type)
        if course_id:
            transactions = transactions.filter(course_id=course_id)
        if gateway_id:
            transactions = transactions.filter(payment_gateway_id=gateway_id)
        if payment_method:
            transactions = transactions.filter(payment_method=payment_method)
        if date_from:
            greg_date = to_gregorian(date_from)
            if greg_date:
                transactions = transactions.filter(transaction_date__gte=greg_date)
        if date_to:
            greg_date = to_gregorian(date_to)
            if greg_date:
                transactions = transactions.filter(transaction_date__lte=greg_date)

        transactions = transactions.order_by('-transaction_date', '-created_at')

        courses = Course.objects.all()
        gateways = PaymentGateway.objects.filter(is_active=True)

        total = transactions.aggregate(t=Sum('amount'))['t'] or 0

        # آمار تفکیکی
        income_total = transactions.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or 0
        expense_total = transactions.filter(transaction_type__in=['expense', 'teacher_payout']).aggregate(t=Sum('amount'))['t'] or 0

        return render(request, 'academy/dashboard/accounting_transactions.html', {
            'transactions': transactions,
            'courses': courses,
            'gateways': gateways,
            'filter_type': tx_type,
            'filter_course': course_id,
            'filter_gateway': gateway_id,
            'filter_method': payment_method,
            'filter_from': date_from,
            'filter_to': date_to,
            'total': total,
            'income_total': income_total,
            'expense_total': expense_total,
        })


class AccountingTransactionCreateView(AdminRequiredMixin, View):
    def get(self, request):
        courses = Course.objects.all()
        students = StudentEnrollment.objects.all()
        categories = ExpenseCategory.objects.all()
        gateways = PaymentGateway.objects.filter(is_active=True)
        teachers = User.objects.filter(role='TEACHER', is_active=True)
        today_jalali = to_jalali(timezone.now().date())
        return render(request, 'academy/dashboard/accounting_transaction_form.html', {
            'courses': courses,
            'students': students,
            'categories': categories,
            'gateways': gateways,
            'teachers': teachers,
            'today_jalali': today_jalali,
        })

    def post(self, request):
        tx_type = request.POST.get('transaction_type')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'cash')
        gateway_id = request.POST.get('payment_gateway')
        card_number = request.POST.get('card_number', '')
        course_id = request.POST.get('course')
        student_id = request.POST.get('student')
        expense_category_id = request.POST.get('expense_category')
        teacher_id = request.POST.get('teacher')
        description = request.POST.get('description', '')
        receipt_number = request.POST.get('receipt_number', '')
        transaction_date_jalali = request.POST.get('transaction_date')

        # تبدیل تاریخ شمسی به میلادی
        transaction_date = to_gregorian(transaction_date_jalali) if transaction_date_jalali else None

        # پاکسازی مقدار جداکننده هزارگان
        if amount:
            amount = amount.replace(',', '')

        errors = []
        if not tx_type:
            errors.append('نوع تراکنش را انتخاب کنید')
        if not amount or not amount.isdigit() or int(amount) <= 0:
            errors.append('مبلغ معتبر وارد کنید')
        if not transaction_date:
            errors.append('تاریخ تراکنش معتبر نیست (فرمت: ۱۴۰۵/۰۴/۰۱)')

        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('academy:accounting_create')

        tx = AccountingTransaction(
            transaction_type=tx_type,
            amount=int(amount),
            payment_method=payment_method,
            payment_gateway_id=gateway_id or None,
            card_number=card_number,
            course_id=course_id or None,
            student_id=student_id or None,
            expense_category_id=expense_category_id or None,
            teacher_id=teacher_id or None,
            description=description,
            receipt_number=receipt_number,
            transaction_date=transaction_date,
            created_by=request.user,
        )
        tx.save()
        messages.success(request, 'تراکنش با موفقیت ثبت شد')
        return redirect('academy:accounting_transactions')


class CourseProfitReportView(AdminRequiredMixin, View):
    def get(self, request):
        courses = Course.objects.all()

        course_stats = []
        for course in courses:
            # ─── درآمد: فقط از پرداخت هنرجویان ───
            revenue = CourseEnrollment.objects.filter(course=course).aggregate(t=Sum('paid_amount'))['t'] or 0

            # ─── شهریه کل ───
            total_tuition = CourseEnrollment.objects.filter(course=course).aggregate(t=Sum('total_amount'))['t'] or 0

            # ─── پرداخت به مدرس ───
            teacher_payouts = AccountingTransaction.objects.filter(course=course, transaction_type='teacher_payout').aggregate(t=Sum('amount'))['t'] or 0

            # ─── سایر هزینه‌ها ───
            other_expenses = AccountingTransaction.objects.filter(course=course, transaction_type='expense').aggregate(t=Sum('amount'))['t'] or 0

            total_expenses = teacher_payouts + other_expenses
            net = revenue - total_expenses

            student_count = course.active_enrollments.count()
            session_count = course.sessions.count()

            teacher_name = str(course.teacher) if course.teacher_id else '—'

            course_stats.append({
                'course': course,
                'teacher_name': teacher_name,
                'revenue': revenue,
                'teacher_payouts': teacher_payouts,
                'other_expenses': other_expenses,
                'total_expenses': total_expenses,
                'net_profit': net,
                'student_count': student_count,
                'session_count': session_count,
                'total_tuition': total_tuition,
            })

        grand_revenue = sum(c['revenue'] for c in course_stats)
        grand_expenses = sum(c['total_expenses'] for c in course_stats)
        grand_net = grand_revenue - grand_expenses

        return render(request, 'academy/dashboard/course_profit_report.html', {
            'course_stats': course_stats,
            'grand_revenue': grand_revenue,
            'grand_expenses': grand_expenses,
            'grand_net': grand_net,
        })


class TeacherPayoutListView(AdminRequiredMixin, View):
    def get(self, request):
        payouts = AccountingTransaction.objects.filter(transaction_type='teacher_payout').select_related('teacher', 'course').order_by('-transaction_date')

        total = payouts.aggregate(t=Sum('amount'))['t'] or 0

        # آمار به تفکیک مدرس
        from django.db.models import Count
        by_teacher = payouts.values(
            'teacher__first_name', 'teacher__last_name', 'teacher__username'
        ).annotate(
            total_paid=Sum('amount'),
            tx_count=Count('id')
        ).order_by('-total_paid')

        # آمار ماه جاری
        today = timezone.now().date()
        month_start = today.replace(day=1)
        month_total = payouts.filter(
            transaction_date__gte=month_start
        ).aggregate(t=Sum('amount'))['t'] or 0

        return render(request, 'academy/dashboard/teacher_payouts.html', {
            'payouts': payouts,
            'total': total,
            'by_teacher': by_teacher,
            'month_total': month_total,
            'payout_count': payouts.count(),
        })


class AccountingTransactionDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        tx = get_object_or_404(AccountingTransaction.objects.all(), pk=pk)
        tx.delete()
        messages.success(request, 'تراکنش حذف شد')
        return redirect('academy:accounting_transactions')
