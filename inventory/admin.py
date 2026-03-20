from django.contrib import admin

from inventory.models import Category, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "created_at")
	search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
	list_display = ("name", "category", "quantity", "location", "updated_at")
	list_filter = ("category",)
	search_fields = ("name", "location")
	readonly_fields = ("created_at", "updated_at")
