"""
Configuration Django SÉCURISÉE - Django 6.0.2
Utilise python-decouple pour gérer les variables d'environnement
"""

from pathlib import Path
from decouple import config, Csv

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ SECURITY: All from environment variables
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')  # MUST be set in .env
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost,http://127.0.0.1',
    cast=Csv()
)

# ✅ SECURITY: Production hardening
if not DEBUG:
    # HTTPS enforcement
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # Security headers
    SECURE_CONTENT_SECURITY_POLICY = {
        'DEFAULT_SRC': ["'self'"],
        'SCRIPT_SRC': ["'self'", "'unsafe-inline'"],  # Consider removing unsafe-inline
        'STYLE_SRC': ["'self'", "'unsafe-inline'"],
        'IMG_SRC': ["'self'", "data:", "https:"],
    }
    
    X_FRAME_OPTIONS = 'DENY'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY_REPORT_ONLY = False

INSTALLED_APPS = [
    # Django apps
    # 'colorfield',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'phonenumber_field',
    'rest_framework',
    'rest_framework_simplejwt',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'drf_spectacular',
    
    # Local apps
    'core',
    'staff',
    'patients',
    'appointment',
    'data',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context'
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ✅ DATABASE: PostgreSQL with connection pooling
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='postgresql://localhost/while_health'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if 'postgresql' in DATABASES['default'].get('ENGINE', ''):
    DATABASES['default'].update({
        'ATOMIC_REQUESTS': False,
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        }
    })

# ✅ CACHE: Redis (can fallback to in-memory for dev)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Fallback to DB if cache fails
        },
        'KEY_PREFIX': 'while_health',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# ✅ PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ INTERNATIONALIZATION
LANGUAGE_CODE = 'fr-FR'
TIME_ZONE = 'Africa/Kinshasa'  # UTC for medical timestamps
USE_I18N = True
USE_TZ = True

# ✅ STATIC FILES
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ AUTHENTICATION
AUTH_USER_MODEL = 'core.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# ✅ SESSION
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Strict'

# ✅ CSRF
CSRF_COOKIE_SAMESITE = 'Strict'

# ✅ MONITORING: Sentry configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=None),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    # Performance monitoring
    traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
    # Release tracking
    release=config('RELEASE_VERSION', default='1.0.0'),
    # Environment
    environment=config('ENVIRONMENT', default='development'),
    # Security
    send_default_pii=False,  # Don't send personally identifiable information
    # Filtering sensitive data
    before_send=lambda event, hint: filter_sensitive_data(event, hint),
)

def filter_sensitive_data(event, hint):
    """Filter out sensitive medical data from Sentry events."""
    if 'request' in event:
        # Remove sensitive headers
        headers = event['request'].get('headers', {})
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            headers.pop(header, None)
    
    # Remove sensitive data from extra/context
    if 'extra' in event:
        sensitive_keys = ['password', 'token', 'ssn', 'medical_record']
        for key in sensitive_keys:
            event['extra'].pop(key, None)
    
    return event

# ✅ LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        # ✅ MONITORING: Sentry handler for errors
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'sentry'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'ERROR',
            'propagate': False,
        },
        'patients': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
        'appointment': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# ✅ REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'COERCE_DECIMAL_TO_STRING': False,
}

# ✅ JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': config('JWT_ACCESS_TOKEN_LIFETIME', default=3600, cast=int),  # 1 hour
    'REFRESH_TOKEN_LIFETIME': config('JWT_REFRESH_TOKEN_LIFETIME', default=604800, cast=int),  # 7 days
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ✅ CRISPY FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ✅ JAZZMIN Admin theme
JAZZMIN_SETTINGS = {
    'site_title': 'While Health',
    'site_header': 'While Health Administration',
    'site_brand': 'While Health',
    'site_logo': 'logo.jpg',
    'site_logo_classes': 'img-circle',
    'site_logo_alt': 'While Health Logo',
    'welcome_sign': 'Bienvenue à While Health',
    'copyright': 'While Health © 2024',
    'show_sidebar': True,
    'navigation_expanded': False,
    'sidebar_fixed': True,
    'show_ui_builder': False,
    'changeform_format': 'horizontal_tabs',
    'custom_css': '''
        /* Logo sur la page de connexion */
        .login-box .login-logo img,
        .login-logo img {
            width: 80px !important;
            height: 80px !important;
            border-radius: 50% !important;
            object-fit: cover !important;
            margin: 0 auto !important;
            display: block !important;
        }

        /* Logo dans la sidebar */
        .main-sidebar .brand-image,
        .brand-image img {
            width: 40px !important;
            height: 40px !important;
            border-radius: 50% !important;
            object-fit: cover !important;
        }

        /* Logo dans le header */
        .main-header .logo img,
        .navbar-brand img {
            width: 40px !important;
            height: 40px !important;
            border-radius: 50% !important;
            object-fit: cover !important;
        }
    ''',
}

JAZZMIN_UI_TWEAKS = {
    'theme': 'darkly',
    'default_theme_mode': 'dark',
    'sidebar': 'sidebar-dark-primary',
    'navbar': 'navbar-dark navbar-dark',
    'theme_chooser': True,
}
