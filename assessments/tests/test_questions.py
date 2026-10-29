import pytest
from django.core.exceptions import ValidationError

from assessments.models import Question


def make_question(module, qtype=Question.Type.SINGLE, choices=((True, "Oui"), (False, "Non")), **kwargs):
    q = Question.objects.create(
        module=module, qtype=qtype, prompt_fr="Q ?", prompt_en="Q?",
        reviewed_fr=True, reviewed_en=True, **kwargs,
    )
    for i, (ok, text) in enumerate(choices):
        q.choices.create(text_fr=text, text_en=text, is_correct=ok, order=i)
    return q


@pytest.mark.django_db
def test_new_question_is_a_draft(module):
    assert make_question(module).status == Question.Status.DRAFT


@pytest.mark.django_db
def test_reviewed_valid_question_can_be_published(module):
    q = make_question(module)
    q.publish()
    q.refresh_from_db()
    assert q.status == Question.Status.PUBLISHED


@pytest.mark.django_db
def test_publishing_without_english_review_is_refused(module):
    q = make_question(module)
    q.reviewed_en = False
    with pytest.raises(ValidationError):
        q.publish()
    q.refresh_from_db()
    assert q.status == Question.Status.DRAFT


@pytest.mark.django_db
def test_publishing_without_french_review_is_refused(module):
    q = make_question(module)
    q.reviewed_fr = False
    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_single_choice_question_with_two_correct_answers_is_refused(module):
    q = make_question(module, choices=((True, "A"), (True, "B"), (False, "C")))
    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_multiple_choice_question_needs_at_least_two_correct_answers(module):
    q = make_question(module, qtype=Question.Type.MULTIPLE, choices=((True, "A"), (False, "B"), (False, "C")))
    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_true_false_question_needs_exactly_two_choices(module):
    q = make_question(module, qtype=Question.Type.TRUE_FALSE, choices=((True, "Vrai"), (False, "Faux"), (False, "?")))
    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_only_published_questions_are_served(module):
    draft = make_question(module)
    published = make_question(module)
    published.publish()
    assert list(Question.objects.published()) == [published]
    assert draft not in Question.objects.published()
