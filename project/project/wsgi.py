import os
import sys

sys.path.insert(0, "/var/www/webroot/ROOT/project")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

application = get_wsgi_application()