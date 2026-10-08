"""Migrate clean DBs for academy/school/control and assert schema isolation.

Usage (from repo root, with project venv):

    python scripts/verify_profile_schemas.py

Uses a temporary install_config.py per mode via DANA_INSTALL_FILE
(product identity is not taken from the environment).
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
MANAGE = ROOT / 'manage.py'

ACADEMY_FORBIDDEN_ON_SCHOOL = (
    'academy_', 'schools_', 'crm_', 'forms_builder_',
    'users_teacher', 'users_studentaccount',
)
ACADEMY_OR_SCHOOL_FORBIDDEN_ON_CONTROL = ACADEMY_FORBIDDEN_ON_SCHOOL + (
    'school_management_',
)


def _write_install_config(path: Path, mode: str) -> None:
    path.write_text(
        f'PRODUCT_MODE = "{mode}"\nWEBSITE_ENABLED = False\n',
        encoding='utf-8',
        newline='\n',
    )


def _run_migrate(mode: str, db_path: Path, install_path: Path) -> None:
    env = os.environ.copy()
    # Product identity comes from the install file only — strip env PRODUCT_MODE.
    env.pop('PRODUCT_MODE', None)
    env.pop('WEBSITE_ENABLED', None)
    env['DANA_INSTALL_FILE'] = str(install_path)
    env['DATABASE_URL'] = f'sqlite:///{db_path.as_posix()}'
    env['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    # Ensure SECRET_KEY exists for settings import (may already be in .env).
    env.setdefault('SECRET_KEY', 'verify-profile-schemas-temporary-key')
    result = subprocess.run(
        [PYTHON, str(MANAGE), 'migrate', '--run-syncdb', '--verbosity', '1'],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(f'migrate failed for PRODUCT_MODE={mode}')


def _tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def _leaked(tables: set[str], prefixes: tuple[str, ...]) -> list[str]:
    return sorted(t for t in tables if any(t.startswith(p) or t == p for p in prefixes))


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix='dana_profiles_'))
    print(f'Working directory: {tmp}')

    results = {}
    for mode in ('academy', 'school', 'control'):
        db_path = tmp / f'{mode}.sqlite3'
        install_path = tmp / f'install_{mode}.py'
        _write_install_config(install_path, mode)
        print(f'\n=== Migrating {mode} -> {db_path.name} ===')
        _run_migrate(mode, db_path, install_path)
        tables = _tables(db_path)
        results[mode] = tables
        print(f'{mode}: {len(tables)} tables')

    academy_tables = results['academy']
    school_tables = results['school']
    control_tables = results['control']

    errors = []

    if not any(t.startswith('academy_') for t in academy_tables):
        errors.append('Academy DB missing academy_* tables')
    if not any(t.startswith('schools_') for t in academy_tables):
        errors.append('Academy DB missing schools_* tables')

    leaked_school = _leaked(school_tables, ACADEMY_FORBIDDEN_ON_SCHOOL)
    if leaked_school:
        errors.append(f'School DB has Academy tables: {leaked_school}')
    if not any(t.startswith('school_management_') for t in school_tables):
        errors.append('School DB missing school_management_* tables')

    leaked_control = _leaked(control_tables, ACADEMY_OR_SCHOOL_FORBIDDEN_ON_CONTROL)
    if leaked_control:
        errors.append(f'Control DB has Academy/School tables: {leaked_control}')
    if not any(t.startswith('control_center_') for t in control_tables):
        errors.append('Control DB missing control_center_* tables')

    for mode, tables in results.items():
        if 'users_user' not in tables:
            errors.append(f'{mode} DB missing users_user')

    if errors:
        print('\nFAILED:')
        for e in errors:
            print(' -', e)
        raise SystemExit(1)

    print('\nOK — profile schemas are isolated.')
    print(f'Artifacts kept at: {tmp}')


if __name__ == '__main__':
    main()
