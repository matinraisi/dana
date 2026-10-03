from django.core.management.base import BaseCommand
from apps.users.models import User


DEFAULT_PASSWORD = '123456789'


class Command(BaseCommand):
    help = 'تنظیم رمز عبور پیش‌فرض (123456789) برای تمام اساتید و هنرجویان'

    def handle(self, *args, **options):
        users = User.objects.filter(role__in=['TEACHER', 'STUDENT'])
        count = 0
        for user in users:
            if not user.has_usable_password():
                user.set_password(DEFAULT_PASSWORD)
                user.save(update_fields=['password'])
                count += 1
                self.stdout.write(f'  ✓ {user.get_full_name() or user.username} ({user.role})')

        self.stdout.write(self.style.SUCCESS(
            f'\nتعداد {count} کاربر رمز عبور پیش‌فرض دریافت کردند.'
        ))
