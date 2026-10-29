import pytest
from django.core.files.base import ContentFile

from courses.models import Annexe, Formation, Module, Partie, Section
from progress.models import SectionView


@pytest.fixture
def sections(module):
    return [
        Section.objects.create(module=module, title_fr="Introduction", order=1, body_md_fr="Le **courant** tue."),
        Section.objects.create(module=module, title_fr="TAF", order=2, kind=Section.Kind.PRACTICAL, body_md_fr="Simulez."),
    ]


@pytest.fixture
def foreign_section(db):
    other = Formation.objects.create(title_fr="Électronique", slug="elec")
    partie = Partie.objects.create(formation=other, title_fr="P", order=1, slug="p")
    module = Module.objects.create(partie=partie, title_fr="M", order=1)
    return Section.objects.create(module=module, title_fr="Secret", order=1)


@pytest.mark.django_db
def test_module_page_lists_sections_with_viewed_state(client, enrolled, module, sections):
    SectionView.objects.create(user=enrolled, section=sections[0])
    client.force_login(enrolled)
    response = client.get(f"/fr/modules/{module.public_id}/")
    assert response.status_code == 200
    assert [(row["section"], row["viewed"]) for row in response.context["sections"]] == [
        (sections[0], True),
        (sections[1], False),
    ]


@pytest.mark.django_db
def test_opening_a_section_marks_it_viewed(client, enrolled, sections):
    client.force_login(enrolled)
    response = client.get(f"/fr/sections/{sections[0].public_id}/")
    assert response.status_code == 200
    assert SectionView.objects.filter(user=enrolled, section=sections[0]).exists()


@pytest.mark.django_db
def test_section_markdown_is_rendered_as_html(client, enrolled, sections):
    client.force_login(enrolled)
    response = client.get(f"/fr/sections/{sections[0].public_id}/")
    assert "Le <strong>courant</strong> tue." in response.content.decode()


@pytest.mark.django_db
def test_section_links_to_previous_and_next_sections(client, enrolled, sections):
    client.force_login(enrolled)
    response = client.get(f"/fr/sections/{sections[0].public_id}/")
    assert response.context["previous"] is None
    assert response.context["next"] == sections[1]


@pytest.mark.django_db
def test_section_from_another_formation_is_not_found(client, enrolled, foreign_section):
    client.force_login(enrolled)
    assert client.get(f"/fr/sections/{foreign_section.public_id}/").status_code == 404
    assert not SectionView.objects.filter(user=enrolled).exists()


@pytest.mark.django_db
def test_module_from_another_formation_is_not_found(client, enrolled, foreign_section):
    client.force_login(enrolled)
    assert client.get(f"/fr/modules/{foreign_section.module.public_id}/").status_code == 404


