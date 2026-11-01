"""DoD-Parcours (parcours A, Ngono Mode SARL) : le contenu versionné s'importe, se publie et se rend sans balise
inconnue ; examen à 4 questions tirées par module, sous-comptes Mobile Money créés (S11, S17, S19)."""
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command

from assessments.models import Assessment, Question
from courses.models import Formation, Section
from referentiel.models import SyscohadaAccount
from simulation.models import Piece

CONTENT = settings.BASE_DIR / "content"


@pytest.fixture
def parcours_a(db):
    out = StringIO()
    call_command("import_syscohada", str(CONTENT / "referentiel" / "syscohada.csv"), stdout=out)
    call_command("import_parameters", str(CONTENT / "referentiel" / "parametres.csv"), stdout=out)
    call_command("import_content", str(CONTENT / "simulation" / "formation.json"), stdout=out)
    call_command("publish_reviewed", stdout=out)
    return Formation.objects.get(slug="simulation")


def test_the_simulation_opens_with_parcours_a_and_its_seven_modules(parcours_a):
    """US-80 (S1, S20) : la formation s'ouvre au catalogue une fois le parcours A livré (ouverture décidée le
    2026-11-01) ; 7 modules."""
    partie = parcours_a.parties.get(slug="a")

    assert (parcours_a.is_open, parcours_a.icon, partie.modules.count()) == (True, "briefcase", 7)
    assert Assessment.exam_for(partie).questions_per_module == 4


def test_every_question_of_parcours_a_is_published(parcours_a):
    questions = Question.objects.filter(module__partie__formation=parcours_a)

    assert questions.count() >= 140
    assert set(questions.values_list("status", flat=True)) == {Question.Status.PUBLISHED}


def test_the_mobile_money_sub_accounts_exist_under_552(parcours_a):
    assert {a.code: a.parent_id for a in SyscohadaAccount.objects.filter(code__in=["5521", "5522"])} == \
        {"5521": "552", "5522": "552"}


def test_every_section_renders_without_unknown_tag(parcours_a):
    """US-82, US-97, C27 : aucune pièce, aucun compte, aucun paramètre ni source inconnus dans le rendu."""
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
    assert Piece.objects.filter(partie__formation=parcours_a).count() >= 12 * 8  # S4 : au moins 8 pièces par mois
