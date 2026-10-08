from django.conf import settings

from config.profile import get_profile


def product_context(request):
    profile = get_profile()
    ctx = {
        "product_mode": settings.PRODUCT_MODE,
        "website_enabled": settings.WEBSITE_ENABLED,
    }
    ctx.update(profile.website_public_context())
    return ctx
