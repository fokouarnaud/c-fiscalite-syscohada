import pytest

from courses.models import Module, Section
from progress.services import mark_section_viewed


@pytest.fixture
def course(partie, module):
    second = Module.objects.create(partie=partie, title_fr="Rapports", order=2)
    s1 = Section.objects.create(module=module, title_fr="Intro", order=1)
    s2 = Section.objects.create(module=module, title_fr="Cas", order=2)
    s3 = Section.objects.create(module=second, title_fr="Plan", order=1)
    return {"modules": [module, second], "sections": [s1, s2, s3]}


@pytest.mark.django_db
def test_section_page_outline_marks_current_module_section_and_viewed_state(client, enrolled, course):
    s1, s2, s3 = course["sections"]
    mark_section_viewed(enrolled, s1)
    client.force_login(enrolled)
    outline = client.get(f"/fr/sections/{s2.public_id}/").context["outline"]
    assert [(row["module"], row["current"]) for row in outline] == [(course["modules"][0], True), (course["modules"][1], False)]
    assert [(i["section"], i["viewed"], i["current"]) for i in outline[0]["sections"]] == [
        (s1, True, False),
        (s2, True, True),  # ouverte à l'instant, donc vue
    ]


@pytest.mark.django_db
def test_module_page_outline_flags_completed_modules(client, enrolled, course):
    s1, s2, s3 = course["sections"]
    mark_section_viewed(enrolled, s3)
    client.force_login(enrolled)
    outline = client.get(f"/fr/modules/{course['modules'][0].public_id}/").context["outline"]
    assert [row["done"] for row in outline] == [False, True]


@pytest.mark.django_db
def test_module_page_says_whether_a_quiz_is_available(client, enrolled, course, question_factory):
    client.force_login(enrolled)
    assert client.get(f"/fr/modules/{course['modules'][0].public_id}/").context["has_quiz"] is False
    question_factory(course["modules"][0])
    assert client.get(f"/fr/modules/{course['modules'][0].public_id}/").context["has_quiz"] is True


@pytest.mark.django_db
def test_dashboard_reports_module_status_and_exam_availability(client, enrolled, course):
    for s in course["sections"][:2]:
        mark_section_viewed(enrolled, s)
    client.force_login(enrolled)
    [row] = client.get("/fr/").context["parts"]
    assert [(m["module"], m["done"]) for m in row["modules"]] == [(course["modules"][0], True), (course["modules"][1], False)]
    assert row["exam_unlocked"] is False


@pytest.mark.django_db
def test_outline_numbers_modules_across_the_formation_like_the_dashboard(client, enrolled, course, partie):
    from courses.models import Partie

    second_part = Partie.objects.create(formation=partie.formation, title_fr="Courant alternatif", order=2, slug="p2")
    later = Module.objects.create(partie=second_part, title_fr="Le courant alternatif", order=1)
    section = Section.objects.create(module=later, title_fr="Sinusoïde", order=1)
    client.force_login(enrolled)

    response = client.get(f"/fr/sections/{section.public_id}/")

    assert [row["number"] for row in response.context["outline"]] == [3]  # deux modules dans la Partie 1
    assert "M3. Le courant alternatif" in response.content.decode()
