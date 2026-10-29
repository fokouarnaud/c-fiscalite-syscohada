"""US-70 et C19 (Lot 0) : le module pilote Compta M1 versionné s'importe, se publie en entier et ouvre la formation."""
import io

import pytest
from django.conf import settings
from django.core.management import call_command

from assessments.models import Question
from courses.models import Formation, Section

CONTENT = settings.BASE_DIR / "content"


@pytest.fixture
def deployed(db):
    """Même enchaînement que deploy.sh : référentiels, contenu, publication des questions relues."""
    out = io.StringIO()
    call_command("import_syscohada", str(CONTENT / "referentiel" / "syscohada.csv"), stdout=out)
    call_command("import_parameters", str(CONTENT / "referentiel" / "parametres.csv"), stdout=out)
    call_command("import_content", str(CONTENT / "compta" / "formation.json"), stdout=out)
    call_command("publish_reviewed", stdout=out)
    return Formation.objects.get(slug="compta")


def test_the_accounting_formation_is_open_with_its_legal_reference(deployed):
    assert deployed.is_open
    assert deployed.icon == "ledger"
    assert deployed.legal_reference_fr and deployed.legal_reference_en
    assert [(p.order, p.slug) for p in deployed.parties.all()][:1] == [(1, "p1")]


def test_every_pilot_question_is_published_none_left_in_draft(deployed):
    questions = Question.objects.filter(module__partie__formation=deployed)

    assert questions.filter(usage="exam", status="published").count() >= 12
    assert questions.filter(usage="quiz", status="published").count() >= 8
    assert not questions.filter(status="draft").exists()


def test_the_pilot_uses_the_journal_entry_question_type(deployed):
    assert Question.objects.filter(module__partie__formation=deployed, qtype="journal", status="published").exists()


def test_every_pilot_section_exists_in_french_and_english(deployed):
    sections = Section.objects.filter(module__partie__formation=deployed)

    assert sections.count() >= 3
    assert all(s.body_md_fr.strip() and s.body_md_en.strip() for s in sections)


def test_part_one_is_complete_with_its_four_modules_each_ready_for_the_exam(deployed):
    """C9 et C19 : la Partie 1 « Fondamentaux » se livre entière (cadre et principes, écriture, actif et passif, charges et
    produits) ; chaque module a sa banque d'examen, son quiz et au moins une écriture `journal`."""
    from courses.models import Module

    modules = Module.objects.filter(partie__formation=deployed, partie__slug="p1").order_by("order")

    assert [m.order for m in modules] == [1, 2, 3, 4]
    for module in modules:
        published = Question.objects.filter(module=module, status="published")
        assert published.filter(usage="exam").count() >= 12, module.title
        assert published.filter(usage="quiz").count() >= 8, module.title
        assert published.filter(qtype="journal").exists(), module.title
        assert module.sections.count() >= 2, module.title


def test_part_two_covers_the_eight_everyday_operation_modules(deployed):
    """C9 et C19 : la Partie 2 « Opérations courantes » (TVA, achats, ventes, réductions, frais accessoires, autres charges
    et produits, paie, règlements) se livre entière, chaque module prêt pour l'examen."""
    from courses.models import Module

    modules = Module.objects.filter(partie__formation=deployed, partie__slug="p2").order_by("order")

    assert [m.order for m in modules] == list(range(1, 9))
    for module in modules:
        published = Question.objects.filter(module=module, status="published")
        assert published.filter(usage="exam").count() >= 12, module.title
        assert published.filter(usage="quiz").count() >= 8, module.title
        assert published.filter(qtype="journal").exists(), module.title
        assert module.sections.count() >= 2, module.title


def test_part_three_covers_investment_and_financing(deployed):
    """C9 : la Partie 3 « Investissement et financement » (immobilisations, titres, financement, subventions, devises)
    se livre entière, chaque module prêt pour l'examen."""
    from courses.models import Module

    modules = Module.objects.filter(partie__formation=deployed, partie__slug="p3").order_by("order")

    assert [m.order for m in modules] == list(range(1, 6))
    for module in modules:
        published = Question.objects.filter(module=module, status="published")
        assert published.filter(usage="exam").count() >= 12, module.title
        assert published.filter(usage="quiz").count() >= 8, module.title
        assert published.filter(qtype="journal").exists(), module.title


def test_part_four_covers_year_end_work(deployed):
    """C9 : la Partie 4 « Travaux d'inventaire » (amortissements, dépréciations, stocks, créances douteuses, provisions,
    cessions, régularisations) se livre entière, chaque module prêt pour l'examen."""
    from courses.models import Module

    modules = Module.objects.filter(partie__formation=deployed, partie__slug="p4").order_by("order")

    assert [m.order for m in modules] == list(range(1, 8))
    for module in modules:
        published = Question.objects.filter(module=module, status="published")
        assert published.filter(usage="exam").count() >= 12, module.title
        assert published.filter(usage="quiz").count() >= 8, module.title
        assert published.filter(qtype="journal").exists(), module.title


def test_part_five_covers_closing_and_financial_statements(deployed):
    """C9 : la Partie 5 « Clôture et états financiers » (clôture et affectation, bilan, compte de résultat, tableau des flux
    de trésorerie, organisation et contrôles) se livre entière ; la formation compte alors ses cinq parties."""
    from courses.models import Module

    assert [p.slug for p in deployed.parties.order_by("order")] == ["p1", "p2", "p3", "p4", "p5"]
    modules = Module.objects.filter(partie__formation=deployed, partie__slug="p5").order_by("order")
    assert [m.order for m in modules] == list(range(1, 6))
    for module in modules:
        published = Question.objects.filter(module=module, status="published")
        assert published.filter(usage="exam").count() >= 12, module.title
        assert published.filter(usage="quiz").count() >= 8, module.title
        assert published.filter(qtype="journal").exists(), module.title
