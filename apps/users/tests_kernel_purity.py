"""Architecture guard: kernel users must not import product apps."""

import ast
import unittest
from pathlib import Path


KERNEL_FORBIDDEN = {
    'apps.academy',
    'apps.schools',
    'apps.school_management',
    'apps.crm',
    'apps.teacher_panel',
    'apps.student_panel',
    'apps.forms_builder',
    'apps.control_center',
}


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


class KernelUsersPurityTests(unittest.TestCase):
    def test_users_app_has_no_product_imports(self):
        users_root = Path(__file__).resolve().parent
        violations = []
        for path in users_root.rglob('*.py'):
            if 'migrations' in path.parts:
                continue
            if path.name.startswith('test'):
                continue
            imports = _imported_modules(path)
            for mod in imports:
                for forbidden in KERNEL_FORBIDDEN:
                    if mod == forbidden or mod.startswith(forbidden + '.'):
                        violations.append(f'{path.relative_to(users_root.parent.parent)}: {mod}')
        self.assertEqual(violations, [], 'Kernel users leaked product imports:\n' + '\n'.join(violations))

    def test_user_model_has_no_school_field(self):
        from apps.users.models import User

        field_names = {f.name for f in User._meta.get_fields()}
        self.assertNotIn('school', field_names)

    def test_teacher_and_studentaccount_live_in_academy(self):
        from django.apps import apps

        from apps.users import models as users_models

        self.assertFalse(hasattr(users_models, 'Teacher'))
        self.assertFalse(hasattr(users_models, 'StudentAccount'))

        Teacher = apps.get_model('academy', 'Teacher')
        StudentAccount = apps.get_model('academy', 'StudentAccount')
        OrganizationMembership = apps.get_model('academy', 'OrganizationMembership')

        self.assertEqual(Teacher._meta.app_label, 'academy')
        self.assertEqual(StudentAccount._meta.app_label, 'academy')
        self.assertEqual(OrganizationMembership._meta.app_label, 'academy')
        self.assertEqual(Teacher._meta.db_table, 'users_teacher')
        self.assertEqual(StudentAccount._meta.db_table, 'users_studentaccount')
