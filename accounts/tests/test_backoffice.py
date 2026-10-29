import pytest

from accounts.importing import import_learners
from accounts.models import User
from assessments.models import Question


def make(username, role):
    return User.objects.create_user(username=username, password="x-Secret-123", role=role)


@pytest.mark.django_db
def test_trainer_gets_back_office_access_to_questions_only(client):
    trainer = make("macaire", User.Role.TRAINER)
    client.force_login(trainer)
    assert client.get("/fr/admin/assessments/question/").status_code == 200
    assert client.get("/fr/admin/accounts/user/").status_code == 403


@pytest.mark.django_db
def test_learner_has_no_back_office_access(client):
    client.force_login(make("awa", User.Role.LEARNER))
    response = client.get("/fr/admin/assessments/question/")
    assert response.status_code == 302  # renvoyé vers la connexion de l'admin


@pytest.mark.django_db
def test_platform_admin_manages_promotions_and_users(client):
    client.force_login(make("chef", User.Role.ADMIN))
    assert client.get("/fr/admin/accounts/promotion/add/").status_code == 200
    assert client.get("/fr/admin/accounts/user/").status_code == 200


@pytest.mark.django_db
def test_demoting_a_trainer_removes_back_office_access(client):
    trainer = make("macaire", User.Role.TRAINER)
    trainer.role = User.Role.LEARNER
    trainer.save()
    trainer.refresh_from_db()
    assert not trainer.is_staff
    assert not trainer.groups.exists()


@pytest.mark.django_db
def test_publish_action_publishes_valid_questions_and_keeps_invalid_ones_as_drafts(client, module, question_factory):
    valid = question_factory(module, publish=False)
    invalid = question_factory(module, publish=False)
    invalid.reviewed_en = False
    invalid.save()
    client.force_login(make("macaire", User.Role.TRAINER))
    response = client.post(
        "/fr/admin/assessments/question/",
        {"action": "publish_selected", "_selected_action": [valid.pk, invalid.pk]},
        follow=True,
    )
    valid.refresh_from_db()
    invalid.refresh_from_db()
    assert valid.status == Question.Status.PUBLISHED
    assert invalid.status == Question.Status.DRAFT
    messages = [str(m) for m in response.context["messages"]]
    assert any("1" in m for m in messages)


CSV_TEXT = "username;first_name;last_name;email\nawa;Awa;Nkoulou;awa@example.cm\nali;Ali;Mbarga;\n"


@pytest.mark.django_db
def test_csv_import_creates_learners_in_the_promotion(promotion):
    report = import_learners(CSV_TEXT, promotion)
    awa = User.objects.get(username="awa")
    assert awa.enrollments.get().promotion == promotion
    assert awa.is_learner
    assert awa.get_full_name() == "Awa Nkoulou"
    assert [row["username"] for row in report.created] == ["awa", "ali"]


@pytest.mark.django_db
def test_csv_import_gives_each_learner_a_working_initial_password(promotion):
    report = import_learners(CSV_TEXT, promotion)
    row = report.created[0]
    assert len(row["password"]) >= 10
    assert User.objects.get(username=row["username"]).check_password(row["password"])
    assert report.created[0]["password"] != report.created[1]["password"]


@pytest.mark.django_db
def test_csv_import_skips_existing_usernames(promotion):
    User.objects.create_user(username="awa", password="x-Secret-123")
    report = import_learners(CSV_TEXT, promotion)
    assert report.skipped == ["awa"]
    assert [row["username"] for row in report.created] == ["ali"]


@pytest.mark.django_db
def test_csv_import_rejects_a_file_without_username_column(promotion):
    with pytest.raises(ValueError):
        import_learners("nom;prenom\nNkoulou;Awa\n", promotion)


@pytest.mark.django_db
def test_admin_can_upload_learner_csv_for_a_promotion(client, promotion):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client.force_login(make("chef", User.Role.ADMIN))
    response = client.post(
        f"/fr/admin/accounts/promotion/{promotion.pk}/import/",
        {"file": SimpleUploadedFile("liste.csv", CSV_TEXT.encode("utf-8"))},
    )
    assert response.status_code == 200
    assert User.objects.filter(enrollments__promotion=promotion).count() == 2
    assert [row["username"] for row in response.context["report"].created] == ["awa", "ali"]


