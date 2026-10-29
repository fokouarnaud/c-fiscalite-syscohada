"""Tests d'intrusion : chaque test rejoue une attaque et vérifie qu'elle échoue.

Familles couvertes (AGENTS.md, Definition of Done, point 4) :
- injection SQL par les URL, les formulaires et la connexion ;
- XSS stocké (Markdown, énoncés, titres, images SVG) et injection de formules CSV ;
- gestion de session (cookies, durée, déconnexion, force brute, clé secrète) ;
- énumération et déduction des données (identifiants publics UUID, fichiers téléversés) ;
- CSRF sur les actions qui modifient l'état.
"""
import csv
import io
import os
import re
import subprocess
import sys
import uuid

import pytest

from conftest import enroll
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from accounts.models import Promotion, User
from assessments.models import Assessment, Attempt, Choice, Question
from assessments.services import start_attempt
from courses.models import Annexe, Formation, Module, Partie, Section
from courses.rendering import render_markdown
from progress.models import SectionView

PASSWORD = "x-Secret-123"
STRONG_KEY = "k8#Zy8q!vR2@pL7$wN4%tB9^mC" * 3


@pytest.fixture
def quiz_question(module, question_factory):
    Section.objects.create(module=module, title_fr="Cours", order=1)
    return question_factory(module)


@pytest.fixture
def attempt(enrolled, module, quiz_question):
    return start_attempt(enrolled, Assessment.quiz_for(module))


@pytest.fixture
def intruder(partie):
    """Apprenant d'une autre promotion de la même formation."""
    other = Promotion.objects.create(name="Jan 2027", formation=partie.formation)
    return enroll(User.objects.create_user(username="mallory", password=PASSWORD), other)


def answer_url(attempt):
    return f"/fr/tentatives/{attempt.public_id}/reponse/"


# --- Énumération et déduction des données (UUID) ----------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("model", [Formation, Partie, Module, Section, Question, Choice, Attempt])
def test_every_exposed_model_has_a_random_public_uuid(model):
    field = model._meta.get_field("public_id")
    assert field.unique and not field.editable
    assert isinstance(field.default(), uuid.UUID) and field.default().version == 4


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["/fr/modules/1/", "/fr/sections/1/", "/fr/examen/1/", "/fr/tentatives/1/", "/fr/tentatives/1/resultat/"])
def test_sequential_integer_urls_no_longer_exist(client, enrolled, attempt, url):
    client.force_login(enrolled)
    assert client.get(url).status_code == 404


@pytest.mark.django_db
def test_pages_never_reveal_database_ids(client, enrolled, attempt, module, partie, quiz_question):
    client.force_login(enrolled)
    pages = [
        "/fr/",
        f"/fr/modules/{module.public_id}/",
        f"/fr/sections/{module.sections.first().public_id}/",
        f"/fr/examen/{partie.public_id}/",
        f"/fr/tentatives/{attempt.public_id}/",
    ]
    for url in pages:
        html = client.get(url).content.decode()
        assert not re.search(r'(?:href|action|hx-post)="[^"]*/(?:modules|sections|examen|quiz|tentatives)/\d+/', html), url
        assert not re.search(r'\b(?:id|aria-labelledby)="(?:q|partie|examen|f)-\d+"', html), url
    attempt_html = client.get(f"/fr/tentatives/{attempt.public_id}/").content.decode()
    for choice in quiz_question.choices.all():
        assert f'value="{choice.pk}"' not in attempt_html
        assert f'value="{choice.public_id}"' in attempt_html


@pytest.mark.django_db
def test_another_learners_attempt_is_invisible_even_with_its_uuid(client, intruder, attempt):
    client.force_login(intruder)
    for suffix in ("", "resultat/"):
        assert client.get(f"/fr/tentatives/{attempt.public_id}/{suffix}").status_code == 404
    assert client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/").status_code == 404
    assert client.post(answer_url(attempt), {"question": "x"}).status_code == 404
    attempt.refresh_from_db()
    assert attempt.submitted_at is None


@pytest.mark.django_db
def test_content_of_another_formation_is_invisible_even_with_its_uuid(client, enrolled):
    other = Formation.objects.create(title_fr="Électronique", slug="elec")
    partie = Partie.objects.create(formation=other, title_fr="P", order=1, slug="p")
    module = Module.objects.create(partie=partie, title_fr="M", order=1)
    section = Section.objects.create(module=module, title_fr="Secret", order=1)
    client.force_login(enrolled)
    assert client.get(f"/fr/modules/{module.public_id}/").status_code == 404
    assert client.get(f"/fr/sections/{section.public_id}/").status_code == 404
    assert client.get(f"/fr/examen/{partie.public_id}/").status_code == 404
    assert client.post(f"/fr/quiz/{module.public_id}/").status_code == 404


