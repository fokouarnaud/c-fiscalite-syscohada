"""US-02 : inscription vérifiée par e-mail. US-03 : piège à robots et limite par IP. US-04 : purge des comptes non
vérifiés. US-09 : mot de passe oublié par e-mail."""
import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from accounts.models import SignupThrottle, User
from accounts.signup import purge_unverified_accounts, reset_maintenance


@pytest.fixture(autouse=True)
def fresh_maintenance_clock():
    reset_maintenance()
    yield
    reset_maintenance()

PASSWORD = "Ohm-Kirchhoff-2026"
FORM = {
    "username": "nadia", "email": "nadia@example.cm", "first_name": "Nadia", "last_name": "Ewane",
    "password1": PASSWORD, "password2": PASSWORD, "website": "",
}


def signup(client, **overrides):
    return client.post("/fr/inscription/", {**FORM, **overrides}, REMOTE_ADDR="203.0.113.7")


def verification_link():
    return re.search(r"https?://[^\s]+/verifier/[^\s]+/", mail.outbox[-1].body).group(0)


# --- US-02 -------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_signup_creates_an_inactive_learner_and_emails_a_verification_link(client):
    response = signup(client)

    assert response.status_code == 302
    user = User.objects.get(username="nadia")
    assert (user.is_active, user.email_verified, user.role) == (False, False, User.Role.LEARNER)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["nadia@example.cm"]
    assert "/fr/inscription/verifier/" in verification_link()


@pytest.mark.django_db
def test_unverified_account_cannot_log_in(client):
    signup(client)

    client.post("/fr/connexion/", {"username": "nadia", "password": PASSWORD})

    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_verification_link_activates_the_account(client):
    signup(client)

    response = client.get(verification_link())

    assert response.status_code == 302
    user = User.objects.get(username="nadia")
    assert (user.is_active, user.email_verified) == (True, True)
    client.post("/fr/connexion/", {"username": "nadia", "password": PASSWORD})
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_verification_link_works_only_once(client):
    signup(client)
    link = verification_link()
    client.get(link)
    User.objects.filter(username="nadia").update(is_active=False)

    response = client.get(link)

    assert response.status_code == 400
    assert not User.objects.get(username="nadia").is_active


@pytest.mark.django_db
def test_tampered_verification_link_is_rejected(client):
    signup(client)

    response = client.get(verification_link().replace("/verifier/", "/verifier/x"))

    assert response.status_code == 400
    assert not User.objects.get(username="nadia").is_active


@pytest.mark.django_db
def test_email_already_used_is_refused_case_insensitively(client):
    User.objects.create_user(username="awa", password=PASSWORD, email="Nadia@Example.cm")

    response = signup(client)

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert not User.objects.filter(username="nadia").exists()


@pytest.mark.django_db
def test_signup_requires_first_and_last_name(client):
    response = signup(client, first_name="", last_name="")

    assert {"first_name", "last_name"} <= set(response.context["form"].errors)


# --- US-03 -------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_filled_honeypot_looks_successful_but_creates_nothing(client):
    response = signup(client, website="https://spam.example")

    assert response.status_code == 302
    assert not User.objects.exists()
    assert mail.outbox == []


@pytest.mark.django_db
def test_an_ip_is_blocked_after_the_hourly_signup_limit(client, settings):
    settings.SIGNUP_MAX_PER_HOUR = 2
    signup(client, username="a1", email="a1@example.cm")
    signup(client, username="a2", email="a2@example.cm")

    response = signup(client, username="a3", email="a3@example.cm")

    assert response.status_code == 429
    assert not User.objects.filter(username="a3").exists()


@pytest.mark.django_db
def test_signup_limit_is_per_ip(client, settings):
    settings.SIGNUP_MAX_PER_HOUR = 1
    signup(client, username="a1", email="a1@example.cm")

    response = client.post("/fr/inscription/", {**FORM, "username": "b1", "email": "b1@example.cm"}, REMOTE_ADDR="198.51.100.4")

    assert response.status_code == 302


@pytest.mark.django_db
def test_signup_limit_forgets_attempts_older_than_an_hour(client, settings):
    settings.SIGNUP_MAX_PER_HOUR = 1
    signup(client, username="a1", email="a1@example.cm")
    SignupThrottle.objects.update(created_at=timezone.now() - timedelta(minutes=61))

    assert signup(client, username="a2", email="a2@example.cm").status_code == 302