@pytest.mark.django_db
def test_trainer_cannot_import_learners(client, promotion):
    client.force_login(make("macaire", User.Role.TRAINER))
    assert client.get(f"/fr/admin/accounts/promotion/{promotion.pk}/import/").status_code == 403


@pytest.mark.django_db
def test_trainer_marks_selected_questions_as_reviewed_in_both_languages(client, module, question_factory):
    first = question_factory(module, publish=False)
    second = question_factory(module, publish=False)
    untouched = question_factory(module, publish=False)
    Question.objects.update(reviewed_fr=False, reviewed_en=False)
    client.force_login(make("macaire", User.Role.TRAINER))
    response = client.post(
        "/fr/admin/assessments/question/",
        {"action": "mark_reviewed", "_selected_action": [first.pk, second.pk]},
        follow=True,
    )
    reviewed = set(Question.objects.filter(reviewed_fr=True, reviewed_en=True).values_list("pk", flat=True))
    assert reviewed == {first.pk, second.pk}
    assert untouched.pk not in reviewed
    assert any("2" in str(m) for m in response.context["messages"])


@pytest.mark.django_db
def test_marking_reviewed_does_not_publish_by_itself(client, module, question_factory):
    question = question_factory(module, publish=False)
    client.force_login(make("macaire", User.Role.TRAINER))
    client.post("/fr/admin/assessments/question/", {"action": "mark_reviewed", "_selected_action": [question.pk]})
    question.refresh_from_db()
    assert question.status == Question.Status.DRAFT


@pytest.mark.django_db
def test_a_trainer_may_edit_the_lines_of_a_journal_question_but_not_the_rates():
    """US-04 : le formateur corrige les écritures attendues ; les taux du CGI restent à l'administrateur."""
    trainer = make("macaire", User.Role.TRAINER)

    assert trainer.has_perm("assessments.change_journalline")
    assert not trainer.has_perm("referentiel.change_fiscalparameter")


@pytest.mark.django_db
def test_the_platform_admin_manages_the_rates_and_the_chart_of_accounts(client):
    """US-61 et US-63 : paramètres fiscaux et plan comptable dans le back-office."""
    client.force_login(make("chef", User.Role.ADMIN))

    assert client.get("/fr/admin/referentiel/fiscalparameter/add/").status_code == 200
    assert client.get("/fr/admin/referentiel/syscohadaaccount/").status_code == 200


@pytest.mark.django_db
def test_the_rate_page_lists_the_questions_to_review(client, module):
    """US-62 : la fiche d'un taux affiche les questions étiquetées avec sa clé."""
    from decimal import Decimal

    from referentiel.models import FiscalParameter

    parameter = FiscalParameter.objects.create(key="tva.taux_global", exercice=2026, value=Decimal("19.25"), unit="%")
    Question.objects.create(module=module, prompt_fr="TVA sur une facture ?", params="tva.taux_global", external_id="C-9")
    Question.objects.create(module=module, prompt_fr="Sans rapport ?", params="is.taux", external_id="C-10")
    client.force_login(make("chef", User.Role.ADMIN))

    html = client.get(f"/fr/admin/referentiel/fiscalparameter/{parameter.pk}/change/").content.decode()

    assert "TVA sur une facture ?" in html
    assert "Sans rapport ?" not in html


@pytest.mark.parametrize("path, fields", [
    ("courses/formation", ("title_fr", "title_en", "description_fr", "description_en")),
    ("courses/section", ("title_fr", "title_en", "body_md_fr", "body_md_en")),
    ("assessments/question", ("prompt_fr", "prompt_en", "explanation_fr", "explanation_en")),
])
@pytest.mark.django_db
def test_us60_back_office_edits_content_in_french_and_in_english(client, path, fields):
    """US-60 : formations, sections et questions s'éditent en FR et en EN dans le back-office."""
    client.force_login(make("ventisax", User.Role.ADMIN))

    form = client.get(f"/fr/admin/{path}/add/").context["adminform"].form

    assert set(fields) <= set(form.fields)
