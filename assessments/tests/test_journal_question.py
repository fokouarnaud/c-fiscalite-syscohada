"""US-34 (C10) : une question `journal` porte une écriture équilibrée sur des comptes du plan SYSCOHADA."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from assessments.models import Question
from referentiel.models import SyscohadaAccount


@pytest.fixture
def plan(db):
    for code in ("6", "60", "601", "4", "44", "445", "4452", "40", "401"):
        SyscohadaAccount.objects.create(code=code, label_fr=f"Compte {code}")


def journal_question(module, lines):
    q = Question.objects.create(module=module, qtype="journal", prompt_fr="Passez l'écriture.", prompt_en="Record it.",
                                reviewed_fr=True, reviewed_en=True, exercice=2026)
    for i, (account, match, side, amount) in enumerate(lines):
        q.journal_lines.create(order=i, account=account, account_match=match, side=side, amount=Decimal(amount))
    return q


PURCHASE = [("601", "3", "debit", "1000000"), ("4452", "4", "debit", "192500"), ("401", "3", "credit", "1192500")]


def test_a_balanced_entry_on_known_accounts_is_published(module, plan):
    q = journal_question(module, PURCHASE)

    q.publish()

    assert q.status == Question.Status.PUBLISHED


def test_an_unbalanced_entry_is_refused(module, plan):
    q = journal_question(module, [("601", "3", "debit", "1000000"), ("401", "3", "credit", "1192500")])

    with pytest.raises(ValidationError):
        q.publish()


def test_an_entry_needs_at_least_two_lines(module, plan):
    with pytest.raises(ValidationError):
        journal_question(module, [("601", "3", "debit", "0")]).publish()


def test_an_account_missing_from_the_syscohada_plan_is_refused(module, plan):
    q = journal_question(module, [("601", "3", "debit", "1000"), ("4019", "exact", "credit", "1000")])

    with pytest.raises(ValidationError) as error:
        q.publish()
    assert "4019" in str(error.value)


def test_the_answer_key_lists_the_expected_lines_in_order(module, plan):
    q = journal_question(module, PURCHASE)

    assert q.journal_key() == [
        {"account": "601", "match": "3", "side": "debit", "amount": Decimal("1000000")},
        {"account": "4452", "match": "4", "side": "debit", "amount": Decimal("192500")},
        {"account": "401", "match": "3", "side": "credit", "amount": Decimal("1192500")},
    ]


# --- Réponse dans une tentative ---------------------------------------------------------------------------------------


@pytest.fixture
def published_journal(module, plan):
    q = journal_question(module, PURCHASE)
    q.publish()
    return q


def quiz_attempt(learner, module):
    from assessments.models import Assessment
    from assessments.services import start_attempt

    return start_attempt(learner, Assessment.quiz_for(module))


GIVEN = [
    {"account": "401", "side": "credit", "amount": "1 192 500", "label": "Fournisseur"},
    {"account": "601", "side": "debit", "amount": "1 000 000", "label": "Achat"},
    {"account": "4452", "side": "credit", "amount": "192 500", "label": "TVA"},  # mauvais sens
]


def test_a_journal_answer_is_saved_then_scored_line_by_line(learner, module, published_journal):
    from assessments.services import save_answer, submit_attempt

    attempt = quiz_attempt(learner, module)
    save_answer(attempt, published_journal.public_id, [], lines=GIVEN)
    submit_attempt(attempt)

    attempt.refresh_from_db()
    assert attempt.score_pct == Decimal("66.67")
    assert attempt.attempt_questions.get().answer_json["lines"][0]["account"] == "401"


def test_a_journal_answer_is_sanitized_before_storage(learner, module, published_journal):
    """Saisie hostile : sens inconnu vidé, champs tronqués, 20 lignes au plus, clés étrangères ignorées."""
    from assessments.services import save_answer

    attempt = quiz_attempt(learner, module)
    noisy = [{"account": "6" * 50, "side": "both", "amount": "9" * 50, "label": "x" * 500, "evil": "<script>"}] * 30
    save_answer(attempt, published_journal.public_id, [], lines=noisy)

    lines = attempt.attempt_questions.get().answer_json["lines"]
    assert len(lines) == 20
    assert lines[0] == {"account": "6" * 12, "side": "", "amount": "9" * 20, "label": "x" * 200}


def test_feedback_marks_each_given_line_and_shows_the_expected_entry(learner, module, published_journal):
    from assessments.services import save_answer

    attempt = quiz_attempt(learner, module)
    save_answer(attempt, published_journal.public_id, [], lines=GIVEN)

    [item] = attempt.feedback()

    assert [row["ok"] for row in item["journal_given"]] == [True, True, False]
    assert [(row["account"], row["side"]) for row in item["journal_expected"]] == [
        ("601", "debit"), ("4452", "debit"), ("401", "credit"),
    ]


def test_journal_lines_are_posted_as_parallel_fields(client, enrolled, module, published_journal):
    """Formulaire de saisie : une valeur par ligne dans line_account, line_side, line_amount et line_label."""
    client.force_login(enrolled)
    attempt = quiz_attempt(enrolled, module)

    response = client.post(f"/fr/tentatives/{attempt.public_id}/reponse/", {
        "question": published_journal.public_id,
        "line_account": ["601", "401"], "line_side": ["debit", "credit"],
        "line_amount": ["1 000 000", "1 000 000"], "line_label": ["Achat", ""],
    }, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert attempt.attempt_questions.get().answer_json["lines"] == [
        {"account": "601", "side": "debit", "amount": "1 000 000", "label": "Achat"},
        {"account": "401", "side": "credit", "amount": "1 000 000", "label": ""},
    ]


# --- Pages de tentative et de correction ------------------------------------------------------------------------------


def test_the_attempt_page_offers_an_entry_grid_prefilled_with_the_saved_lines(client, enrolled, module, published_journal):
    """US-34 : six lignes au moins (une de plus que les lignes déjà saisies), sens en liste déroulante, sans JavaScript."""
    from assessments.services import save_answer

    attempt = quiz_attempt(enrolled, module)
    save_answer(attempt, published_journal.public_id, [], lines=GIVEN)
    client.force_login(enrolled)

    html = client.get(f"/fr/tentatives/{attempt.public_id}/").content.decode()

    assert html.count('name="line_account"') == 6
    assert html.count('name="line_side"') == 6
    assert 'name="line_amount" value="1 192 500"' in html
    assert '<option value="credit" selected>' in html


def test_the_quiz_correction_marks_each_line_and_shows_the_expected_entry(client, enrolled, module, published_journal):
    from assessments.services import save_answer, submit_attempt

    attempt = quiz_attempt(enrolled, module)
    save_answer(attempt, published_journal.public_id, [], lines=GIVEN)
    submit_attempt(attempt)
    client.force_login(enrolled)

    html = client.get(f"/fr/tentatives/{attempt.public_id}/resultat/").content.decode()

    assert html.count('class="journal-line is-correct"') == 2
    assert html.count('class="journal-line is-wrong"') == 1
    assert "Écriture attendue" in html and "1\u00a0192\u00a0500" in html
