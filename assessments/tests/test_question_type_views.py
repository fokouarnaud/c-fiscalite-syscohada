"""US-16 à US-18, US-20 : formulaire de réponse et page de tentative pour les nouveaux types de question."""
from decimal import Decimal

import pytest

from assessments.models import Assessment, Question
from assessments.services import start_attempt

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><rect width="100" height="50"/></svg>'


def published(module, qtype, **fields):
    q = Question.objects.create(
        module=module, qtype=qtype, prompt_fr="Q ?", prompt_en="Q?", reviewed_fr=True, reviewed_en=True, **fields
    )
    return q


@pytest.fixture
def numeric_q(module):
    q = published(module, "numeric", numeric_value=Decimal("1250000"), unit="FCFA", exercice=2026)
    q.publish()
    return q


@pytest.fixture
def matching_q(module):
    q = published(module, "matching")
    q.pairs.create(left_fr="R", left_en="R", right_fr="Résistance", right_en="Resistor", order=0)
    q.pairs.create(left_fr="C", left_en="C", right_fr="Condensateur", right_en="Capacitor", order=1)
    q.publish()
    return q


@pytest.fixture
def hotspot_q(module):
    q = published(module, "hotspot", hotspot_svg=SVG)
    q.choices.create(text_fr="Base", text_en="Base", is_correct=True, shape={"x": 0, "y": 0, "w": 20, "h": 20})
    q.choices.create(text_fr="Collecteur", text_en="Collector", shape={"x": 50, "y": 0, "w": 20, "h": 20})
    q.publish()
    return q


def answer_url(attempt):
    return f"/fr/tentatives/{attempt.public_id}/reponse/"


@pytest.mark.django_db
def test_numeric_answer_and_time_are_posted(client, enrolled, module, numeric_q):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    response = client.post(answer_url(attempt), {
        "question": numeric_q.public_id, "answer_text": "1 250 000 FCFA", "time_spent": "18",
    }, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    aq = attempt.attempt_questions.get()
    assert (aq.answer_text, aq.time_spent_s) == ("1 250 000 FCFA", 18)


@pytest.mark.django_db
def test_matching_pairs_are_posted_one_field_per_left_item(client, enrolled, module, matching_q):
    r, c = (str(p.public_id) for p in matching_q.pairs.all())
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    client.post(answer_url(attempt), {"question": matching_q.public_id, f"pair_{r}": r, f"pair_{c}": r})

    assert attempt.attempt_questions.get().answer_json == {r: r, c: r}


@pytest.mark.django_db
def test_malformed_pair_identifier_is_rejected(client, enrolled, module, matching_q):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    response = client.post(answer_url(attempt), {"question": matching_q.public_id, "pair_x' OR 1=1": "1"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_malformed_time_is_rejected(client, enrolled, module, numeric_q):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    response = client.post(answer_url(attempt), {"question": numeric_q.public_id, "answer_text": "1", "time_spent": "1e9x"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_attempt_page_renders_each_question_type(client, enrolled, module, numeric_q, matching_q, hotspot_q):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    html = client.get(f"/fr/tentatives/{attempt.public_id}/").content.decode()

    assert 'name="answer_text"' in html
    # Sur téléphone, le clavier des lettres doit rester accessible pour taper « FCFA » ou « % » (inputmode="decimal" n'ouvre que le pavé numérique).
    assert 'inputmode="decimal"' not in html and 'inputmode="text"' in html
    assert 'autocapitalize="off"' in html and 'autocorrect="off"' in html
    assert html.count('name="pair_') == 2
    assert "<svg" in html and 'data-zone="' in html


@pytest.mark.django_db
def test_quiz_correction_shows_the_expected_numeric_value(client, enrolled, module, numeric_q):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)
    client.post(answer_url(attempt), {"question": numeric_q.public_id, "answer_text": "5 000"})
    client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/")

    html = client.get(f"/fr/tentatives/{attempt.public_id}/resultat/").content.decode()

    assert "1 250 000 FCFA" in html and "5 000" in html


@pytest.mark.django_db
def test_schematic_edited_after_publication_is_never_rendered_if_active(client, enrolled, module, hotspot_q):
    Question.objects.filter(pk=hotspot_q.pk).update(hotspot_svg=SVG.replace("<rect", "<rect onload=alert(1)"))
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    html = client.get(f"/fr/tentatives/{attempt.public_id}/").content.decode()

    assert "onload" not in html
