import pytest

from conftest import enroll

from accounts.models import Promotion, User
from courses.models import Formation


@pytest.fixture
def formation():
    return Formation.objects.create(title_fr="Électronique", slug="electro")


def make_user(username, role):
    return User.objects.create_user(username=username, password="x-Secret-123", role=role)


@pytest.mark.django_db
def test_trainer_sees_only_promotions_they_are_attached_to(formation):
    trainer = make_user("macaire", User.Role.TRAINER)
    mine = Promotion.objects.create(name="Oct 2026", formation=formation)
    Promotion.objects.create(name="Jan 2027", formation=formation)
    mine.trainers.add(trainer)
    assert list(Promotion.objects.visible_to(trainer)) == [mine]


@pytest.mark.django_db
def test_admin_sees_every_promotion(formation):
    admin = make_user("chef", User.Role.ADMIN)
    Promotion.objects.create(name="Oct 2026", formation=formation)
    Promotion.objects.create(name="Jan 2027", formation=formation)
    assert Promotion.objects.visible_to(admin).count() == 2


@pytest.mark.django_db
def test_learner_sees_only_their_own_promotion(formation):
    mine = Promotion.objects.create(name="Oct 2026", formation=formation)
    Promotion.objects.create(name="Jan 2027", formation=formation)
    learner = enroll(User.objects.create_user(username="awa", password="x-Secret-123"), mine)
    assert list(Promotion.objects.visible_to(learner)) == [mine]


@pytest.mark.django_db
def test_learner_without_promotion_sees_nothing(formation):
    Promotion.objects.create(name="Oct 2026", formation=formation)
    learner = make_user("awa", User.Role.LEARNER)
    assert not Promotion.objects.visible_to(learner).exists()


@pytest.mark.django_db
def test_superuser_counts_as_admin(formation):
    Promotion.objects.create(name="Oct 2026", formation=formation)
    root = User.objects.create_superuser(username="root", password="x-Secret-123")
    assert Promotion.objects.visible_to(root).count() == 1
