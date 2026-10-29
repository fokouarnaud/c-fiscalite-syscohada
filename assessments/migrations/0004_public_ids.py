"""Identifiants publics UUID (anti-énumération) et noms de fichiers aléatoires. Migration en trois temps :
champ nullable, une valeur distincte par ligne existante, puis contrainte d'unicité."""
import uuid

import django.core.validators
from django.db import migrations, models

import config.uploads

MODELS = ["Question", "Choice", "Attempt"]


def fill_public_ids(apps, schema_editor):
    for name in MODELS:
        model = apps.get_model("assessments", name)
        for pk in model.objects.values_list("pk", flat=True):
            model.objects.filter(pk=pk).update(public_id=uuid.uuid4())


class Migration(migrations.Migration):
    dependencies = [("assessments", "0003_assessment_duration_minutes_assessment_max_attempts_and_more")]

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
            model_name="question", name="image",
            field=models.FileField(
                blank=True, upload_to=config.uploads.RandomFilename("questions"), verbose_name="image",
                validators=[
                    django.core.validators.FileExtensionValidator(["webp", "png", "jpg", "jpeg", "svg"]),
                    config.uploads.validate_inert_svg,
                ],
            ),
        ),
    ]
