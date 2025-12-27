"""
Production-ready Django settings for OroShine Dental App
"""

import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media" / "avatars"
DEFAULT_AVATAR_PATH = MEDIA_DIR / "default.png"

# ==========================================
# SECURITY SETTINGS
# ==========================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1',
                       cast=lambda v: [s.strip() for s in v.split(',')])



#  for test vurnable 


# Security enhancements
SECURE_SSL_REDIRECT = False     # true when add ss certificate to redirect to https port all below 
SESSION_COOKIE_SECURE = False 
CSRF_COOKIE_SECURE = False 
# SECURE_BROWSER_XSS_FILTER = 
# SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True


# temp


SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = None
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = None




# ==========================================
# APPLICATION DEFINITION
# ==========================================
INSTALLED_APPS = [
    'django_prometheus',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'django_celery_beat',
    'django_celery_results',
    'compressor',
    'django_minify_html',
    'imagekit',
    'django.contrib.humanize',
    # 'tempus_dominus',
    # 'django_celery_results',

    # Social authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.linkedin_oauth2',



    # Your app
    'oroshine_webapp',
]

SITE_ID = 1

# MIDDLEWARE = [
# 'django.middleware.security.SecurityMiddleware',
# 'whitenoise.middleware.WhiteNoiseMiddleware',
# 'django.contrib.sessions.middleware.SessionMiddleware',
# 'django.middleware.common.CommonMiddleware',
# 'django.middleware.cache.UpdateCacheMiddleware',
# 'django.middleware.cache.FetchFromCacheMiddleware',
# 'django.middleware.csrf.CsrfViewMiddleware',
# 'django.contrib.auth.middleware.AuthenticationMiddleware',
# 'django.contrib.messages.middleware.MessageMiddleware',
# 'django.middleware.clickjacking.XFrameOptionsMiddleware',
# 'allauth.account.middleware.AccountMiddleware',

# ]



MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'oroshine_webapp.middleware.RateLimitMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
    'oroshine_webapp.metrics.PrometheusMetricsMiddleware',


    # Page cache should be AFTER user auth, not before! causing issue to test commented 
    # 'django.middleware.cache.UpdateCacheMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
]



ROOT_URLCONF = 'oroshine_app.urls'

# ==========================================
# TEMPLATES
# ==========================================
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
            ],
        },
    },
]

WSGI_APPLICATION = 'oroshine_app.wsgi.application'

# ==========================================
# DATABASE WITH CONNECTION POOLING
# ==========================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config('PG_DB', default='oroshine'),
        "USER": config('PG_USER', default='postgres'),
        "PASSWORD": config('PG_PASSWORD'),
        "HOST": config('PG_HOST', default='localhost'),
        "PORT": config('PG_PORT', default='5432'),
        "CONN_MAX_AGE": 200,
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=3000ms"
        }
    }
}

# ==========================================
# CACHING WITH REDIS
# ==========================================
REDIS_PASSWORD = config('REDIS_PASSWORD', '')
REDIS_HOST = config('REDIS_HOST', 'redis')
REDIS_PORT = config('REDIS_PORT', '6379')
REDIS_DB = config('REDIS_DB', '0')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
        "OPTIONS": {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 25},
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        "KEY_PREFIX": "oroshine",
        "TIMEOUT": 300,
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 604800  # 1 week
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ==========================================
# CELERY CONFIGURATION
# ==========================================

# ==========================================
# CELERY CONFIGURATION (IMPROVED)
# ==========================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'

# Task tracking
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_RESULT_EXTENDED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # One task at a time
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50  # Restart after 50 tasks
CELERY_TASK_ACKS_LATE = True  # Acknowledge after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Retry settings
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3



CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


# Beat schedule (keep your existing schedule)
# CELERY_BEAT_SCHEDULE = {
#     'check-appointment-reminders': {
#         'task': 'oroshine_webapp.tasks.check_and_send_reminders',
#         'schedule': 3600.0,  # Every hour
#     },
# }

# Task routes (keep your existing routes)
# CELERY_TASK_ROUTES = {
#     "oroshine_webapp.tasks.send_appointment_email_task": {"queue": "email"},
#     "oroshine_webapp.tasks.send_contact_email_task": {"queue": "email"},
#     "oroshine_webapp.tasks.send_appointment_reminder_task": {"queue": "email"},
#     "oroshine_webapp.tasks.create_calendar_event_task": {"queue": "calendar"},
#     # "oroshine_webapp.tasks.download_social_avatar_task": {"queue": "cpu"},
# }

