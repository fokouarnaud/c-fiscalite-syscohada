"""US-34 (C10) : notation d'une écriture au journal, ligne à ligne et sans ordre imposé."""
from decimal import Decimal
from fractions import Fraction

import pytest

from assessments.scoring import account_matches, score_journal

# Achat de marchandises à crédit : 1 000 000 HT, TVA 19,25 %, fournisseur 1 192 500.
PURCHASE = [
    {"account": "601", "match": "3", "side": "debit", "amount": Decimal("1000000")},
    {"account": "4452", "match": "4", "side": "debit", "amount": Decimal("192500")},
    {"account": "401", "match": "3", "side": "credit", "amount": Decimal("1192500")},
]


def line(account, side, amount):
    return {"account": account, "side": side, "amount": amount}


@pytest.mark.parametrize("expected, match, given, ok", [
    ("4452", "exact", "4452", True),
    ("4452", "exact", "445", False),
    ("4452", "3", "445", True),       # au niveau du compte à 3 chiffres, 445 suffit
    ("4452", "3", "4451", True),      # un sous-compte de 445 aussi
    ("4452", "3", "44", False),       # trop vague
    ("4452", "4", "44521", True),     # sous-compte d'un compte à 4 chiffres
    ("4452", "4", "4451", False),
    ("601", "class", "602", True),    # classe 6 seulement
    ("601", "class", "701", False),
    ("601", "3", " 601 ", True),      # espaces tolérées
    ("601", "3", "", False),
])
def test_an_account_is_checked_at_the_level_the_question_asks(expected, match, given, ok):
    assert account_matches(expected, match, given) is ok


def test_the_exact_entry_scores_full_marks_in_any_order():
    given = [line("401", "credit", "1 192 500"), line("601", "debit", "1000000"), line("4452", "debit", "192.500")]

    assert score_journal(PURCHASE, given) == 1


def test_each_right_line_earns_its_share():
    given = [line("601", "debit", "1000000"), line("4452", "credit", "192500"), line("401", "credit", "1192500")]

    assert score_journal(PURCHASE, given) == Fraction(2, 3)  # TVA du mauvais côté


def test_an_amount_must_be_exact_to_the_franc():
    given = [line("601", "debit", "1000001"), line("4452", "debit", "192500"), line("401", "credit", "1192500")]

    assert score_journal(PURCHASE, given) == Fraction(2, 3)


def test_each_extra_line_costs_half_a_line_with_a_floor_at_zero():
    right = [line("601", "debit", "1000000"), line("4452", "debit", "192500"), line("401", "credit", "1192500")]

    assert score_journal(PURCHASE, right + [line("571", "credit", "5000")]) == Fraction(5, 6)
    assert score_journal(PURCHASE, [line("571", "credit", "1")] * 9) == 0


def test_blank_lines_are_ignored():
    given = [line("601", "debit", "1000000"), line("", "", ""), line("4452", "debit", "192500"),
             line("401", "credit", "1192500")]

    assert score_journal(PURCHASE, given) == 1


def test_one_given_line_cannot_satisfy_two_expected_lines():
    """Deux lignes attendues identiques au niveau 3 : il faut les deux saisies, pas une seule comptée deux fois."""
    expected = [{"account": "601", "match": "3", "side": "debit", "amount": Decimal("500")},
                {"account": "601", "match": "3", "side": "debit", "amount": Decimal("500")},
                {"account": "401", "match": "3", "side": "credit", "amount": Decimal("1000")}]

    assert score_journal(expected, [line("601", "debit", "500"), line("401", "credit", "1000")]) == Fraction(2, 3)


def test_an_unreadable_amount_is_a_wrong_line():
    given = [line("601", "debit", "un million"), line("4452", "debit", "192500"), line("401", "credit", "1192500")]

    assert score_journal(PURCHASE, given) == Fraction(2, 3)
