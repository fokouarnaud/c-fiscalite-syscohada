"""US-48, US-53 et US-56 : une troisième partie de quatre modules se suit sans verrou ; son examen et son certificat ne dépendent que d'elle."""
import pytest

from assessments.models import Assessment
from certificates.models import Badge, Certificate
from certificates.tests.test_achievements import complete_module, take_exam
from courses.models import Module, Partie, Section

P3_MODULES = ("Les amplificateurs à transistor", "Les oscillateurs", "Le transformateur", "Les alimentations")


@pytest.fixture
def part_three(partie, question_factory):
    """Partie 3 de la même formation : M8 à M11, une section et un quiz chacun, une banque d'examen."""
    p3 = Partie.objects.create(formation=partie.formation, title_fr="Amplification, oscillateurs et alimentations", order=3, slug="p3")
    for order, title in enumerate(P3_MODULES, start=1):
        module = Module.objects.create(partie=p3, title_fr=title, order=order, duration_hours=8)
        Section.objects.create(module=module, title_fr=f"Section de {title}", order=1)
        question_factory(module)
        question_factory(module, usage="exam")
    Assessment.exam_for(p3)
    return p3


@pytest.fixture
def named(enrolled):
    enrolled.first_name, enrolled.last_name = "Awa", "Nkoulou"
    enrolled.save()
    return enrolled


@pytest.fixture
def part_one_course(partie, module, question_factory):
    Section.objects.create(module=module, title_fr="Loi d'Ohm", order=1)
    question_factory(module)
    for _ in range(4):
        question_factory(module, usage="exam")
    return partie


@pytest.mark.django_db
def test_part_three_section_opens_without_passing_the_previous_parts(client, enrolled, part_one_course, part_three):
    section = Section.objects.filter(module__partie=part_three).first()
    client.force_login(enrolled)

    assert client.get(f"/fr/sections/{section.public_id}/").status_code == 200


@pytest.mark.django_db
def test_part_three_section_stays_closed_to_a_learner_not_enrolled(client, part_three):
    from accounts.models import User

    outsider = User.objects.create_user(username="intrus", password="x-Secret-123")
    section = Section.objects.filter(module__partie=part_three).first()
    client.force_login(outsider)

    assert client.get(f"/fr/sections/{section.public_id}/").status_code in (302, 404)


@pytest.mark.django_db
def test_part_three_exam_needs_all_four_of_its_modules(named, part_one_course, part_three):
    from progress.services import exam_unlocked

    m8, m9, m10, m11 = part_three.modules.order_by("order")
    for module in (m8, m9, m10):
        complete_module(named, module)
    assert not exam_unlocked(named, part_three)

    complete_module(named, m11)

    assert exam_unlocked(named, part_three)
    assert not exam_unlocked(named, part_one_course)


@pytest.mark.django_db
def test_passing_part_three_issues_a_third_distinct_certificate_and_badge(named, part_one_course, module, part_three):
    complete_module(named, module)
    take_exam(named, part_one_course, right=True)
    for p3_module in part_three.modules.all():
        complete_module(named, p3_module)

    take_exam(named, part_three, right=True)

    certificates = Certificate.objects.filter(user=named).order_by("partie__order")
    assert [c.partie.slug for c in certificates] == ["p1", "p3"]
    assert certificates[0].public_id != certificates[1].public_id
    assert set(Badge.objects.filter(user=named, kind="partie").values_list("partie__slug", flat=True)) == {"p1", "p3"}


@pytest.mark.django_db
def test_failing_part_three_issues_no_certificate_for_it(named, part_three):
    for p3_module in part_three.modules.all():
        complete_module(named, p3_module)

    take_exam(named, part_three, right=False)

    assert not Certificate.objects.filter(user=named, partie=part_three).exists()


@pytest.mark.django_db
def test_part_three_certificate_is_publicly_verifiable(client, named, part_three):
    for p3_module in part_three.modules.all():
        complete_module(named, p3_module)
    take_exam(named, part_three, right=True)
    certificate = Certificate.objects.get(user=named, partie=part_three)

    response = client.get(f"/fr/verify/{certificate.public_id}/")

    assert response.status_code == 200
    assert "Amplification, oscillateurs et alimentations" in response.content.decode()


# --- US-56 : l'espace formateur couvre la Partie 3 sans changement de code -------------------------------------------


@pytest.fixture
def trainer(promotion):
    from accounts.models import User

    user = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(user)
    return user


@pytest.mark.django_db
def test_trainer_table_has_part_three_modules_and_exam_column(client, trainer, enrolled, module, part_three):
    client.force_login(trainer)

    response = client.get("/fr/formateur/")
    [table] = response.context["tables"]

    assert [m.title for m in table["modules"]] == ["Sécurité dans les travaux", *P3_MODULES]
    assert ">Examen P2</th>" in response.content.decode()  # deuxième partie de cette formation de test : p1 puis p3


@pytest.mark.django_db
def test_csv_export_has_the_part_three_module_columns(client, trainer, enrolled, module, part_three):
    client.force_login(trainer)

    header, *rows = client.get("/fr/formateur/export.csv").content.decode("utf-8-sig").splitlines()

    assert all(title in header for title in P3_MODULES)
    assert any(enrolled.username in row for row in rows)


@pytest.mark.django_db
def test_trainer_of_another_promotion_does_not_see_part_three_learners(client, enrolled, module, part_three):
    from accounts.models import Promotion, User

    stranger = User.objects.create_user(username="autre", password="x-Secret-123", role=User.Role.TRAINER)
    other = Promotion.objects.create(name="Autre promo", formation=part_three.formation)
    other.trainers.add(stranger)
    client.force_login(stranger)

    header_and_rows = client.get("/fr/formateur/export.csv").content.decode("utf-8-sig").splitlines()

    assert all(enrolled.username not in row for row in header_and_rows[1:])


@pytest.mark.django_db
def test_deadline_targets_list_modules_part_by_part(client, trainer, promotion, module, part_three):
    """US-56 : sur la page des dates limites, les quiz suivent l'ordre du cours (partie, puis module), M8 à M11 après M1."""
    second = Module.objects.create(partie=module.partie, title_fr="La diode", order=2, duration_hours=8)
    client.force_login(trainer)

    [target] = client.get("/fr/formateur/echeances/").context["targets"]

    assert [m.title for m in target["modules"]] == [module.title, second.title, *P3_MODULES]
    assert [p.slug for p in target["parties"]] == ["p1", "p3"]


@pytest.mark.django_db
def test_dashboard_names_each_part_exam_and_the_formation_once(client, enrolled, part_one_course, part_three):
    """Tableau de bord à plusieurs parties : chaque carte d'examen dit sa partie ; la formation n'est nommée qu'une fois."""
    client.force_login(enrolled)

    html = client.get("/fr/").content.decode()

    assert "Examen de la Partie 1" in html and "Examen de la Partie 3" in html
    assert html.count('course-formation"') == 1


@pytest.mark.django_db
def test_catalogue_and_dashboard_number_the_parts(client, enrolled, part_one_course, part_three):
    """Les descriptions renvoient aux « Parties 1 et 2 » : le catalogue et le tableau de bord numérotent donc chaque partie."""
    formation = part_three.formation
    formation.is_open = True
    formation.save()

    fiche = client.get(f"/fr/catalogue/{formation.public_id}/").content.decode()
    client.force_login(enrolled)
    dashboard = client.get("/en/").content.decode()

    assert "Partie 1 :" in fiche and "Partie 3 :" in fiche
    assert "Part 3:" in dashboard
