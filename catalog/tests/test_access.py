"""US-07 / US-11 : l'accès au contenu et aux promotions découle des inscriptions (Enrollment)."""
import pytest

from accounts.models import Promotion, User
from catalog.models import Enrollment
from courses.access import accessible_formations
from courses.models import Formation, Partie


@pytest.fixture
def second_formation(db):
    formation = Formation.objects.create(title_fr="Électricité bâtiment", slug="elec")
    Partie.objects.create(formation=formation, title_fr="Bases", order=1, slug="p1")
    return formation


def test_learner_reaches_every_formation_they_are_enrolled_in(learner, promotion, second_formation):
    Enrollment.objects.create(user=learner, formation=promotion.formation, promotion=promotion)
    Enrollment.objects.create(user=learner, formation=second_formation)

    assert set(accessible_formations(learner).values_list("slug", flat=True)) == {"compta", "elec"}


def test_learner_without_enrollment_reaches_no_formation(learner, partie):
    assert not accessible_formations(learner).exists()


def test_learner_sees_the_promotions_of_their_enrollments_only(learner, promotion):
    Promotion.objects.create(name="Autre", formation=promotion.formation)
    Enrollment.objects.create(user=learner, formation=promotion.formation, promotion=promotion)

    assert list(Promotion.objects.visible_to(learner)) == [promotion]


def test_dashboard_lists_the_parts_of_every_enrolled_formation(client, learner, partie, second_formation):
    Enrollment.objects.create(user=learner, formation=partie.formation)
    Enrollment.objects.create(user=learner, formation=second_formation)
    client.force_login(learner)

    response = client.get("/fr/")

    titles = [row["partie"].title for row in response.context["parts"]]
    assert titles == ["Habilitation et sécurité", "Bases"]


def test_csv_import_enrolls_learners_in_the_promotion(promotion):
    from accounts.importing import import_learners

    import_learners("username;first_name\nali;Ali\n", promotion)

    enrollment = Enrollment.objects.get(user__username="ali")
    assert (enrollment.formation, enrollment.promotion, enrollment.source) == (
        promotion.formation, promotion, Enrollment.Source.IMPORT,
    )
    assert User.objects.get(username="ali").role == User.Role.LEARNER


def test_non_enrolled_learner_is_sent_to_the_catalogue_page_of_an_open_formation(client, learner, module):
    module.partie.formation.is_open = True
    module.partie.formation.save()
    client.force_login(learner)

    response = client.get(f"/fr/modules/{module.public_id}/")

    assert response.status_code == 302
    assert response["Location"] == f"/fr/catalogue/{module.partie.formation.public_id}/"


def test_non_enrolled_learner_gets_not_found_for_a_closed_formation(client, learner, module):
    client.force_login(learner)

    assert client.get(f"/fr/modules/{module.public_id}/").status_code == 404
