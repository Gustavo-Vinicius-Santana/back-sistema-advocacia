import os
from pathlib import Path
from corsheaders.defaults import default_headers
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEVELOPMENT_SECRET_KEY = 'django-insecure-development-only-change-before-production'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', DEVELOPMENT_SECRET_KEY)

DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'

if not DEBUG and SECRET_KEY == DEVELOPMENT_SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured when DEBUG=False.')

# IMPORTANTE PARA DOCKER
if os.getenv('DOCKER') == '1':
    ALLOWED_HOSTS = os.getenv(
        'DJANGO_ALLOWED_HOSTS',
        'localhost,127.0.0.1,restapi_django,host.docker.internal',
    ).split(',')

else:
    # Ambiente local (Django rodando localmente)
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'restApi.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',
        'password_reset': '3/hour',
        'token_refresh': '30/minute',
    },
    'DATE_FORMAT': "%Y-%m-%d",
    'DATETIME_FORMAT': "%Y-%m-%d",
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000',
).split(',')

# A aplicação Next e a API devem usar o mesmo hostname em desenvolvimento
# (por exemplo, ambas em "localhost", e não alternar com 127.0.0.1).
# Cookies SameSite=None, usados em produção, exigem HTTPS nos navegadores.
JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Lax')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000').rstrip('/')
CORS_ALLOW_HEADERS = list(default_headers) + [
    'advkey',
]

# CSRF trusted origins for cookie-based authentication
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Disable CSRF for API views (using JWT authentication)
CSRF_COOKIE_SECURE = JWT_COOKIE_SECURE
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = JWT_COOKIE_SAMESITE

SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

API_SECRET_KEY = os.getenv('API_SECRET_KEY', '')
API_HEADER_NAME = "AdvKey"
ROOT_URLCONF = 'restApi.urls'
AUTH_USER_MODEL = 'main.Advogado'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'restApi.wsgi.application'

# ----------------------------------------------
# ✅ SQLITE DENTRO DO CONTAINER DOCKER
# ----------------------------------------------
if os.environ.get("DOCKER") == "1":
    # ▶ Docker → PostgreSQL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "restapi"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": "db",        # nome do serviço no docker-compose
            "PORT": 5432,
        }
    }
else:
    # ▶ Fora do Docker → SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
# ----------------------------------------------

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
L1ON = False

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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

SIMPLE_JWT = {
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.getenv('JWT_SIGNING_KEY', SECRET_KEY),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
