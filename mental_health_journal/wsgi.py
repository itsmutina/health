"""
WSGI config for mental_health_journal project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_journal.settings')

application = get_wsgi_application()
