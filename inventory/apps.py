"""Django AppConfig for the inventory app.

Presentation notes:
- Hooks into Django lifecycle events.
- After migrations, we ensure a default admin exists (demo convenience).
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        # This import is inside ready() to avoid side effects during app loading.
        from inventory.default_admin import ensure_default_admin

        def _ensure_admin_after_migrate(sender, **kwargs):
            if getattr(sender, "name", None) != "inventory":
                return
            ensure_default_admin()

        post_migrate.connect(_ensure_admin_after_migrate, dispatch_uid="inventory.ensure_default_admin")