@pytest.mark.django_db
def test_anonymous_visitor_cannot_read_a_section(client, sections):
    response = client.get(f"/fr/sections/{sections[0].public_id}/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_practical_section_offers_its_annexes_for_download(client, enrolled, sections, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    annexe = Annexe(section=sections[1], title_fr="Fiche d'intervention")
    annexe.file.save("fiche.xlsx", ContentFile(b"data"))
    client.force_login(enrolled)
    response = client.get(f"/fr/sections/{sections[1].public_id}/")
    assert annexe.file.url in response.content.decode()


@pytest.mark.django_db
def test_untranslated_section_is_flagged_as_french_fallback_in_english(client, enrolled, sections):
    client.force_login(enrolled)
    response = client.get(f"/en/sections/{sections[0].public_id}/")
    assert response.context["fallback_fr"] is True
    assert "Le <strong>courant</strong> tue." in response.content.decode()


@pytest.mark.django_db
def test_translated_section_is_not_flagged_in_english(client, enrolled, sections):
    sections[0].body_md_en = "Current **kills**."
    sections[0].save()
    client.force_login(enrolled)
    response = client.get(f"/en/sections/{sections[0].public_id}/")
    assert response.context["fallback_fr"] is False


@pytest.mark.django_db
def test_calculator_script_loads_only_on_sections_that_use_one(client, enrolled, module):
    from courses.models import Section

    with_calc = Section.objects.create(module=module, title_fr="La TVA", order=1, body_md_fr="[[calc:tva]]")
    plain = Section.objects.create(module=module, title_fr="Texte", order=2, body_md_fr="Du texte.")
    client.force_login(enrolled)

    assert "calculators.js" in client.get(f"/fr/sections/{with_calc.public_id}/").content.decode()
    assert "calculators.js" not in client.get(f"/fr/sections/{plain.public_id}/").content.decode()


@pytest.mark.django_db
def test_a_calculator_receives_the_rates_in_force_without_inline_script(client, enrolled, module):
    """US-26 : les taux de FiscalParameter arrivent par json_script (donnée inerte, CSP sans script en ligne)."""
    from decimal import Decimal

    from referentiel.models import FiscalParameter

    FiscalParameter.objects.create(key="tva.taux_global", exercice=2026, value=Decimal("19.25"), unit="%")
    FiscalParameter.objects.create(key="tva.taux_global", exercice=2025, value=Decimal("18"), unit="%")
    section = Section.objects.create(module=module, title_fr="La TVA", order=1, body_md_fr="[[calc:tva]]")
    client.force_login(enrolled)

    html = client.get(f"/fr/sections/{section.public_id}/").content.decode()

    assert '<script id="calc-params" type="application/json">{"tva.taux_global": "19.25"}</script>' in html


@pytest.mark.django_db
def test_a_section_without_calculator_carries_no_rates(client, enrolled, sections):
    client.force_login(enrolled)

    assert "calc-params" not in client.get(f"/fr/sections/{sections[0].public_id}/").content.decode()


def test_a_section_shows_the_legal_reference_of_its_formation(client, enrolled, sections):
    """US-25 : chaque leçon de fiscalité affiche « Référence : CGI Cameroun, éd. 2026 »."""
    formation = sections[0].module.partie.formation
    formation.legal_reference_fr = "CGI Cameroun, éd. 2026"
    formation.legal_reference_en = "Cameroon GTC, 2026 ed."
    formation.save()
    client.force_login(enrolled)

    assert "Référence : CGI Cameroun, éd. 2026" in client.get(f"/fr/sections/{sections[0].public_id}/").content.decode()
    assert "Reference: Cameroon GTC, 2026 ed." in client.get(f"/en/sections/{sections[0].public_id}/").content.decode()


def test_a_formation_without_legal_reference_shows_none(client, enrolled, sections):
    client.force_login(enrolled)
    assert "Référence :" not in client.get(f"/fr/sections/{sections[0].public_id}/").content.decode()


@pytest.mark.django_db
def test_a_calculator_page_loads_the_shared_engine_before_the_widgets_with_business_labels(client, enrolled, module):
    """US-26 : calc-core.js (formules vérifiées contre Python) précède calculators.js ; libellés traduits, sans électronique."""
    section = Section.objects.create(module=module, title_fr="La TVA", order=1, body_md_fr="[[calc:tva]]",
                                     body_md_en="[[calc:tva]]")
    client.force_login(enrolled)

    fr = client.get(f"/fr/sections/{section.public_id}/").content.decode()
    en = client.get(f"/en/sections/{section.public_id}/").content.decode()

    assert 0 < fr.index("acad/js/calc-core.js") < fr.index("acad/js/calculators.js")
    assert 'data-tva-title="Calculateur : TVA"' in fr and 'data-tva-title="Calculator: VAT"' in en
    assert 'data-paie-title="Calculateur : retenues sur salaire"' in fr
    assert "loi d’Ohm" not in fr


@pytest.mark.django_db
def test_us21_unenrolled_learner_is_sent_to_the_programme_of_an_open_formation(client, enrolled, foreign_section):
    """US-21 : un non-inscrit est renvoyé vers le programme d'une formation ouverte, sans que la section soit marquée vue."""
    formation = foreign_section.module.partie.formation
    formation.is_open = True
    formation.save()
    client.force_login(enrolled)
    response = client.get(f"/fr/sections/{foreign_section.public_id}/")
    assert response.status_code == 302
    assert response["Location"] == f"/fr/catalogue/{formation.public_id}/"
    assert not SectionView.objects.filter(user=enrolled).exists()
