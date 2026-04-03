from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from rest_framework.test import APITestCase

from inventory.models import Category, Item


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
