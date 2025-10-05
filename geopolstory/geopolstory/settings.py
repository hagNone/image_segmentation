"""
Django settings for geopolstory project.

Environment-driven configuration suitable for local dev (SQLite) and production
with PostgreSQL. Includes structured logging (structlog), Sentry, Celery, and
email settings (SendGrid via SMTP by default when SENDGRID_API_KEY provided).
"""

from pathlib import Path
import os
import environ
import structlog

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_SECRET_KEY=(str, "dev-secret-key-change-me"),
    DJANGO_ALLOWED_HOSTS=(str, ""),
    DJANGO_DB_ENGINE=(str, "sqlite"),
    DJANGO_DB_NAME=(str, "db.sqlite3"),
    DJANGO_DB_USER=(str, ""),
    DJANGO_DB_PASSWORD=(str, ""),
    DJANGO_DB_HOST=(str, ""),
    DJANGO_DB_PORT=(str, ""),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    DEFAULT_FROM_EMAIL=(str, "GeopolStory <no-reply@geopolstory.local>"),
    SENDGRID_API_KEY=(str, ""),
    SENTRY_DSN=(str, ""),
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
environ.Env.read_env(os.path.join(BASE_DIR.parent, ".env"))

# SECURITY
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS").split(",") if h] or ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Project apps
    'users',
    'geopol',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geopolstory.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR / 'geopol' / 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'geopolstory.wsgi.application'


# Database
DB_ENGINE = env("DJANGO_DB_ENGINE").lower()
if DB_ENGINE == "postgres" or DB_ENGINE == "postgresql":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DJANGO_DB_NAME'),
            'USER': env('DJANGO_DB_USER'),
            'PASSWORD': env('DJANGO_DB_PASSWORD'),
            'HOST': env('DJANGO_DB_HOST'),
            'PORT': env('DJANGO_DB_PORT'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / env('DJANGO_DB_NAME')),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = str(BASE_DIR / 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR / 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Email (SendGrid via SMTP if SENDGRID_API_KEY provided)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
if env('SENDGRID_API_KEY'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = env('SENDGRID_API_KEY')
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
else:
    # Fall back to console backend in dev
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery configuration
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TIMEZONE = 'Asia/Kolkata'  # Ensure 07:00 IST schedules run as expected

# Sentry
SENTRY_DSN = env('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# Logging with structlog
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'plain': {
            '()': 'structlog.stdlib.ProcessorFormatter',
            'processor': structlog.processors.JSONRenderer(),
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'plain',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    cache_logger_on_first_use=True,
)
