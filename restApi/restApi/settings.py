import os
from pathlib import Path
from corsheaders.defaults import default_headers
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-gop1+ud5cyvxp(t^rnmn9)=h1x22(#m&*-_v2=+qt$aa5)&+x2'

DEBUG = True

# IMPORTANTE PARA DOCKER
if os.getenv('DOCKER') == '1':
    print("🔄 Ambiente Docker detectado")
    
    ALLOWED_HOSTS = [
        '*',                    # Aceita qualquer host
        'restapi_django',       # Nome do container
        'localhost',            # Para acessar do host
        '127.0.0.1',
        '0.0.0.0',
        'host.docker.internal', # Host da máquina (para Windows/Mac)
    ]
    
    # Patch para Docker
    import django.http.request
    django.http.request.host_validation_re = None
    
    original_get_host = django.http.HttpRequest.get_host
    
    def docker_get_host(self):
        host = self.META.get('HTTP_HOST', 'restapi_django')
        # Se for um host com porta, remove para validação
        if ':' in host:
            host_without_port = host.split(':')[0]
            # Retorna o host original, mas valida sem porta
            if host_without_port in ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
                return host
        return original_get_host(self)
    
    django.http.HttpRequest.get_host = docker_get_host

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
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
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

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'advkey',
]

API_SECRET_KEY = "3f0c35dc-73b4-4c7d-862e-09ee041c5a7c"
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
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "BLACKLIST_AFTER_ROTATION": True,
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
