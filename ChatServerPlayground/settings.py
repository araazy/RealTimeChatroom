import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
print(sys.path)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '70ujru1(gr#ey_53jvle4=6h9&2p#9@2$2woj8)8j!7dcg=_6n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # development ONLY

ALLOWED_HOSTS = []

AUTH_USER_MODEL = "account.Account"
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.AllowAllUsersModelBackend',
    'apps.account.backends.CaseInsensitiveModelBackend'
)

# Application definition

INSTALLED_APPS = [
    # My apps
    'personal',
    'account',
    'friend',
    'public_chat',

    # 自带app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'ChatServerPlayground.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # templates：路径
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'ChatServerPlayground.wsgi.application'


# Database 使用Postgres
DB_NAME = 'chat_server_playground'
DB_USER = 'django'
DB_PASSWORD = 'a1ssjltx'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': '81.70.152.144',
        'PORT': '5432',
    }
}

# Redis配置
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('81.70.152.144', 6379)],
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# 静态资源与文件配置

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'media'),
]
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_cdn')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_cdn')

TEMP = os.path.join(BASE_DIR, 'media_cdn/temp')

BASE_URL = "http://127.0.0.1:8000"

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

if DEBUG:
    import mimetypes
    mimetypes.add_type("application/javascript", ".js", True)
