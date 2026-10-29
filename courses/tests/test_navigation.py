"""Critique UX du 2026-10-26 : savoir où l'on est (fil d'Ariane, M1, M2…) et ce qu'il faut faire ensuite, à chaque page du parcours."""
import pytest

from assessments.models import Assessment
from assessments.services import save_answer, start_attempt, submit_attempt
from conftest import make_question
from courses.models import Module, Partie, Section
from progress.services import mark_section_viewed, module_number


@pytest.fixture
def course(partie, module):
    """Partie 1 : M1 (2 sections, un quiz), M2 (1 section) ; Partie 2 : M3 (2 sections)."""
    second = Module.objects.create(partie=partie, title_fr="Les schémas", order=2, duration_hours=8)
    p2 = Partie.objects.create(formation=partie.formation, title_fr="Courant alternatif", order=2, slug="p2")
    third = Module.objects.create(partie=p2, title_fr="Le courant alternatif", order=1, duration_hours=8)
    sections = {
        m: [Section.objects.create(module=m, title_fr=f"{m.title_fr} {k}", order=k) for k in range(1, n + 1)]
        for m, n in ((module, 2), (second, 1), (third, 2))
    }
    quiz = make_question(module)
    return {"modules": [module, second, third], "sections": sections, "p2": p2, "quiz": quiz}


def html(client, url):
    return client.get(url).content.decode()


# --- Numérotation M1, M2… sur toute la formation -------------------------------------------------------------------


@pytest.mark.django_db
def test_module_number_counts_the_modules_of_the_earlier_parts(course):
    assert [module_number(m) for m in course["modules"]] == [1, 2, 3]


@pytest.mark.django_db
def test_exam_page_numbers_the_missing_modules_across_the_formation(client, enrolled, course):
    client.force_login(enrolled)

    page = html(client, f"/fr/examen/{course['p2'].public_id}/")

    assert '<span class="num" aria-hidden="true">M3</span>' in page


# --- Fil d'Ariane Formation › Partie › Module --------------------------------------------------------------------


@pytest.mark.django_db
def test_section_page_has_a_breadcrumb_formation_part_module(client, enrolled, course, partie):
    third = course["modules"][2]
    client.force_login(enrolled)

    page = html(client, f"/fr/sections/{course['sections'][third][0].public_id}/")

    crumbs = page.split('<nav class="crumbs"')[1].split("</nav>")[0]
    assert f'href="/fr/?formation={partie.formation.public_id}"' in crumbs and "Comptabilité SYSCOHADA" in crumbs
    assert f'href="/fr/?formation={partie.formation.public_id}#plan-{course["p2"].public_id}"' in crumbs and "Partie 2" in crumbs
    assert f'href="/fr/modules/{third.public_id}/"' in crumbs and "M3. Le courant alternatif" in crumbs


@pytest.mark.django_db
def test_module_page_has_a_breadcrumb_and_its_number(client, enrolled, course, partie):
    second = course["modules"][1]
    client.force_login(enrolled)

    page = html(client, f"/fr/modules/{second.public_id}/")

    crumbs = page.split('<nav class="crumbs"')[1].split("</nav>")[0]
    assert "Comptabilité SYSCOHADA" in crumbs and "Partie 1" in crumbs
    assert "Les schémas" not in crumbs  # la page du module ne se cite pas elle-même
    assert '<span class="mod-num">M2</span>' in page


@pytest.mark.django_db
def test_section_page_says_where_it_stands_in_the_module(client, enrolled, course, module):
    client.force_login(enrolled)

    assert "Section 2 sur 2" in html(client, f"/fr/sections/{course['sections'][module][1].public_id}/")


# --- Page de module : le bouton principal est l'étape suivante --------------------------------------------------


def primary(page):
    """Premier bouton plein (ni fantôme ni lien de section) de la zone d'actions du module."""
    return page.split('<div class="cta-row module-next">')[1].split("</div>")[0]


@pytest.mark.django_db
def test_module_primary_action_follows_the_progress(client, enrolled, course, module):
    s1, s2 = course["sections"][module]
    second = course["modules"][1]
    client.force_login(enrolled)
    url = f"/fr/modules/{module.public_id}/"

    assert f'class="btn" href="/fr/sections/{s1.public_id}/"' in primary(html(client, url))

    mark_section_viewed(enrolled, s1)
    assert f'class="btn" href="/fr/sections/{s2.public_id}/"' in primary(html(client, url))

    mark_section_viewed(enrolled, s2)
    zone = primary(html(client, url))
    assert f'action="/fr/quiz/{module.public_id}/"' in zone and 'class="btn" type="submit"' in zone

    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    submit_attempt(attempt)
    assert f'class="btn" href="/fr/modules/{second.public_id}/"' in primary(html(client, url))


