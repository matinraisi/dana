from django.conf import settings


def product_context(request):
    return {"product_mode": settings.PRODUCT_MODE}
