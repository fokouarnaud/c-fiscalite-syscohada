"""manage.py import_parameters <csv> : charge les taux et seuils du CGI (US-61), idempotent, tout ou rien."""
import csv
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from referentiel.models import FiscalParameter


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("path")

    @transaction.atomic
    def handle(self, path, **options):
        with open(path, encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
        for line, row in enumerate(rows, start=2):
            if row["unit"] not in FiscalParameter.Unit.values:
                raise CommandError(f"Ligne {line} : unité inconnue « {row['unit']} ».")
            try:
                value = Decimal(row["value"].replace(",", "."))
            except InvalidOperation:
                raise CommandError(f"Ligne {line} : valeur illisible « {row['value']} ».") from None
            FiscalParameter.objects.update_or_create(
                key=row["key"], exercice=int(row["exercice"]),
                defaults={"value": value, "unit": row["unit"], "label_fr": row["label_fr"], "label_en": row["label_en"],
                          "source_article": row["source_article"]},
            )
        self.stdout.write(f"{len(rows)} paramètres fiscaux importés.")
