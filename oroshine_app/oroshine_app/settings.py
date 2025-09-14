"""
Django settings for oroshine_app project.
"""

import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-gxc@%s4*n+rv@md$+d#@4s7(1i@_o5g9^t5aiv+t)_0pt32gou')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# More secure ALLOWED_HOSTS configuration
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sites",
    
    # Bootstrap and crispy forms
    'crispy_forms',
    'crispy_bootstrap5',
    # css compression and minify
    "compressor",
    # Third party - django-allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.linkedin_oauth2",
    
    # Third party - social-django
    'social_django',
    
    # Local app  
    'oroshine_webapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Social Django middleware
    'social_django.middleware.SocialAuthExceptionMiddleware',
    
    # Django Allauth middleware
    'allauth.account.middleware.AccountMiddleware',
# static compression middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    
]

ROOT_URLCONF = 'oroshine_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            Path(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                
                # Social Django context processors
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]


STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",  # ✅ required for compressor
]

WSGI_APPLICATION = 'oroshine_app.wsgi.application'

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
   os.path.join(BASE_DIR, 'oroshine_webapp/static') 
]

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False
WHITENOISE_USE_FINDERS = True


#  cache 
WHITENOISE_MAX_AGE = 2628000   # 1 month in seconds
WHITENOISE_AUTOREFRESH = False  # disable auto refresh in prod (good for performance)


# COMPRESS_OFFLINE = False # Only True if you want pre-build during collectstatic

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config('PG_DB', default='oroshine'),
        "USER": config('PG_USER', default='postgres'),
        "PASSWORD": config('PG_PASSWORD', default='postgres'),
        "HOST": config('PG_HOST', default='localhost'),
        "PORT": config('PG_PORT', default='5432'),
    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Calendar event creation
NOCODEAPI_BASE_URL = config('NOCODEAPI_BASE_URL')

# AUTHENTICATION CONFIGURATION
SITE_ID = 1

# Custom user model
AUTH_USER_MODEL = "oroshine_webapp.CustomUser"

# Combined Authentication Backends - UPDATED FOR YOUR REQUIREMENTS
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Default username/password
    "oroshine_webapp.backends.EmailUsernameBackend",  # Custom email/username backend
    "allauth.account.auth_backends.AuthenticationBackend",  # Allauth (social + email)
]

# LOGIN/LOGOUT REDIRECTS
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# DJANGO-ALLAUTH SETTINGS
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": config('ALLAUTH_GOOGLE_CLIENT_ID', default='YOUR_GOOGLE_CLIENT_ID'),
            "secret": config('ALLAUTH_GOOGLE_CLIENT_SECRET', default='YOUR_GOOGLE_CLIENT_SECRET'),
            "key": ""
        },
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
    },
    "facebook": {
        "APP": {
            "client_id": config('ALLAUTH_FACEBOOK_APP_ID', default='YOUR_FACEBOOK_APP_ID'),
            "secret": config('ALLAUTH_FACEBOOK_APP_SECRET', default='YOUR_FACEBOOK_APP_SECRET'),
            "key": ""
        },
        "METHOD": "oauth2",
        "SDK_URL": "//connect.facebook.net/{locale}/sdk.js",
        "SCOPE": ["email", "public_profile"],
        "AUTH_PARAMS": {"auth_type": "reauthenticate"},
        "INIT_PARAMS": {"cookie": True},
        "FIELDS": [
            "id",
            "first_name",
            "last_name",
            "middle_name",
            "name",
            "name_format",
            "picture",
            "short_name",
            "email",
        ],
        "EXCHANGE_TOKEN": True,
        "LOCALE_FUNC": "path.to.callable",
        "VERIFIED_EMAIL": False,
        "VERSION": "v13.0",
        "GRAPH_API_URL": "https://graph.facebook.com/v13.0",
    },
    "linkedin_oauth2": {
        "APP": {
            "client_id": config('ALLAUTH_LINKEDIN_CLIENT_ID', default='YOUR_LINKEDIN_CLIENT_ID'),
            "secret": config('ALLAUTH_LINKEDIN_CLIENT_SECRET', default='YOUR_LINKEDIN_CLIENT_SECRET'),
            "key": ""
        },
        "SCOPE": [
            "r_liteprofile",
            "r_emailaddress",
        ],
        "PROFILE_FIELDS": [
            "id",
            "first-name",
            "last-name",
            "email-address",
            "picture-url",
            "public-profile-url",
        ]
    },
    "github": {
        "APP": {
            "client_id": config('ALLAUTH_GITHUB_CLIENT_ID', default='YOUR_GITHUB_CLIENT_ID'),
            "secret": config('ALLAUTH_GITHUB_CLIENT_SECRET', default='YOUR_GITHUB_CLIENT_SECRET'),
            "key": ""
        },
        "SCOPE": [
            "user:email",
        ],
    }
}

# SOCIAL-DJANGO SETTINGS
SOCIAL_AUTH_LOGIN_URL = '/login/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGOUT_URL = '/logout/'
SOCIAL_AUTH_LOGOUT_REDIRECT_URL = '/'

# Social Auth Pipeline
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Google OAuth2 Settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_CLIENT_ID', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

# Facebook OAuth2 Settings
SOCIAL_AUTH_FACEBOOK_KEY = config('FACEBOOK_APP_ID', default='')
SOCIAL_AUTH_FACEBOOK_SECRET = config('FACEBOOK_APP_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']

# LinkedIn OAuth2 Settings  
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = config('LINKEDIN_CLIENT_ID', default='')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = config('LINKEDIN_CLIENT_SECRET', default='')
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ['r_liteprofile', 'r_emailaddress']

# GitHub OAuth2 Settings
SOCIAL_AUTH_GITHUB_KEY = config('GITHUB_CLIENT_ID', default='')
SOCIAL_AUTH_GITHUB_SECRET = config('GITHUB_CLIENT_SECRET', default='')
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

# Social Auth User Fields
SOCIAL_AUTH_USER_FIELDS = ['email', 'first_name', 'last_name']

# Social Auth Extra Data
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = [
    ('name', 'name'),
    ('email', 'email'),
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = [
    ('name', 'name'),
    ('email', 'email'),
]

# Handle login errors
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login/'
SOCIAL_AUTH_RAISE_EXCEPTIONS = False

# Database for social auth
SOCIAL_AUTH_STORAGE = 'social_django.models.DjangoStorage'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Security settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Logging Configuration
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'django.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}:{lineno} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'mode': 'a',  # Append mode
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'oroshine_webapp': {
            'handlers': ['file', 'console'] if DEBUG else ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'social_django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'allauth': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}