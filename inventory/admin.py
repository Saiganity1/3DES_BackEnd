"""Django admin configuration.

Presentation notes:
- Registers core models in the Django admin site.
- Provides quick search/list columns for demos and debugging.
"""

from django.contrib import admin

from inventory.models import Category, Item


def _safe_text(value: object) -> str:
	try:
		return "" if value is None else str(value)
	except Exception:
		return ""


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "created_at")
	search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
	list_display = ("name", "category", "quantity", "safe_location", "updated_at")
	list_filter = ("category",)
	search_fields = ("name",)
	readonly_fields = ("created_at", "updated_at")

	@admin.display(description="Location")
	def safe_location(self, obj: Item) -> str:
		# Location is encrypted-at-rest; decryption can fail if the key changed or
		# isn't configured in the environment. Never crash the admin list page.
		try:
			return _safe_text(obj.location)
		except Exception:
			return "[unavailable]"
