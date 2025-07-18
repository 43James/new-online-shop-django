import os
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kr1p-zj6!vss$(xd2f7vk8nw*3g@-ao92zzg8^@u!mj(l#s)+i'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = False
DEBUG = True

ALLOWED_HOSTS = ['*']

# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'encoding': 'utf-8',  # เพิ่มบรรทัดนี้เพื่อรองรับการเข้ารหัส utf-8
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ตัวอย่างการตั้งค่า CSRF ที่ถูกต้อง
# CSRF_COOKIE_SECURE = True  # ในกรณีที่คุณใช้ HTTPS
# CSRF_COOKIE_HTTPONLY = True

# SESSION_COOKIE_SAMESITE = None
# CSRF_COOKIE_SAMESITE = None

CSRF_USE_SESSIONS = False
# CSRF_COOKIE_AGE = None
# CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'


# CSRF_CHECK_REFERER = False
# CSRF_COOKIE_SAMESITE = 'Strict'  # หรือ 'Lax'
# SECURE_REFERRER_POLICY = 'same-origin'

# SESSION_ENGINE = "django.contrib.sessions.backends.db"  # หรือตั้งค่าให้เหมาะสม
# SESSION_SAVE_EVERY_REQUEST = True

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
CART_SESSION_ID = 'cart'
STATIC_DIR = BASE_DIR / 'static'
# Application definition

INSTALLED_APPS = [
    'shop.apps.ShopConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'crispy_forms',
    'app_linebot.apps.AppLinebotConfig',
    'cart.apps.CartConfig',
    'orders.apps.OrdersConfig',
    'dashboard.apps.DashboardConfig',
    'accounts.apps.AccountsConfig',
    'assets.apps.AssetsConfig',
    'django_filters',
    'django.contrib.humanize',
    
]


# CRON_CLASSES = [
#     'shop.cron.RecordMonthlyStockCronJob',
# ]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'online_shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        # 'DIRS': [os.path.join(BASE_DIR, 'templates')],  # ✅ ตรวจสอบว่ามีโฟลเดอร์ templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'online_shop.context_processors.return_cart',
                'online_shop.context_processors.return_categories',
                'dashboard.context_processors.stock_record_exists',
                'dashboard.context_processors.pending_outofstock',
                'dashboard.context_processors.count_pending_orders',
            ],
        },
    },
]

WSGI_APPLICATION = 'online_shop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": "shop_test4",
#         "HOST" : "127.0.0.1",
#         "USER" : "root",
#         "PASSWORD" : "root",
#         "PORT" : "3306",
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "database_patsadu",
        "HOST" : "127.0.0.1",
        "USER" : "root",
        "PASSWORD" : "root",
        "PORT" : "3306",
    }
}

AUTH_USER_MODEL = 'accounts.MyUser'

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'th'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Bangkok'

USE_I18N = True

USE_TZ = True
# USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# STATIC_URL = '/static/'
# STATICFILES = [
#     STATIC_DIR,
# ]

# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# # directory that we want to store uploaded files
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


STATIC_URL = '/static/'

# ให้ Django รู้ว่าให้ค้นหาไฟล์ static ในโฟลเดอร์นี้
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # โฟลเดอร์ที่เก็บไฟล์ static ของโปรเจ็กต์
]

# กำหนดตำแหน่งที่จะเก็บไฟล์ static หลังจากรัน collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# STATICFILES_DIRS = [
#     BASE_DIR / "static",  # ถ้าคุณใช้โฟลเดอร์ static ใน root ของโปรเจค
# ]

# STATIC_ROOT = BASE_DIR / "staticfiles"


# กำหนดที่เก็บไฟล์ที่ผู้ใช้จะอัปโหลด
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CRISPY_TEMPLATE_PACK = 'bootstrap4'


LOGIN_URL = 'accounts:user_login'

# settings.py
# AUTH_USER_MODEL = 'accounts.MyUser'



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'username@example.com'
EMAIL_HOST_PASSWORD = 'your-password'

