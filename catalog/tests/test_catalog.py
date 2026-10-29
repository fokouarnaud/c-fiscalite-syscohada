"""US-01 : catalogue public des formations ouvertes."""
import pytest

from courses.models import Formation, Module, Partie


@pytest.fixture
def open_formation(db):
    formation = Formation.objects.create(
        title_fr="Électronique", title_en="Electronics", slug="electro", is_open=True,
        description_fr="Du courant continu au transistor.",
    )
    partie = Partie.objects.create(formation=formation, title_fr="DC et semi-conducteurs", order=1, slug="p1")
    Module.objects.create(partie=partie, title_fr="Révision DC", order=1, duration_hours=6)
    Module.objects.create(partie=partie, title_fr="La diode", order=2, duration_hours=4)
    return formation


@pytest.fixture
def closed_formation(db):
    return Formation.objects.create(title_fr="Froid", slug="froid", is_open=False)


def test_anonymous_visitor_sees_only_open_formations(client, open_formation, closed_formation):
    response = client.get("/fr/catalogue/")

    assert response.status_code == 200
    assert [row["formation"] for row in response.context["rows"]] == [open_formation]


def test_catalogue_entry_sums_the_module_hours_and_lists_the_parts(client, open_formation):
    [row] = client.get("/fr/catalogue/").context["rows"]

    assert row["hours"] == 10
    assert [p.title for p in row["parties"]] == ["DC et semi-conducteurs"]


def test_catalogue_is_served_in_english(client, open_formation):
    assert "Electronics" in client.get("/en/catalogue/").content.decode()


def test_open_formation_has_a_public_detail_page(client, open_formation):
    response = client.get(f"/fr/catalogue/{open_formation.public_id}/")

    assert response.status_code == 200
    assert "Du courant continu au transistor." in response.content.decode()


def test_closed_formation_detail_is_not_found(client, closed_formation):
    assert client.get(f"/fr/catalogue/{closed_formation.public_id}/").status_code == 404


def test_catalogue_marks_the_formations_the_learner_already_follows(client, learner, open_formation):
    from catalog.models import Enrollment

    Formation.objects.create(title_fr="Électricité", slug="elec", is_open=True)
    Enrollment.objects.create(user=learner, formation=open_formation)
    client.force_login(learner)

    rows = client.get("/fr/catalogue/").context["rows"]

    assert {row["formation"].slug: row["enrolled"] for row in rows} == {"electro": True, "elec": False}


def test_detail_page_counts_modules_for_the_visitor(client, open_formation):
    row = client.get(f"/fr/catalogue/{open_formation.public_id}/").context["row"]

    assert row["module_count"] == 2
    assert row["enrolled"] is False


@pytest.mark.parametrize("lang, text", [("fr", "À suivre après la Partie 1."), ("en", "Best taken after Part 1.")])
def test_formation_page_shows_the_description_of_each_part(client, open_formation, lang, text):
    """US-40 : la fiche publique affiche la description d'une partie (ordre conseillé, sans blocage)."""
    Partie.objects.create(
        formation=open_formation, title_fr="Courant alternatif", order=2, slug="p2",
        description_fr="À suivre après la Partie 1.", description_en="Best taken after Part 1.",
    )
    assert text in client.get(f"/{lang}/catalogue/{open_formation.public_id}/").content.decode()


# --- US-58 (formation `moteurs`) : chaque carte du catalogue porte l'icône de sa formation ---------------------------

ENGINE_PATH = 'd="M8 7h6"'  # tracé propre à templates/icons/receipt.svg (C16, Fiscalité)
CPU_PATH = 'd="M9 4v16"'  # tracé propre à templates/icons/ledger.svg (C16, Comptabilité, icône par défaut)


def test_each_catalogue_card_shows_the_icon_of_its_formation(client, open_formation):
    Formation.objects.create(title_fr="Moteurs électriques et commande", slug="moteurs", is_open=True, order=2, icon="receipt")

    html = client.get("/fr/catalogue/").content.decode()

    cards = html.split('class="course-card"')[1:]
    assert [CPU_PATH in card for card in cards] == [True, False]
    assert [ENGINE_PATH in card for card in cards] == [False, True]


def test_header_names_the_platform_and_its_two_domains(client, db):
    """C16 : marque « ComptaFisca Acad Ventisax » et slogan compta SYSCOHADA + fiscalité camerounaise."""
    fr = client.get("/fr/catalogue/").content.decode()
    en = client.get("/en/catalogue/").content.decode()

    assert "ComptaFisca Acad" in fr and "Electro Acad" not in fr
    assert "Comptabilité SYSCOHADA et fiscalité camerounaise, formation et évaluation" in fr
    assert "SYSCOHADA accounting and Cameroonian taxation, training and assessment" in en


def test_a_closed_formation_cannot_be_enrolled_in(client, learner, closed_formation):
    """US-14 : la Fiscalité masquée pendant la production (is_open=False) refuse l'inscription."""
    from catalog.models import Enrollment

    client.force_login(learner)
    response = client.post(f"/fr/catalogue/{closed_formation.public_id}/inscription/")

    assert response.status_code == 404
    assert not Enrollment.objects.filter(user=learner).exists()


def test_us15_programme_shows_the_advisory_prerequisite_in_each_language(client, open_formation):
    """US-15 : le programme affiche le prérequis indicatif, en FR et en EN."""
    open_formation.prerequisite_note_fr = "Recommandé après les Parties 1 et 2 de Comptabilité"
    open_formation.prerequisite_note_en = "Recommended after Parts 1 and 2 of Accounting"
    open_formation.save()

    assert "Recommandé après les Parties 1 et 2 de Comptabilité" in client.get(
        f"/fr/catalogue/{open_formation.public_id}/").content.decode()
    assert "Recommended after Parts 1 and 2 of Accounting" in client.get(
        f"/en/catalogue/{open_formation.public_id}/").content.decode()


def test_us15_a_prerequisite_never_blocks_enrolment(client, learner, open_formation):
    """US-15 : le prérequis reste indicatif, l'inscription en un clic aboutit."""
    from catalog.models import Enrollment

    open_formation.prerequisite_note_fr = "Recommandé après les Parties 1 et 2 de Comptabilité"
    open_formation.save()
    client.force_login(learner)

    client.post(f"/fr/catalogue/{open_formation.public_id}/inscription/")

    assert Enrollment.objects.filter(user=learner, formation=open_formation).exists()
