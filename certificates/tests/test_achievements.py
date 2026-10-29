"""US-23 : badges. US-24 : certificat. US-25 : PDF réservé. US-26 : page publique de vérification."""
import uuid

import pytest
from django.utils import timezone

from accounts.models import User
from assessments.models import Assessment, Attempt
from assessments.services import save_answer, start_attempt, submit_attempt
from certificates.models import Badge, Certificate
from conftest import enroll
from courses.models import Section
from progress.services import mark_section_viewed


def answer_all(attempt, right):
    for aq in attempt.attempt_questions.select_related("question"):
        choices = aq.question.choices.filter(is_correct=right).values_list("public_id", flat=True)[:1 if not right else None]
        save_answer(attempt, aq.question.public_id, list(choices))


def complete_module(user, module):
    for section in Section.objects.filter(module=module):
        mark_section_viewed(user, section)
    attempt = start_attempt(user, Assessment.quiz_for(module))
    submit_attempt(attempt)


def take_exam(user, partie, right):
    attempt = start_attempt(user, Assessment.exam_for(partie))
    answer_all(attempt, right)
    return submit_attempt(attempt)


@pytest.fixture
def course(partie, module, question_factory):
    Section.objects.create(module=module, title_fr="Loi d'Ohm", order=1)
    question_factory(module)
    for _ in range(4):
        question_factory(module, usage="exam")
    Assessment.exam_for(partie)
    return partie


@pytest.fixture
def named(enrolled):
    enrolled.first_name, enrolled.last_name = "Awa", "Nkoulou"
    enrolled.save()
    return enrolled


# --- US-23 : badges ---------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_completing_a_module_awards_its_badge_once(named, course, module):
    complete_module(named, module)
    complete_module(named, module)

    assert list(Badge.objects.filter(user=named).values_list("kind", "module")) == [("module", module.pk)]


@pytest.mark.django_db
def test_reading_sections_without_the_quiz_awards_no_badge(named, course, module):
    for section in Section.objects.filter(module=module):
        mark_section_viewed(named, section)

    assert not Badge.objects.exists()


@pytest.mark.django_db
def test_passing_the_part_exam_awards_the_part_badge(named, course, module):
    complete_module(named, module)

    take_exam(named, course, right=True)

    assert Badge.objects.filter(user=named, kind="partie", partie=course).exists()


@pytest.mark.django_db
def test_failing_the_part_exam_awards_no_part_badge(named, course, module):
    complete_module(named, module)

    take_exam(named, course, right=False)

    assert not Badge.objects.filter(kind="partie").exists()


# --- US-24 : certificat -----------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_passing_the_exam_issues_a_certificate_with_the_frozen_full_name(named, course, module):
    complete_module(named, module)

    take_exam(named, course, right=True)

    certificate = Certificate.objects.get(user=named, partie=course)
    assert (certificate.holder_name, certificate.score_pct) == ("Awa Nkoulou", 100)
    named.last_name = "Autre"
    named.save()
    certificate.refresh_from_db()
    assert certificate.holder_name == "Awa Nkoulou"


@pytest.mark.django_db
def test_failed_exam_issues_no_certificate(named, course, module):
    complete_module(named, module)

    take_exam(named, course, right=False)

    assert not Certificate.objects.exists()


@pytest.mark.django_db
def test_certificate_waits_for_the_full_name(client, enrolled, course, module):
    complete_module(enrolled, module)
    take_exam(enrolled, course, right=True)
    assert not Certificate.objects.exists()
    client.force_login(enrolled)

    response = client.post("/fr/certificats/", {"first_name": "Awa", "last_name": "Nkoulou"})

    assert response.status_code == 302
    assert Certificate.objects.get(user=enrolled).holder_name == "Awa Nkoulou"


@pytest.mark.django_db
def test_better_attempt_updates_the_certificate_score(named, course, module, settings):
    complete_module(named, module)
    exam = Assessment.exam_for(course)
    first = start_attempt(named, exam)
    aqs = list(first.attempt_questions.select_related("question"))
    for i, aq in enumerate(aqs):
        save_answer(first, aq.question.public_id, list(aq.question.choices.filter(is_correct=i < 3).values_list("public_id", flat=True)[:1]))
    submit_attempt(first)
    issued = Certificate.objects.get(user=named)
    assert issued.score_pct == 75

    take_exam(named, course, right=True)

    issued.refresh_from_db()
    assert issued.score_pct == 100
    assert Certificate.objects.filter(user=named).count() == 1


