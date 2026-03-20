"""
ASGI config for inventory_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_backend.settings')

application = get_asgi_application()

# Safety net: ensure the demo default admin exists even if deploy scripts
# (migrate/management commands) are misconfigured.
try:
	from inventory.default_admin import ensure_default_admin

	print(ensure_default_admin())
except Exception as exc:
	print(f"Default admin ensure skipped/failed: {exc}")
