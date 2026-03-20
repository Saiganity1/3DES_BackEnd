from __future__ import annotations

import threading

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
