"""Authentication serializers.

Presentation notes:
- `RegisterSerializer` validates user signup fields.
- `MeSerializer` exposes a safe subset of user fields to the frontend.
"""

from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "email"]

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data.get("email", ""),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    can_decrypt_item_details = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_superuser",
            "can_decrypt_item_details",
        ]

    def get_can_decrypt_item_details(self, obj):
        try:
            return bool(obj.has_perm("inventory.can_decrypt_item_details"))
        except Exception:
            return False
