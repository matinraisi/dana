"""Product profile registry — bootstrap composition for Dana instances.

``PRODUCT_MODE`` from ``install_config.py`` selects one profile. Business
logic must not become a scattered PRODUCT_MODE switchboard; ask the active
profile instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from django.core.exceptions import ImproperlyConfigured

from .product_mode import ACADEMY, CONTROL, SCHOOL, VALID_PRODUCT_MODES, get_product_mode


# ---------------------------------------------------------------------------
# Kernel (always installed)
# ---------------------------------------------------------------------------

KERNEL_APPS: tuple[str, ...] = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'tailwind',
    'theme',
    'django_jalali',
    'apps.users',
    'apps.installation',
    # notifications is a pure Python package (no AppConfig / models).
)

KERNEL_MIDDLEWARE: tuple[str, ...] = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

KERNEL_CONTEXT_PROCESSORS: tuple[str, ...] = (
    'django.template.context_processors.request',
    'apps.installation.context_processors.installation',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'config.context_processors.product_context',
)


def _academy_home(user) -> str | None:
    if not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser or getattr(user, 'is_admin_staff', False):
        return 'academy:dashboard_home'
    if getattr(user, 'role', None) == 'TEACHER':
        return 'teacher:dashboard'
    if getattr(user, 'role', None) == 'STUDENT':
        return 'student:dashboard'
    return None


def _school_home(user) -> str | None:
    if not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser or user.is_staff or getattr(user, 'is_school_user', False):
        return 'school_management:home'
    return None


def _control_home(user) -> str | None:
    if not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser or user.is_staff:
        return 'control_center:request_list'
    return None


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    apps: tuple[str, ...]
    middleware: tuple[str, ...] = ()
    context_processors: tuple[str, ...] = ()
    urls_module: str = ''
    login_url: str = 'admin:login'
    login_redirect_url: str = '/admin/'
    root_redirect: str = '/admin/'
    authenticated_home: Callable | None = None
    # Optional public Website surface — targets are URL names or absolute paths.
    # Templates must use these hooks instead of hard-coding product URLs.
    website_cta_target: str | None = None  # None → login_url
    website_cta_nav_label: str = 'ورود'
    website_cta_hero_label: str = 'شروع'
    website_cta_closing_label: str = 'ورود به پنل'
    website_extra_links: tuple[tuple[str, str], ...] = ()  # (target, label)
    website_closing_title: str = ''
    website_closing_body: str = ''

    def resolve_authenticated_home(self, user) -> str | None:
        if self.authenticated_home is None:
            return None
        return self.authenticated_home(user)

    def resolve_public_url(self, target: str) -> str:
        """Resolve a named URL or pass through an absolute path."""
        if str(target).startswith('/'):
            return str(target)
        from django.urls import reverse

        return reverse(target)

    def website_public_context(self) -> dict:
        """Profile-owned public Website CTAs for templates (no PRODUCT_MODE branching)."""
        target = self.website_cta_target or self.login_url
        primary_url = self.resolve_public_url(target)
        extras = [
            {'url': self.resolve_public_url(link_target), 'label': label}
            for link_target, label in self.website_extra_links
        ]
        return {
            'website_cta_url': primary_url,
            'website_cta_nav_label': self.website_cta_nav_label,
            'website_cta_hero_label': self.website_cta_hero_label,
            'website_cta_closing_label': self.website_cta_closing_label,
            'website_extra_links': extras,
            'website_closing_title': self.website_closing_title,
            'website_closing_body': self.website_closing_body,
        }


PROFILES: dict[str, Profile] = {
    ACADEMY: Profile(
        key=ACADEMY,
        label='Academy',
        apps=(
            'apps.schools',          # Academy Organization (legacy name)
            'apps.academy',
            'apps.crm',
            'apps.teacher_panel',
            'apps.student_panel',
            'apps.forms_builder',
        ),
        context_processors=('apps.schools.context_processors.school_context',),
        urls_module='apps.academy.urls_profile',
        login_url='academy:login',
        login_redirect_url='academy:dashboard_home',
        root_redirect='academy:login',
        authenticated_home=_academy_home,
        website_cta_nav_label='ورود مدیریت',
        website_cta_hero_label='شروع رایگان',
        website_cta_closing_label='ورود به پنل مدیریت',
        website_extra_links=(
            ('users:teacher_login', 'ورود استاد'),
            ('users:student_login', 'ورود هنرجو'),
        ),
        website_closing_title='آموزشگاه هوشمند را امروز شروع کنید',
        website_closing_body='با دانا و قدرت هوش مصنوعی، مدیریت آموزشگاه را متحول کنید',
    ),
    SCHOOL: Profile(
        key=SCHOOL,
        label='School',
        apps=('apps.school_management',),
        urls_module='apps.school_management.urls_profile',
        login_url='school_admin:login',
        login_redirect_url='/school-panel/',
        root_redirect='/school-panel/',
        authenticated_home=_school_home,
        website_cta_nav_label='ورود مدیریت',
        website_cta_hero_label='ورود به پنل مدرسه',
        website_cta_closing_label='ورود به پنل مدرسه',
        website_extra_links=(),
        website_closing_title='مدرسه خود را با دانا هوشمند مدیریت کنید',
        website_closing_body='وارد پنل مدرسه شوید و ساختار آموزشی را مدیریت کنید.',
    ),
    CONTROL: Profile(
        key=CONTROL,
        label='Control',
        apps=('apps.control_center',),
        urls_module='apps.control_center.urls_profile',
        login_url='admin:login',
        login_redirect_url='/control/requests/',
        root_redirect='/control/requests/',
        authenticated_home=_control_home,
        website_cta_target='control_center:request_create',
        website_cta_nav_label='درخواست دمو',
        website_cta_hero_label='درخواست دمو',
        website_cta_closing_label='ثبت درخواست دمو',
        website_extra_links=(),
        website_closing_title='مدرسه یا آموزشگاه خود را با دانا هوشمند کنید',
        website_closing_body='برای دریافت دمو و راه‌اندازی اختصاصی درخواست خود را ثبت کنید.',
    ),
}


def get_profile(mode: str | None = None) -> Profile:
    """Return the Profile for ``mode`` (or current settings.PRODUCT_MODE)."""
    if mode is None:
        from django.conf import settings
        if not hasattr(settings, 'PRODUCT_MODE'):
            raise ImproperlyConfigured(
                'settings.PRODUCT_MODE is not configured. '
                'Set PRODUCT_MODE in install_config.py (or DANA_INSTALL_FILE).'
            )
        mode = settings.PRODUCT_MODE
    mode = get_product_mode(mode)
    try:
        return PROFILES[mode]
    except KeyError as exc:
        raise ImproperlyConfigured(f'Unknown product profile: {mode!r}') from exc


def installed_apps_for(mode: str, *, debug: bool = False, website_enabled: bool = True) -> list[str]:
    profile = get_profile(mode)
    apps = list(KERNEL_APPS) + list(profile.apps)
    if website_enabled:
        apps.append('website')
    if debug:
        apps.append('django_browser_reload')
    return apps


def middleware_for(mode: str, *, debug: bool = False) -> list[str]:
    profile = get_profile(mode)
    items = list(KERNEL_MIDDLEWARE) + list(profile.middleware)
    if debug:
        # Insert reload middleware before the last (XFrame) entry for parity.
        items.insert(-1, 'django_browser_reload.middleware.BrowserReloadMiddleware')
    return items


def context_processors_for(mode: str) -> list[str]:
    profile = get_profile(mode)
    return list(KERNEL_CONTEXT_PROCESSORS) + list(profile.context_processors)


def profile_app_labels(mode: str) -> frozenset[str]:
    """Short app labels owned exclusively by the profile (not kernel)."""
    profile = get_profile(mode)
    labels = set()
    for app in profile.apps:
        labels.add(app.rsplit('.', 1)[-1])
    return frozenset(labels)


# Forbidden product app labels for architecture tests
ACADEMY_DOMAIN_LABELS = frozenset({
    'academy', 'schools', 'crm', 'teacher_panel', 'student_panel', 'forms_builder',
})
SCHOOL_DOMAIN_LABELS = frozenset({'school_management'})
CONTROL_DOMAIN_LABELS = frozenset({'control_center'})

__all__ = [
    'ACADEMY', 'SCHOOL', 'CONTROL', 'VALID_PRODUCT_MODES',
    'KERNEL_APPS', 'PROFILES', 'Profile',
    'get_profile', 'installed_apps_for', 'middleware_for', 'context_processors_for',
    'profile_app_labels',
    'ACADEMY_DOMAIN_LABELS', 'SCHOOL_DOMAIN_LABELS', 'CONTROL_DOMAIN_LABELS',
]
