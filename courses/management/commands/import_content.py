from django.core.management.base import BaseCommand

from courses.importer import import_formation


class Command(BaseCommand):
    help = "Importe (ou met à jour) une ou plusieurs formations depuis leur manifeste JSON. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("manifests", nargs="+", help="Chemin de chaque formation.json")

    def handle(self, *args, manifests, **options):
        for manifest in manifests:
            stats = import_formation(manifest)
            self.stdout.write(self.style.SUCCESS(f"{manifest} : {stats['sections']} sections, {stats['questions']} questions importées."))
