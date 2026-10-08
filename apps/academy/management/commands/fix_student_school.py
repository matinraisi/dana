from django.core.management.base import BaseCommand

from apps.academy.models import Course, StudentEnrollment
from apps.academy.org import get_instance_organization, set_organization
from apps.users.models import User


class Command(BaseCommand):
    help = 'Stamp null school FKs and memberships with the singleton Academy Organization'

    def handle(self, *args, **options):
        org = get_instance_organization()
        if not org:
            self.stdout.write(self.style.ERROR('No Academy Organization found!'))
            return

        users_fixed = 0
        for user in User.objects.filter(academy_membership__isnull=True).exclude(is_superuser=True):
            set_organization(user, org)
            users_fixed += 1

        courses_fixed = Course.objects.filter(school__isnull=True).update(school=org)
        students_fixed = StudentEnrollment.objects.filter(school__isnull=True).update(school=org)

        self.stdout.write(self.style.SUCCESS(
            f'Done. Fixed {users_fixed} users, {courses_fixed} courses, {students_fixed} students. '
            f'Organization id={org.pk}'
        ))
