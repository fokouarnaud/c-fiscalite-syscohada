"""US-23 et US-24 : sources citées en badges et taux lus dans la table des paramètres, remplacés après bleach."""
from decimal import Decimal

import pytest
from django.utils import translation

from courses.rendering import render_markdown
from referentiel.models import FiscalParameter, SyscohadaAccount


@pytest.fixture
def referentiel(db):
    FiscalParameter.objects.create(key="tva.taux_global", exercice=2026, value=Decimal("19.25"), unit="%",
                                   source_article="CGI art. 142")
    FiscalParameter.objects.create(key="is.minimum_perception", exercice=2026, value=Decimal("1500000"), unit="FCFA")
    SyscohadaAccount.objects.create(code="4452", label_fr="État, TVA récupérable sur achats",
                                    label_en="State, recoverable VAT on purchases")


def test_a_rate_is_read_from_the_parameter_table(referentiel):
    html = render_markdown("La TVA est de [[param:tva.taux_global]].")

    assert '<span class="param" title="CGI art. 142">19,25 %</span>' in html
    assert "[[" not in html


def test_a_rate_follows_the_language_format(referentiel):
    with translation.override("en"):
        assert ">19.25%</span>" in render_markdown("[[param:tva.taux_global]]")


def test_an_amount_parameter_is_grouped_in_fcfa(referentiel):
    assert ">1 500 000 FCFA</span>" in render_markdown("[[param:is.minimum_perception]]")


def test_changing_the_rate_changes_the_lesson_without_touching_its_text(referentiel, settings):
    FiscalParameter.objects.create(key="tva.taux_global", exercice=2027, value=Decimal("20"), unit="%")
    settings.FISCAL_YEAR = 2027

    assert ">20 %</span>" in render_markdown("[[param:tva.taux_global]]")


def test_an_unknown_parameter_is_flagged_never_shown_raw(referentiel):
    html = render_markdown("[[param:tva.inconnu]]")

    assert "[[param:" not in html
    assert '<mark class="param-missing">tva.inconnu</mark>' in html


def test_a_cgi_article_becomes_a_source_badge_in_the_active_language(db):
    assert '<cite class="source" tabindex="0" title="Code général des impôts du Cameroun, édition 2026">' \
           'CGI 2026, art. 127</cite>' in render_markdown("Voir [[cgi:art. 127]].")
    with translation.override("en"):
        assert ">GTC 2026, s. 127</cite>" in render_markdown("See [[cgi:art. 127]].")


def test_a_syscohada_account_shows_its_label_in_the_active_language(referentiel):
    assert ">4452 · État, TVA récupérable sur achats</cite>" in render_markdown("[[syscohada:4452]]")
    with translation.override("en"):
        assert ">4452 · State, recoverable VAT on purchases</cite>" in render_markdown("[[syscohada:4452]]")


def test_an_account_missing_from_the_plan_is_flagged(referentiel):
    assert '<mark class="source-missing">4019</mark>' in render_markdown("[[syscohada:4019]]")


def test_a_guide_chapter_becomes_a_source_badge(db):
    assert ">Guide SYSCOHADA, ch. 12</cite>" in render_markdown("[[guide:ch. 12]]")


def test_markup_inside_a_tag_cannot_escape_the_badge(db):
    html = render_markdown('[[cgi:<script>alert(1)</script>]]')

    assert "<script>" not in html


def test_an_account_without_english_label_falls_back_to_french(db):
    """U5 : le plan SYSCOHADA fourni n'a que des libellés français ; l'anglais retombe sur eux plutôt que sur un vide."""
    SyscohadaAccount.objects.create(code="571", label_fr="Caisse siège social")

    with translation.override("en"):
        assert ">571 · Caisse siège social</cite>" in render_markdown("[[syscohada:571]]")
