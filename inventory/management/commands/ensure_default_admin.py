import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Ensure a default admin user exists (for demos)."

    def handle(self, *args, **options):
        if os.getenv("DISABLE_DEFAULT_ADMIN", "false").lower() == "true":
            self.stdout.write("Default admin creation disabled.")
            return

        username = os.getenv("DEFAULT_ADMIN_USERNAME", "Admin")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123")

        User = get_user_model()
        try:
            user, created = User.objects.get_or_create(username=username)
        except OperationalError:
            self.stdout.write("Database not migrated yet; run 'python manage.py migrate' first.")
            return

        # Always ensure this account can be used to log in.
        # NOTE: This will reset the password on every deploy/start unless you override
        # DEFAULT_ADMIN_PASSWORD or disable via DISABLE_DEFAULT_ADMIN.
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(update_fields=["is_staff", "is_superuser", "password"])

        if created:
            self.stdout.write(f"Created default admin user: {username}")
        else:
            self.stdout.write(f"Updated default admin user (password/flags ensured): {username}")
