"""US-71, US-72, US-73 et US-79 : une partie de la formation `fisca` (trois modules) se suit, s'examine et se certifie
sans dépendre d'`compta` ; fermée au catalogue, elle reste ouverte au compte de test inscrit par l'admin."""
import pytest

from accounts.models import User
from assessments.models import Assessment
from assessments.services import start_attempt
from catalog.models import Enrollment
from certificates.models import Certificate
from certificates.tests.test_achievements import complete_module, take_exam
from courses.models import Formation, Module, Partie, Section

P1_MODULES = ("La sécurité électrique", "Lire les schémas et les plaques signalétiques", "Transformateurs et distribution")


@pytest.fixture
def fisca_p1(db, question_factory):
    """Partie 1 de `fisca` : trois modules, une section, un quiz et douze questions d'examen chacun (M4, M16)."""
    formation = Formation.objects.create(
        title_fr="Fiscalité CGI Cameroun", slug="fisca", order=2, is_open=True, icon="receipt",
    )
    p1 = Partie.objects.create(formation=formation, title_fr="Sécurité, schémas et distribution", order=1, slug="p1")
    for order, title in enumerate(P1_MODULES, start=1):
        module = Module.objects.create(partie=p1, title_fr=title, order=order, duration_hours=8)
        Section.objects.create(module=module, title_fr=f"Section de {title}", order=1)
        question_factory(module)
        for _ in range(12):
            question_factory(module, usage="exam")
    return p1


@pytest.fixture
def fisca_learner(fisca_p1):
    user = User.objects.create_user(username="ebode", password="x-Secret-123", first_name="Paul", last_name="Ebode")
    Enrollment.objects.create(user=user, formation=fisca_p1.formation, source=Enrollment.Source.CATALOG)
    return user


def first_section(partie):
    return Section.objects.filter(module__partie=partie).order_by("module__order", "order").first()


# --- US-71 : aucun verrou, ni entre parties ni avec `compta` --------------------------------------------------------


def test_a_fisca_section_opens_without_any_compta_enrollment(client, fisca_learner, fisca_p1):
    client.force_login(fisca_learner)

    assert client.get(f"/fr/sections/{first_section(fisca_p1).public_id}/").status_code == 200


def test_a_learner_enrolled_only_in_compta_cannot_read_fisca(client, enrolled, fisca_p1):
    client.force_login(enrolled)

    assert client.get(f"/fr/sections/{first_section(fisca_p1).public_id}/").status_code in (302, 404)


# --- US-72 : examen de 30 questions, ouvert quand les trois modules sont terminés ------------------------------------


def test_the_part_exam_opens_only_once_its_three_modules_are_done(fisca_learner, fisca_p1):
    from progress.services import exam_unlocked

    m1, m2, m3 = fisca_p1.modules.order_by("order")
    complete_module(fisca_learner, m1)
    complete_module(fisca_learner, m2)
    assert not exam_unlocked(fisca_learner, fisca_p1)

    complete_module(fisca_learner, m3)

    assert exam_unlocked(fisca_learner, fisca_p1)


def test_the_part_exam_draws_ten_of_the_twelve_questions_of_each_module(fisca_learner, fisca_p1):
    exam = Assessment.exam_for(fisca_p1)
    assert (exam.pass_threshold, exam.max_attempts, exam.duration_minutes) == (70, 3, 60)
    for module in fisca_p1.modules.all():
        complete_module(fisca_learner, module)

    attempt = start_attempt(fisca_learner, exam)

    per_module = {}
    for aq in attempt.attempt_questions.select_related("question__module"):
        per_module[aq.question.module.title_fr] = per_module.get(aq.question.module.title_fr, 0) + 1
    assert per_module == {title: 10 for title in P1_MODULES}


# --- US-73 : un certificat par partie, distinct de ceux d'`compta`, aucun certificat de formation ------------------


def test_passing_fisca_part_one_issues_its_own_verifiable_certificate(client, fisca_learner, fisca_p1):
    for module in fisca_p1.modules.all():
        complete_module(fisca_learner, module)

    take_exam(fisca_learner, fisca_p1, right=True)

    [certificate] = Certificate.objects.filter(user=fisca_learner)
    assert certificate.partie == fisca_p1
    page = client.get(f"/fr/verify/{certificate.public_id}/").content.decode()
    assert "Sécurité, schémas et distribution" in page


def test_compta_and_fisca_part_one_give_two_distinct_certificates(learner, promotion, partie, module, fisca_p1,
                                                                     question_factory):
    from conftest import enroll

    learner.first_name, learner.last_name = "Awa", "Nkoulou"
    learner.save()
    enroll(learner, promotion)
    Enrollment.objects.create(user=learner, formation=fisca_p1.formation, source=Enrollment.Source.CATALOG)
    Section.objects.create(module=module, title_fr="Loi d'Ohm", order=1)
    for _ in range(4):
        question_factory(module, usage="exam")
    question_factory(module)
    for p in (partie, fisca_p1):
        for m in p.modules.all():
            complete_module(learner, m)
        take_exam(learner, p, right=True)

    certificates = Certificate.objects.filter(user=learner).order_by("partie__formation__order")
    assert [(c.partie.formation.slug, c.partie.slug) for c in certificates] == [("compta", "p1"), ("fisca", "p1")]
    assert certificates[0].public_id != certificates[1].public_id


# --- US-79 : formation fermée pendant la fumée de production --------------------------------------------------------


@pytest.fixture
def closed_fisca(fisca_p1):
    formation = fisca_p1.formation
    formation.is_open = False
    formation.save()
    return formation


def test_a_closed_fisca_is_absent_from_the_catalogue(client, closed_fisca):
    assert closed_fisca not in [row["formation"] for row in client.get("/fr/catalogue/").context["rows"]]


def test_a_closed_fisca_refuses_free_enrollment(client, learner, closed_fisca):
    client.force_login(learner)

    response = client.post(f"/fr/catalogue/{closed_fisca.public_id}/inscription/")

    assert response.status_code == 404
    assert not Enrollment.objects.filter(user=learner).exists()


def test_the_admin_enrolled_test_account_follows_a_closed_fisca(client, learner, closed_fisca, fisca_p1):
    Enrollment.objects.create(user=learner, formation=closed_fisca, source=Enrollment.Source.ADMIN)
    client.force_login(learner)

    assert client.get(f"/fr/sections/{first_section(fisca_p1).public_id}/").status_code == 200
