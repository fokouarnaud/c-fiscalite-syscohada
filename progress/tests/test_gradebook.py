"""US-28 : détail d'une tentative. US-29 : taux de réussite par question (carnet de notes formateur)."""
import pytest

from accounts.models import Promotion, User
from assessments.models import Assessment
from assessments.services import save_answer, start_attempt, submit_attempt
from conftest import enroll


@pytest.fixture
def trainer(promotion):
    user = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(user)
    return user


@pytest.fixture
def outsider(partie):
    other = Promotion.objects.create(name="Jan 2027", formation=partie.formation)
    return enroll(User.objects.create_user(username="zoe", password="x-Secret-123"), other)


def quiz(user, module, right, time_spent=0):
    attempt = start_attempt(user, Assessment.quiz_for(module))
    for aq in attempt.attempt_questions.select_related("question"):
        ids = aq.question.choices.filter(is_correct=right).values_list("public_id", flat=True)[:1]
        save_answer(attempt, aq.question.public_id, list(ids), time_spent_s=time_spent)
    return attempt


def detail_url(attempt):
    return f"/fr/formateur/tentatives/{attempt.public_id}/"


# --- US-28 ------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_trainer_reads_each_answer_of_a_submitted_attempt(client, trainer, enrolled, module, question_factory):
    q = question_factory(module)
    attempt = submit_attempt(quiz(enrolled, module, right=False, time_spent=42))
    client.force_login(trainer)

    response = client.get(detail_url(attempt))

    assert response.status_code == 200
    [row] = response.context["rows"]
    assert (row["question"], row["score"], row["time_spent_s"]) == (q, 0, 42)
    assert row["answer"] == "Faux"


@pytest.mark.django_db
def test_attempt_in_progress_is_hidden_from_the_trainer(client, trainer, enrolled, module, question_factory):
    question_factory(module)
    attempt = quiz(enrolled, module, right=True)
    client.force_login(trainer)

    assert client.get(detail_url(attempt)).status_code == 404


@pytest.mark.django_db
def test_trainer_cannot_read_an_attempt_of_another_promotion(client, trainer, outsider, module, question_factory):
    question_factory(module)
    attempt = submit_attempt(quiz(outsider, module, right=True))
    client.force_login(trainer)

    assert client.get(detail_url(attempt)).status_code == 404


@pytest.mark.django_db
def test_learner_cannot_open_the_attempt_detail(client, enrolled, module, question_factory):
    question_factory(module)
    attempt = submit_attempt(quiz(enrolled, module, right=True))
    client.force_login(enrolled)

    assert client.get(detail_url(attempt)).status_code == 403


@pytest.mark.django_db
def test_platform_admin_reads_any_submitted_attempt(client, outsider, module, question_factory):
    question_factory(module)
    attempt = submit_attempt(quiz(outsider, module, right=True))
    client.force_login(User.objects.create_user(username="chef", password="x-Secret-123", role=User.Role.ADMIN))

    assert client.get(detail_url(attempt)).status_code == 200


# --- US-29 ------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_question_success_rate_covers_the_trainers_learners_only(client, trainer, enrolled, outsider, promotion, module, question_factory):
    q = question_factory(module)
    ali = enroll(User.objects.create_user(username="ali", password="x-Secret-123"), promotion)
    submit_attempt(quiz(enrolled, module, right=True))
    submit_attempt(quiz(ali, module, right=False))
    submit_attempt(quiz(outsider, module, right=False))
    quiz(ali, module, right=True)  # en cours : ignorée
    client.force_login(trainer)

    response = client.get("/fr/formateur/questions/")

    [stat] = response.context["stats"]
    assert (stat["question"], stat["answers"], stat["success_pct"]) == (q, 2, 50)


@pytest.mark.django_db
def test_question_statistics_are_refused_to_learners(client, enrolled):
    client.force_login(enrolled)

    assert client.get("/fr/formateur/questions/").status_code == 403


@pytest.mark.django_db
def test_trainer_table_links_each_submitted_attempt_of_a_learner(client, trainer, enrolled, module, question_factory):
    question_factory(module)
    done = submit_attempt(quiz(enrolled, module, right=True))
    quiz(enrolled, module, right=True)  # en cours : pas de lien
    client.force_login(trainer)

    [row] = client.get("/fr/formateur/").context["rows"]

    assert [a.public_id for a in row["submitted"]] == [done.public_id]
