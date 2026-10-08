"""Academy organization helpers for the single-org-per-instance model."""

from django.core.exceptions import ObjectDoesNotExist


def get_instance_organization():
    """Return the single Academy Organization for this instance, or None."""
    from apps.schools.models import School

    return School.get_instance()


def get_instance_organization_id():
    org = get_instance_organization()
    return org.pk if org else None


def get_organization(user):
    """Return the Academy Organization linked to the user via membership.

    Falls back to the instance organization when the user is authenticated
    but has no membership row yet (common for legacy accounts).
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.academy_membership.organization
    except ObjectDoesNotExist:
        return get_instance_organization()


def set_organization(user, organization=None):
    """Assign the user to an Academy organization (defaults to instance org)."""
    from .models import OrganizationMembership

    if organization is None:
        organization = get_instance_organization()
    if organization is None:
        OrganizationMembership.objects.filter(user=user).delete()
        return None
    membership, _ = OrganizationMembership.objects.update_or_create(
        user=user,
        defaults={'organization': organization},
    )
    return membership
