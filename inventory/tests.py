from django.contrib.auth.models import User

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
