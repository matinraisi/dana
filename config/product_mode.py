"""Product-mode boundaries for a Dana installation.

One customer installation runs one operational product.  The source code can
contain both products, but URL exposure is selected explicitly by
``PRODUCT_MODE`` in ``install_config.py`` (not ``.env``).
"""

from django.core.exceptions import ImproperlyConfigured


ACADEMY = "academy"
SCHOOL = "school"
CONTROL = "control"

VALID_PRODUCT_MODES = frozenset({ACADEMY, SCHOOL, CONTROL})


def get_product_mode(value: str | None) -> str:
    """Validate and normalize the operational mode for this install.

    ``PRODUCT_MODE`` must be set explicitly in ``install_config.py``
    (or the file pointed to by ``DANA_INSTALL_FILE``).
    There is no silent default to academy.
    """
    if value is None or not str(value).strip():
        available = ", ".join(sorted(VALID_PRODUCT_MODES))
        raise ImproperlyConfigured(
            "PRODUCT_MODE is required and must be set explicitly to one of: "
            f"{available}. Set it in install_config.py "
            f'(example: PRODUCT_MODE = "academy") '
            "or via DANA_INSTALL_FILE. There is no silent default."
        )
    mode = str(value).strip().lower()
    if mode not in VALID_PRODUCT_MODES:
        available = ", ".join(sorted(VALID_PRODUCT_MODES))
        raise ImproperlyConfigured(
            f"PRODUCT_MODE must be one of: {available}. Received: {value!r}. "
            "Set PRODUCT_MODE in install_config.py (or DANA_INSTALL_FILE)."
        )
    return mode
