from django.apps import AppConfig
from django.db.models.signals import post_migrate


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        from inventory.default_admin import ensure_default_admin

        def _ensure_admin_after_migrate(sender, **kwargs):
            if getattr(sender, "name", None) != "inventory":
                return
            ensure_default_admin()

        post_migrate.connect(_ensure_admin_after_migrate, dispatch_uid="inventory.ensure_default_admin")
