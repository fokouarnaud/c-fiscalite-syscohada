"""US-60 et US-61 (formation `fisca`) : deux formations côte à côte, sans fuite de l'une vers l'autre."""
import pytest

from accounts.models import Promotion, User
from assessments.models import Assessment
from assessments.services import save_answer, start_attempt, submit_attempt
from catalog.models import Enrollment
from conftest import enroll, make_question
from courses.models import Formation, Module, Partie

ENGINE_PATH = 'd="M8 7h6"'  # tracé propre à templates/icons/receipt.svg
CPU_PATH = 'd="M9 4v16"'  # tracé propre à templates/icons/ledger.svg


@pytest.fixture
def fisca(db):
    formation = Formation.objects.create(
        title_fr="Fiscalité CGI Cameroun", slug="fisca", order=2, is_open=True, icon="receipt",
    )
    partie = Partie.objects.create(formation=formation, title_fr="Sécurité, schémas et distribution", order=1, slug="p1")
    Module.objects.create(partie=partie, title_fr="La sécurité électrique", order=1, duration_hours=8)
    return formation


@pytest.fixture
def fisca_module(fisca):
    return Module.objects.get(partie__formation=fisca)


@pytest.fixture
def fisca_promotion(fisca):
    return Promotion.objects.create(name="Électrotechnique 2026", formation=fisca)


@pytest.fixture
def fisca_trainer(fisca_promotion):
    user = User.objects.create_user(username="ngono", password="x-Secret-123", role=User.Role.TRAINER)
    fisca_promotion.trainers.add(user)
    return user


@pytest.fixture
def compta_trainer(promotion):
    user = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(user)
    return user


@pytest.fixture
def both(learner, promotion, fisca_promotion):
    """Apprenant inscrit à `compta` (promotion de la fixture commune) et à `fisca`."""
    enroll(learner, promotion)
    return enroll(learner, fisca_promotion)


def submitted_quiz(user, module):
    make_question(module)
    attempt = start_attempt(user, Assessment.quiz_for(module))
    for aq in attempt.attempt_questions.select_related("question"):
        ids = aq.question.choices.filter(is_correct=True).values_list("public_id", flat=True)[:1]
        save_answer(attempt, aq.question.public_id, list(ids))
    return submit_attempt(attempt)


# --- US-60 : l'apprenant ---------------------------------------------------------------------------------------------


def test_joining_fisca_from_the_catalogue_does_not_enroll_in_compta(client, learner, fisca, partie):
    client.force_login(learner)

    client.post(f"/fr/catalogue/{fisca.public_id}/inscription/")

    assert list(Enrollment.objects.filter(user=learner).values_list("formation__slug", flat=True)) == ["fisca"]


def test_dashboard_shows_both_formations_in_catalogue_order_each_with_its_icon(client, both):
    client.force_login(both)

    response = client.get("/fr/")

    assert [row["partie"].formation.slug for row in response.context["parts"]] == ["compta", "fisca"]
    html = response.content.decode()
    compta, fisca = (tab.split("</a>")[0] for tab in html.split('class="formation-tab"')[1:3])
    assert CPU_PATH in compta and ENGINE_PATH not in compta
    assert ENGINE_PATH in fisca and CPU_PATH not in fisca


# --- US-61 : le formateur ne voit que la formation de ses promotions -------------------------------------------------


def test_fisca_trainer_table_holds_only_the_fisca_formation(client, fisca_trainer, both):
    client.force_login(fisca_trainer)

    tables = client.get("/fr/formateur/").context["tables"]

    assert [t["formation"].slug for t in tables] == ["fisca"]


def test_fisca_trainer_cannot_read_the_compta_attempt_of_a_shared_learner(client, fisca_trainer, both, module):
    attempt = submitted_quiz(both, module)  # `module` : fixture commune, dans `compta`
    client.force_login(fisca_trainer)

    assert client.get(f"/fr/formateur/tentatives/{attempt.public_id}/").status_code == 404


def test_compta_trainer_cannot_read_the_fisca_attempt_of_a_shared_learner(client, compta_trainer, both, fisca_module):
    attempt = submitted_quiz(both, fisca_module)
    client.force_login(compta_trainer)

    assert client.get(f"/fr/formateur/tentatives/{attempt.public_id}/").status_code == 404


def test_fisca_trainer_still_reads_the_fisca_attempt_of_a_shared_learner(client, fisca_trainer, both, fisca_module):
    attempt = submitted_quiz(both, fisca_module)
    client.force_login(fisca_trainer)

    assert client.get(f"/fr/formateur/tentatives/{attempt.public_id}/").status_code == 200


def test_compta_trainer_question_stats_ignore_fisca_questions(client, compta_trainer, both, module, fisca_module):
    submitted_quiz(both, module)
    submitted_quiz(both, fisca_module)
    client.force_login(compta_trainer)

    stats = client.get("/fr/formateur/questions/").context["stats"]

    assert {s["question"].module.partie.formation.slug for s in stats} == {"compta"}


def test_fisca_trainer_csv_export_lists_no_compta_module(client, fisca_trainer, both, module):
    client.force_login(fisca_trainer)

    csv = client.get("/fr/formateur/export.csv").content.decode("utf-8")

    assert "La sécurité électrique" in csv
    assert module.title not in csv


# --- Tableau de bord à plusieurs formations : une formation par bloc, reprise, parties repliées ----------------------


def sections(module, n):
    from courses.models import Section

    return [Section.objects.create(module=module, title_fr=f"Section {k}", order=k) for k in range(1, n + 1)]


