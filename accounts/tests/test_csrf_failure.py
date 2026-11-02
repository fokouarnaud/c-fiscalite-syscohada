"""US-02 : un formulaire de connexion resoumis après une connexion réussie ne bloque pas l'utilisateur.

Constat en production (2026-11-02) : la connexion réussit (302), Django renouvelle le jeton CSRF, puis la même
page, resoumise (double clic ou retour arrière), reçoit la page 403 brute de Django « CSRF verification failed ».
"""
import pytest
from django.test import Client


def stale_login_post(client, lang="en", next_url="/en/"):
    return client.post(f"/{lang}/connexion/?next={next_url}",
                       {"username": "awa", "password": "x-Secret-123", "next": next_url,
                        "csrfmiddlewaretoken": "jeton-perime"})


@pytest.mark.django_db
def test_us02_a_signed_in_user_resubmitting_the_login_form_goes_on_to_next(learner):
    client = Client(enforce_csrf_checks=True)
    client.force_login(learner)

    response = stale_login_post(client)

    assert response.status_code == 302 and response.url == "/en/"


@pytest.mark.django_db
def test_us02_the_redirect_after_a_stale_login_form_never_leaves_the_site(learner):
    client = Client(enforce_csrf_checks=True)
    client.force_login(learner)

    response = stale_login_post(client, next_url="https://exemple.invalid/")

    assert response.status_code == 302 and response.url == "/en/"


@pytest.mark.django_db
def test_us02_a_signed_in_user_opening_the_login_page_goes_on_to_next(client, learner):
    client.force_login(learner)

    response = client.get("/fr/connexion/?next=/fr/catalogue/")

    assert response.status_code == 302 and response.url == "/fr/catalogue/"


@pytest.mark.django_db
@pytest.mark.parametrize("lang, text", [("fr", "La page a expiré"), ("en", "This page has expired")])
def test_us02_an_anonymous_csrf_failure_explains_how_to_recover(lang, text):
    client = Client(enforce_csrf_checks=True)

    response = stale_login_post(client, lang=lang, next_url=f"/{lang}/")

    body = response.content.decode()
    assert response.status_code == 403
    assert text in body and f'href="/{lang}/connexion/?next=/{lang}/"' in body
    assert "CSRF verification failed" not in body


@pytest.mark.django_db
def test_us02_a_csrf_failure_elsewhere_is_never_turned_into_a_redirect(learner):
    client = Client(enforce_csrf_checks=True)
    client.force_login(learner)

    response = client.post("/fr/deconnexion/", {"csrfmiddlewaretoken": "jeton-perime"})

    assert response.status_code == 403 and "La page a expiré" in response.content.decode()
