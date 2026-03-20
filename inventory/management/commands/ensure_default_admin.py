from django.core.management.base import BaseCommand

from inventory.default_admin import ensure_default_admin


class Command(BaseCommand):
    help = "Ensure a default admin user exists (for demos)."

    def handle(self, *args, **options):
        self.stdout.write(ensure_default_admin())
