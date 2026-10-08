"""Architecture tests: profile registry composition and import boundaries."""

import ast
from pathlib import Path

from django.test import SimpleTestCase

from config.profile import (
    ACADEMY,
    ACADEMY_DOMAIN_LABELS,
    CONTROL,
    SCHOOL,
    SCHOOL_DOMAIN_LABELS,
    get_profile,
    installed_apps_for,
    profile_app_labels,
)


ROOT = Path(__file__).resolve().parent.parent


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def _scan_imports(app_dir: Path, forbidden_prefixes: set[str]) -> list[str]:
    violations = []
    if not app_dir.exists():
        return violations
    for path in app_dir.rglob('*.py'):
        if 'migrations' in path.parts:
            continue
        if path.name.startswith('test'):
            continue
        for mod in _imported_modules(path):
            for forbidden in forbidden_prefixes:
                if mod == forbidden or mod.startswith(forbidden + '.'):
                    violations.append(f'{path.relative_to(ROOT)} → {mod}')
    return violations


class ProfileRegistryTests(SimpleTestCase):
    def test_academy_apps_exclude_school_and_control(self):
        labels = profile_app_labels(ACADEMY)
        self.assertIn('academy', labels)
        self.assertIn('schools', labels)
        self.assertNotIn('school_management', labels)
        self.assertNotIn('control_center', labels)

    def test_school_apps_exclude_academy(self):
        apps = installed_apps_for(SCHOOL, website_enabled=False)
        joined = ' '.join(apps)
        for label in ACADEMY_DOMAIN_LABELS:
            self.assertNotIn(f'apps.{label}', joined)
        self.assertIn('apps.school_management', apps)
        self.assertIn('apps.users', apps)
        self.assertIn('apps.installation', apps)

    def test_control_apps_exclude_academy_and_school(self):
        apps = installed_apps_for(CONTROL, website_enabled=False)
        joined = ' '.join(apps)
        for label in ACADEMY_DOMAIN_LABELS | SCHOOL_DOMAIN_LABELS:
            self.assertNotIn(f'apps.{label}', joined)
        self.assertIn('apps.control_center', apps)

    def test_profile_login_destinations_differ(self):
        self.assertEqual(get_profile(ACADEMY).login_url, 'academy:login')
        self.assertEqual(get_profile(SCHOOL).login_url, 'school_admin:login')
        self.assertEqual(get_profile(CONTROL).login_url, 'admin:login')

    def test_active_settings_match_registry(self):
        from django.conf import settings
        profile = get_profile(settings.PRODUCT_MODE)
        for app in profile.apps:
            self.assertIn(app, settings.INSTALLED_APPS)


class KernelImportPurityTests(SimpleTestCase):
    FORBIDDEN = {
        'apps.academy', 'apps.schools', 'apps.crm', 'apps.forms_builder',
        'apps.teacher_panel', 'apps.student_panel',
        'apps.school_management', 'apps.control_center',
    }

    def test_users_has_no_product_imports(self):
        self.assertEqual(_scan_imports(ROOT / 'apps' / 'users', self.FORBIDDEN), [])

    def test_installation_has_no_product_imports(self):
        self.assertEqual(_scan_imports(ROOT / 'apps' / 'installation', self.FORBIDDEN), [])

    def test_notifications_has_no_product_imports(self):
        self.assertEqual(_scan_imports(ROOT / 'apps' / 'notifications', self.FORBIDDEN), [])


class CrossProfileImportTests(SimpleTestCase):
    def test_school_does_not_import_academy(self):
        self.assertEqual(
            _scan_imports(
                ROOT / 'apps' / 'school_management',
                {'apps.academy', 'apps.schools', 'apps.crm', 'apps.forms_builder',
                 'apps.teacher_panel', 'apps.student_panel', 'apps.control_center'},
            ),
            [],
        )

    def test_control_does_not_import_academy_or_school(self):
        self.assertEqual(
            _scan_imports(
                ROOT / 'apps' / 'control_center',
                {'apps.academy', 'apps.schools', 'apps.crm', 'apps.forms_builder',
                 'apps.teacher_panel', 'apps.student_panel', 'apps.school_management'},
            ),
            [],
        )

    def test_academy_does_not_import_school_product(self):
        self.assertEqual(
            _scan_imports(
                ROOT / 'apps' / 'academy',
                {'apps.school_management', 'apps.control_center'},
            ),
            [],
        )

    def test_website_does_not_import_product_domain(self):
        violations = _scan_imports(
            ROOT / 'website',
            {
                'apps.academy', 'apps.schools', 'apps.crm',
                'apps.school_management', 'apps.control_center',
                'apps.forms_builder', 'apps.teacher_panel', 'apps.student_panel',
            },
        )
        self.assertEqual(violations, [])
