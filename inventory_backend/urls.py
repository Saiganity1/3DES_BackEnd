"""
URL configuration for inventory_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def _root_status(_request):
    disabled = os.getenv("DISABLE_DEFAULT_ADMIN", "false").lower() == "true"
    username = os.getenv("DEFAULT_ADMIN_USERNAME", "Admin")
    git_commit = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT")
    return JsonResponse(
        {
            "status": "ok",
            "api": "/api/",
            "git_commit": git_commit,
            "default_admin": {
                "disabled": disabled,
                "username": username,
            },
        }
    )


urlpatterns = [
    path('', _root_status),
    path('admin/', admin.site.urls),
    path('api/', include('inventory.urls')),
]