@pytest.fixture
def two_parts(partie, module, fisca_module):
    """`compta` : Partie 1 (un module de 2 sections) et Partie 2 (un module de 2 sections) ; `fisca` : un module de 2 sections."""
    second_partie = Partie.objects.create(formation=partie.formation, title_fr="Courant alternatif", order=2, slug="p2")
    second = Module.objects.create(partie=second_partie, title_fr="Le courant alternatif", order=1, duration_hours=8)
    for m in (module, second, fisca_module):
        sections(m, 2)
    return module, second


def test_dashboard_groups_parts_by_formation(client, both, two_parts):
    first, _ = two_parts
    client.force_login(both)

    response = client.get("/fr/")

    blocks = response.context["formations"]
    assert [b["formation"].slug for b in blocks] == ["compta", "fisca"]
    assert [[row["partie"].slug for row in b["parts"]] for b in blocks] == [["p1", "p2"], ["p1"]]
    assert blocks[0]["resume"] == first and blocks[0]["progress"] == 0


def test_resume_moves_past_finished_modules_and_formation_progress_counts_their_steps(client, both, two_parts):
    from progress.services import mark_section_viewed

    first, second = two_parts
    for section in first.sections.all():
        mark_section_viewed(both, section)
    client.force_login(both)

    compta = client.get("/fr/").context["formations"][0]

    assert compta["resume"] == second
    assert compta["progress"] == 50  # 2 sections vues sur 4 dans la formation


def test_finished_formation_has_no_resume_link(client, both, two_parts):
    from progress.services import mark_section_viewed

    for m in two_parts:
        for section in m.sections.all():
            mark_section_viewed(both, section)
    client.force_login(both)

    compta = client.get("/fr/").context["formations"][0]

    assert (compta["resume"], compta["resume_section"]) == (None, None)
    assert compta["progress"] == 100


# --- « Mes cours » : une formation à la fois, reprise à la section, plan numéroté M1, M2… ---------------------------


def test_dashboard_shows_one_formation_at_a_time(client, both, two_parts, fisca_module):
    first, _ = two_parts
    client.force_login(both)

    html = client.get("/fr/").content.decode()

    assert first.title in html and fisca_module.title not in html


def test_the_selector_switches_to_the_other_formation(client, both, two_parts, fisca, fisca_module):
    first, _ = two_parts
    client.force_login(both)

    response = client.get(f"/fr/?formation={fisca.public_id}")

    html = response.content.decode()
    assert response.context["current"]["formation"] == fisca
    assert fisca_module.title in html and first.title not in html
    assert f'href="?formation={fisca.public_id}" aria-current="page"' in html


def test_default_formation_is_the_last_one_worked_on(client, both, two_parts, fisca, fisca_module):
    from progress.services import mark_section_viewed

    first, _ = two_parts
    mark_section_viewed(both, first.sections.first())
    mark_section_viewed(both, fisca_module.sections.first())
    client.force_login(both)

    assert client.get("/fr/").context["current"]["formation"] == fisca


def test_a_formation_outside_the_enrollments_or_unknown_falls_back_to_the_default(client, both, two_parts, learner):
    other = Formation.objects.create(title_fr="Autre formation", slug="autre", order=3, is_open=True, icon="ledger")
    Module.objects.create(
        partie=Partie.objects.create(formation=other, title_fr="Partie secrète", order=1, slug="p1"),
        title_fr="Module secret", order=1, duration_hours=1,
    )
    client.force_login(both)

    for query in (f"?formation={other.public_id}", "?formation=pas-un-uuid"):
        response = client.get(f"/fr/{query}")
        assert response.status_code == 200
        assert response.context["current"]["formation"].slug == "compta"
        assert "Module secret" not in response.content.decode()


def test_resume_links_to_the_first_unread_section_then_to_the_quiz(client, both, two_parts):
    from progress.services import mark_section_viewed

    first, _ = two_parts
    s1, s2 = first.sections.all()
    client.force_login(both)
    assert f'class="btn resume-go" href="/fr/sections/{s1.public_id}/"' in client.get("/fr/").content.decode()

    mark_section_viewed(both, s1)
    assert f'class="btn resume-go" href="/fr/sections/{s2.public_id}/"' in client.get("/fr/").content.decode()

    make_question(first)  # le module a désormais un quiz ; ses sections sont toutes lues
    mark_section_viewed(both, s2)
    html = client.get("/fr/").content.decode()
    assert f'method="post" action="/fr/quiz/{first.public_id}/"' in html  # lancer un quiz modifie l'état : POST
    assert 'class="btn resume-go" type="submit"' in html


def test_modules_are_numbered_across_the_formation(client, both, two_parts):
    _, second = two_parts
    client.force_login(both)

    html = client.get("/fr/").content.decode()

    row = html.split(f'href="/fr/modules/{second.public_id}/"')[1].split("</a>")[0]
    assert '<span class="num">M2</span>' in row


def test_every_part_of_the_plan_is_unfolded_with_its_exam(client, both, two_parts):
    first, second = two_parts
    client.force_login(both)

    html = client.get("/fr/").content.decode()

    assert "<details" not in html.split('class="plan"')[1]
    assert html.count('class="plan-exam') == 2


def test_the_selector_appears_only_for_a_learner_of_two_formations(client, both, learner, two_parts, fisca):
    client.force_login(both)
    html = client.get("/fr/").content.decode()
    assert f'href="?formation={fisca.public_id}"' in html

    solo = User.objects.create_user(username="solo", password="x-Secret-123")
    Enrollment.objects.create(user=solo, formation=fisca)
    client.force_login(solo)
    assert 'class="formation-tabs"' not in client.get("/fr/").content.decode()
