import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure a default admin user exists (for demos)."

    def handle(self, *args, **options):
        if os.getenv("DISABLE_DEFAULT_ADMIN", "false").lower() == "true":
            self.stdout.write("Default admin creation disabled.")
            return

        username = os.getenv("DEFAULT_ADMIN_USERNAME", "Admin")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123")

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        if created:
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save(update_fields=["is_staff", "is_superuser", "password"])
            self.stdout.write(f"Created default admin user: {username}")
        else:
            # Ensure it stays admin-capable.
            changed = False
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if not user.is_superuser:
                user.is_superuser = True
                changed = True
            if changed:
                user.save(update_fields=["is_staff", "is_superuser"])
                self.stdout.write(f"Updated existing user to admin: {username}")
            else:
                self.stdout.write(f"Default admin user already exists: {username}")
