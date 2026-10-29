import pytest

from assessments.models import Assessment
from assessments.services import start_attempt, submit_attempt
from courses.models import Module, Section
from progress.models import SectionView
from progress.services import exam_unlocked, mark_section_viewed, module_completed, progress_pct


@pytest.fixture
def sections(module):
    return [
        Section.objects.create(module=module, title_fr="Cours", order=1),
        Section.objects.create(module=module, title_fr="TAF", order=2, kind=Section.Kind.PRACTICAL),
    ]


def pass_quiz(user, module):
    submit_attempt(start_attempt(user, Assessment.quiz_for(module)))


@pytest.mark.django_db
def test_viewing_a_section_twice_records_it_once(learner, sections):
    mark_section_viewed(learner, sections[0])
    mark_section_viewed(learner, sections[0])
    assert SectionView.objects.filter(user=learner).count() == 1


@pytest.mark.django_db
def test_module_is_not_completed_while_a_section_is_unseen(learner, module, sections, question_factory):
    question_factory(module)
    mark_section_viewed(learner, sections[0])
    pass_quiz(learner, module)
    assert not module_completed(learner, module)


@pytest.mark.django_db
def test_module_is_not_completed_without_a_submitted_quiz(learner, module, sections, question_factory):
    question_factory(module)
    for s in sections:
        mark_section_viewed(learner, s)
    start_attempt(learner, Assessment.quiz_for(module))  # commencé mais pas envoyé
    assert not module_completed(learner, module)


@pytest.mark.django_db
def test_module_is_completed_when_all_sections_seen_and_quiz_submitted(learner, module, sections, question_factory):
    question_factory(module)
    for s in sections:
        mark_section_viewed(learner, s)
    pass_quiz(learner, module)
    assert module_completed(learner, module)


@pytest.mark.django_db
def test_module_without_published_quiz_questions_does_not_require_a_quiz(learner, module, sections):
    for s in sections:
        mark_section_viewed(learner, s)
    assert module_completed(learner, module)


@pytest.mark.django_db
def test_another_learners_activity_does_not_count(learner, module, sections, django_user_model):
    other = django_user_model.objects.create_user(username="ali", password="x-Secret-123")
    for s in sections:
        mark_section_viewed(other, s)
    assert not module_completed(learner, module)


@pytest.mark.django_db
def test_exam_stays_locked_until_every_module_of_the_part_is_completed(learner, partie, module, sections):
    second = Module.objects.create(partie=partie, title_fr="Rapports", order=2)
    Section.objects.create(module=second, title_fr="Cours", order=1)
    for s in sections:
        mark_section_viewed(learner, s)
    assert not exam_unlocked(learner, partie)
    mark_section_viewed(learner, second.sections.get())
    assert exam_unlocked(learner, partie)


@pytest.mark.django_db
def test_progress_counts_sections_and_quizzes_as_steps(learner, partie, module, sections, question_factory):
    question_factory(module)  # 2 sections + 1 quiz = 3 étapes
    mark_section_viewed(learner, sections[0])
    assert progress_pct(learner, partie) == 33
    mark_section_viewed(learner, sections[1])
    pass_quiz(learner, module)
    assert progress_pct(learner, partie) == 100


@pytest.mark.django_db
def test_progress_of_empty_part_is_zero(learner, partie):
    assert progress_pct(learner, partie) == 0