@pytest.mark.django_db
def test_uploaded_files_get_unguessable_names(module):
    section = Section.objects.create(module=module, title_fr="TAF", order=1, kind=Section.Kind.PRACTICAL)
    field = Annexe._meta.get_field("file")
    name = field.generate_filename(Annexe(section=section), "Fiche client Dupont.PDF").replace("\\", "/")
    assert re.fullmatch(r"annexes/[0-9a-f]{32}\.pdf", name)
    image_name = Question._meta.get_field("image").generate_filename(Question(), "schéma.svg").replace("\\", "/")
    assert re.fullmatch(r"questions/[0-9a-f]{32}\.svg", image_name)


# --- Injection SQL --------------------------------------------------------------------------------------------------


SQL_PAYLOADS = ["1 OR 1=1", "1; DROP TABLE accounts_user;--", "' OR '1'='1", "1 UNION SELECT password FROM accounts_user"]


@pytest.mark.django_db
@pytest.mark.parametrize("payload", SQL_PAYLOADS)
def test_sql_injection_in_url_paths_is_rejected_by_the_router(client, enrolled, payload):
    client.force_login(enrolled)
    for prefix in ("modules", "sections", "examen", "tentatives"):
        assert client.get(f"/fr/{prefix}/{payload}/").status_code == 404
    assert User.objects.filter(username="awa").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("payload", SQL_PAYLOADS)
def test_sql_injection_in_answer_fields_is_a_clean_400(client, enrolled, attempt, quiz_question, payload):
    client.force_login(enrolled)
    assert client.post(answer_url(attempt), {"question": payload}).status_code == 400
    response = client.post(answer_url(attempt), {"question": str(quiz_question.public_id), "choices": [payload]})
    assert response.status_code == 400
    assert not attempt.attempt_questions.get().selected_choices.exists()


@pytest.mark.django_db
def test_answer_without_question_or_with_a_foreign_question_is_refused(client, enrolled, attempt, module, question_factory):
    client.force_login(enrolled)
    assert client.post(answer_url(attempt), {}).status_code == 400
    outside = question_factory(module)  # publiée après le tirage : absente de la tentative
    assert client.post(answer_url(attempt), {"question": str(outside.public_id)}).status_code == 404


@pytest.mark.django_db
def test_choices_of_another_question_are_ignored(client, enrolled, attempt, quiz_question, module, question_factory):
    other = question_factory(module)
    client.force_login(enrolled)
    foreign = [str(c.public_id) for c in other.choices.all()]
    assert client.post(answer_url(attempt), {"question": str(quiz_question.public_id), "choices": foreign}).status_code == 302
    assert not attempt.attempt_questions.get(question=quiz_question).selected_choices.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("username", ["awa' OR '1'='1", "awa'--", "' OR 1=1 --"])
def test_sql_injection_in_login_does_not_authenticate(client, learner, username):
    response = client.post("/fr/connexion/", {"username": username, "password": "' OR '1'='1"})
    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


# --- XSS -----------------------------------------------------------------------------------------------------------


XSS_MARKDOWN = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "[clic](javascript:alert(1))",
    "<a href=\"javascript:alert(1)\">clic</a>",
    "<iframe src=\"https://evil.example\"></iframe>",
    "<svg onload=alert(1)>",
    "![x](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)",
    "<p style=\"background:url(javascript:alert(1))\">x</p>",
]


@pytest.mark.parametrize("payload", XSS_MARKDOWN)
def test_markdown_rendering_strips_active_content(payload):
    html = render_markdown(payload).lower()
    for marker in ("<script", "onerror", "onload", "javascript:", "<iframe", "<svg", "data:text/html", "style="):
        assert marker not in html


@pytest.mark.django_db
def test_section_page_never_executes_injected_markdown(client, enrolled, module):
    section = Section.objects.create(module=module, title_fr="T", order=1, body_md_fr="<script>alert('xss')</script>")
    client.force_login(enrolled)
    html = client.get(f"/fr/sections/{section.public_id}/").content.decode()
    assert "<script>alert('xss')</script>" not in html


