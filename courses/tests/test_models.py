import pytest
from django.utils import translation

from courses.models import Formation, Module, Partie, Section


@pytest.fixture
def module():
    formation = Formation.objects.create(title_fr="Électronique", slug="electro")
    partie = Partie.objects.create(formation=formation, title_fr="Habilitation et sécurité", order=1, slug="p1")
    return Module.objects.create(partie=partie, title_fr="Sécurité dans les travaux", order=1, duration_hours=8)


@pytest.mark.django_db
def test_sections_are_listed_in_their_teaching_order(module):
    Section.objects.create(module=module, title_fr="Études de cas", order=2, body_md_fr="...")
    Section.objects.create(module=module, title_fr="Introduction", order=1, body_md_fr="...")
    assert [s.title_fr for s in module.sections.all()] == ["Introduction", "Études de cas"]


@pytest.mark.django_db
def test_untranslated_title_falls_back_to_french_in_english(module):
    with translation.override("en"):
        assert Module.objects.get(pk=module.pk).title == "Sécurité dans les travaux"


@pytest.mark.django_db
def test_translated_title_is_used_in_english(module):
    module.title_en = "Safety at work"
    module.save()
    with translation.override("en"):
        assert Module.objects.get(pk=module.pk).title == "Safety at work"


@pytest.mark.django_db
def test_practical_sections_are_separated_from_content_sections(module):
    Section.objects.create(module=module, title_fr="Cours", order=1, body_md_fr="...")
    Section.objects.create(module=module, title_fr="TAF", order=2, body_md_fr="...", kind=Section.Kind.PRACTICAL)
    assert [s.title_fr for s in module.sections.practical()] == ["TAF"]


# --- E45 : rang unique, pour que trois parties (et leurs modules) restent dans un ordre sans ambiguïté -----------------


@pytest.mark.django_db
def test_two_parts_of_a_formation_cannot_share_a_rank(module):
    from django.db import IntegrityError, transaction

    formation = module.partie.formation
    Partie.objects.create(formation=formation, title_fr="Courant alternatif et filtres", order=2, slug="p2")
    with pytest.raises(IntegrityError), transaction.atomic():
        Partie.objects.create(formation=formation, title_fr="Amplification, oscillateurs et alimentations", order=2, slug="p3")


@pytest.mark.django_db
def test_the_same_rank_is_allowed_in_another_formation(module):
    other = Formation.objects.create(title_fr="Froid", slug="froid")
    assert Partie.objects.create(formation=other, title_fr="Bases", order=module.partie.order, slug="p1").pk


@pytest.mark.django_db
def test_two_modules_of_a_part_cannot_share_a_rank(module):
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        Module.objects.create(partie=module.partie, title_fr="Les oscillateurs", order=module.order, duration_hours=8)


# --- US-59 (formation `moteurs`, M13) : icône Tabler d'une formation, liste fermée ---------------------------------


@pytest.mark.django_db
def test_a_formation_with_a_known_icon_is_valid():
    formation = Formation(title_fr="Moteurs électriques et commande", slug="moteurs", icon="receipt")
    formation.full_clean()


@pytest.mark.django_db
def test_an_icon_outside_the_closed_list_is_refused():
    from django.core.exceptions import ValidationError

    formation = Formation(title_fr="Moteurs électriques et commande", slug="moteurs", icon="rocket")
    with pytest.raises(ValidationError) as error:
        formation.full_clean()
    assert "icon" in error.value.message_dict


@pytest.mark.django_db
def test_a_formation_without_an_explicit_icon_shows_the_accounting_ledger():
    assert Formation.objects.create(title_fr="Électronique", slug="electro").icon == "ledger"


def test_every_formation_icon_exists_in_the_project_icon_set():
    from django.conf import settings

    for name, _label in Formation.Icon.choices:
        assert (settings.BASE_DIR / "templates" / "icons" / f"{name}.svg").exists(), name
