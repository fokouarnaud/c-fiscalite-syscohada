"""Code d'accès des promotions (US-06), en trois temps : champ nullable, une valeur par ligne, puis unicité."""
from django.db import migrations, models

import accounts.models


def fill_codes(apps, schema_editor):
    Promotion = apps.get_model("accounts", "Promotion")
    used = set()
    for promotion in Promotion.objects.all():
        code = accounts.models.new_join_code()
        while code in used:
            code = accounts.models.new_join_code()
        used.add(code)
        promotion.join_code = code
        promotion.save(update_fields=["join_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_promotion_to_enrollment"),
    ]

    operations = [
        migrations.AddField(
            model_name="promotion",
            name="join_code",
            field=models.CharField(editable=False, max_length=8, null=True, verbose_name="code d'accès"),
        ),
        migrations.AddField(
            model_name="promotion",
            name="join_code_active",
            field=models.BooleanField(default=True, verbose_name="code d'accès actif"),
        ),
        migrations.RunPython(fill_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="promotion",
            name="join_code",
            field=models.CharField(
                default=accounts.models.new_join_code, editable=False, max_length=8, unique=True,
                verbose_name="code d'accès",
            ),
        ),
    ]
