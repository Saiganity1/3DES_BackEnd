"""API tests for the inventory system.

Presentation notes:
- These tests demonstrate the most important security/role requirements:
	- Viewers are read-only and only see staff-posted items.
	- Decryption requires a specific permission and is only available via /decrypt/.
	- Audit fields and activity logs are recorded.
"""

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from rest_framework.test import APITestCase

from inventory.models import Category, Item
from inventory.models import ActivityLog


class ViewerPermissionsTests(APITestCase):
	def setUp(self):
		self.category = Category.objects.create(name="Test Category")

		self.admin = User.objects.create_user(username="admin_user", password="pass12345")
		self.admin.is_staff = True
		self.admin.is_superuser = True
		self.admin.save(update_fields=["is_staff", "is_superuser"])

		self.viewer = User.objects.create_user(username="viewer_user", password="pass12345")

		# One item created by staff/admin
		Item.objects.create(category=self.category, name="Staff Item", quantity=1, created_by=self.admin)
		# One item created by viewer (should NOT be visible to viewers)
		Item.objects.create(category=self.category, name="Viewer Item", quantity=1, created_by=self.viewer)

	def test_viewer_cannot_create_item(self):
		self.client.force_authenticate(user=self.viewer)
		res = self.client.post(
			"/api/items/",
			{"name": "New Item", "quantity": 1, "category": self.category.id},
			format="json",
		)
		self.assertEqual(res.status_code, 403)

	def test_viewer_only_sees_staff_items(self):
		self.client.force_authenticate(user=self.viewer)
		res = self.client.get("/api/items/")
		self.assertEqual(res.status_code, 200)
		names = {i["name"] for i in res.json()}
		self.assertIn("Staff Item", names)
		self.assertNotIn("Viewer Item", names)

	def test_admin_can_grant_viewer_decrypt_permission(self):
		# Create an item with sensitive fields.
		it = Item.objects.create(category=self.category, name="Secret", quantity=1, created_by=self.admin)
		it.location = "Lab 1"
		it.serial_number = "SN-123"
		it.notes = "Top secret"
		it.save()

		# Viewer initially sees ciphertext, not plaintext.
		self.client.force_authenticate(user=self.viewer)
		res1 = self.client.get("/api/items/")
		self.assertEqual(res1.status_code, 200)
		secret = [x for x in res1.json() if x["name"] == "Secret"][0]
		self.assertNotEqual(secret["location"], "Lab 1")
		self.assertNotEqual(secret["serial_number"], "SN-123")
		self.assertNotEqual(secret["notes"], "Top secret")

		# Admin grants decrypt permission.
		perm = Permission.objects.get(codename="can_decrypt_item_details", content_type__app_label="inventory")
		self.viewer.user_permissions.add(perm)
		# Refresh auth user to avoid permission cache.
		self.viewer = User.objects.get(pk=self.viewer.pk)
		self.client.force_authenticate(user=self.viewer)

		# Viewer list remains ciphertext by default.
		res2 = self.client.get("/api/items/")
		self.assertEqual(res2.status_code, 200)
		secret2 = [x for x in res2.json() if x["name"] == "Secret"][0]
		self.assertNotEqual(secret2["location"], "Lab 1")
		self.assertNotEqual(secret2["serial_number"], "SN-123")
		self.assertNotEqual(secret2["notes"], "Top secret")

		# Viewer can explicitly request decryption.
		res3 = self.client.get(f"/api/items/{it.id}/decrypt/")
		self.assertEqual(res3.status_code, 200)
		data3 = res3.json()
		self.assertEqual(data3["location"], "Lab 1")
		self.assertEqual(data3["serial_number"], "SN-123")
		self.assertEqual(data3["notes"], "Top secret")


class ItemAuditFieldsTests(APITestCase):
	def setUp(self):
		self.category = Category.objects.create(name="Audit Category")
		self.staff1 = User.objects.create_user(username="staff_one", password="pass12345", is_staff=True)
		self.staff2 = User.objects.create_user(username="staff_two", password="pass12345", is_staff=True)

	def test_updated_by_tracks_last_editor(self):
		self.client.force_authenticate(user=self.staff1)
		res_create = self.client.post(
			"/api/items/",
			{
				"name": "Audit Item",
				"quantity": 1,
				"min_quantity": 2,
				"photo_url": "https://example.com/photo.jpg",
				"category": self.category.id,
				"location": "Lab",
			},
			format="json",
		)
		self.assertEqual(res_create.status_code, 201)
		item_id = res_create.json()["id"]
		self.assertEqual(res_create.json().get("updated_by"), "staff_one")
		self.assertEqual(res_create.json().get("min_quantity"), 2)
		self.assertEqual(res_create.json().get("photo_url"), "https://example.com/photo.jpg")
		self.assertTrue(ActivityLog.objects.filter(action=ActivityLog.ACTION_ITEM_CREATED, item_id=item_id).exists())

		self.client.force_authenticate(user=self.staff2)
		res_patch = self.client.patch(
			f"/api/items/{item_id}/",
			{"name": "Audit Item Updated"},
			format="json",
		)
		self.assertEqual(res_patch.status_code, 200)
		self.assertEqual(res_patch.json().get("updated_by"), "staff_two")
		self.assertTrue(ActivityLog.objects.filter(action=ActivityLog.ACTION_ITEM_UPDATED, item_id=item_id).exists())
