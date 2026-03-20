import os

from django.contrib.auth import get_user_model
from django.db.utils import OperationalError


def ensure_default_admin() -> str:
    """Create/update the default admin user.

    Returns a short status string suitable for logging.

    Controlled by env vars:
    - DISABLE_DEFAULT_ADMIN=true to disable
    - DEFAULT_ADMIN_USERNAME (default: Admin)
    - DEFAULT_ADMIN_PASSWORD (default: Admin123)

    WARNING: This is intended for demos/school projects. Do not use these
    default credentials for a real production system.
    """

    if os.getenv("DISABLE_DEFAULT_ADMIN", "false").lower() == "true":
        return "Default admin creation disabled."

    username = os.getenv("DEFAULT_ADMIN_USERNAME", "Admin")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123")

    User = get_user_model()

    try:
        user, created = User.objects.get_or_create(username=username)
    except OperationalError:
        return "Database not migrated yet; run migrations first."

    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save(update_fields=["is_active", "is_staff", "is_superuser", "password"])

    if created:
        return f"Created default admin user: {username}"
    return f"Updated default admin user (password/flags ensured): {username}"
