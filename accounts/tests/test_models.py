import pytest

from accounts.models import User


@pytest.mark.django_db
def test_new_user_is_a_learner_by_default():
    user = User.objects.create_user(username="awa", password="x-Secret-123")
    assert user.role == "learner"
    assert user.is_learner
    assert not user.is_trainer
