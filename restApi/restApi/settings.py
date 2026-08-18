import os
from pathlib import Path
import dj_database_url
from corsheaders.defaults import default_headers
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEVELOPMENT_SECRET_KEY = 'django-insecure-development-only-change-before-production'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', DEVELOPMENT_SECRET_KEY)

DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'

if not DEBUG and SECRET_KEY == DEVELOPMENT_SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured when DEBUG=False.')

def env_csv(name, default=''):
    """Lê uma variável CSV, descartando espaços e itens vazios."""
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


# O Render informa automaticamente o hostname público do serviço. Domínios
# personalizados devem ser incluídos em DJANGO_ALLOWED_HOSTS.
ALLOWED_HOSTS = env_csv(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,restapi_django,host.docker.internal' if DEBUG else '',
)
render_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

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
CORS_ALLOWED_ORIGINS = env_csv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000' if DEBUG else '',
)

# A aplicação Next e a API devem usar o mesmo hostname em desenvolvimento
# (por exemplo, ambas em "localhost", e não alternar com 127.0.0.1).
#
# Para cross-site (Vercel + outro provedor):
# - Produção: JWT_COOKIE_SECURE=true, JWT_COOKIE_SAMESITE=None
# - Desenvolvimento: JWT_COOKIE_SECURE=false, JWT_COOKIE_SAMESITE=Lax
#
# Cookies SameSite=None exigem HTTPS nos navegadores.
JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Lax')
FRONTEND_URL = os.getenv(
    'FRONTEND_URL',
    'http://localhost:3000' if DEBUG else '',
).rstrip('/')
CORS_ALLOW_HEADERS = list(default_headers) + [
    'advkey',
]

# Configuração de CSRF
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', str(not DEBUG)).lower() == 'true'
CSRF_COOKIE_HTTPONLY = False  # JavaScript precisa ler o token
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
CSRF_TRUSTED_ORIGINS = env_csv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000' if DEBUG else '',
)

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

# O Render fornece DATABASE_URL. Ela tem prioridade sobre a configuração
# Docker local e não deve ser versionada.
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif os.environ.get("DOCKER") == "1":
    # Docker local → PostgreSQL
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
    # Fora do Docker/Render → SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

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
