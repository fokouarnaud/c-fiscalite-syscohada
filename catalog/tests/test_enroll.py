"""US-05 : inscription libre à une formation ouverte. US-06 : rejoindre une promotion avec son code."""
import pytest

from accounts.models import Promotion, User
from catalog.models import Enrollment
from courses.models import Formation


@pytest.fixture
def open_formation(partie):
    partie.formation.is_open = True
    partie.formation.save()
    return partie.formation


def enroll_url(formation):
    return f"/fr/catalogue/{formation.public_id}/inscription/"


# --- US-05 : inscription libre ----------------------------------------------------------------------------------------


def test_learner_enrolls_in_an_open_formation_in_the_open_group(client, learner, open_formation):
    client.force_login(learner)

    response = client.post(enroll_url(open_formation))

    assert response.status_code == 302
    enrollment = Enrollment.objects.get(user=learner)
    assert (enrollment.formation, enrollment.promotion, enrollment.source) == (open_formation, None, "catalog")


def test_enrolling_twice_keeps_a_single_enrollment(client, learner, open_formation):
    client.force_login(learner)
    client.post(enroll_url(open_formation))
    client.post(enroll_url(open_formation))

    assert Enrollment.objects.filter(user=learner).count() == 1


def test_closed_formation_refuses_free_enrollment(client, learner, partie):
    client.force_login(learner)

    assert client.post(enroll_url(partie.formation)).status_code == 404
    assert not Enrollment.objects.exists()


def test_anonymous_visitor_is_sent_to_login_before_enrolling(client, open_formation):
    response = client.post(enroll_url(open_formation))

    assert response.status_code == 302 and "/connexion/" in response["Location"]
    assert not Enrollment.objects.exists()


def test_enrollment_requires_a_post(client, learner, open_formation):
    client.force_login(learner)

    assert client.get(enroll_url(open_formation)).status_code == 405


def test_trainer_cannot_enroll_as_a_learner(client, open_formation):
    trainer = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    client.force_login(trainer)

    assert client.post(enroll_url(open_formation)).status_code == 403
    assert not Enrollment.objects.exists()


# --- US-06 : code de promotion ----------------------------------------------------------------------------------------

AMBIGUOUS = set("0O1IL")


def test_new_promotion_receives_an_unambiguous_eight_character_code(promotion):
    assert len(promotion.join_code) == 8
    assert not AMBIGUOUS & set(promotion.join_code)
    assert promotion.join_code_active


def test_two_promotions_never_share_a_code(partie):
    a = Promotion.objects.create(name="A", formation=partie.formation)
    b = Promotion.objects.create(name="B", formation=partie.formation)

    assert a.join_code != b.join_code


def test_regenerating_the_code_invalidates_the_old_one(promotion):
    old = promotion.join_code

    promotion.regenerate_join_code()

    promotion.refresh_from_db()
    assert promotion.join_code != old


def test_learner_joins_a_promotion_with_its_code(client, learner, promotion):
    client.force_login(learner)

    response = client.post("/fr/rejoindre/", {"code": f"  {promotion.join_code.lower()} "})

    assert response.status_code == 302
    enrollment = Enrollment.objects.get(user=learner)
    assert (enrollment.formation, enrollment.promotion, enrollment.source) == (promotion.formation, promotion, "code")


def test_joining_moves_an_open_group_learner_into_the_promotion(client, learner, promotion):
    Enrollment.objects.create(user=learner, formation=promotion.formation, source="catalog")
    client.force_login(learner)

    client.post("/fr/rejoindre/", {"code": promotion.join_code})

    assert Enrollment.objects.get(user=learner).promotion == promotion


def test_unknown_code_is_refused(client, learner, promotion):
    client.force_login(learner)

    response = client.post("/fr/rejoindre/", {"code": "ZZZZZZZZ"})

    assert response.status_code == 200
    assert response.context["form"].errors
    assert not Enrollment.objects.exists()


def test_deactivated_code_is_refused(client, learner, promotion):
    promotion.join_code_active = False
    promotion.save()
    client.force_login(learner)

    response = client.post("/fr/rejoindre/", {"code": promotion.join_code})

    assert response.context["form"].errors
    assert not Enrollment.objects.exists()


def test_join_code_works_even_for_a_closed_formation(client, learner, promotion):
    assert not Formation.objects.get(pk=promotion.formation_id).is_open
    client.force_login(learner)

    client.post("/fr/rejoindre/", {"code": promotion.join_code})

    assert Enrollment.objects.filter(user=learner, promotion=promotion).exists()
