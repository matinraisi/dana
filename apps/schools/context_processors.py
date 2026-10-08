from apps.installation.utils import get_installation_config
from apps.academy.org import get_instance_organization


def school_context(request):
    """Branding: Academy Organization first, then InstallationConfig fallback."""
    installation = get_installation_config()
    school = get_instance_organization()

    title = (
        (school.title if school else None)
        or installation.organization_name
        or 'دانا'
    )
    logo = None
    if school and school.logo:
        logo = school.logo.url
    elif installation.logo:
        logo = installation.logo.url
    favicon = None
    if school and school.favicon:
        favicon = school.favicon.url
    elif installation.favicon:
        favicon = installation.favicon.url
    color = (
        (school.primary_color if school else None)
        or installation.primary_color
        or '#4f46e5'
    )
    return {
        'school': school,
        'school_title': title,
        'school_logo': logo,
        'school_favicon': favicon,
        'school_color': color,
    }
