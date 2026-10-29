"""Commande publish_reviewed : publie les questions relues en FR et en EN, jamais les autres."""
from io import StringIO

import pytest
from django.core.management import call_command

from assessments.models import Question


def draft(module, reviewed=True, correct=1):
    q = Question.objects.create(module=module, prompt_fr="Q ?", prompt_en="Q?", reviewed_fr=reviewed, reviewed_en=reviewed)
    for i in range(2):
        q.choices.create(text_fr=f"C{i}", text_en=f"C{i}", is_correct=i < correct, order=i)
    return q


@pytest.mark.django_db
def test_reviewed_drafts_are_published_and_others_stay_drafts(module):
    ok, unreviewed = draft(module), draft(module, reviewed=False)
    out = StringIO()

    call_command("publish_reviewed", stdout=out)

    ok.refresh_from_db(); unreviewed.refresh_from_db()
    assert (ok.status, unreviewed.status) == ("published", "draft")
    assert "1" in out.getvalue()


@pytest.mark.django_db
def test_inconsistent_question_is_reported_not_published(module):
    broken = draft(module, correct=0)  # QCM sans bonne réponse
    out = StringIO()

    call_command("publish_reviewed", stdout=out)

    broken.refresh_from_db()
    assert broken.status == "draft"
    assert broken.external_id is None and "refus" in out.getvalue().lower()


@pytest.mark.django_db
def test_publishing_twice_changes_nothing(module):
    draft(module)
    call_command("publish_reviewed", stdout=StringIO())

    call_command("publish_reviewed", stdout=StringIO())

    assert Question.objects.published().count() == 1


@pytest.mark.django_db
def test_publication_is_reported_formation_by_formation(module):
    """US-63 (formation `fisca`) : le compte rendu du déploiement distingue les formations."""
    from courses.models import Formation, Module, Partie

    fisca = Formation.objects.create(title_fr="Fiscalité CGI Cameroun", slug="fisca", order=2)
    partie = Partie.objects.create(formation=fisca, title_fr="Sécurité", order=1, slug="p1")
    motor_module = Module.objects.create(partie=partie, title_fr="La sécurité électrique", order=1, duration_hours=8)
    draft(module), draft(motor_module), draft(motor_module)
    broken = draft(motor_module, correct=0)
    broken.external_id = "m-p1-m1-q03"
    broken.save()
    out = StringIO()

    call_command("publish_reviewed", stdout=out)

    lines = out.getvalue().splitlines()
    assert "compta : 1 question(s) publiée(s)." in lines
    assert "fisca : 2 question(s) publiée(s)." in lines
    assert any(line.startswith("Refusée m-p1-m1-q03 (fisca) : ") for line in lines)
