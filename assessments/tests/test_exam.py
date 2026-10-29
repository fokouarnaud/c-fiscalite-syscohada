from datetime import timedelta

import pytest
from django.utils import timezone

from assessments.models import Assessment
from assessments.services import (
    AttemptClosed,
    AttemptLimitReached,
    ExamLocked,
    close_if_expired,
    save_answer,
    start_attempt,
    submit_attempt,
)
from courses.models import Module, Section
from progress.services import mark_section_viewed

T0 = timezone.make_aware(timezone.datetime(2026, 11, 2, 9, 0))


@pytest.fixture
def two_modules(partie, module):
    second = Module.objects.create(partie=partie, title_fr="Rapports", order=2)
    for m in (module, second):
        Section.objects.create(module=m, title_fr="Cours", order=1)
    return [module, second]


@pytest.fixture
def exam(partie, two_modules, question_factory):
    for m in two_modules:
        for _ in range(3):
            question_factory(m, usage="exam")
    exam = Assessment.exam_for(partie)
    exam.questions_per_module = 2
    exam.save()
    return exam


@pytest.fixture
def unlocked(learner, two_modules):
    for m in two_modules:
        mark_section_viewed(learner, m.sections.get())
    return learner


def answer_all_correctly(attempt, now):
    for aq in attempt.attempt_questions.all():
        save_answer(attempt, aq.question.public_id, aq.question.choices.filter(is_correct=True).values_list("public_id", flat=True), now)


@pytest.mark.django_db
def test_exam_defaults_follow_netacad_rules(partie):
    exam = Assessment.exam_for(partie)
    assert (exam.pass_threshold, exam.max_attempts, exam.duration_minutes, exam.shuffle) == (70, 3, 60, True)


@pytest.mark.django_db
def test_module_quiz_has_no_attempt_limit_or_duration(module):
    quiz = Assessment.quiz_for(module)
    assert quiz.max_attempts is None and quiz.duration_minutes is None


@pytest.mark.django_db
def test_locked_exam_cannot_be_started(learner, exam):
    with pytest.raises(ExamLocked):
        start_attempt(learner, exam, now=T0)


@pytest.mark.django_db
def test_exam_draws_the_configured_number_of_exam_questions_per_module(unlocked, exam, two_modules, question_factory):
    question_factory(two_modules[0], usage="quiz")  # jamais tirée dans un examen
    submit_attempt(start_attempt(unlocked, Assessment.quiz_for(two_modules[0]), now=T0))
    attempt = start_attempt(unlocked, exam, now=T0)
    drawn = [aq.question for aq in attempt.attempt_questions.all()]
    assert len(drawn) == 4
    assert all(q.usage == "exam" for q in drawn)
    assert sorted(q.module_id for q in drawn) == sorted([two_modules[0].pk] * 2 + [two_modules[1].pk] * 2)