CELERY_TASK_ROUTES = {}



CELERY_TASK_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('email', Exchange('email'), routing_key='email'),
    Queue('calendar', Exchange('calendar'), routing_key='calendar'),
)


# Rate limits
CELERY_TASK_ANNOTATIONS = {
    'oroshine_webapp.tasks.send_appointment_email_task': {
        'rate_limit': '10/m',  # 10 emails per minute
        'time_limit': 300,  # 5 minutes max
    },
}

# ==========================================
# AUTHENTICATION and all auth 
# ==========================================
AUTHENTICATION_BACKENDS = [
    "allauth.account.auth_backends.AuthenticationBackend",  # must be first for social login
    "django.contrib.auth.backends.ModelBackend",            # keep this for username/email login
]






ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Allow login with username or email
ACCOUNT_EMAIL_REQUIRED = True  # Email is required
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Don't force email verification (change to 'mandatory' if needed)
ACCOUNT_UNIQUE_EMAIL = True  # Ensure unique emails
ACCOUNT_USERNAME_REQUIRED = True  # Username is required
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True  # Require password confirmation
ACCOUNT_SESSION_REMEMBER = True  # Remember user session
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True  # Auto-login after email confirmation
ACCOUNT_CONFIRM_EMAIL_ON_GET = True


# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True  # Auto-create account from social login
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'  # Don't require email verification for social accounts
SOCIALACCOUNT_QUERY_EMAIL = True  # Request email from social provider
SOCIALACCOUNT_STORE_TOKENS = True  # Store social auth tokens (useful for API access)

# Custom adapters
ACCOUNT_ADAPTER = "oroshine_webapp.adapters.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "oroshine_webapp.adapters.CustomSocialAccountAdapter"


# Redirect URLs
LOGIN_URL = '/custom_login/'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
ACCOUNT_LOGOUT_REDIRECT_URL = 'home'
ACCOUNT_SIGNUP_REDIRECT_URL = '/custom-register'
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True




#  Social provider setting

SOCIALACCOUNT_PROVIDERS = {
  'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
        'VERIFIED_EMAIL': True,  # Only allow Google-verified emails
        'EMAIL_REQUIRED': True,
    },
    'linkedin_oauth2': {
        'SCOPE': [
            'r_basicprofile',
            'r_emailaddress'
        ],
        'PROFILE_FIELDS': [
            'id',
            'first-name',
            'last-name',
            'email-address',
            'picture-url',
            'public-profile-url',
        ]
    }
}



ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/1h",        # 5 failed logins per hour
    "email_verification": "3/1h",  # optional
    "password_reset": "5/1h",      # optional
}


# Username constraints
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_USERNAME_BLACKLIST = ['admin', 'root', 'system', 'test', 'user']

# Password strength
ACCOUNT_PASSWORD_MIN_LENGTH = 8


# ==========================================
# PASSWORD VALIDATION
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================
# INTERNATIONALIZATION
# ==========================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ==========================================
# STATIC & MEDIA FILES
# ==========================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'oroshine_webapp' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000


STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
]


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==========================================
# COMPRESSOR
# ==========================================
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_CSS_HASHING_METHOD = 'content'
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_JS_FILTERS = ['compressor.filters.jsmin.JSMinFilter']

# ==========================================
# EMAIL CONFIGURATION and nocode api (caakender event )
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
ADMIN_EMAIL = config('ADMIN_EMAIL', default=EMAIL_HOST_USER)

NOCODEAPI_BASE_URL = config('NOCODEAPI_BASE_URL')

# ==========================================
# LOGGING
# ==========================================
LOG_DIR = BASE_DIR / 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'simple': {'format': '{levelname} {message}', 'style': '{'}},
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'simple',
        },
        'console': {'level': 'WARNING', 'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'oroshine_webapp': {'handlers': ['file', 'console'], 'level': 'WARNING', 'propagate': False},
        'celery': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}

# ==========================================
# OTHER SETTINGS
# ==========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
# Development tools
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

    # Allow toolbar in Docker
    import socket
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ] + [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
        'INTERCEPT_REDIRECTS': False


    }



# File upload limits

FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2 MB
