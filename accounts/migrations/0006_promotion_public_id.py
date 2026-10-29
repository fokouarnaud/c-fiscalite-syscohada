"""Identifiant public des promotions, en trois temps : champ nullable, une valeur par ligne, puis unicité."""
import uuid

from django.db import migrations, models


def fill_public_ids(apps, schema_editor):
    Promotion = apps.get_model("accounts", "Promotion")
    for promotion in Promotion.objects.all():
        promotion.public_id = uuid.uuid4()
        promotion.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_signup"),
    ]

    operations = [
        migrations.AddField(
            model_name="promotion", name="public_id", field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(fill_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="promotion", name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
