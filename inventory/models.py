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
	# Encrypted-at-rest fields (3DES)
	location_encrypted = models.TextField(blank=True, default="")

	serial_number_encrypted = models.TextField(blank=True, default="")
	notes_encrypted = models.TextField(blank=True, default="")

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["name", "id"]

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
