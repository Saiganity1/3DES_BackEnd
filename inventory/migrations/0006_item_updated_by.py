"""Migration that adds `updated_by` tracking to Item.

Presentation note: migrations describe schema changes executed by Django.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_item_can_decrypt_permission"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
