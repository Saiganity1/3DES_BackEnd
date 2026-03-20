from rest_framework import serializers

from django.contrib.auth.models import User

from inventory.models import Category, Item


class CategorySerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "created_by", "created_at"]


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    archived_by = serializers.CharField(source="archived_by.username", read_only=True)

    # Plaintext fields exposed via model properties (encrypted at rest)
    location = serializers.CharField(required=False, allow_blank=True)
    serial_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "category",
            "category_name",
            "created_by",
            "is_archived",
            "archived_at",
            "archived_by",
            "name",
            "quantity",
            "location",
            "serial_number",
            "notes",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        can_view_sensitive = bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
        if not can_view_sensitive:
            # Viewer sees encrypted strings (ciphertext), not plaintext.
            data["location"] = instance.location_encrypted or ""
            data["serial_number"] = instance.serial_number_encrypted or ""
            data["notes"] = instance.notes_encrypted or ""

            # Viewer also should not browse categories.
            data["category"] = None
        return data

    def create(self, validated_data):
        location = validated_data.pop("location", "")
        serial_number = validated_data.pop("serial_number", "")
        notes = validated_data.pop("notes", "")
        item = Item(**validated_data)
        item.location = location
        item.serial_number = serial_number
        item.notes = notes
        item.save()
        return item

    def update(self, instance, validated_data):
        if getattr(instance, "is_archived", False):
            raise serializers.ValidationError({"detail": "Item is archived. Restore it before editing."})

        if "location" in validated_data:
            instance.location = validated_data.pop("location")
        if "serial_number" in validated_data:
            instance.serial_number = validated_data.pop("serial_number")
        if "notes" in validated_data:
            instance.notes = validated_data.pop("notes")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
