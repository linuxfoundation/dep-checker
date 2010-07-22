import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

sys.path.append('/var/www/html/dep-checker')
sys.path.append('/var/www/html/dep-checker/compliance')
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
