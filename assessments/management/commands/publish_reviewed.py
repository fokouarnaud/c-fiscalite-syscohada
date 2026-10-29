"""Publie les questions en brouillon relues en français et en anglais (US-33), sans jamais forcer les autres."""
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from assessments.models import Question


class Command(BaseCommand):
    help = "Publie les questions en brouillon marquées relues en FR et en EN ; signale celles qui sont incohérentes."

    def handle(self, *args, **options):
        # US-63 : un compte rendu par formation, dans l'ordre du catalogue.
        published, refused = {}, []
        drafts = Question.objects.filter(status=Question.Status.DRAFT, reviewed_fr=True, reviewed_en=True)
        drafts = drafts.select_related("module__partie__formation").order_by("module__partie__formation__order", "pk")
        for question in drafts:
            slug = question.module.partie.formation.slug
            published.setdefault(slug, 0)
            try:
                question.publish()
                published[slug] += 1
            except ValidationError as exc:
                refused.append(f"{question.external_id or question.pk} ({slug}) : {' '.join(exc.messages)}")
        if not published:
            self.stdout.write("0 question(s) publiée(s).")
        for slug, count in published.items():
            self.stdout.write(f"{slug} : {count} question(s) publiée(s).")
        for reason in refused:
            self.stdout.write(f"Refusée {reason}")
