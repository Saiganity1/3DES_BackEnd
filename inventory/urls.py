"""inventory app URL routing.

Presentation notes:
- Registers ViewSets under `/api/` using a DRF router.
- Auth endpoints are mounted under `/api/auth/...`.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from inventory.auth_views import MeView, RegisterView
from inventory.views import AccountViewSet, ActivityLogViewSet, CategoryViewSet, ItemViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"items", ItemViewSet, basename="item")
router.register(r"activity", ActivityLogViewSet, basename="activity")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="auth-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("", include(router.urls)),
]
