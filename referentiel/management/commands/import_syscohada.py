"""manage.py import_syscohada <csv> : importe le plan SYSCOHADA révisé (US-63), idempotent, parents avant fils."""
import csv

from django.core.management.base import BaseCommand
from django.db import transaction

from referentiel.models import SyscohadaAccount


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("path")

    @transaction.atomic
    def handle(self, path, **options):
        with open(path, encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
        # Les codes courts d'abord : le parent existe quand son fils est enregistré.
        for row in sorted(rows, key=lambda r: (len(r["code"]), r["code"])):
            account = SyscohadaAccount.objects.filter(code=row["code"]).first() or SyscohadaAccount(code=row["code"])
            account.label_fr, account.label_en = row["label_fr"], row["label_en"]
            account.save()
        self.stdout.write(f"{len(rows)} comptes SYSCOHADA importés.")
