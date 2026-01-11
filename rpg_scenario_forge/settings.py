"""
Django settings for rpg_scenario_forge project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# БАЗОВЫЕ НАСТРОЙКИ
# ==============================

# Определяем среду выполнения
PRODUCTION = os.getenv('PRODUCTION', 'False') == 'True'

# Секретный ключ
SECRET_KEY = os.getenv('SECRET_KEY', 'oz09hk30@al37^(8w257@la54@a%b^!525n20ifk)a)w8yry=t')

# Режим отладки
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Разрешенные хосты
ALLOWED_HOSTS = [
    'MasterGoldy.pythonanywhere.com',
    'www.MasterGoldy.pythonanywhere.com',
    'www.mastergoldy.pythonanywhere.com',
    'mastergoldy.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
    '.pythonanywhere.com',
]


# ==============================
# НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА
# ==============================

if PRODUCTION:
    # HTTPS/SSL настройки
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Безопасность cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Дополнительная безопасность
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # Защита от переполнения
    DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
    FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

    # DEBUG должен быть False в продакшене
    DEBUG = False

# ==============================
# ПРИЛОЖЕНИЯ
# ==============================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние приложения
    'crispy_forms',
    'crispy_bootstrap5',

    # Локальные приложения
    'core.apps.CoreConfig'
]

ROOT_URLCONF = 'rpg_scenario_forge.urls'

# ==============================
# MIDDLEWARE
# ==============================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Для статических файлов
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================
# ШАБЛОНЫ
# ==============================

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
                'core.views.get_game_systems',
            ],
        },
    },
]

# ==============================
# WSGI/ASGI
# ==============================

WSGI_APPLICATION = 'rpg_scenario_forge.wsgi.application'

# ==============================
# БАЗА ДАННЫХ
# ==============================

if PRODUCTION:
    # Конфигурация для PythonAnywhere (MySQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'MasterGoldy$default'),
            'USER': os.getenv('DB_USER', 'MasterGoldy'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'MasterGoldy.mysql.pythonanywhere-services.com'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
            'CONN_MAX_AGE': 60,  # Пул соединений
        }
    }
else:
    # SQLite для разработки
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==============================
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# ==============================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==============================
# ИНТЕРНАЦИОНАЛИЗАЦИЯ
# ==============================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==============================
# СТАТИЧЕСКИЕ ФАЙЛЫ
# ==============================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Куда collectstatic собирает файлы

# Директории со статическими файлами
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Хранилище для статических файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Белый список для WhiteNoise
WHITENOISE_ROOT = BASE_DIR / 'staticfiles'

# ==============================
# МЕДИА ФАЙЛЫ
# ==============================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================
# CRISPY FORMS
# ==============================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ==============================
# АУТЕНТИФИКАЦИЯ
# ==============================

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# ==============================
# ЛОГИРОВАНИЕ
# ==============================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        # Добавьте если нужно:
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}
# ==============================
# НАСТРОЙКИ ДЛЯ РАЗРАБОТКИ
# ==============================

if not PRODUCTION:
    # Debug Toolbar
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

    # Отключаем некоторые настройки безопасности для разработки
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    # Показываем SQL запросы в консоли
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
        }

# ==============================
# ВНЕШНИЕ API
# ==============================

DND_API_URL = os.getenv('DND_API_URL', 'https://www.dnd5eapi.co/api')

# ==============================
# ПРОВЕРКИ ДЛЯ ПРОДАКШЕНА
# ==============================

if PRODUCTION:
    # Проверяем критически важные настройки
    if SECRET_KEY == 'oz09hk30@al37^(8w257@la54@a%b^!525n20ifk)a)w8yry=t':
        raise ValueError('SECRET_KEY must be changed for production!')

    if DEBUG:
        raise ValueError('DEBUG must be False in production!')

    if not ALLOWED_HOSTS:
        raise ValueError('ALLOWED_HOSTS must be set in production!')

# ==============================
# ПРОЧИЕ НАСТРОЙКИ
# ==============================

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Домен для ссылок в письмах (если есть email)
if PRODUCTION:
    DEFAULT_FROM_EMAIL = 'noreply@mastergoldy.pythonanywhere.com'
    SERVER_EMAIL = 'noreply@mastergoldy.pythonanywhere.com'
else:
    DEFAULT_FROM_EMAIL = 'webmaster@localhost'
    SERVER_EMAIL = 'webmaster@localhost'