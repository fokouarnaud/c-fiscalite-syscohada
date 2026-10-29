"""US-61 : les taux et seuils du CGI vivent dans une table éditable, une ligne par exercice (C3, C14)."""
from decimal import Decimal

import pytest
from django.db import IntegrityError

from referentiel.models import FiscalParameter


@pytest.fixture
def tva_history(db):
    FiscalParameter.objects.create(key="tva.taux_global", exercice=2025, value=Decimal("19.25"), unit="%",
                                   label_fr="Taux global de TVA", source_article="CGI art. 142")
    FiscalParameter.objects.create(key="tva.taux_global", exercice=2027, value=Decimal("20"), unit="%",
                                   label_fr="Taux global de TVA", source_article="CGI art. 142")


def test_the_current_value_is_the_latest_exercice_not_after_the_reference_year(tva_history, settings):
    settings.FISCAL_YEAR = 2026

    assert FiscalParameter.objects.current("tva.taux_global").value == Decimal("19.25")


def test_moving_the_reference_year_picks_the_new_rate(tva_history, settings):
    settings.FISCAL_YEAR = 2027

    assert FiscalParameter.objects.current("tva.taux_global").value == Decimal("20")


def test_an_unknown_key_has_no_current_value(db):
    assert FiscalParameter.objects.current("tva.inconnu") is None


def test_a_key_has_a_single_value_per_exercice(tva_history):
    with pytest.raises(IntegrityError):
        FiscalParameter.objects.create(key="tva.taux_global", exercice=2025, value=Decimal("18"), unit="%")


def question(module, external_id, params):
    from assessments.models import Question

    return Question.objects.create(module=module, external_id=external_id, prompt_fr="Q ?", params=params)


def test_changing_a_rate_lists_the_questions_tagged_with_its_key(module, tva_history):
    """US-62 : après la loi de finances, l'admin retrouve les questions bâties sur ce taux, et seulement elles."""
    tva = question(module, "C-1", "tva.taux_global is.taux")
    question(module, "C-2", "is.taux")
    question(module, "C-3", "tva.taux_global_reduit")  # clé voisine : ne doit pas remonter

    parameter = FiscalParameter.objects.get(key="tva.taux_global", exercice=2025)

    assert list(parameter.questions_to_review()) == [tva]


HEADER = "key;exercice;value;unit;label_fr;label_en;source_article\n"


def test_the_rates_are_imported_from_a_versioned_csv_and_updated_in_place(db, tmp_path):
    """US-61 et US-74 : le déploiement charge les taux de la loi de finances ; un second import met à jour sans doubler."""
    from django.core.management import call_command

    path = tmp_path / "parametres.csv"
    path.write_text(HEADER + "tva.taux_principal;2026;17,5;%;Taux général de TVA;Standard VAT rate;CGI art. 142\n",
                    encoding="utf-8")
    call_command("import_parameters", str(path), verbosity=0)
    path.write_text(HEADER + "tva.taux_principal;2026;17.5;%;Taux général de la TVA;Standard VAT rate;CGI art. 142 (1)\n",
                    encoding="utf-8")
    call_command("import_parameters", str(path), verbosity=0)

    parameter = FiscalParameter.objects.get()
    assert (parameter.value, parameter.unit, parameter.label_en) == (Decimal("17.5"), "%", "Standard VAT rate")
    assert (parameter.label_fr, parameter.source_article) == ("Taux général de la TVA", "CGI art. 142 (1)")


def test_a_csv_with_an_unknown_unit_is_refused_whole(db, tmp_path):
    from django.core.management import CommandError, call_command

    path = tmp_path / "parametres.csv"
    path.write_text(HEADER + "tva.taux_principal;2026;17,5;%;TVA;VAT;CGI art. 142\n"
                    "is.taux;2026;30;pourcent;IS;CIT;CGI art. 17\n", encoding="utf-8")

    with pytest.raises(CommandError):
        call_command("import_parameters", str(path), verbosity=0)
    assert not FiscalParameter.objects.exists()


@pytest.fixture
def versioned_rates(db):
    from django.conf import settings
    from django.core.management import call_command

    call_command("import_parameters", str(settings.BASE_DIR / "content" / "referentiel" / "parametres.csv"), verbosity=0)


def test_the_versioned_overall_vat_rate_is_the_standard_rate_plus_the_council_cents(versioned_rates):
    """Cohérence de content/referentiel/parametres.csv : 17,5 % × (1 + 10 %) = 19,25 % (CGI art. 142 et C 83)."""
    current = FiscalParameter.objects.current
    principal, cac = current("tva.taux_principal").value, current("cac.taux").value

    assert current("tva.taux_global").value == principal * (1 + cac / 100)


def test_every_versioned_rate_cites_its_article(versioned_rates):
    assert FiscalParameter.objects.exists()
    assert not FiscalParameter.objects.filter(source_article="").exists()
    assert not FiscalParameter.objects.filter(label_en="").exists()
