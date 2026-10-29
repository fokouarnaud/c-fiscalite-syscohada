import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from accounts.models import Promotion
from catalog.models import Enrollment
from courses.models import Formation


@pytest.fixture
def other_formation(db):
    return Formation.objects.create(title_fr="Électricité bâtiment", slug="elec")


def test_learner_can_follow_several_formations(learner, partie, other_formation):
    Enrollment.objects.create(user=learner, formation=partie.formation)
    Enrollment.objects.create(user=learner, formation=other_formation)

    assert set(learner.enrollments.values_list("formation__slug", flat=True)) == {"compta", "elec"}


def test_learner_cannot_enroll_twice_in_the_same_formation(learner, partie):
    Enrollment.objects.create(user=learner, formation=partie.formation)

    with pytest.raises(IntegrityError):
        Enrollment.objects.create(user=learner, formation=partie.formation)


def test_enrollment_without_promotion_belongs_to_the_open_group(learner, partie):
    enrollment = Enrollment.objects.create(user=learner, formation=partie.formation)

    assert enrollment.promotion is None
    assert enrollment.in_open_group


def test_promotion_must_belong_to_the_enrolled_formation(learner, partie, other_formation):
    foreign = Promotion.objects.create(name="Elec 2026", formation=other_formation)
    enrollment = Enrollment(user=learner, formation=partie.formation, promotion=foreign)

    with pytest.raises(ValidationError):
        enrollment.full_clean()
