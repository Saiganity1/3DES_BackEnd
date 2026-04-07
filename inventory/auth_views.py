"""Authentication views (register + /me) for the frontend.

Presentation notes:
- RegisterView: creates a new user account.
- MeView: returns the currently authenticated user's profile and flags.
"""

from rest_framework import generics, permissions
from rest_framework.response import Response

from inventory.auth_serializers import MeSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class MeView(generics.GenericAPIView):
    serializer_class = MeSerializer

    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(request.user).data)
