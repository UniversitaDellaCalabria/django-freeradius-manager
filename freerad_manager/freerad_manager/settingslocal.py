import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(-^n-uzbk31@g)172-wr479*ga2ujtir#l7ay5)+v%tmf4hy+d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True


FQDN = 'freeradmanager.it'
BASE_URL = 'https://{}'.format(FQDN)
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # installed
    'django_countries',
    'django_freeradius',
    'identity',
    'template'
]

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
#DATABASES = {
    #'default': {
        #'ENGINE': 'django.db.backends.sqlite3',
        #'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #}
#}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'radius',
        'HOST': '10.0.3.85',
        'USER': 'radius',
        'PASSWORD': 'radiussecret',
        'PORT': '',
    }
}

RADIUS_SERVER = '10.0.3.85'
RADIUS_PORT = 1812
RADIUS_SECRET = 'radiussecret'

#AUTHENTICATION_BACKENDS = [
                            #~ 'django.contrib.auth.backends.ModelBackend',
                            #'guest_unical_it.auth.SessionUniqueBackend',
                          #]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'

EMAIL_HOST = 'smtp.thatsmtp.it'
# EMAIL_HOST_USER = 'myemail@hotmail.com'
# EMAIL_HOST_PASSWORD = 'mypassword'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@{}'.format(FQDN)

EMAIL_SEND_TOKEN = True

ADMINS = [('Giuseppe De Marco', 'thamail@thathost.it'),]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
    'verbose': {
        'format': '%(levelname)s [%(asctime)s] %(module)s %(message)s'
        },
    },
    'handlers': {
        'console': {
        'level': 'DEBUG',
        #'level': 'INFO',
        'class': 'logging.StreamHandler',
        #'formatter': 'simple'
        },
        #'file': {
            #'class': 'logging.handlers.RotatingFileHandler',
            #'formatter': 'verbose',
            #'filename': '/tmp/guest.unical.it-error-handler.log',
            #'maxBytes': 1024000,
            #'backupCount': 3,
        #},
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        # disables Invalid HTTP_HOST header emails
        'django.security.DisallowedHost': {
                'handlers': ['mail_admins'],
                'level': 'CRITICAL',
                'propagate': False,
        },
        'django': {
            'handlers': ['console','mail_admins'], #'file', 
            'propagate': True,
            'level': 'ERROR',
        },
    }
}

# IDENTITY TOKEN SETTINGS
IDENTITY_TOKEN_EXPIRATION_DAYS = 5
IDENTITY_TOKEN_MSG_SUBJECT = 'Token for your {} account'.format(FQDN)
IDENTITY_MSG = """Dear {},

This message was sent to you by $BASE_URL, the system dedicated to
guest's wireless accesses of $FQDN.

Please do not reply to this email.

A Password request, regarding {} (this is your username), has been requested for you.
This reset token will be valid until: {}.

If you want to reset your FQDN password please click on this link and follow the instructions:
$BASE_URL{}

If the Token is expired you can obtain a new one at this url:
$BASE_URL/reset_password

If you're experiencing in problems please contacts our technical staff.
Best regards
""".replace('$FQDN', FQDN).replace('$BASE_URL', BASE_URL)

IDENTITY_MSG_WRONG_EMAIL = """{} is tryng to send token to {} instead of {}.\
Please contact him for assistance!"""
