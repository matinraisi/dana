"""PRODUCT_MODE must be explicit via install_config — no silent academy fallback."""

import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.install_loader import (
    load_install_config_module,
    resolve_install_config_path,
    website_enabled_from_module,
)
from config.product_mode import ACADEMY, CONTROL, SCHOOL, get_product_mode


class ProductModeRequiredTests(SimpleTestCase):
    def test_valid_modes(self):
        self.assertEqual(get_product_mode("academy"), ACADEMY)
        self.assertEqual(get_product_mode("SCHOOL"), SCHOOL)
        self.assertEqual(get_product_mode(" control "), CONTROL)

    def test_missing_raises(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            get_product_mode(None)
        self.assertIn("PRODUCT_MODE is required", str(ctx.exception))
        self.assertIn("install_config.py", str(ctx.exception))

        with self.assertRaises(ImproperlyConfigured):
            get_product_mode("")

        with self.assertRaises(ImproperlyConfigured):
            get_product_mode("   ")

    def test_invalid_raises(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            get_product_mode("both")
        self.assertIn("must be one of", str(ctx.exception))
        self.assertIn("install_config.py", str(ctx.exception))


class InstallLoaderTests(SimpleTestCase):
    def test_resolve_default_path(self):
        base = Path(tempfile.mkdtemp())
        path = resolve_install_config_path(base)
        self.assertEqual(path, (base / "install_config.py").resolve())

    def test_resolve_dana_install_file_override(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as fh:
            override = Path(fh.name)
        try:
            with self.settings():  # no-op; we patch env via os.environ
                import os

                previous = os.environ.get("DANA_INSTALL_FILE")
                os.environ["DANA_INSTALL_FILE"] = str(override)
                try:
                    path = resolve_install_config_path(Path(tempfile.mkdtemp()))
                    self.assertEqual(path, override.resolve())
                finally:
                    if previous is None:
                        os.environ.pop("DANA_INSTALL_FILE", None)
                    else:
                        os.environ["DANA_INSTALL_FILE"] = previous
        finally:
            override.unlink(missing_ok=True)

    def test_missing_file_raises_actionable(self):
        missing = Path(tempfile.mkdtemp()) / "install_config.py"
        with self.assertRaises(ImproperlyConfigured) as ctx:
            load_install_config_module(missing)
        msg = str(ctx.exception)
        self.assertIn("not found", msg.lower())
        self.assertIn("install_config.example.py", msg)

    def test_load_product_mode_and_website(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8", newline="\n"
        ) as fh:
            fh.write('PRODUCT_MODE = "school"\nWEBSITE_ENABLED = False\n')
            path = Path(fh.name)
        try:
            module = load_install_config_module(path)
            self.assertEqual(get_product_mode(getattr(module, "PRODUCT_MODE", None)), SCHOOL)
            self.assertIs(website_enabled_from_module(module), False)
        finally:
            path.unlink(missing_ok=True)

    def test_website_default_when_omitted(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8", newline="\n"
        ) as fh:
            fh.write('PRODUCT_MODE = "control"\n')
            path = Path(fh.name)
        try:
            module = load_install_config_module(path)
            self.assertEqual(get_product_mode(module.PRODUCT_MODE), CONTROL)
            self.assertIs(website_enabled_from_module(module, default=True), True)
        finally:
            path.unlink(missing_ok=True)
