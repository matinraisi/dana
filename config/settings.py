from pathlib import Path
import os
import environ

from .install_loader import (
    load_install_config_module,
    resolve_install_config_path,
    website_enabled_from_module,
)
from .product_mode import get_product_mode
from .profile import (
    context_processors_for,
    get_profile,
    installed_apps_for,
    middleware_for,
)

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Infrastructure / secrets only. Product identity lives in install_config.py.
# Local alternate secrets file: DANA_ENV_FILE=/path/to/.env.school
ENV_FILE = Path(os.environ.get('DANA_ENV_FILE', BASE_DIR / '.env'))
environ.Env.read_env(ENV_FILE)

SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG', default=False)

# Bootstrap identity (pre-DB): PRODUCT_MODE + optional WEBSITE_ENABLED.
# Not read from .env — see install_config.example.py / DANA_INSTALL_FILE.
_INSTALL_CONFIG_PATH = resolve_install_config_path(BASE_DIR)
_INSTALL = load_install_config_module(_INSTALL_CONFIG_PATH)
PRODUCT_MODE = get_product_mode(getattr(_INSTALL, 'PRODUCT_MODE', None))
PROFILE = get_profile(PRODUCT_MODE)
WEBSITE_ENABLED = website_enabled_from_module(_INSTALL, default=True)

# Initial password assigned to new teacher/student accounts. Override in production.
DEFAULT_INITIAL_PASSWORD = env('DEFAULT_INITIAL_PASSWORD', default='ChangeMeNow!')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['yourdomain.com', 'localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:8000', 'http://127.0.0.1:8000'])
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)

INSTALLED_APPS = installed_apps_for(
    PRODUCT_MODE,
    debug=DEBUG,
    website_enabled=WEBSITE_ENABLED,
)

TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = env('NPM_BIN_PATH', default=r'C:\Program Files\nodejs\npm.cmd')

MIDDLEWARE = middleware_for(PRODUCT_MODE, debug=DEBUG)

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
            'context_processors': context_processors_for(PRODUCT_MODE),
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
}

AUTH_USER_MODEL = 'users.User'
LOGIN_URL = PROFILE.login_url
LOGIN_REDIRECT_URL = PROFILE.login_redirect_url

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
# آدرس عمومی پنل این مشتری، برای return_url و notify_url درگاه
# خالی = از request/host ساخته می‌شود؛ نباید دامنهٔ مشتری دیگری hardcode شود
PANEL_PUBLIC_URL = env('PANEL_PUBLIC_URL', default='')

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
