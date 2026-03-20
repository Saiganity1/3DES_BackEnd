from django.db import migrations, models


def forwards_encrypt_location(apps, schema_editor):
    Item = apps.get_model("inventory", "Item")

    # Import inside migration to avoid app-loading issues.
    from inventory.crypto.triple_des import encrypt_text

    for item in Item.objects.all().only("id", "location", "location_encrypted"):
        plaintext = getattr(item, "location", "") or ""
        if plaintext and not getattr(item, "location_encrypted", ""):
            item.location_encrypted = encrypt_text(plaintext) or ""
            item.save(update_fields=["location_encrypted"])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_category_created_by_item_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='location_encrypted',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.RunPython(forwards_encrypt_location, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='item',
            name='location',
        ),
    ]
