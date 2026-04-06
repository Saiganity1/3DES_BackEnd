from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_item_updated_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="min_quantity",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="item",
            name="photo_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("category_created", "Category created"),
                            ("item_created", "Item created"),
                            ("item_updated", "Item updated"),
                            ("item_archived", "Item archived"),
                            ("item_restored", "Item restored"),
                            ("account_taken_down", "Account taken down"),
                            ("account_promoted", "Account promoted"),
                            ("decrypt_granted", "Decrypt granted"),
                            ("decrypt_revoked", "Decrypt revoked"),
                        ],
                        max_length=64,
                    ),
                ),
                ("message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="activity_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="activity_logs",
                        to="inventory.item",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
