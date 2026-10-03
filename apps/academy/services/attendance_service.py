from django.db import transaction
from django.db.models import Count, Q
from ..models import Attendance, Session, StudentEnrollment


class AttendanceService:

    STATUS_CHOICES = [
        ('present', 'حاضر'),
        ('absent', 'غایب'),
        ('late', 'تأخیر'),
        ('excused', 'موجه'),
    ]

    @staticmethod
    @transaction.atomic
    def bulk_save(session_id: int, attendance_data: dict) -> int:
        session = Session.objects.get(id=session_id)
        saved = 0
        for student_id, status in attendance_data.items():
            Attendance.objects.update_or_create(
                session=session,
                student_id=student_id,
                defaults={'status': status},
            )
            saved += 1
        AttendanceService._notify_absents(session, attendance_data)
        return saved

    @staticmethod
    def get_sheet(session_id: int) -> dict:
        session = Session.objects.select_related('course').get(id=session_id)
        enrolled_students = StudentEnrollment.objects.filter(
            active_enrollments__course=session.course
        ).order_by('first_name', 'last_name')

        existing = {
            a.student_id: a.status
            for a in Attendance.objects.filter(session=session)
        }

        sheet = [
            {'student': s, 'status': existing.get(s.id, 'absent')}
            for s in enrolled_students
        ]

        return {
            'session': session,
            'sheet': sheet,
            'status_choices': AttendanceService.STATUS_CHOICES,
        }

    @staticmethod
    def get_student_report(student_id: int, course_id: int) -> dict:
        attendances = Attendance.objects.filter(
            student_id=student_id,
            session__course_id=course_id,
        ).select_related('session').order_by('session__session_number')

        total = attendances.count()
        present = attendances.filter(status__in=['present', 'late']).count()
        absent = attendances.filter(status='absent').count()
        excused = attendances.filter(status='excused').count()
        percent = round((present / total * 100), 1) if total > 0 else 0

        return {
            'attendances': attendances,
            'total': total,
            'present': present,
            'absent': absent,
            'excused': excused,
            'percent': percent,
        }

    @staticmethod
    def get_course_summary(course_id: int):
        return StudentEnrollment.objects.filter(
            active_enrollments__course_id=course_id
        ).annotate(
            present_count=Count(
                'attendances',
                filter=Q(
                    attendances__session__course_id=course_id,
                    attendances__status__in=['present', 'late'],
                ),
            ),
            absent_count=Count(
                'attendances',
                filter=Q(
                    attendances__session__course_id=course_id,
                    attendances__status='absent',
                ),
            ),
        )

    @staticmethod
    def _notify_absents(session, attendance_data: dict):
        from .sms_service import SmsService
        absent_ids = [sid for sid, status in attendance_data.items() if status == 'absent']
        if not absent_ids:
            return
        for student in StudentEnrollment.objects.filter(id__in=absent_ids):
            SmsService.notify_absence(student, session)
