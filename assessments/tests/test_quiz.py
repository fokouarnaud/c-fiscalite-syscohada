import pytest

from assessments.models import Assessment
from assessments.services import save_answer, start_attempt, submit_attempt


def correct_ids(q):
    return [c.pk for c in q.choices.filter(is_correct=True)]


def public_ids(q, correct):
    return [c.public_id for c in q.choices.filter(is_correct=correct)][: None if correct else 1]


def wrong_ids(q):
    return [c.pk for c in q.choices.filter(is_correct=False)][:1]


@pytest.mark.django_db
def test_quiz_serves_only_published_quiz_questions_of_its_module(module, learner, question_factory):
    quiz_q = question_factory(module)
    question_factory(module, usage="exam")
    question_factory(module, publish=False)
    attempt = start_attempt(learner, Assessment.quiz_for(module))
    assert [aq.question for aq in attempt.attempt_questions.all()] == [quiz_q]


@pytest.mark.django_db
def test_quiz_has_no_deadline(module, learner, question_factory):
    question_factory(module)
    attempt = start_attempt(learner, Assessment.quiz_for(module))
    assert attempt.deadline is None


@pytest.mark.django_db
def test_quiz_can_be_retaken_without_limit(module, learner, question_factory):
    question_factory(module)
    quiz = Assessment.quiz_for(module)
    for _ in range(5):
        submit_attempt(start_attempt(learner, quiz))
    assert quiz.attempts.filter(user=learner).count() == 5


@pytest.mark.django_db
def test_submitted_quiz_is_scored_as_percentage(module, learner, question_factory):
    q1, q2 = question_factory(module), question_factory(module)
    attempt = start_attempt(learner, Assessment.quiz_for(module))
    save_answer(attempt, q1.public_id, public_ids(q1, True))
    save_answer(attempt, q2.public_id, public_ids(q2, False))
    submit_attempt(attempt)
    attempt.refresh_from_db()
    assert attempt.submitted_at is not None
    assert attempt.score_pct == 50


@pytest.mark.django_db
def test_quiz_feedback_reveals_correct_choices_and_explanation(module, learner, question_factory):
    q = question_factory(module)
    attempt = start_attempt(learner, Assessment.quiz_for(module))
    save_answer(attempt, q.public_id, public_ids(q, False))
    submit_attempt(attempt)
    [item] = attempt.feedback()
    assert item["correct_choice_ids"] == correct_ids(q)
    assert item["selected_choice_ids"] == wrong_ids(q)
    assert item["explanation"] == "Parce que."
    assert item["score"] == 0


@pytest.mark.django_db
def test_unanswered_question_scores_zero(module, learner, question_factory):
    question_factory(module)
    attempt = start_attempt(learner, Assessment.quiz_for(module))
    submit_attempt(attempt)
    attempt.refresh_from_db()
    assert attempt.score_pct == 0