@pytest.mark.django_db
def test_titles_prompts_and_choices_are_escaped(client, enrolled, partie, module, question_factory):
    evil = "<img src=x onerror=alert(1)>"
    module.title_fr = evil
    module.save()
    partie.title_fr = evil
    partie.save()
    Section.objects.create(module=module, title_fr=evil, order=1)
    question = question_factory(module, choices=((True, evil), (False, "Non")))
    question.prompt_fr = evil
    question.save()
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)
    for url in ("/fr/", f"/fr/modules/{module.public_id}/", f"/fr/tentatives/{attempt.public_id}/"):
        html = client.get(url).content.decode()
        assert evil not in html, url
        assert "&lt;img src=x onerror=alert(1)&gt;" in html, url


@pytest.mark.parametrize("svg", [
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"><text>x</text></a></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><body xmlns="http://www.w3.org/1999/xhtml"/></foreignObject></svg>',
    b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg>&x;</svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><SCRIPT>alert(1)</SCRIPT></svg>',
])
def test_question_image_rejects_active_svg(svg):
    field = Question._meta.get_field("image")
    with pytest.raises(ValidationError):
        field.run_validators(SimpleUploadedFile("schema.svg", svg, content_type="image/svg+xml"))


def test_question_image_accepts_a_plain_svg():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="#0b2d46"/></svg>'
    Question._meta.get_field("image").run_validators(SimpleUploadedFile("schema.svg", svg, content_type="image/svg+xml"))


@pytest.mark.django_db
def test_content_security_policy_blocks_inline_and_foreign_scripts(client, learner):
    response = client.get("/fr/connexion/")
    policy = response["Content-Security-Policy"]
    directives = dict(d.strip().split(" ", 1) for d in policy.split(";") if d.strip())
    assert directives["default-src"] == "'self'"
    assert directives["script-src"] == "'self'"
    assert directives["object-src"] == "'none'"
    assert directives["frame-ancestors"] == "'none'"
    assert directives["base-uri"] == "'self'"
    assert directives["form-action"] == "'self'"
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"


