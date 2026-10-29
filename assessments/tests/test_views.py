from datetime import timedelta

import pytest

from conftest import enroll
from django.utils import timezone

from assessments.models import Assessment, Attempt
from assessments.services import start_attempt, submit_attempt
from courses.models import Section
from progress.services import mark_section_viewed


def correct_ids(question):
    return list(question.choices.filter(is_correct=True).values_list("public_id", flat=True))


@pytest.fixture
def quiz_question(module, question_factory):
    Section.objects.create(module=module, title_fr="Cours", order=1)
    return question_factory(module)


@pytest.fixture
def exam(partie, module, question_factory):
    for _ in range(2):
        question_factory(module, usage="exam")
    return Assessment.exam_for(partie)


def complete_module(user, module):
    for s in module.sections.all():
        mark_section_viewed(user, s)
    submit_attempt(start_attempt(user, Assessment.quiz_for(module)))


@pytest.mark.django_db
def test_opening_a_module_quiz_starts_an_attempt(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    response = client.post(f"/fr/quiz/{module.public_id}/")
    attempt = Attempt.objects.get(user=enrolled)
    assert response.status_code == 302
    assert response.url == f"/fr/tentatives/{attempt.public_id}/"


@pytest.mark.django_db
def test_attempt_page_shows_questions_in_drawn_order(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    response = client.get(f"/fr/tentatives/{attempt.public_id}/")
    assert response.status_code == 200
    assert [row["question"] for row in response.context["rows"]] == [quiz_question]


@pytest.mark.django_db
def test_another_learners_attempt_is_not_found(client, enrolled, module, quiz_question, django_user_model):
    other = enroll(django_user_model.objects.create_user(username="ali", password="x-Secret-123"), enrolled.enrollments.get().promotion)
    attempt = start_attempt(other, Assessment.quiz_for(module))
    client.force_login(enrolled)
    assert client.get(f"/fr/tentatives/{attempt.public_id}/").status_code == 404


@pytest.mark.django_db
def test_quiz_of_another_formation_is_not_found(client, learner, module, quiz_question):
    client.force_login(learner)  # pas de promotion
    assert client.post(f"/fr/quiz/{module.public_id}/").status_code == 404


@pytest.mark.django_db
def test_answer_is_saved_as_soon_as_it_is_posted(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    response = client.post(
        f"/fr/tentatives/{attempt.public_id}/reponse/", {"question": quiz_question.public_id, "choices": correct_ids(quiz_question)},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    aq = attempt.attempt_questions.get()
    assert list(aq.selected_choices.values_list("public_id", flat=True)) == correct_ids(quiz_question)


@pytest.mark.django_db
def test_answer_after_deadline_is_rejected_with_conflict(client, enrolled, partie, module, quiz_question, exam):
    complete_module(enrolled, module)
    attempt = start_attempt(enrolled, exam, now=timezone.now() - timedelta(minutes=61))
    question = attempt.attempt_questions.first().question
    client.force_login(enrolled)
    response = client.post(
        f"/fr/tentatives/{attempt.public_id}/reponse/", {"question": question.public_id, "choices": correct_ids(question)},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_submitting_a_quiz_shows_the_correction(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    response = client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/", {"confirm": "1"})  # question laissée vide
    assert response.status_code == 302
    result = client.get(response.url)
    assert result.context["show_correction"] is True
    assert "Parce que." in result.content.decode()


@pytest.mark.django_db
def test_exam_result_shows_module_scores_but_not_the_correction(client, enrolled, module, quiz_question, exam):
    complete_module(enrolled, module)
    attempt = start_attempt(enrolled, exam)
    submit_attempt(attempt)
    client.force_login(enrolled)
    response = client.get(f"/fr/tentatives/{attempt.public_id}/resultat/")
    assert response.context["show_correction"] is False
    assert response.context["module_scores"] == {module: 0}
    assert response.context["attempts_left"] == 2
    assert "Parce que." not in response.content.decode()


@pytest.mark.django_db
def test_locked_exam_page_lists_unfinished_modules(client, enrolled, partie, module, quiz_question, exam):
    client.force_login(enrolled)
    response = client.get(f"/fr/examen/{partie.public_id}/")
    assert response.status_code == 200
    assert response.context["unlocked"] is False
    assert [m["module"] for m in response.context["missing_modules"]] == [module]


@pytest.mark.django_db
def test_starting_a_locked_exam_is_forbidden(client, enrolled, partie, module, quiz_question, exam):
    client.force_login(enrolled)
    assert client.post(f"/fr/examen/{partie.public_id}/").status_code == 403
    assert not exam.attempts.exists()


@pytest.mark.django_db
def test_unlocked_exam_starts_on_post(client, enrolled, partie, module, quiz_question, exam):
    complete_module(enrolled, module)
    client.force_login(enrolled)
    response = client.post(f"/fr/examen/{partie.public_id}/")
    attempt = exam.attempts.get(user=enrolled)
    assert response.url == f"/fr/tentatives/{attempt.public_id}/"


@pytest.mark.django_db
def test_exam_start_is_forbidden_after_three_attempts(client, enrolled, partie, module, quiz_question, exam):
    complete_module(enrolled, module)
    for _ in range(3):
        submit_attempt(start_attempt(enrolled, exam))
    client.force_login(enrolled)
    assert client.get(f"/fr/examen/{partie.public_id}/").context["attempts_left"] == 0
    assert client.post(f"/fr/examen/{partie.public_id}/").status_code == 403


@pytest.mark.django_db
def test_exam_page_gives_remaining_time_computed_by_server(client, enrolled, module, quiz_question, exam):
    complete_module(enrolled, module)
    attempt = start_attempt(enrolled, exam, now=timezone.now() - timedelta(minutes=15))
    client.force_login(enrolled)
    remaining = client.get(f"/fr/tentatives/{attempt.public_id}/").context["remaining_seconds"]
    assert 44 * 60 < remaining <= 45 * 60


@pytest.mark.django_db
def test_expired_attempt_page_redirects_to_auto_submitted_result(client, enrolled, module, quiz_question, exam):
    complete_module(enrolled, module)
    attempt = start_attempt(enrolled, exam, now=timezone.now() - timedelta(minutes=70))
    client.force_login(enrolled)
    response = client.get(f"/fr/tentatives/{attempt.public_id}/")
    attempt.refresh_from_db()
    assert response.url == f"/fr/tentatives/{attempt.public_id}/resultat/"
    assert attempt.auto_submitted


@pytest.mark.django_db
def test_switching_to_english_keeps_the_same_attempt_and_answers(client, enrolled, module, quiz_question):
    quiz_question.prompt_en = "Is current dangerous?"
    quiz_question.save()
    client.force_login(enrolled)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.post(f"/fr/tentatives/{attempt.public_id}/reponse/", {"question": quiz_question.public_id, "choices": correct_ids(quiz_question)})
    response = client.get(f"/en/tentatives/{attempt.public_id}/")
    assert "Is current dangerous?" in response.content.decode()
    [row] = response.context["rows"]
    assert row["selected"] == set(correct_ids(quiz_question))
    assert Attempt.objects.count() == 1


@pytest.mark.django_db
def test_answer_saved_without_javascript_returns_to_the_attempt(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    response = client.post(f"/fr/tentatives/{attempt.public_id}/reponse/", {"question": quiz_question.public_id, "choices": correct_ids(quiz_question)})
    assert response.status_code == 302
    assert response.url == f"/fr/tentatives/{attempt.public_id}/#q-{quiz_question.public_id}"


@pytest.mark.django_db
def test_answer_saved_by_htmx_gets_an_empty_success(client, enrolled, module, quiz_question):
    client.force_login(enrolled)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    response = client.post(
        f"/fr/tentatives/{attempt.public_id}/reponse/", {"question": quiz_question.public_id, "choices": correct_ids(quiz_question)},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_exam_page_offers_to_resume_an_open_attempt(client, enrolled, partie, module, quiz_question, exam):
    complete_module(enrolled, module)
    attempt = start_attempt(enrolled, exam)
    client.force_login(enrolled)
    assert client.get(f"/fr/examen/{partie.public_id}/").context["open_attempt"] == attempt


@pytest.mark.django_db
def test_exam_page_has_no_open_attempt_after_submission(client, enrolled, partie, module, quiz_question, exam):
    complete_module(enrolled, module)
    submit_attempt(start_attempt(enrolled, exam))
    client.force_login(enrolled)
    assert client.get(f"/fr/examen/{partie.public_id}/").context["open_attempt"] is None
