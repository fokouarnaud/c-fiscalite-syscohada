"""Identifiants publics UUID (anti-énumération) et noms de fichiers aléatoires. Migration en trois temps :
champ nullable, une valeur distincte par ligne existante, puis contrainte d'unicité."""
import uuid

from django.db import migrations, models

import config.uploads

MODELS = ["Formation", "Partie", "Module", "Section"]


def fill_public_ids(apps, schema_editor):
    for name in MODELS:
        model = apps.get_model("courses", name)
        for pk in model.objects.values_list("pk", flat=True):
            model.objects.filter(pk=pk).update(public_id=uuid.uuid4())


class Migration(migrations.Migration):
    dependencies = [("courses", "0001_initial")]

    operations = [
        *[
            migrations.AddField(model_name=name.lower(), name="public_id", field=models.UUIDField(null=True, editable=False))
            for name in MODELS
        ],
        migrations.RunPython(fill_public_ids, migrations.RunPython.noop),
        *[
            migrations.AlterField(
                model_name=name.lower(), name="public_id",
                field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
            )
            for name in MODELS
        ],
        migrations.AlterField(
            model_name="annexe", name="file",
            field=models.FileField(upload_to=config.uploads.RandomFilename("annexes")),
        ),
    ]