@pytest.mark.django_db
def test_no_inline_script_in_rendered_pages(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    pages = ("/fr/connexion/", "/fr/admin/login/", "/fr/", f"/fr/modules/{module.public_id}/", f"/fr/sections/{module.sections.first().public_id}/")
    for url in pages:
        html = client.get(url).content.decode()
        for tag in re.findall(r"<script\b[^>]*>", html):
            assert "src=" in tag, f"script en ligne dans {url}"
        assert not re.search(r"\son[a-z]+=", html), url


@pytest.mark.django_db
def test_csv_export_neutralises_formula_injection(client, promotion):
    trainer = User.objects.create_user(username="macaire", password=PASSWORD, role=User.Role.TRAINER)
    promotion.trainers.add(trainer)
    enroll(User.objects.create_user(
        username="eve", password=PASSWORD,
        first_name="=HYPERLINK(\"https://evil.example\",\"x\")", last_name="+cmd|' /C calc'!A0",
    ), promotion)
    client.force_login(trainer)
    content = client.get("/fr/formateur/export.csv").content.decode("utf-8-sig")
    cells = [cell for row in csv.reader(io.StringIO(content), delimiter=";") for cell in row]
    assert all(not cell or cell[0] not in "=+-@\t\r" for cell in cells)
    assert any(cell.startswith("'=HYPERLINK") for cell in cells)


# --- CSRF et méthodes HTTP ------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_starting_a_quiz_requires_post(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    assert client.get(f"/fr/quiz/{module.public_id}/").status_code == 405
    assert not Attempt.objects.exists()


@pytest.mark.django_db
def test_state_changing_requests_without_csrf_token_are_refused(enrolled, attempt, module, quiz_question):
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(enrolled)
    choice = quiz_question.choices.first()
    assert browser.post(f"/fr/quiz/{module.public_id}/").status_code == 403
    assert browser.post(answer_url(attempt), {"question": str(quiz_question.public_id), "choices": [str(choice.public_id)]}).status_code == 403
    assert browser.post(f"/fr/tentatives/{attempt.public_id}/envoyer/").status_code == 403
    attempt.refresh_from_db()
    assert attempt.submitted_at is None


# --- Session --------------------------------------------------------------------------------------------------------


def test_session_and_csrf_cookies_are_hardened():
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.SESSION_COOKIE_AGE <= 8 * 3600


@pytest.mark.django_db
def test_login_rotates_the_session_key(client, learner):
    client.get("/fr/connexion/")
    session = client.session
    session["marker"] = "avant"
    session.save()
    before = session.session_key
    client.post("/fr/connexion/", {"username": "awa", "password": PASSWORD})
    assert client.session.session_key != before


@pytest.mark.django_db
def test_logout_requires_post_and_destroys_the_session(client, learner):
    client.force_login(learner)
    assert client.get("/fr/deconnexion/").status_code == 405
    key = client.session.session_key
    client.post("/fr/deconnexion/")
    from django.contrib.sessions.models import Session

    assert not Session.objects.filter(session_key=key).exists()
    assert client.get("/fr/").status_code == 302


@pytest.mark.django_db
def test_password_change_invalidates_other_sessions(client, learner):
    client.force_login(learner)
    learner.set_password("n0uveau-Secret-456")
    learner.save()
    assert client.get("/fr/").status_code == 302


@pytest.mark.django_db
def test_brute_force_locks_the_account_after_five_failures(client, learner):
    for _ in range(settings.LOGIN_MAX_FAILURES):
        client.post("/fr/connexion/", {"username": "awa", "password": "mauvais"})
    response = client.post("/fr/connexion/", {"username": "awa", "password": PASSWORD})
    assert not response.wsgi_request.user.is_authenticated
    assert "Trop de tentatives" in response.content.decode()


@pytest.mark.django_db
def test_lockout_does_not_reveal_whether_the_username_exists(client):
    for _ in range(settings.LOGIN_MAX_FAILURES + 1):
        response = client.post("/fr/connexion/", {"username": "fantome", "password": "mauvais"})
    assert "Trop de tentatives" in response.content.decode()


@pytest.mark.django_db
def test_lockout_expires_and_success_resets_the_counter(client, learner, settings):
    from accounts.models import LoginFailure

    for _ in range(settings.LOGIN_MAX_FAILURES):
        client.post("/fr/connexion/", {"username": "awa", "password": "mauvais"})
    LoginFailure.objects.update(created_at=LoginFailure.objects.first().created_at - settings.LOGIN_LOCKOUT)
    assert client.post("/fr/connexion/", {"username": "AWA ", "password": "mauvais"}).status_code == 200
    response = client.post("/fr/connexion/", {"username": "awa", "password": PASSWORD})
    assert response.status_code == 302
    assert not LoginFailure.objects.filter(username="awa").exists()


@pytest.mark.django_db
def test_lockout_of_one_user_does_not_block_another(client, learner, intruder):
    for _ in range(settings.LOGIN_MAX_FAILURES):
        client.post("/fr/connexion/", {"username": "awa", "password": "mauvais"})
    assert client.post("/fr/connexion/", {"username": "mallory", "password": PASSWORD}).status_code == 302


def _production_env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    return {**env, "DJANGO_DEBUG": "0", "DJANGO_ALLOWED_HOSTS": "acad.example", **extra}


def test_production_refuses_to_start_without_a_strong_secret_key():
    for key in ("", "dev-insecure-key-ne-pas-utiliser-en-production", "court", "s" * 60):
        result = subprocess.run(
            [sys.executable, "manage.py", "check"], cwd=settings.BASE_DIR,
            env=_production_env(DJANGO_SECRET_KEY=key), capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "DJANGO_SECRET_KEY" in result.stderr


def test_production_settings_pass_the_deploy_check_without_warnings():
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"], cwd=settings.BASE_DIR,
        env=_production_env(DJANGO_SECRET_KEY=STRONG_KEY),
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_production_cookies_use_host_prefixes():
    code = (
        "from django.conf import settings as s;"
        "print(s.SESSION_COOKIE_NAME, s.CSRF_COOKIE_NAME, s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.SECURE_HSTS_SECONDS)"
    )
    result = subprocess.run(
        [sys.executable, "-c", f"import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings');django.setup();{code}"],
        cwd=settings.BASE_DIR, env=_production_env(DJANGO_SECRET_KEY=STRONG_KEY), capture_output=True, text=True, check=True,
    )
    session_name, csrf_name, session_secure, csrf_secure, hsts = result.stdout.split()
    assert session_name.startswith("__Host-") and csrf_name.startswith("__Host-")
    assert session_secure == csrf_secure == "True"
    assert int(hsts) >= 31536000
