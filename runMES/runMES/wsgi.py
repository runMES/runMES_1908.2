"""
WSGI config for runMES3 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'runMES.settings')

application = get_wsgi_application()

# for gunicorn
# from whitenoise import WhiteNoise
# application = WhiteNoise(application, root='runMES/static')

from whitenoise import WhiteNoise
application = WhiteNoise(application)