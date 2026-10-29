"""US-71 à US-73 : les règles du contenu, vérifiées sur des textes témoins avant tout contenu réel."""
from courses.tests.content_rules import (
    book_mentions,
    cites_a_source,
    question_problems,
    unknown_accounts,
    unknown_parameters,
    volume_shortfalls,
)

ACCOUNTS = {"601", "4452", "401"}
PARAMS = {"tva.taux_global"}


def test_a_lesson_citing_the_cgi_or_an_account_or_the_guide_cites_a_source():
    assert cites_a_source("La TVA est exigible [[cgi:art. 128]].")
    assert cites_a_source("On débite [[syscohada:601]].")
    assert cites_a_source("Voir [[guide:ch. 2]].")


def test_a_lesson_without_any_tag_cites_no_source():
    assert not cites_a_source("Selon le CGI, la TVA est exigible à la livraison.")


def test_accounts_cited_in_a_lesson_must_exist_in_the_plan():
    assert unknown_accounts("[[syscohada:601]] puis [[syscohada:4019]] et [[syscohada:401]]", ACCOUNTS) == ["4019"]


def test_parameters_used_in_a_lesson_must_exist():
    assert unknown_parameters("[[param:tva.taux_global]] et [[param:tva.taux_reduit]]", PARAMS) == ["tva.taux_reduit"]


def test_the_source_books_are_never_named():
    text = "Exercice tiré du DCG 9 (Dunod), corrigé de Disle ; voir aussi Plagnet, ISBN 978-2-10-053910-9."

    assert book_mentions(text) == ["DCG", "Dunod", "Disle", "Plagnet", "ISBN 978-2-10-053910-9"]


def test_ordinary_words_are_not_taken_for_a_book():
    assert book_mentions("Le dunodien n'existe pas ; un DCGI non plus ; la comptabilité de Douala.") == []


def journal(account="601", **extra):
    return {"id": "C-P1-M1-001", "type": "journal", "usage": "exam", "exercice": 2026,
            "prompt": {"fr": "Passez l'écriture.", "en": "Record the entry."},
            "explanation": {"fr": "Achat à crédit.", "en": "Purchase on credit."},
            "journal": [{"account": account, "side": "debit", "amount": "1000"},
                        {"account": "401", "side": "credit", "amount": "1000"}], **extra}


def test_a_complete_bilingual_journal_question_has_no_problem():
    assert question_problems(journal(), "C", ACCOUNTS) == []


def test_a_question_needs_both_languages_and_an_explanation():
    problems = question_problems(journal(prompt={"fr": "Passez l'écriture.", "en": ""}, explanation={"fr": "", "en": ""}),
                                 "C", ACCOUNTS)

    assert problems == ["C-P1-M1-001 : énoncé EN manquant", "C-P1-M1-001 : explication FR manquante",
                        "C-P1-M1-001 : explication EN manquante"]


def test_a_journal_answer_on_an_unknown_account_is_reported():
    assert question_problems(journal(account="6019"), "C", ACCOUNTS) == ["C-P1-M1-001 : compte inconnu 6019"]


def test_a_question_id_must_carry_the_prefix_of_its_formation():
    assert question_problems(journal(id="E-P1-M1-001"), "C", ACCOUNTS) == ["E-P1-M1-001 : identifiant sans préfixe C-"]


def test_an_amount_question_must_name_its_exercice():
    numeric = {"id": "F-P1-M1-002", "type": "numeric", "prompt": {"fr": "Montant ?", "en": "Amount?"},
               "explanation": {"fr": "Calcul.", "en": "Computation."}, "numeric": {"value": "1000", "unit": "FCFA"}}

    assert question_problems(numeric, "F", ACCOUNTS) == ["F-P1-M1-002 : question chiffrée sans exercice"]


def test_a_module_needs_twelve_exam_and_eight_quiz_questions():
    bank = [{"usage": "exam"}] * 11 + [{"usage": "quiz"}] * 8

    assert volume_shortfalls(bank) == ["11 questions d'examen sur 12"]
    assert volume_shortfalls([{"usage": "exam"}] * 12 + [{"usage": "quiz"}] * 7) == ["7 questions de quiz sur 8"]
    assert volume_shortfalls([{"usage": "exam"}] * 12 + [{}] * 8) == []  # usage par défaut : quiz
