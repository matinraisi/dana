from django.core.management.base import BaseCommand
from apps.academy.models import Course
from django.utils.text import slugify
import uuid


class Command(BaseCommand):
    help = "Fix course registration_slug safely"

    def handle(self, *args, **kwargs):

        courses = Course.objects.all()
        updated = 0

        for course in courses:
            base = slugify(getattr(course, "title", "course"))
            course.registration_slug = f"{base}-{uuid.uuid4().hex[:8]}"
            course.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated {updated} courses."
        ))