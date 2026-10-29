"""C6, C9 et C19 : la formation Fiscalité (CGI Cameroun éd. 2026), versionnée dans content/fisca, s'importe entière."""
import io

import pytest
from django.conf import settings
from django.core.management import call_command

from assessments.models import Question
from courses.models import Formation, Module, Section

CONTENT = settings.BASE_DIR / "content"


@pytest.fixture
def fisca(db):
    out = io.StringIO()
    call_command("import_syscohada", str(CONTENT / "referentiel" / "syscohada.csv"), stdout=out)
    call_command("import_parameters", str(CONTENT / "referentiel" / "parametres.csv"), stdout=out)
    call_command("import_content", str(CONTENT / "fisca" / "formation.json"), stdout=out)
    call_command("publish_reviewed", stdout=out)
    return Formation.objects.get(slug="fisca")


def test_the_tax_formation_is_complete_and_therefore_open(fisca):
    """C19 : masquée tant qu'elle était incomplète, la Fiscalité s'ouvre une fois ses trois parties livrées."""
    assert fisca.is_open
    assert fisca.icon == "receipt"
    assert fisca.legal_reference_fr == "CGI Cameroun, éd. 2026"
    assert [p.slug for p in fisca.parties.order_by("order")] == ["p1", "p2", "p3"]


def test_the_plan_follows_the_tax_code_in_eight_modules(fisca):
    """C6 : revenus (système et régimes, IS, IRPP), dépense et droits (TVA et accises, enregistrement et timbre, fiscalité
    locale), procédures (obligations et contrôle, sanctions et contentieux)."""
    counts = [Module.objects.filter(partie=p).count() for p in fisca.parties.order_by("order")]

    assert counts == [3, 3, 2]


def test_every_tax_module_is_ready_for_the_exam(fisca):
    for module in Module.objects.filter(partie__formation=fisca):
        published = Question.objects.filter(module=module, status="published")
        assert published.filter(usage="exam").count() >= 12, module.title
        assert published.filter(usage="quiz").count() >= 8, module.title
        assert not Question.objects.filter(module=module, status="draft").exists(), module.title


def test_every_tax_section_cites_an_article_of_the_tax_code(fisca):
    sections = Section.objects.filter(module__partie__formation=fisca)

    assert sections.count() >= 16
    assert all("[[cgi:" in s.body_md_fr and "[[cgi:" in s.body_md_en for s in sections)


def test_us15_the_tax_formation_recommends_accounting_parts_one_and_two(fisca):
    """US-15 : la Fiscalité est recommandée après les Parties 1 et 2 de Comptabilité."""
    assert fisca.prerequisite_note_fr == "Recommandé après les Parties 1 et 2 de Comptabilité"
    assert fisca.prerequisite_note_en == "Recommended after Parts 1 and 2 of Accounting"
