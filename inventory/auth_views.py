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
