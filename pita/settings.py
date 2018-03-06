import collections
import os


# General

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open('.keys/secret_key.txt', 'r') as f:
    SECRET_KEY = f.read().strip()

DEBUG = os.path.isfile('development')

ALLOWED_HOSTS = [
    '127.0.0.1',
    'saltedpita.com',
]

# Email settings

with open(os.path.join(BASE_DIR, '.keys/mailgun.txt'), 'r') as f:
    MAILGUN_API_KEY = f.read().strip()

ANYMAIL = {
    'MAILGUN_API_KEY': MAILGUN_API_KEY,
    'MAILGUN_SENDER_DOMAIN': 'saltedpita.com',
}

EMAIL_BACKEND = 'anymail.backends.mailgun.MailgunBackend'
DEFAULT_FROM_EMAIL = 'Django <django@saltedpita.com>'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pita',
    'anymail',
    'constance',
    'constance.backends.database',
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

ROOT_URLCONF = 'pita.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'constance.context_processors.config',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pita.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'data.db'),
    }
}

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Eastern'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATE_FORMAT = 'D, Y-m-d'
SHORT_DATE_FORMAT = 'm-d'

DATETIME_FORMAT = 'D, Y-m-d H:i:s'
SHORT_DATETIME_FORMAT = 'm-d H:i'


# Static files

if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'


# Media

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# Custom settings

# Custom: general

CONSTANCE_GENERAL = {
    'TITLE': ("Art by Peter Sang", "The site title, used in tab titles"),
    'NAME': ("Peter Sang", ""),
    'DESCRIPTION': ("", "The site description, used for metadata"),
    'COPYRIGHT_YEARS': ("2018-2018", ""),
    'TERMS_OF_SERVICE_URL': ("", ""),
}

# Custom: contact information

CONSTANCE_CONTACT = {
    'CONTACT_TITLE': ("Contact", "The title of the contact page"),
    'CONTACT_DESCRIPTION': ("", "The text to display above the contact form"),
    'EMAIL_NAME': ("Peter Sang", "The name to send email as"),
    'EMAIL_ADDRESS': ("saltedpita@gmail.com", "The email address"),
    'SUBJECT_PREFIX': (
        "[saltedpita.com]",
        "The subject line prefix for any emails sent from the contact form"),
}

# Custom: email options

CONSTANCE_EMAIL = {
    'API_ERROR': ("The server was unable to send your email. Please try "
                  "again later, or directly send an email to {email}.", ""),
    'ERROR': ("An unknown error occurred when sending your email. Please try "
              "again later, or directly send an email to {email}.", ""),
    'INVALID': ("An unknown error occurred when sending your email. Please try "
                "again later, or directly send an email to {email}.", ""),
    'INVALID_ADDRESS': ("Invalid email address.", ""),
    'SUCCESS': ("Email sent successfully.", ""),
}

# Load custom settings

CONSTANCE_CONFIG = {
    **CONSTANCE_GENERAL, **CONSTANCE_CONTACT, **CONSTANCE_EMAIL}

CONSTANCE_CONFIG_FIELDSETS = collections.OrderedDict({
    'General': CONSTANCE_GENERAL.keys(),
    'Contact': CONSTANCE_CONTACT.keys(),
    'Email': CONSTANCE_EMAIL.keys(),
})
