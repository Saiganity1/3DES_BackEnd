from __future__ import annotations

"""Middleware utilities.

Presentation notes:
- Ensures a default admin exists once per process.
- This is a safety net for demo environments where deploy/startup ordering can be unpredictable.
"""

import threading
import traceback

from inventory.default_admin import ensure_default_admin


_lock = threading.Lock()
_ensured = False


class EnsureDefaultAdminOnceMiddleware:
    """Ensure the demo default admin exists once per process.

    This is a safety net for environments where startup hooks run before the DB
    is ready. It retries on the first request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _ensured
        if not _ensured:
            with _lock:
                if not _ensured:
                    try:
                        ensure_default_admin()
                        _ensured = True
                    except Exception:
                        # If DB isn't ready yet, keep _ensured=False so we retry
                        # on the next request.
                        pass

        return self.get_response(request)


class LogUnhandledExceptionsMiddleware:
    """Log unhandled exceptions with full traceback.

    Render/Gunicorn sometimes won't show the stack trace unless explicitly
    logged. This middleware ensures we always get a traceback in logs for 500s.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:  # noqa: BLE001
            print("\n=== Unhandled exception ===")
            print(f"Path: {getattr(request, 'path', '')}")
            print(traceback.format_exc())
            raise
