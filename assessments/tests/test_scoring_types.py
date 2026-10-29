"""Notation des types (US-35, C11) : numérique en FCFA, % ou durée avec tolérance absolue, appariement, zone cliquable."""
from decimal import Decimal
from fractions import Fraction

import pytest

from assessments.scoring import parse_quantity, score_answer, score_matching, score_numeric

NBSP, NNBSP = " ", " "


@pytest.mark.parametrize("text, expected", [
    ("1250000", (Decimal("1250000"), "")),
    ("1 250 000", (Decimal("1250000"), "")),
    (f"1{NBSP}250{NBSP}000", (Decimal("1250000"), "")),       # espace insécable copiée d'un énoncé
    (f"1{NNBSP}250{NNBSP}000", (Decimal("1250000"), "")),     # espace fine insécable (format français de Django)
    ("1.250.000", (Decimal("1250000"), "")),                  # points de milliers
    ("1.250", (Decimal("1250"), "")),                         # un seul point suivi de 3 chiffres : milliers
    ("1 250 000 FCFA", (Decimal("1250000"), "FCFA")),
    ("1 250 000 F CFA", (Decimal("1250000"), "FCFA")),
    ("1 250 000 F", (Decimal("1250000"), "FCFA")),
    ("1250000 XAF", (Decimal("1250000"), "FCFA")),
    ("1250000fcfa", (Decimal("1250000"), "FCFA")),
    ("19,25", (Decimal("19.25"), "")),                        # virgule décimale
    ("19.25", (Decimal("19.25"), "")),                        # point décimal (2 chiffres après : pas des milliers)
    ("19,25 %", (Decimal("19.25"), "%")),
    ("19,25%", (Decimal("19.25"), "%")),
    ("1,250,000.50", (Decimal("1250000.50"), "")),            # saisie anglaise : virgules de milliers, point décimal
    ("1.250.000,50", (Decimal("1250000.50"), "")),            # saisie française complète
    ("-15 000", (Decimal("-15000"), "")),
    ("−15 000", (Decimal("-15000"), "")),                 # signe moins typographique
    ("30 jours", (Decimal("30"), "jours")),
    ("30 days", (Decimal("30"), "jours")),
    ("6 mois", (Decimal("6"), "mois")),
    ("5 ans", (Decimal("5"), "années")),
    ("5 années", (Decimal("5"), "années")),
    ("5 years", (Decimal("5"), "années")),
])
def test_parse_quantity_reads_french_and_english_amounts(text, expected):
    assert parse_quantity(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "FCFA", "12 V", "4,7 k", "1 250 kFCFA", "19,25 %%", "1..250", "1 2,5,0"])
def test_parse_quantity_rejects_garbage_and_si_prefixes(text):
    assert parse_quantity(text) is None


@pytest.mark.parametrize("answer, score", [
    ("1 250 000", 1),
    ("1 250 001", 1),        # arrondi : 1 FCFA d'écart toléré
    ("1 249 999 FCFA", 1),
    ("1 250 002", 0),
    ("1 250 000 %", 0),      # unité incohérente
    ("1,25 million", 0),
    ("", 0),
])
def test_an_amount_is_right_within_the_absolute_tolerance(answer, score):
    assert score_numeric(Decimal("1250000"), "FCFA", Decimal("0"), answer, tolerance_abs=Decimal("1")) == Fraction(score)


def test_an_exact_amount_is_required_when_the_absolute_tolerance_is_zero():
    assert score_numeric(Decimal("240625"), "FCFA", Decimal("0"), "240 626", tolerance_abs=Decimal("0")) == 0
    assert score_numeric(Decimal("240625"), "FCFA", Decimal("0"), "240 625", tolerance_abs=Decimal("0")) == 1


def test_the_relative_tolerance_remains_available_on_top_of_the_absolute_one():
    """Écart de 1 % sur un grand montant estimé : faux en absolu (1 FCFA), juste avec 2 % relatifs."""
    assert score_numeric(Decimal("1000000"), "FCFA", Decimal("2"), "1 010 000", tolerance_abs=Decimal("1")) == 1
    assert score_numeric(Decimal("1000000"), "FCFA", Decimal("0"), "1 010 000", tolerance_abs=Decimal("1")) == 0


def test_a_rate_in_percent_is_compared_in_percent():
    assert score_numeric(Decimal("19.25"), "%", Decimal("0"), "19,25 %", tolerance_abs=Decimal("0")) == 1
    assert score_numeric(Decimal("19.25"), "%", Decimal("0"), "19,25", tolerance_abs=Decimal("0")) == 1
    assert score_numeric(Decimal("19.25"), "%", Decimal("0"), "19,25 FCFA", tolerance_abs=Decimal("0")) == 0
    assert score_numeric(Decimal("19.25"), "%", Decimal("0"), "18,25", tolerance_abs=Decimal("0")) == 0


def test_matching_scores_the_share_of_right_pairs():
    expected = {"r": "resistance", "c": "capacitance", "l": "inductance", "d": "diode"}

    assert score_matching(expected, {"r": "resistance", "c": "inductance", "l": "capacitance", "d": "diode"}) == Fraction(1, 2)
    assert score_matching(expected, dict(expected)) == 1
    assert score_matching(expected, {}) == 0


def test_matching_ignores_pairs_that_do_not_exist():
    assert score_matching({"r": "resistance"}, {"r": "resistance", "x": "resistance"}) == 1


def test_hotspot_is_all_or_nothing_on_the_clicked_zone():
    assert score_answer("hotspot", [7], [7]) == 1
    assert score_answer("hotspot", [7], [8]) == 0
