from pathlib import Path
import os
import environ

from .product_mode import ACADEMY, CONTROL, SCHOOL, get_product_mode

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# A deployment normally reads ``.env``. Local development can point the same
# source tree at an isolated product configuration (for example ``.env.school``)
# without copying code or risking the academy database.
ENV_FILE = Path(os.environ.get('DANA_ENV_FILE', BASE_DIR / '.env'))
environ.Env.read_env(ENV_FILE)

SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG', default=False)

# Each customer installation exposes exactly one operational product.  The
# default preserves the current live academy behaviour until an installation
# is deliberately provisioned as a school or central control instance.
PRODUCT_MODE = get_product_mode(env('PRODUCT_MODE', default='academy'))

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['yourdomain.com', 'localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:8000', 'http://127.0.0.1:8000'])
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)

INSTALLED_APPS = [
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
    # ``users.StudentAccount`` is a legacy academy relation. The academy app
    # must remain registered until that model is migrated safely, even in a
    # school/control installation. Its URLs remain product-gated below.
    'apps.academy',
    'apps.schools',
]

# Product-only apps are loaded only by their owning installation. Operational
# access is also gated at URL level in ``config.urls``.
if PRODUCT_MODE == ACADEMY:
    INSTALLED_APPS += [
        'apps.crm',
        'apps.teacher_panel',
        'apps.student_panel',
        'apps.forms_builder',
    ]
elif PRODUCT_MODE == SCHOOL:
    INSTALLED_APPS += ['apps.school_management']
elif PRODUCT_MODE == CONTROL:
    INSTALLED_APPS += ['apps.control_center']

if DEBUG:
    INSTALLED_APPS += ['django_browser_reload']

TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = env('NPM_BIN_PATH', default=r'C:\Program Files\nodejs\npm.cmd')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.schools.middleware.SchoolMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(-1, "django_browser_reload.middleware.BrowserReloadMiddleware")

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'theme', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.schools.context_processors.school_context',
                'config.context_processors.product_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
}

AUTH_USER_MODEL = 'users.User'
if PRODUCT_MODE == ACADEMY:
    LOGIN_URL = 'academy:login'
    LOGIN_REDIRECT_URL = 'academy:dashboard_home'
elif PRODUCT_MODE == SCHOOL:
    LOGIN_URL = 'school_admin:login'
    LOGIN_REDIRECT_URL = '/admin/'
else:
    LOGIN_URL = 'admin:login'
    LOGIN_REDIRECT_URL = '/control/requests/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa-ir'
USE_I18N = True
USE_TZ = True

TIME_ZONE = 'Asia/Tehran'

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'theme', 'static'),
]
STATIC_ROOT = env('STATIC_ROOT', default=os.path.join(BASE_DIR, 'staticfiles'))
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

PRIVATE_STORAGE_ROOT = os.path.join(BASE_DIR, 'private-media')
PRIVATE_STORAGE_AUTH_FUNCTION = 'private_storage.permissions.allow_staff'

IPPANEL_API_TOKEN = env('IPPANEL_API_TOKEN', default='')
IPPANEL_SENDER = env('IPPANEL_SENDER', default='')
SMS_ADMIN_PHONES = env.list('SMS_ADMIN_PHONES', default=[])

# آدرس برگشت پرداخت — اگه تنظیم نشه از دامنه جاری استفاده میشه
PAYMENT_CALLBACK_URL = env('PAYMENT_CALLBACK_URL', default='')
# درگاه پرداخت سان‌تک — وقتی هر سه پر باشند، پرداخت‌ها از این درگاه ساخته
# می‌شوند؛ خالی = روش قبلی (مستقیم با آقای پرداخت). apps/academy/services/payment_flow.py
PAYMENT_GATEWAY_URL = env('PAYMENT_GATEWAY_URL', default='')
PAYMENT_GATEWAY_CLIENT_ID = env('PAYMENT_GATEWAY_CLIENT_ID', default='')
PAYMENT_GATEWAY_SECRET = env('PAYMENT_GATEWAY_SECRET', default='')
# آدرس عمومی پنل، برای return_url و notify_url که به درگاه داده می‌شود
PANEL_PUBLIC_URL = env('PANEL_PUBLIC_URL', default='https://panel.aihousesb.ir')

JITSI_DOMAIN = env('JITSI_DOMAIN', default='meet.jit.si')

JALALI_DATE_DEFAULTS = {
    'Strftime': {
        'date': '%y/%m/%d',
        'datetime': '%y/%m/%d %H:%M:%S',
    },
    'Static': {
        'css': ['admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css'],
    },
}
