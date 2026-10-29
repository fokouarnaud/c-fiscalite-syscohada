"""US-03 : le lien de mot de passe oublié est valable 24 h, pas davantage."""
from datetime import datetime, timedelta

import pytest
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator

from accounts.models import User

ISSUED = datetime(2026, 10, 28, 8, 0)


@pytest.fixture
def token_at(monkeypatch):
    def at(moment):
        monkeypatch.setattr(PasswordResetTokenGenerator, "_now", lambda self: moment)
    return at


@pytest.mark.django_db
@pytest.mark.parametrize("hours, valid", [(23, True), (25, False)])
def test_the_reset_link_expires_after_twenty_four_hours(token_at, hours, valid):
    user = User.objects.create_user(username="awa", password="x-Secret-123", email="awa@example.org")
    token_at(ISSUED)
    token = default_token_generator.make_token(user)

    token_at(ISSUED + timedelta(hours=hours))

    assert default_token_generator.check_token(user, token) is valid
