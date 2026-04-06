from django.db import models

from django.conf import settings

from inventory.crypto.triple_des import decrypt_text, encrypt_text


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="created_categories",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class Item(models.Model):
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items")
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="created_items",
	)
	# Archive (soft-delete) fields
	is_archived = models.BooleanField(default=False)
	archived_at = models.DateTimeField(null=True, blank=True)
	archived_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="archived_items",
	)
	name = models.CharField(max_length=200)
	quantity = models.PositiveIntegerField(default=1)
	min_quantity = models.PositiveIntegerField(default=0)
	photo_url = models.URLField(blank=True, default="")
	# Encrypted-at-rest fields (3DES)
	location_encrypted = models.TextField(blank=True, default="")

	serial_number_encrypted = models.TextField(blank=True, default="")
	notes_encrypted = models.TextField(blank=True, default="")

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="updated_items",
	)

	class Meta:
		ordering = ["name", "id"]
		permissions = [
			("can_decrypt_item_details", "Can decrypt item details"),
		]

	def __str__(self) -> str:
		return f"{self.name} ({self.category.name})"

	@property
	def location(self) -> str:
		return decrypt_text(self.location_encrypted) or ""

	@location.setter
	def location(self, value: str) -> None:
		self.location_encrypted = encrypt_text(value) or ""

	@property
	def serial_number(self) -> str:
		return decrypt_text(self.serial_number_encrypted) or ""

	@serial_number.setter
	def serial_number(self, value: str) -> None:
		self.serial_number_encrypted = encrypt_text(value) or ""

	@property
	def notes(self) -> str:
		return decrypt_text(self.notes_encrypted) or ""

	@notes.setter
	def notes(self, value: str) -> None:
		self.notes_encrypted = encrypt_text(value) or ""


class ActivityLog(models.Model):
	ACTION_CATEGORY_CREATED = "category_created"
	ACTION_ITEM_CREATED = "item_created"
	ACTION_ITEM_UPDATED = "item_updated"
	ACTION_ITEM_ARCHIVED = "item_archived"
	ACTION_ITEM_RESTORED = "item_restored"
	ACTION_ACCOUNT_TAKEDOWN = "account_taken_down"
	ACTION_ACCOUNT_PROMOTED = "account_promoted"
	ACTION_DECRYPT_GRANTED = "decrypt_granted"
	ACTION_DECRYPT_REVOKED = "decrypt_revoked"

	ACTION_CHOICES = [
		(ACTION_CATEGORY_CREATED, "Category created"),
		(ACTION_ITEM_CREATED, "Item created"),
		(ACTION_ITEM_UPDATED, "Item updated"),
		(ACTION_ITEM_ARCHIVED, "Item archived"),
		(ACTION_ITEM_RESTORED, "Item restored"),
		(ACTION_ACCOUNT_TAKEDOWN, "Account taken down"),
		(ACTION_ACCOUNT_PROMOTED, "Account promoted"),
		(ACTION_DECRYPT_GRANTED, "Decrypt granted"),
		(ACTION_DECRYPT_REVOKED, "Decrypt revoked"),
	]

	actor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="activity_logs",
	)
	action = models.CharField(max_length=64, choices=ACTION_CHOICES)
	item = models.ForeignKey(
		Item,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="activity_logs",
	)
	message = models.TextField(blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at", "-id"]
