"""US-31 : annonces de promotion. US-32 : dates limites indicatives et marqueur « en retard »."""
from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import Promotion, User
from assessments.models import Assessment
from assessments.services import start_attempt, submit_attempt
from conftest import enroll
from progress.models import Announcement, Deadline
from progress.services import late_deadlines


@pytest.fixture
def trainer(promotion):
    user = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(user)
    return user


@pytest.fixture
def other_promotion(partie):
    return Promotion.objects.create(name="Jan 2027", formation=partie.formation)


# --- US-31 ------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_trainer_posts_an_announcement_to_their_promotion(client, trainer, promotion):
    client.force_login(trainer)

    response = client.post("/fr/formateur/annonces/", {
        "promotion": promotion.public_id, "title": "Atelier jeudi", "body": "Apportez votre multimètre.",
    })

    assert response.status_code == 302
    announcement = Announcement.objects.get()
    assert (announcement.promotion, announcement.author, announcement.title) == (promotion, trainer, "Atelier jeudi")


@pytest.mark.django_db
def test_trainer_cannot_post_to_a_promotion_they_do_not_teach(client, trainer, other_promotion):
    client.force_login(trainer)

    response = client.post("/fr/formateur/annonces/", {
        "promotion": other_promotion.public_id, "title": "Pirate", "body": "x",
    })

    assert response.status_code == 200
    assert "promotion" in response.context["form"].errors
    assert not Announcement.objects.exists()


@pytest.mark.django_db
def test_learners_see_only_their_promotion_announcements(client, trainer, enrolled, promotion, other_promotion):
    Announcement.objects.create(promotion=promotion, author=trainer, title_fr="Pour vous", body_fr="…")
    Announcement.objects.create(promotion=other_promotion, author=trainer, title_fr="Pas pour vous", body_fr="…")
    client.force_login(enrolled)

    response = client.get("/fr/")

    assert [a.title for a in response.context["announcements"]] == ["Pour vous"]


@pytest.mark.django_db
def test_learner_cannot_post_an_announcement(client, enrolled, promotion):
    client.force_login(enrolled)

    response = client.post("/fr/formateur/annonces/", {"promotion": promotion.public_id, "title": "x", "body": "x"})

    assert response.status_code == 403


# --- US-32 ------------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_trainer_sets_a_deadline_on_a_module_quiz(client, trainer, promotion, module):
    client.force_login(trainer)
    due = timezone.now() + timedelta(days=3)

    response = client.post("/fr/formateur/echeances/", {
        "promotion": promotion.public_id, "target": f"quiz:{module.public_id}", "due_at": due.strftime("%Y-%m-%dT%H:%M"),
    })

    assert response.status_code == 302
    deadline = Deadline.objects.get()
    assert (deadline.promotion, deadline.assessment) == (promotion, Assessment.quiz_for(module))


@pytest.mark.django_db
def test_setting_the_same_deadline_again_moves_it(client, trainer, promotion, partie):
    client.force_login(trainer)
    for day in ("2026-11-01T10:00", "2026-11-15T10:00"):
        client.post("/fr/formateur/echeances/", {
            "promotion": promotion.public_id, "target": f"exam:{partie.public_id}", "due_at": day,
        })

    assert Deadline.objects.get().due_at.day == 15


@pytest.mark.django_db
def test_deadline_target_must_belong_to_the_promotion_formation(client, trainer, promotion):
    from courses.models import Formation, Module, Partie

    foreign = Formation.objects.create(title_fr="Autre", slug="autre")
    alien = Module.objects.create(partie=Partie.objects.create(formation=foreign, title_fr="P", slug="p"), title_fr="M")
    client.force_login(trainer)

    response = client.post("/fr/formateur/echeances/", {
        "promotion": promotion.public_id, "target": f"quiz:{alien.public_id}", "due_at": "2026-11-01T10:00",
    })

    assert response.status_code == 200
    assert not Deadline.objects.exists()


@pytest.mark.django_db
def test_learner_is_late_when_the_quiz_is_not_submitted_after_the_deadline(enrolled, promotion, module, question_factory):
    question_factory(module)
    now = timezone.now()
    Deadline.objects.create(promotion=promotion, assessment=Assessment.quiz_for(module), due_at=now - timedelta(hours=1))

    assert len(late_deadlines(enrolled, promotion, now)) == 1


@pytest.mark.django_db
def test_learner_who_submitted_the_quiz_is_not_late(enrolled, promotion, module, question_factory):
    question_factory(module)
    now = timezone.now()
    quiz = Assessment.quiz_for(module)
    Deadline.objects.create(promotion=promotion, assessment=quiz, due_at=now - timedelta(hours=1))
    submit_attempt(start_attempt(enrolled, quiz))

    assert late_deadlines(enrolled, promotion, now) == []


@pytest.mark.django_db
def test_nobody_is_late_before_the_deadline(enrolled, promotion, module):
    now = timezone.now()
    Deadline.objects.create(promotion=promotion, assessment=Assessment.quiz_for(module), due_at=now + timedelta(hours=1))

    assert late_deadlines(enrolled, promotion, now) == []


@pytest.mark.django_db
def test_exam_deadline_requires_a_passed_exam(enrolled, promotion, partie, module, question_factory):
    question_factory(module, usage="exam")
    now = timezone.now()
    exam = Assessment.exam_for(partie)
    Deadline.objects.create(promotion=promotion, assessment=exam, due_at=now - timedelta(hours=1))
    exam.attempts.create(user=enrolled, number=1, started_at=now, submitted_at=now, score_pct=40)

    assert len(late_deadlines(enrolled, promotion, now)) == 1


@pytest.mark.django_db
def test_late_deadline_never_blocks_the_exam(client, enrolled, promotion, partie, module, question_factory):
    question_factory(module, usage="exam")
    Deadline.objects.create(promotion=promotion, assessment=Assessment.exam_for(partie), due_at=timezone.now() - timedelta(days=1))
    client.force_login(enrolled)

    response = client.post(f"/fr/examen/{partie.public_id}/")

    assert response.status_code == 302  # examen démarré : la date limite est seulement indicative


@pytest.mark.django_db
def test_trainer_table_flags_late_learners(client, trainer, enrolled, promotion, module, question_factory):
    question_factory(module)
    Deadline.objects.create(promotion=promotion, assessment=Assessment.quiz_for(module), due_at=timezone.now() - timedelta(hours=1))
    client.force_login(trainer)

    [row] = client.get("/fr/formateur/").context["rows"]

    assert len(row["late"]) == 1


@pytest.mark.django_db
def test_single_promotion_is_preselected_in_trainer_forms(client, trainer, promotion):
    client.force_login(trainer)

    for url in ("/fr/formateur/annonces/", "/fr/formateur/echeances/"):
        assert client.get(url).context["form"]["promotion"].value() == promotion.public_id


@pytest.mark.django_db
def test_several_promotions_are_not_preselected(client, trainer, promotion, other_promotion):
    other_promotion.trainers.add(trainer)
    client.force_login(trainer)

    assert client.get("/fr/formateur/annonces/").context["form"]["promotion"].value() is None
