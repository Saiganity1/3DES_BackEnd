from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from inventory.models import Category, Item
from rest_framework.permissions import IsAdminUser

from inventory.permissions import IsSuperUser, StaffWriteOtherwiseReadOnly
from inventory.serializers import AccountSerializer, CategorySerializer, ItemSerializer


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
		return Response(self.get_serializer(user).data)


class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

	# Categories are staff-only (viewers should not see categories).
	permission_classes = [IsAdminUser]

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)


class ItemViewSet(viewsets.ModelViewSet):
	queryset = Item.objects.select_related("category").all()
	serializer_class = ItemSerializer

	# Viewers: read-only; Staff/Admin: full CRUD
	permission_classes = [StaffWriteOtherwiseReadOnly]

	def get_queryset(self):
		user = self.request.user
		base = Item.objects.select_related("category", "created_by", "archived_by")
		if user.is_staff or user.is_superuser:
			return base.filter(is_archived=False)
		# Viewer: only inventory posted by staff
		return base.filter(created_by__is_staff=True, is_archived=False)

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)

	@action(detail=False, methods=["get"], url_path="archived", permission_classes=[IsAdminUser])
	def archived(self, request):
		qs = Item.objects.select_related("category", "created_by", "archived_by").filter(is_archived=True)
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
		item.save(update_fields=["is_archived", "archived_at", "archived_by", "updated_at"])
		serializer = self.get_serializer(item)
		return Response(serializer.data)

	def destroy(self, request, *args, **kwargs):
		item = self.get_object()
		if item.is_archived:
			return Response(status=status.HTTP_204_NO_CONTENT)

		item.is_archived = True
		item.archived_at = timezone.now()
		item.archived_by = request.user
		item.save(update_fields=["is_archived", "archived_at", "archived_by", "updated_at"])
		return Response(status=status.HTTP_204_NO_CONTENT)
