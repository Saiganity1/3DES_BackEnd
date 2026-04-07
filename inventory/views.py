"""REST API endpoints (DRF ViewSets).

Presentation notes:
- This file wires together CRUD behavior, filtering, and role enforcement.
- It also emits audit log entries (ActivityLog) for admin review.

Security notes:
- Items contain encrypted-at-rest fields; we do NOT return decrypted values by default.
- Decryption is only available via `GET /api/items/{id}/decrypt/` and is permission-gated.
"""

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from inventory.models import ActivityLog, Category, Item
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated

from inventory.permissions import IsSuperUser, StaffWriteOtherwiseReadOnly
from inventory.serializers import AccountSerializer, ActivityLogSerializer, CategorySerializer, ItemSerializer


def _log_activity(*, actor, action, item=None, message=""):
	try:
		ActivityLog.objects.create(actor=actor, action=action, item=item, message=message)
	except Exception:
		# Presentation note: audit logging must never break the main request.
		return


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = User.objects.all().order_by("id")
	serializer_class = AccountSerializer
	permission_classes = [IsSuperUser]

	@action(detail=True, methods=["post"], url_path="promote")
	def promote(self, request, pk=None):
		user = self.get_object()
		if user.is_superuser:
			return Response({"detail": "Cannot modify a superuser."}, status=status.HTTP_400_BAD_REQUEST)
		user.is_staff = True
		user.save(update_fields=["is_staff"])
		_log_activity(actor=request.user, action=ActivityLog.ACTION_ACCOUNT_PROMOTED, message=f"Promoted {user.username} to staff")
		return Response(self.get_serializer(user).data)

	@action(detail=True, methods=["post"], url_path="take_down")
	def take_down(self, request, pk=None):
		user = self.get_object()
		if user.pk == request.user.pk:
			return Response({"detail": "You cannot take down your own account."}, status=status.HTTP_400_BAD_REQUEST)
		if user.is_superuser:
			return Response({"detail": "Cannot take down a superuser."}, status=status.HTTP_400_BAD_REQUEST)
		user.is_active = False
		user.save(update_fields=["is_active"])
		_log_activity(actor=request.user, action=ActivityLog.ACTION_ACCOUNT_TAKEDOWN, message=f"Took down account {user.username}")
		return Response(self.get_serializer(user).data)

	def _get_decrypt_permission(self):
		return Permission.objects.get(
			codename="can_decrypt_item_details",
			content_type__app_label="inventory",
		)

	@action(detail=True, methods=["post"], url_path="grant_decrypt")
	def grant_decrypt(self, request, pk=None):
		user = self.get_object()
		if user.is_superuser:
			return Response({"detail": "Cannot modify a superuser."}, status=status.HTTP_400_BAD_REQUEST)
		perm = self._get_decrypt_permission()
		user.user_permissions.add(perm)
		_log_activity(actor=request.user, action=ActivityLog.ACTION_DECRYPT_GRANTED, message=f"Granted decrypt permission to {user.username}")
		return Response(self.get_serializer(user).data)

	@action(detail=True, methods=["post"], url_path="revoke_decrypt")
	def revoke_decrypt(self, request, pk=None):
		user = self.get_object()
		if user.is_superuser:
			return Response({"detail": "Cannot modify a superuser."}, status=status.HTTP_400_BAD_REQUEST)
		perm = self._get_decrypt_permission()
		user.user_permissions.remove(perm)
		_log_activity(actor=request.user, action=ActivityLog.ACTION_DECRYPT_REVOKED, message=f"Revoked decrypt permission from {user.username}")
		return Response(self.get_serializer(user).data)


class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

	# Categories are staff-only (viewers should not see categories).
	permission_classes = [IsAdminUser]

	def perform_create(self, serializer):
		cat = serializer.save(created_by=self.request.user)
		_log_activity(actor=self.request.user, action=ActivityLog.ACTION_CATEGORY_CREATED, message=f"Created category {cat.name}")


class ItemViewSet(viewsets.ModelViewSet):
	queryset = Item.objects.select_related("category").all()
	serializer_class = ItemSerializer

	# Viewers: read-only; Staff/Admin: full CRUD
	permission_classes = [StaffWriteOtherwiseReadOnly]

	def get_queryset(self):
		user = self.request.user
		base = Item.objects.select_related("category", "created_by", "archived_by", "updated_by")
		if user.is_staff or user.is_superuser:
			return base.filter(is_archived=False)
		# Viewer: only inventory posted by staff
		return base.filter(created_by__is_staff=True, is_archived=False)

	def perform_create(self, serializer):
		item = serializer.save(created_by=self.request.user, updated_by=self.request.user)
		_log_activity(actor=self.request.user, action=ActivityLog.ACTION_ITEM_CREATED, item=item, message=f"Created item {item.name}")

	def perform_update(self, serializer):
		item = serializer.save(updated_by=self.request.user)
		_log_activity(actor=self.request.user, action=ActivityLog.ACTION_ITEM_UPDATED, item=item, message=f"Updated item {item.name}")

	@action(detail=True, methods=["get"], url_path="decrypt", permission_classes=[IsAuthenticated])
	def decrypt(self, request, pk=None):
		item = self.get_object()
		user = request.user
		# Permission gate:
		# - Staff/Admin can decrypt (operational need)
		# - Viewers must be explicitly granted `inventory.can_decrypt_item_details`
		can_decrypt = bool(user and user.is_authenticated and (user.is_staff or user.is_superuser or user.has_perm("inventory.can_decrypt_item_details")))
		if not can_decrypt:
			return Response({"detail": "You do not have permission to decrypt item details."}, status=status.HTTP_403_FORBIDDEN)

		serializer = self.get_serializer(item, context={**self.get_serializer_context(), "force_decrypt_sensitive": True})
		return Response(serializer.data)

	@action(detail=False, methods=["get"], url_path="archived", permission_classes=[IsAdminUser])
	def archived(self, request):
		qs = Item.objects.select_related("category", "created_by", "archived_by", "updated_by").filter(is_archived=True)
		page = self.paginate_queryset(qs)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = self.get_serializer(qs, many=True)
		return Response(serializer.data)

	@action(detail=True, methods=["post"], url_path="restore", permission_classes=[IsAdminUser])
	def restore(self, request, pk=None):
		try:
			item = (
				Item.objects.select_related("category", "created_by", "archived_by")
				.filter(is_archived=True)
				.get(pk=pk)
			)
		except Item.DoesNotExist:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
		item.is_archived = False
		item.archived_at = None
		item.archived_by = None
		item.updated_by = request.user
		item.save(update_fields=["is_archived", "archived_at", "archived_by", "updated_at", "updated_by"])
		_log_activity(actor=request.user, action=ActivityLog.ACTION_ITEM_RESTORED, item=item, message=f"Restored item {item.name}")
		serializer = self.get_serializer(item)
		return Response(serializer.data)

	def destroy(self, request, *args, **kwargs):
		item = self.get_object()
		if item.is_archived:
			return Response(status=status.HTTP_204_NO_CONTENT)

		item.is_archived = True
		item.archived_at = timezone.now()
		item.archived_by = request.user
		item.updated_by = request.user
		item.save(update_fields=["is_archived", "archived_at", "archived_by", "updated_at", "updated_by"])
		_log_activity(actor=request.user, action=ActivityLog.ACTION_ITEM_ARCHIVED, item=item, message=f"Archived item {item.name}")
		return Response(status=status.HTTP_204_NO_CONTENT)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ActivityLog.objects.select_related("actor", "item")
	serializer_class = ActivityLogSerializer
	permission_classes = [IsAdminUser]
