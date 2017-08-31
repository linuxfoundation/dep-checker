# Django settings for compliance project.

import os
import os.path
import time

# Function for finding the project root.

def get_project_root():
    current_path = os.path.abspath(__file__)
    while current_path != "/":
        (current_path, fn) = os.path.split(current_path)
        if os.path.basename(current_path) != "local" and \
           os.path.exists(os.path.join(current_path, "bin/readelf.py")):
            return current_path

    # If that doesn't work, try an old common path.
    if os.path.exists("/opt/linuxfoundation/bin/readelf.py"):
        return "/opt/linuxfoundation"

    # Shouldn't get here unless we can't find the path.
    raise RuntimeError, "could not find the project path"

# Return the proper directory to use for userdir mode.

def get_userdir():
    return os.path.join(os.environ["HOME"], ".dep-checker")

# Should we use userdir mode?

def use_userdir():
    if os.getuid() == 0 or os.environ["LOGNAME"] == "compliance":
        return False
    project_root = get_project_root()
    if os.access(os.path.join(project_root, "compliance"), os.W_OK):
        return False

    return True

# Find the doc root.

def get_doc_root(candidate_paths, default_path):
    docdir = None
    for d in candidate_paths:
        if os.path.exists(os.path.join(d, "docs/index.html")):
            docdir = d
            break

    return (docdir and docdir or default_path)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.

if 'TZ' not in os.environ:  # env is clear => timezone is the system one
    TIME_ZONE = 'Etc/GMT%+d' % (time.altzone / 3600)
else:                       # env is updated => timezone is obsolete
    TIME_ZONE = os.environ['TZ']

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Project root.
PROJECT_ROOT = get_project_root()

# Command-line client.
CLI_COMMAND = os.path.join(PROJECT_ROOT, 'bin/readelf.py')

# Writable file setup; use different settings for userdir or normal mode.
if use_userdir():
    USERDIR_ROOT = get_userdir()
    DATABASES['default']['NAME'] = os.path.join(USERDIR_ROOT, "compliance")
    STATE_ROOT = USERDIR_ROOT
else:
    USERDIR_ROOT = ''
    DATABASES['default']['NAME'] = os.path.join(get_project_root(),
                                                'compliance', 'compliance')
    STATE_ROOT = os.path.join(PROJECT_ROOT, 'compliance')

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '' 

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'
STATIC_URL = '/site_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'wzb!69=4(kj=w)vl&lyp-j1ff9#fi8^)p^i4xr9$kokcu5j9pk'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'compliance.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), "templates"),
    os.path.join(PROJECT_ROOT, "compliance/templates"),
)

STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__), "media"),
    os.path.join(PROJECT_ROOT, "compliance/media"),
)

STATIC_DOC_ROOT = get_doc_root(list(STATICFILES_DIRS),
                               os.path.join(PROJECT_ROOT, "compliance/media"))

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'compliance.linkage',
)