@pytest.mark.django_db
def test_exam_deadline_is_sixty_minutes_after_start(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    assert attempt.deadline == T0 + timedelta(minutes=60)


@pytest.mark.django_db
def test_starting_again_resumes_the_open_attempt(unlocked, exam):
    first = start_attempt(unlocked, exam, now=T0)
    again = start_attempt(unlocked, exam, now=T0 + timedelta(minutes=20))
    assert again.pk == first.pk
    assert exam.attempts.count() == 1


@pytest.mark.django_db
def test_resumed_attempt_keeps_answers_and_choice_order(unlocked, exam):
    first = start_attempt(unlocked, exam, now=T0)
    aq = first.attempt_questions.first()
    order_before = aq.ordered_choices()
    save_answer(first, aq.question.public_id, [order_before[0].public_id], T0 + timedelta(minutes=1))
    resumed = start_attempt(unlocked, exam, now=T0 + timedelta(minutes=30))
    aq_again = resumed.attempt_questions.get(pk=aq.pk)
    assert aq_again.ordered_choices() == order_before
    assert list(aq_again.selected_choices.values_list("pk", flat=True)) == [order_before[0].pk]


@pytest.mark.django_db
def test_fourth_exam_attempt_is_refused(unlocked, exam):
    for i in range(3):
        submit_attempt(start_attempt(unlocked, exam, now=T0 + timedelta(hours=i)), now=T0 + timedelta(hours=i, minutes=5))
    with pytest.raises(AttemptLimitReached):
        start_attempt(unlocked, exam, now=T0 + timedelta(hours=5))


@pytest.mark.django_db
def test_answer_after_deadline_is_refused(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    aq = attempt.attempt_questions.first()
    with pytest.raises(AttemptClosed):
        save_answer(attempt, aq.question.public_id, [], T0 + timedelta(minutes=61))


@pytest.mark.django_db
def test_answer_after_submission_is_refused(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    submit_attempt(attempt, now=T0 + timedelta(minutes=10))
    aq = attempt.attempt_questions.first()
    with pytest.raises(AttemptClosed):
        save_answer(attempt, aq.question.public_id, [], T0 + timedelta(minutes=11))


@pytest.mark.django_db
def test_expired_attempt_is_auto_submitted_with_given_answers(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    answer_all_correctly(attempt, T0 + timedelta(minutes=5))
    close_if_expired(attempt, now=T0 + timedelta(minutes=90))
    attempt.refresh_from_db()
    assert attempt.auto_submitted
    assert attempt.submitted_at == T0 + timedelta(minutes=60)
    assert attempt.score_pct == 100


@pytest.mark.django_db
def test_attempt_still_running_is_not_closed(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    close_if_expired(attempt, now=T0 + timedelta(minutes=59))
    attempt.refresh_from_db()
    assert attempt.submitted_at is None


@pytest.mark.django_db
def test_starting_after_expiry_closes_old_attempt_and_opens_a_new_one(unlocked, exam):
    first = start_attempt(unlocked, exam, now=T0)
    second = start_attempt(unlocked, exam, now=T0 + timedelta(hours=2))
    first.refresh_from_db()
    assert first.auto_submitted
    assert second.number == 2


@pytest.mark.django_db
def test_exam_is_passed_at_seventy_percent(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    aqs = list(attempt.attempt_questions.all())
    for aq in aqs[:3]:  # 3 bonnes réponses sur 4 = 75 %
        save_answer(attempt, aq.question.public_id, aq.question.choices.filter(is_correct=True).values_list("public_id", flat=True), T0)
    submit_attempt(attempt, now=T0 + timedelta(minutes=10))
    attempt.refresh_from_db()
    assert attempt.score_pct == 75
    assert attempt.passed


@pytest.mark.django_db
def test_exam_below_threshold_is_failed(unlocked, exam):
    attempt = start_attempt(unlocked, exam, now=T0)
    aq = attempt.attempt_questions.first()
    save_answer(attempt, aq.question.public_id, aq.question.choices.filter(is_correct=True).values_list("public_id", flat=True), T0)
    submit_attempt(attempt, now=T0 + timedelta(minutes=10))  # 1 sur 4 = 25 %
    attempt.refresh_from_db()
    assert not attempt.passed


@pytest.mark.django_db
def test_best_score_is_kept_across_attempts(unlocked, exam):
    good = start_attempt(unlocked, exam, now=T0)
    answer_all_correctly(good, T0)
    submit_attempt(good, now=T0 + timedelta(minutes=5))
    submit_attempt(start_attempt(unlocked, exam, now=T0 + timedelta(hours=1)), now=T0 + timedelta(hours=1, minutes=5))
    assert exam.best_attempt(unlocked).pk == good.pk


@pytest.mark.django_db
def test_exam_result_breaks_score_down_by_module(unlocked, exam, two_modules):
    attempt = start_attempt(unlocked, exam, now=T0)
    for aq in attempt.attempt_questions.filter(question__module=two_modules[0]):
        save_answer(attempt, aq.question.public_id, aq.question.choices.filter(is_correct=True).values_list("public_id", flat=True), T0)
    submit_attempt(attempt, now=T0 + timedelta(minutes=10))
    assert attempt.module_scores() == {two_modules[0]: 100, two_modules[1]: 0}


@pytest.mark.django_db
def test_module_scores_follow_course_order_not_draw_order(unlocked, exam, two_modules):
    attempt = start_attempt(unlocked, exam, now=T0)
    # Force un tirage où toutes les questions du module 2 sortent en premier.
    for aq in attempt.attempt_questions.all():
        aq.order = aq.order + (0 if aq.question.module == two_modules[1] else 100)
        aq.save()
    submit_attempt(attempt, now=T0 + timedelta(minutes=5))
    assert list(attempt.module_scores()) == two_modules
