from django.core.management.base import BaseCommand
from apps.academy.models import StudentEnrollment, Course
from apps.users.models import User
from apps.schools.models import School


class Command(BaseCommand):
    help = 'Fix school=null on Users, Courses, and StudentEnrollments'

    def handle(self, *args, **options):
        default_school = School.objects.filter(is_active=True).first()
        if not default_school:
            self.stdout.write(self.style.ERROR('No active school found!'))
            return

        # 1. Fix Users without school — infer from owned school
        orphaned_users = User.objects.filter(school__isnull=True).exclude(is_superuser=True)
        users_fixed = 0
        for user in orphaned_users:
            owned = School.objects.filter(owner=user).first()
            if owned:
                user.school = owned
                user.save(update_fields=['school'])
                users_fixed += 1
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Skipping user {user.username} (id={user.id}) — no owned school'
                ))

        # 2. Fix Courses without school — assign to default school
        orphaned_courses = Course.objects.filter(school__isnull=True)
        courses_fixed = 0
        for course in orphaned_courses:
            course.school = default_school
            course.save(update_fields=['school'])
            courses_fixed += 1

        # 3. Fix Students without school — infer from enrolled courses
        orphaned_students = StudentEnrollment.objects.filter(school__isnull=True)
        students_fixed = 0
        for student in orphaned_students:
            first_course = student.active_enrollments.select_related('course').first()
            if first_course and first_course.course.school_id:
                student.school_id = first_course.course.school_id
                student.save(update_fields=['school'])
                students_fixed += 1
            else:
                student.school = default_school
                student.save(update_fields=['school'])
                students_fixed += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Fixed {users_fixed} users, {courses_fixed} courses, {students_fixed} students. '
            f'Default school: {default_school.title}'
        ))
