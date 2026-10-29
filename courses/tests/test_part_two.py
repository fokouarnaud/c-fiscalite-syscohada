"""US-40 et US-44 : une seconde partie se suit sans verrou ; son examen et son certificat ne dépendent que d'elle."""
import pytest

from assessments.models import Assessment
from certificates.models import Badge, Certificate
from certificates.tests.test_achievements import complete_module, take_exam
from courses.models import Module, Partie, Section


@pytest.fixture
def part_two(partie, question_factory):
    """Partie 2 de la même formation : un module, une section, un quiz et une banque d'examen."""
    p2 = Partie.objects.create(formation=partie.formation, title_fr="Courant alternatif et filtres", order=2, slug="p2")
    m5 = Module.objects.create(partie=p2, title_fr="Le courant alternatif", order=1, duration_hours=8)
    Section.objects.create(module=m5, title_fr="La sinusoïde", order=1)
    question_factory(m5)
    for _ in range(4):
        question_factory(m5, usage="exam")
    Assessment.exam_for(p2)
    return p2


@pytest.fixture
def part_one_course(partie, module, question_factory):
    Section.objects.create(module=module, title_fr="Loi d'Ohm", order=1)
    question_factory(module)
    for _ in range(4):
        question_factory(module, usage="exam")
    return partie


@pytest.fixture
def named(enrolled):
    enrolled.first_name, enrolled.last_name = "Awa", "Nkoulou"
    enrolled.save()
    return enrolled


@pytest.mark.django_db
def test_part_two_section_opens_without_passing_part_one(client, enrolled, part_one_course, part_two):
    section = Section.objects.get(module__partie=part_two)
    client.force_login(enrolled)

    assert client.get(f"/fr/sections/{section.public_id}/").status_code == 200


@pytest.mark.django_db
def test_part_two_exam_unlocks_with_its_own_modules_only(client, named, part_one_course, part_two):
    from progress.services import exam_unlocked

    complete_module(named, part_two.modules.get())

    assert exam_unlocked(named, part_two)
    assert not exam_unlocked(named, part_one_course)


@pytest.mark.django_db
def test_passing_part_two_issues_its_own_certificate_and_badge(named, part_one_course, module, part_two):
    complete_module(named, module)
    take_exam(named, part_one_course, right=True)
    complete_module(named, part_two.modules.get())

    take_exam(named, part_two, right=True)

    certificates = Certificate.objects.filter(user=named).order_by("partie__order")
    assert [c.partie.slug for c in certificates] == ["p1", "p2"]
    assert certificates[0].public_id != certificates[1].public_id
    assert set(Badge.objects.filter(user=named, kind="partie").values_list("partie__slug", flat=True)) == {"p1", "p2"}


@pytest.mark.django_db
def test_failing_part_two_leaves_the_part_one_certificate_alone(named, part_one_course, module, part_two):
    complete_module(named, module)
    take_exam(named, part_one_course, right=True)
    complete_module(named, part_two.modules.get())

    take_exam(named, part_two, right=False)

    assert list(Certificate.objects.filter(user=named).values_list("partie__slug", flat=True)) == ["p1"]


# --- US-47 : l'espace formateur couvre la Partie 2 sans changement de code -------------------------------------------


@pytest.fixture
def trainer(promotion):
    from accounts.models import User

    user = User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER)
    promotion.trainers.add(user)
    return user


@pytest.mark.django_db
def test_trainer_table_has_part_two_modules_and_exam(client, trainer, enrolled, module, part_two):
    client.force_login(trainer)

    [table] = client.get("/fr/formateur/").context["tables"]

    assert [m.title for m in table["modules"]] == ["Sécurité dans les travaux", "Le courant alternatif"]
    assert [p.slug for p in table["parties"]] == ["p1", "p2"]


@pytest.mark.django_db
def test_csv_export_has_a_part_two_module_column(client, trainer, enrolled, module, part_two):
    client.force_login(trainer)

    header = client.get("/fr/formateur/export.csv").content.decode("utf-8-sig").splitlines()[0]

    assert "Le courant alternatif" in header


@pytest.mark.django_db
def test_trainer_table_abbreviates_exam_columns_with_a_legend(client, trainer, enrolled, module, part_two):
    """Deux parties : colonnes « Examen P1 / P2 » courtes, titres complets dans la légende (comme M1… pour les modules)."""
    client.force_login(trainer)

    html = client.get("/fr/formateur/").content.decode()

    assert ">Examen P1</th>" in html and ">Examen P2</th>" in html
    assert "P2 : Courant alternatif et filtres" in html
