"""Load non-secret install identity from install_config.py (pre-DB bootstrap).

Product profile must be known before INSTALLED_APPS and migrations. This loader
uses only the stdlib — no Django apps, no database, no secrets.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

from django.core.exceptions import ImproperlyConfigured


DEFAULT_INSTALL_FILENAME = "install_config.py"
EXAMPLE_INSTALL_FILENAME = "install_config.example.py"


def resolve_install_config_path(base_dir: Path | str) -> Path:
    """Return the install config path (DANA_INSTALL_FILE or ``base_dir/install_config.py``)."""
    override = os.environ.get("DANA_INSTALL_FILE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(base_dir).resolve() / DEFAULT_INSTALL_FILENAME


def load_install_config_module(path: Path) -> ModuleType:
    """Import ``path`` as a Python module named ``dana_install_config``."""
    path = Path(path)
    if not path.is_file():
        example = path.with_name(EXAMPLE_INSTALL_FILENAME)
        hint = (
            f"Copy {EXAMPLE_INSTALL_FILENAME} to {DEFAULT_INSTALL_FILENAME} "
            "and set PRODUCT_MODE (academy | school | control). "
            "Or set DANA_INSTALL_FILE to an absolute path."
        )
        if example.is_file() or path.name == DEFAULT_INSTALL_FILENAME:
            raise ImproperlyConfigured(
                f"Install identity file not found: {path}. {hint}"
            )
        raise ImproperlyConfigured(
            f"Install identity file not found: {path}. {hint}"
        )

    spec = importlib.util.spec_from_file_location("dana_install_config", path)
    if spec is None or spec.loader is None:
        raise ImproperlyConfigured(
            f"Cannot load install identity file: {path}. "
            f"Ensure it is a valid Python file (see {EXAMPLE_INSTALL_FILENAME})."
        )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 — surface as config error
        raise ImproperlyConfigured(
            f"Failed to execute install identity file {path}: {exc}. "
            f"See {EXAMPLE_INSTALL_FILENAME}."
        ) from exc
    return module


def website_enabled_from_module(module: ModuleType, *, default: bool = True) -> bool:
    """Read WEBSITE_ENABLED from the install module (bool; default if omitted)."""
    if not hasattr(module, "WEBSITE_ENABLED"):
        return default
    value = getattr(module, "WEBSITE_ENABLED")
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    raise ImproperlyConfigured(
        f"WEBSITE_ENABLED in install_config must be a boolean. Received: {value!r}."
    )
