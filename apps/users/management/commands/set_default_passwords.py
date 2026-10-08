from django.conf import settings
from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    help = 'Set DEFAULT_INITIAL_PASSWORD for teachers/students without a usable password'

    def handle(self, *args, **options):
        password = settings.DEFAULT_INITIAL_PASSWORD
        users = User.objects.filter(role__in=['TEACHER', 'STUDENT'])
        count = 0
        for user in users:
            if not user.has_usable_password():
                user.set_password(password)
                user.save(update_fields=['password'])
                count += 1
                self.stdout.write(f'  ✓ {user.get_full_name() or user.username} ({user.role})')

        self.stdout.write(self.style.SUCCESS(
            f'\nتعداد {count} کاربر رمز اولیه دریافت کردند (از DEFAULT_INITIAL_PASSWORD).'
        ))
