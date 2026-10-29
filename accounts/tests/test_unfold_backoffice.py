"""US-34 : back-office Django Unfold (formations, promotions et codes). US-36 : groupe ouvert. US-33 : paires en ligne."""
import re

import pytest

from accounts.models import Promotion, User
from catalog.models import Enrollment
from conftest import enroll
from courses.models import Formation


def make(username, role):
    return User.objects.create_user(username=username, password="x-Secret-123", role=role)


@pytest.fixture
def admin_client(client):
    client.force_login(make("chef", User.Role.ADMIN))
    return client


@pytest.mark.django_db
def test_back_office_is_rendered_by_unfold(admin_client):
    response = admin_client.get("/fr/admin/")

    assert response.status_code == 200
    assert any(t.name.startswith("unfold/") for t in response.templates)


@pytest.mark.django_db
def test_back_office_pages_run_no_inline_script(admin_client, promotion):
    for url in ("/fr/admin/", "/fr/admin/accounts/promotion/", f"/fr/admin/accounts/promotion/{promotion.pk}/change/"):
        html = admin_client.get(url).content.decode()
        for tag in re.findall(r"<script\b[^>]*>", html):
            assert "src=" in tag or "application/json" in tag, f"script en ligne dans {url} : {tag}"


@pytest.mark.django_db
def test_promotion_page_shows_its_join_code(admin_client, promotion):
    html = admin_client.get(f"/fr/admin/accounts/promotion/{promotion.pk}/change/").content.decode()

    assert promotion.join_code in html


@pytest.mark.django_db
def test_admin_action_regenerates_join_codes(admin_client, promotion):
    old = promotion.join_code

    admin_client.post("/fr/admin/accounts/promotion/", {
        "action": "regenerate_join_codes", "_selected_action": [promotion.pk],
    })

    promotion.refresh_from_db()
    assert promotion.join_code != old


@pytest.mark.django_db
def test_admin_can_deactivate_a_join_code(admin_client, promotion):
    admin_client.post("/fr/admin/accounts/promotion/", {
        "action": "deactivate_join_codes", "_selected_action": [promotion.pk],
    })

    promotion.refresh_from_db()
    assert not promotion.join_code_active


@pytest.mark.django_db
def test_formations_can_be_filtered_by_catalogue_opening(admin_client, partie):
    Formation.objects.create(title_fr="Ouverte", slug="ouverte", is_open=True)

    response = admin_client.get("/fr/admin/courses/formation/?is_open__exact=1")

    assert [f.slug for f in response.context["cl"].result_list] == ["ouverte"]


@pytest.mark.django_db
def test_open_group_lists_learners_without_promotion(admin_client, learner, promotion):
    free = make("libre", User.Role.LEARNER)
    Enrollment.objects.create(user=free, formation=promotion.formation, source="catalog")
    enroll(learner, promotion)

    response = admin_client.get("/fr/admin/catalog/enrollment/?promotion__isnull=True")

    assert [e.user.username for e in response.context["cl"].result_list] == ["libre"]


@pytest.mark.django_db
def test_trainer_edits_matching_pairs_inline(client, module, question_factory):
    question = question_factory(module, publish=False)
    client.force_login(make("macaire", User.Role.TRAINER))

    html = client.get(f"/fr/admin/assessments/question/{question.pk}/change/").content.decode()

    assert 'name="pairs-TOTAL_FORMS"' in html


@pytest.mark.django_db
def test_trainer_still_cannot_manage_promotions(client, promotion):
    client.force_login(make("macaire", User.Role.TRAINER))

    assert client.get("/fr/admin/accounts/promotion/").status_code == 403


@pytest.mark.django_db
def test_only_the_back_office_allows_alpine_evaluation(admin_client):
    admin_csp = admin_client.get("/fr/admin/")["Content-Security-Policy"]
    site_csp = admin_client.get("/fr/catalogue/")["Content-Security-Policy"]

    assert "'unsafe-eval'" in admin_csp  # Alpine.js d'Unfold évalue ses expressions (new Function)
    assert "'unsafe-eval'" not in site_csp
    assert "'unsafe-inline'" not in admin_csp.split("script-src")[1].split(";")[0]