# --- Sommaire : quiz, examen, toutes les parties -------------------------------------------------------------------


@pytest.mark.django_db
def test_outline_offers_the_module_quiz_the_part_exam_and_all_parts(client, enrolled, course, module, partie):
    client.force_login(enrolled)

    page = html(client, f"/fr/sections/{course['sections'][module][0].public_id}/")

    outline = page.split('id="sommaire"')[1].split("</details>")[0]
    assert f'action="/fr/quiz/{module.public_id}/"' in outline
    assert f'href="/fr/examen/{partie.public_id}/"' in outline
    assert f'href="/fr/?formation={partie.formation.public_id}"' in outline


# --- Quiz : pas d'envoi à l'aveugle, correction filtrable ---------------------------------------------------------


@pytest.fixture
def two_questions(module):
    return [make_question(module), make_question(module)]


@pytest.mark.django_db
def test_submitting_with_unanswered_questions_asks_for_confirmation(client, enrolled, module, two_questions):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    response = client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/")

    attempt.refresh_from_db()
    assert attempt.submitted_at is None
    page = client.get(response.url).content.decode()
    assert "2 questions sans réponse" in page
    for aq in attempt.attempt_questions.all():
        assert f'href="#q-{aq.question.public_id}"' in page
    assert 'name="confirm" value="1"' in page

    client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/", {"confirm": "1"})
    attempt.refresh_from_db()
    assert attempt.submitted_at is not None


@pytest.mark.django_db
def test_a_fully_answered_attempt_is_sent_at_once(client, enrolled, module, two_questions):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    for aq in attempt.attempt_questions.select_related("question"):
        save_answer(attempt, aq.question.public_id, [aq.question.choices.get(is_correct=True).public_id])
    client.force_login(enrolled)

    client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/")

    attempt.refresh_from_db()
    assert attempt.submitted_at is not None


@pytest.mark.django_db
def test_correction_can_show_only_the_mistakes(client, enrolled, module, two_questions):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    good = attempt.attempt_questions.select_related("question").first().question
    save_answer(attempt, good.public_id, [good.choices.get(is_correct=True).public_id])
    submit_attempt(attempt)
    client.force_login(enrolled)
    url = f"/fr/tentatives/{attempt.public_id}/resultat/"

    assert len(client.get(url).context["feedback"]) == 2
    mistakes = client.get(url + "?erreurs=1")
    assert [item["question"] for item in mistakes.context["feedback"]] != [good]
    assert len(mistakes.context["feedback"]) == 1
    assert 'href="?erreurs=1"' in html(client, url)


@pytest.mark.django_db
def test_an_empty_numeric_answer_reads_no_answer(client, enrolled, module):
    from assessments.models import Question

    q = Question.objects.create(
        module=module, qtype="numeric", usage="quiz", prompt_fr="τ ?", prompt_en="τ?", numeric_value=1, unit="s",
        explanation_fr="RC.", reviewed_fr=True, reviewed_en=True,
    )
    q.publish()
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    submit_attempt(attempt)
    client.force_login(enrolled)

    page = html(client, f"/fr/tentatives/{attempt.public_id}/resultat/")

    assert "Votre réponse : <strong>Sans réponse</strong>" in page


@pytest.mark.django_db
def test_a_quiz_that_completes_the_module_points_to_the_next_one(client, enrolled, course, module):
    for s in course["sections"][module]:
        mark_section_viewed(enrolled, s)
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    submit_attempt(attempt)
    client.force_login(enrolled)

    page = html(client, f"/fr/tentatives/{attempt.public_id}/resultat/")

    second = course["modules"][1]
    assert "Module terminé" in page
    assert f'class="btn" href="/fr/modules/{second.public_id}/"' in page and "M2. Les schémas" in page


@pytest.mark.django_db
def test_a_quiz_of_an_unfinished_module_does_not_announce_the_end(client, enrolled, course, module):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    submit_attempt(attempt)
    client.force_login(enrolled)

    assert "Module terminé" not in html(client, f"/fr/tentatives/{attempt.public_id}/resultat/")


# --- En-tête : les icônes gardent un nom lisible par les lecteurs d'écran ------------------------------------------


def test_header_labels_are_visually_hidden_not_removed_on_phones():
    from pathlib import Path

    css = (Path(__file__).resolve().parents[2] / "static/acad/css/app.css").read_text(encoding="utf-8")
    assert ".topnav .label { display: none; }" not in css and ".topnav .label, .brand small { display: none; }" not in css
    assert ".brand small, .topnav .label { display: none; }" not in css
