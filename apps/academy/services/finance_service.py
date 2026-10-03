from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from ..models import CourseEnrollment, AcademyInstallment


class FinanceService:

    @staticmethod
    def get_dashboard_stats() -> dict:
        today = timezone.now().date()
        AcademyInstallment.objects.filter(status='pending', due_date__lt=today).update(status='overdue')

        total_revenue = CourseEnrollment.objects.aggregate(t=Sum('paid_amount'))['t'] or 0
        total_debt = CourseEnrollment.objects.aggregate(
            t=Sum('total_amount')
        )['t'] or 0
        remaining = total_debt - total_revenue

        overdue = AcademyInstallment.objects.filter(status='overdue').aggregate(t=Sum('amount'))['t'] or 0
        upcoming = AcademyInstallment.objects.filter(
            status='pending',
            due_date__range=[today, today + timezone.timedelta(days=30)],
        ).aggregate(t=Sum('amount'))['t'] or 0

        return {
            'total_revenue': total_revenue,
            'total_debt': total_debt,
            'remaining': remaining,
            'overdue': overdue,
            'upcoming_30d': upcoming,
        }

    @staticmethod
    @transaction.atomic
    def create_installment_plan(enrollment_id: int, installments: list) -> int:
        """
        installments: [{'amount': 1000000, 'due_date': date(2025, 1, 1)}, ...]
        Returns number of installments created.
        """
        enrollment = CourseEnrollment.objects.get(id=enrollment_id)
        AcademyInstallment.objects.filter(enrollment=enrollment, status='pending').delete()

        created = []
        for item in installments:
            created.append(AcademyInstallment(
                enrollment=enrollment,
                amount=item['amount'],
                due_date=item['due_date'],
            ))
        AcademyInstallment.objects.bulk_create(created)
        return len(created)

    @staticmethod
    @transaction.atomic
    def mark_installment_paid(installment_id: int) -> bool:
        inst = AcademyInstallment.objects.select_for_update().get(id=installment_id)
        if inst.status == 'paid':
            return False
        inst.status = 'paid'
        inst.paid_at = timezone.now()
        inst.save()
        inst.enrollment.update_paid_amount()
        return True

    @staticmethod
    def get_teacher_earnings(teacher_id: int) -> dict:
        from ..models import Course
        courses = Course.objects.filter(teacher_id=teacher_id)
        course_ids = courses.values_list('id', flat=True)
        enrollments = CourseEnrollment.objects.filter(course_id__in=course_ids)

        total_paid = enrollments.aggregate(t=Sum('paid_amount'))['t'] or 0
        total_sessions = sum(c.sessions.count() for c in courses)

        return {
            'courses': courses,
            'total_paid': total_paid,
            'total_sessions': total_sessions,
            'course_count': courses.count(),
            'student_count': enrollments.values('student').distinct().count(),
        }
