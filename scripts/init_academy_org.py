"""Create or attach the singleton Academy Organization for this Academy instance.

Run only when PRODUCT_MODE=academy, after migrate and createsuperuser.

Usage:
  python scripts/init_academy_org.py --title "Customer Academy Name"
  python scripts/init_academy_org.py --title "Customer Academy Name" --slug customer-slug

Does not invent Suntech/default demo data. Existing singleton is left unchanged
unless --force-title is passed (updates title only).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.academy.models import Course, OrganizationMembership, StudentEnrollment
from apps.academy.org import set_organization
from apps.schools.models import School


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Academy Organization singleton")
    parser.add_argument(
        "--title",
        required=True,
        help="Real customer organization name (required; no hardcoded default)",
    )
    parser.add_argument(
        "--slug",
        default="",
        help="Optional unique slug (auto-derived from title if omitted)",
    )
    parser.add_argument(
        "--force-title",
        action="store_true",
        help="If organization already exists, update its title to --title",
    )
    args = parser.parse_args()

    if getattr(settings, "PRODUCT_MODE", None) != "academy":
        print(
            f"ERROR: PRODUCT_MODE is {getattr(settings, 'PRODUCT_MODE', None)!r}. "
            "This script is only for Academy installs "
            '(set PRODUCT_MODE = "academy" in install_config.py).',
            file=sys.stderr,
        )
        return 1

    title = (args.title or "").strip()
    if not title:
        print("ERROR: --title must be a non-empty customer organization name.", file=sys.stderr)
        return 1

    User = get_user_model()
    existing = School.get_instance()
    if existing:
        school = existing
        print(f"Using existing Academy Organization (id={school.id}, title={school.title!r})")
        if args.force_title and school.title != title:
            school.title = title
            school.save()
            print(f"Updated organization title to {title!r}")
    else:
        owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not owner:
            print(
                "ERROR: No user available to own the Academy Organization. "
                "Run: python manage.py createsuperuser",
                file=sys.stderr,
            )
            return 1
        slug = (args.slug or "").strip() or slugify(title, allow_unicode=True) or "org"
        # Keep slug unique if collision
        base_slug = slug[:80]
        candidate = base_slug
        n = 1
        while School.objects.filter(slug=candidate).exists():
            n += 1
            candidate = f"{base_slug[:70]}-{n}"
        school = School(
            title=title,
            slug=candidate,
            owner=owner,
            is_active=True,
        )
        school.save()
        print(f"Created Academy Organization id={school.id} title={title!r} slug={candidate!r}")

    for user in User.objects.filter(academy_membership__isnull=True):
        set_organization(user, school)

    Course.objects.filter(school__isnull=True).update(school_id=school.id)
    StudentEnrollment.objects.filter(school__isnull=True).update(school_id=school.id)

    print(f"Users assigned: {OrganizationMembership.objects.filter(organization=school).count()}")
    print(f"Courses stamped: {Course.objects.filter(school=school).count()}")
    print(f"Students stamped: {StudentEnrollment.objects.filter(school=school).count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