@pytest.mark.django_db
def test_ip_address_is_never_stored_in_clear(client):
    signup(client)

    assert "203.0.113.7" not in SignupThrottle.objects.get().ip_hash


# --- US-04 -------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_purge_removes_unverified_accounts_older_than_seven_days():
    now = timezone.now()
    old = User.objects.create_user(username="old", password=PASSWORD, is_active=False)
    User.objects.filter(pk=old.pk).update(date_joined=now - timedelta(days=7, minutes=1))
    User.objects.create_user(username="recent", password=PASSWORD, is_active=False)

    assert purge_unverified_accounts(now) == 1
    assert list(User.objects.values_list("username", flat=True)) == ["recent"]


@pytest.mark.django_db
def test_purge_keeps_accounts_created_by_the_centre_even_without_verified_email():
    now = timezone.now()
    imported = User.objects.create_user(username="imported", password=PASSWORD)  # actif, créé par l'admin
    disabled = User.objects.create_user(username="disabled", password=PASSWORD, email_verified=True, is_active=False)
    User.objects.filter(pk__in=[imported.pk, disabled.pk]).update(date_joined=now - timedelta(days=30))

    assert purge_unverified_accounts(now) == 0


@pytest.mark.django_db
def test_daily_maintenance_purges_unverified_accounts(rf):
    from progress.middleware import DailyBackupMiddleware

    old = User.objects.create_user(username="old", password=PASSWORD, is_active=False)
    User.objects.filter(pk=old.pk).update(date_joined=timezone.now() - timedelta(days=8))

    DailyBackupMiddleware(lambda request: None)(rf.get("/"))

    assert not User.objects.filter(username="old").exists()


# --- US-09 -------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_password_reset_emails_a_link_to_a_known_address(client):
    User.objects.create_user(username="awa", password=PASSWORD, email="awa@example.cm")

    response = client.post("/fr/mot-de-passe/", {"email": "awa@example.cm"})

    assert response.status_code == 302
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_password_reset_does_not_reveal_unknown_addresses(client):
    known = client.post("/fr/mot-de-passe/", {"email": "nobody@example.cm"})

    assert known.status_code == 302
    assert mail.outbox == []


@pytest.mark.django_db
def test_password_reset_link_sets_a_new_password(client):
    User.objects.create_user(username="awa", password=PASSWORD, email="awa@example.cm")
    client.post("/fr/mot-de-passe/", {"email": "awa@example.cm"})
    link = re.search(r"https?://[^\s]+/mot-de-passe/[^\s]+/", mail.outbox[0].body).group(0)

    form_url = client.get(link)["Location"]
    client.post(form_url, {"new_password1": "Nouveau-Mot-2026", "new_password2": "Nouveau-Mot-2026"})

    assert User.objects.get(username="awa").check_password("Nouveau-Mot-2026")


@pytest.mark.django_db
def test_us03_password_reset_page_sends_accounts_without_email_to_their_trainer(client):
    """US-03 : un compte sans e-mail est renvoyé vers son formateur."""
    body = client.get("/fr/mot-de-passe/").content.decode()

    assert "Demandez un nouveau mot de passe à votre formateur." in body


class BrokenMailBackend:
    """Serveur SMTP qui refuse l'authentification, comme Gmail sans mot de passe d'application valide."""

    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, messages):
        import smtplib

        raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")


@pytest.mark.django_db
def test_us01_signup_says_when_the_verification_email_could_not_be_sent(client, settings, caplog):
    """US-01 : un envoi refusé n'annonce pas « Vérifiez vos e-mails » ; le compte en attente est retiré pour réessayer,
    et l'erreur est journalisée pour l'administrateur."""
    settings.EMAIL_BACKEND = "accounts.tests.test_signup.BrokenMailBackend"

    response = signup(client)

    assert response.status_code == 200
    import html

    assert "L'e-mail de confirmation n'a pas pu être envoyé" in html.unescape(response.content.decode())
    assert not User.objects.filter(username="nadia").exists()
    assert any(r.levelname == "ERROR" and "nadia@example.cm" in r.getMessage() for r in caplog.records)
