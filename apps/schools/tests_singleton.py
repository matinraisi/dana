"""Phase 2: one Academy Organization per instance."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.academy.models import Course, OrganizationMembership, StudentEnrollment
from apps.academy.org import (
    get_instance_organization,
    get_organization,
    set_organization,
)
from apps.schools.models import School

User = get_user_model()


class AcademyOrganizationSingletonTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='org_owner', password='x', role='MANAGER_ACADEMY'
        )
        self.org = School.objects.create(
            title='Org A', slug='org-a', owner=self.owner, is_active=True
        )

    def test_get_instance_returns_the_only_org(self):
        self.assertEqual(School.get_instance(), self.org)
        self.assertEqual(get_instance_organization(), self.org)

    def test_second_organization_is_rejected(self):
        other_owner = User.objects.create_user(username='other', password='x')
        with self.assertRaises(ValidationError):
            School.objects.create(
                title='Org B', slug='org-b', owner=other_owner, is_active=True
            )
        self.assertEqual(School.objects.count(), 1)

    def test_membership_links_user_to_instance_org(self):
        user = User.objects.create_user(username='member', password='x', role='TEACHER')
        set_organization(user)
        self.assertEqual(get_organization(user), self.org)
        self.assertEqual(
            OrganizationMembership.objects.get(user=user).organization_id,
            self.org.pk,
        )

    def test_school_fk_stamp_uses_singleton(self):
        course = Course.objects.create(
            title='C1', code='C1', school=get_instance_organization()
        )
        student = StudentEnrollment.objects.create(
            first_name='A', last_name='B', national_code='001',
            phone_number='09121111111', school=get_instance_organization(),
        )
        self.assertEqual(course.school_id, self.org.pk)
        self.assertEqual(student.school_id, self.org.pk)

    def test_context_processor_uses_singleton_org(self):
        from apps.schools.context_processors import school_context

        ctx = school_context(request=type('R', (), {})())
        self.assertEqual(ctx['school'], self.org)
        self.assertEqual(ctx['school_title'], self.org.title)