@pytest.mark.django_db
def test_worse_attempt_never_lowers_the_certificate(named, course, module):
    complete_module(named, module)
    take_exam(named, course, right=True)

    take_exam(named, course, right=False)

    assert Certificate.objects.get(user=named).score_pct == 100


# --- US-25 : PDF réservé ----------------------------------------------------------------------------------------------


@pytest.fixture
def certificate(named, course, module):
    complete_module(named, module)
    take_exam(named, course, right=True)
    return Certificate.objects.get(user=named)


def pdf_url(certificate):
    return f"/fr/certificats/{certificate.public_id}/pdf/"


@pytest.mark.django_db
def test_holder_downloads_the_pdf(client, certificate):
    client.force_login(certificate.user)

    response = client.get(pdf_url(certificate))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "Nkoulou".encode() in response.content


@pytest.mark.django_db
def test_the_pdf_names_the_issuing_platform(client, certificate):
    """US-41 (C16) : le certificat dit qui le délivre, comme la page de vérification publique."""
    client.force_login(certificate.user)

    assert b"ComptaFisca Acad Ventisax" in client.get(pdf_url(certificate)).content


@pytest.mark.django_db
def test_another_learner_cannot_download_the_pdf(client, certificate, promotion):
    intruder = enroll(User.objects.create_user(username="mallory", password="x-Secret-123"), promotion)
    client.force_login(intruder)

    assert client.get(pdf_url(certificate)).status_code == 404


@pytest.mark.django_db
def test_trainer_of_the_promotion_downloads_the_pdf(client, certificate, promotion):
    trainer = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(trainer)
    client.force_login(trainer)

    assert client.get(pdf_url(certificate)).status_code == 200


@pytest.mark.django_db
def test_trainer_of_another_promotion_cannot_download_the_pdf(client, certificate, partie):
    from accounts.models import Promotion

    other = Promotion.objects.create(name="Jan 2027", formation=partie.formation)
    trainer = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    other.trainers.add(trainer)
    client.force_login(trainer)

    assert client.get(pdf_url(certificate)).status_code == 404


@pytest.mark.django_db
def test_anonymous_visitor_is_sent_to_login_for_the_pdf(client, certificate):
    response = client.get(pdf_url(certificate))

    assert response.status_code == 302 and "/connexion/" in response["Location"]


@pytest.mark.django_db
def test_learner_page_lists_certificates_and_badges(client, certificate):
    client.force_login(certificate.user)

    response = client.get("/fr/certificats/")

    assert list(response.context["certificates"]) == [certificate]
    assert len(response.context["badges"]) == 2


# --- US-26 : vérification publique ------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_anyone_can_verify_a_certificate_by_its_number(client, certificate):
    html = client.get(f"/fr/verify/{certificate.public_id}/").content.decode()

    assert "Awa Nkoulou" in html
    assert "Habilitation et sécurité" in html
    assert "valide" in html


@pytest.mark.django_db
def test_unknown_certificate_number_is_not_found(client):
    assert client.get(f"/fr/verify/{uuid.uuid4()}/").status_code == 404


@pytest.mark.django_db
def test_a_lower_passing_attempt_never_lowers_the_certificate_score(certificate):
    """US-41 : le score d'un certificat peut monter, jamais baisser, quelle que soit la tentative transmise."""
    from certificates.services import issue_certificate

    lower = Attempt.objects.create(user=certificate.user, assessment=certificate.attempt.assessment, number=9, started_at=timezone.now(),
                                   score_pct=75)

    issue_certificate(certificate.user, certificate.partie, lower)

    certificate.refresh_from_db()
    assert certificate.score_pct == 100
    assert certificate.attempt_id != lower.pk


@pytest.mark.django_db
@pytest.mark.parametrize("lang, label, score", [("fr", "Score", "100 %"), ("en", "Score", "100%")])
def test_the_public_verification_shows_the_score(client, certificate, lang, label, score):
    """US-42 : la page publique affiche titulaire, partie, date et score, au format de la langue."""
    html = client.get(f"/{lang}/verify/{certificate.public_id}/").content.decode()

    assert f"<dt>{label}</dt><dd>{score}</dd>" in html
