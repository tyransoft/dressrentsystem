import sys
import os

print("PYTHON EXEC:", sys.executable)
print("PATH:", sys.path)
print("ENV:", os.environ.get("DJANGO_SETTINGS_MODULE"))


VENV = "/home/apache/venv"

sys.path.insert(0, "/var/www/webroot/ROOT/project")
sys.path.insert(0, VENV + "/lib/python3.13/site-packages")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()