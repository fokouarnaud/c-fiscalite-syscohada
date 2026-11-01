"""US-83 (U17) : la pièce citée par l'énoncé est visible pendant la tentative, en quiz comme en examen ; la balise brute
n'apparaît jamais, y compris dans l'espace formateur."""
import datetime
from decimal import Decimal

import pytest

from assessments.models import Assessment, Question
from assessments.services import start_attempt
from simulation.models import Piece


@pytest.fixture
def piece_question(module):
    piece = Piece.objects.create(
        partie=module.partie, ref="S-A-01-002", kind=Piece.Kind.MOMO_RECEIPT, issued_on=datetime.date(2026, 1, 8),
        title_fr="Reçu MTN MoMo", title_en="MTN MoMo receipt",
        payload={"fields": [{"label": {"fr": "Payeur", "en": "Payer"}, "value": "Cliente Ekane"}],
                 "totals": [{"label": {"fr": "Montant reçu", "en": "Amount received"}, "amount": 23850}]})
    question = Question.objects.create(
        module=module, qtype="numeric", usage="exam", numeric_value=Decimal("23850"), unit="FCFA", exercice=2026,
        prompt_fr="Montant encaissé ?\n\n[[piece:S-A-01-002]]", prompt_en="Amount collected?\n\n[[piece:S-A-01-002]]",
        reviewed_fr=True, reviewed_en=True)
    question.pieces.set([piece])
    question.publish()
    return question


@pytest.mark.django_db
def test_the_exam_page_shows_the_piece_of_the_prompt_without_the_raw_tag(client, enrolled, module, piece_question):
    attempt = start_attempt(enrolled, Assessment.exam_for(module.partie))
    client.force_login(enrolled)

    html = client.get(f"/fr/tentatives/{attempt.public_id}/").content.decode()

    assert "Montant encaissé ?" in html
    assert '<figure class="piece"' in html and "Cliente Ekane" in html
    assert "[[piece:" not in html


@pytest.mark.django_db
def test_the_quiz_result_shows_the_piece_too(client, enrolled, module, piece_question):
    piece_question.usage = "quiz"
    piece_question.save()
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)
    client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/", {"confirm": "1"})

    html = client.get(f"/fr/tentatives/{attempt.public_id}/resultat/").content.decode()

    assert "Cliente Ekane" in html
    assert "[[piece:" not in html


def test_the_prompt_text_filter_drops_the_piece_tags():
    from simulation.templatetags.acad_pieces import prompt_text

    assert prompt_text("Montant ?\n\n[[piece:S-A-01-002]]") == "Montant ?"


@pytest.fixture
def declaration_question(module):
    """US-85 : l'explication cite le formulaire rempli ; l'énoncé ne cite que la pièce de travail."""
    work = Piece.objects.create(
        partie=module.partie, ref="S-A-01-010", kind=Piece.Kind.SALES_INVOICE, issued_on=datetime.date(2026, 1, 20),
        title_fr="Ventes de janvier", payload={"fields": [{"label": "Client", "value": "Boutique Akwa"}]})
    form = Piece.objects.create(
        partie=module.partie, ref="S-A-02-015", kind=Piece.Kind.DECLARATION, issued_on=datetime.date(2026, 2, 15),
        title_fr="Déclaration de janvier", payload={"fields": [{"label": "TVA due", "value": "Case remplie 192 500"}]})
    question = Question.objects.create(
        module=module, qtype="numeric", usage="quiz", numeric_value=Decimal("192500"), unit="FCFA", exercice=2026,
        prompt_fr="TVA due ?\n\n[[piece:S-A-01-010]]", prompt_en="VAT due?\n\n[[piece:S-A-01-010]]",
        explanation_fr="Collectée − déductible.\n\n[[piece:S-A-02-015]]",
        explanation_en="Charged − recoverable.\n\n[[piece:S-A-02-015]]", reviewed_fr=True, reviewed_en=True)
    question.pieces.set([work, form])
    question.publish()
    return question


@pytest.mark.django_db
def test_the_quiz_correction_shows_the_filled_return(client, enrolled, module, declaration_question):
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)
    client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/", {"confirm": "1"})

    html = client.get(f"/fr/tentatives/{attempt.public_id}/resultat/").content.decode()

    assert "Case remplie 192 500" in html and "Collectée − déductible." in html
    assert "[[piece:" not in html


@pytest.mark.django_db
def test_the_attempt_never_shows_the_pieces_of_the_correction(client, enrolled, module, declaration_question):
    """US-83 : pendant la tentative, seule la pièce de l'énoncé est visible, jamais le formulaire corrigé."""
    attempt = start_attempt(enrolled, Assessment.quiz_for(module))
    client.force_login(enrolled)

    html = client.get(f"/fr/tentatives/{attempt.public_id}/").content.decode()

    assert "Boutique Akwa" in html
    assert "Case remplie 192 500" not in html


@pytest.mark.django_db
def test_the_exam_result_shows_no_correction(client, enrolled, module, declaration_question):
    """US-83 : en examen, ni l'écriture officielle ni le formulaire corrigé ne sont montrés, seul le score par module."""
    declaration_question.usage = "exam"
    declaration_question.save()
    attempt = start_attempt(enrolled, Assessment.exam_for(module.partie))
    client.force_login(enrolled)
    client.post(f"/fr/tentatives/{attempt.public_id}/envoyer/", {"confirm": "1"})

    html = client.get(f"/fr/tentatives/{attempt.public_id}/resultat/").content.decode()

    assert "Case remplie 192 500" not in html and "Collectée − déductible." not in html
