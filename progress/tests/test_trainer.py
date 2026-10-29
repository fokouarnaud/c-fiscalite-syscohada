import csv
import io

import pytest

from conftest import enroll

from accounts.models import Promotion, User
from assessments.models import Assessment
from assessments.services import save_answer, start_attempt, submit_attempt
from courses.models import Section
from progress.services import mark_section_viewed


@pytest.fixture
def trainer(promotion):
    user = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(user)
    return user


@pytest.fixture
def outsider(partie):
    other = Promotion.objects.create(name="Jan 2027", formation=partie.formation)
    return enroll(User.objects.create_user(username="zoe", password="x-Secret-123"), other)


@pytest.fixture
def scored(enrolled, partie, module, question_factory):
    """L'apprenant a terminé le module et obtenu 100 % à l'examen."""
    section = Section.objects.create(module=module, title_fr="Cours", order=1)
    mark_section_viewed(enrolled, section)
    question_factory(module, usage="exam")
    attempt = start_attempt(enrolled, Assessment.exam_for(partie))
    for aq in attempt.attempt_questions.all():
        save_answer(attempt, aq.question.public_id, aq.question.choices.filter(is_correct=True).values_list("public_id", flat=True))
    submit_attempt(attempt)
    return enrolled


@pytest.mark.django_db
def test_trainer_table_lists_only_learners_of_their_promotions(client, trainer, scored, outsider):
    client.force_login(trainer)
    response = client.get("/fr/formateur/")
    assert response.status_code == 200
    assert [row["learner"] for row in response.context["rows"]] == [scored]


@pytest.mark.django_db
def test_trainer_table_shows_module_completion_and_best_exam_score_per_part(client, trainer, scored, partie):
    client.force_login(trainer)
    [row] = client.get("/fr/formateur/").context["rows"]
    assert row["modules"] == [True]
    assert row["exams"] == [{"partie": partie, "best": 100, "attempts": 1, "max_attempts": 3}]


@pytest.mark.django_db
def test_learner_cannot_open_the_trainer_table(client, enrolled):
    client.force_login(enrolled)
    assert client.get("/fr/formateur/").status_code == 403


@pytest.mark.django_db
def test_admin_sees_learners_of_every_promotion(client, scored, outsider):
    admin = User.objects.create_user(username="chef", password="x-Secret-123", role=User.Role.ADMIN)
    client.force_login(admin)
    learners = {row["learner"] for row in client.get("/fr/formateur/").context["rows"]}
    assert learners == {scored, outsider}


@pytest.mark.django_db
def test_csv_export_has_one_line_per_visible_learner(client, trainer, scored, outsider, module):
    client.force_login(trainer)
    response = client.get("/fr/formateur/export.csv")
    assert response["Content-Type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
    assert rows[0] == ["Promotion", "Identifiant", "Nom", "Sécurité dans les travaux", "Examen Habilitation et sécurité (%)", "Tentatives Habilitation et sécurité"]
    assert rows[1:] == [["Oct 2026", "awa", "", "oui", "100.00", "1"]]


@pytest.mark.django_db
def test_learner_cannot_export_csv(client, enrolled):
    client.force_login(enrolled)
    assert client.get("/fr/formateur/export.csv").status_code == 403


@pytest.mark.django_db
def test_trainer_home_redirects_to_the_progress_table(client, trainer):
    client.force_login(trainer)
    response = client.get("/fr/")
    assert response.status_code == 302
    assert response.url == "/fr/formateur/"


@pytest.mark.django_db
def test_learner_home_stays_the_course_dashboard(client, enrolled):
    client.force_login(enrolled)
    assert client.get("/fr/").status_code == 200


@pytest.mark.django_db
def test_csv_export_neutralizes_spreadsheet_formulas(client, trainer, scored):
    """US-53 : un nom saisi « =HYPERLINK(…) » s'exporte en texte inerte, précédé d'une apostrophe."""
    scored.last_name = '=HYPERLINK("http://evil.example","clic")'
    scored.save()
    client.force_login(trainer)

    body = client.get("/fr/formateur/export.csv").content.decode("utf-8-sig")

    assert "'=HYPERLINK" in body
    assert ";=HYPERLINK" not in body and "\n=HYPERLINK" not in body


@pytest.mark.django_db
def test_us53_csv_export_starts_with_a_bom_for_excel(client, trainer, scored):
    """US-53 : le fichier commence par le BOM UTF-8, sans quoi Excel lit mal les accents."""
    client.force_login(trainer)

    assert client.get("/fr/formateur/export.csv").content.startswith(b"\xef\xbb\xbf")
