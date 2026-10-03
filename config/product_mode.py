"""Product-mode boundaries for a Dana installation.

One customer installation runs one operational product.  The source code can
contain both products, but URL exposure is selected explicitly by the
``PRODUCT_MODE`` environment variable.
"""

from django.core.exceptions import ImproperlyConfigured


ACADEMY = "academy"
SCHOOL = "school"
CONTROL = "control"

VALID_PRODUCT_MODES = frozenset({ACADEMY, SCHOOL, CONTROL})


def get_product_mode(value: str) -> str:
    """Validate and normalize the operational mode configured for this install."""
    mode = (value or "").strip().lower()
    if mode not in VALID_PRODUCT_MODES:
        available = ", ".join(sorted(VALID_PRODUCT_MODES))
        raise ImproperlyConfigured(
            f"PRODUCT_MODE must be one of: {available}. Received: {value!r}."
        )
    return mode
