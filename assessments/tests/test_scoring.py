from fractions import Fraction

import pytest

from assessments.scoring import score_answer

# Bonnes réponses : choix 1, 2 et 3 ; mauvaises : 4 et 5.
CORRECT = {1, 2, 3}


@pytest.mark.parametrize(
    "selected, expected",
    [
        ({1, 2, 3}, Fraction(1)),
        ({1, 2}, Fraction(2, 3)),
        ({1, 2, 4}, Fraction(1, 3)),
        ({1, 4, 5}, Fraction(0)),  # plancher à 0, jamais négatif
        ({4, 5}, Fraction(0)),
        (set(), Fraction(0)),
    ],
)
def test_multiple_choice_gives_partial_credit_with_floor_at_zero(selected, expected):
    assert score_answer("multiple", CORRECT, selected) == expected


@pytest.mark.parametrize("qtype", ["single", "truefalse"])
def test_single_answer_question_is_all_or_nothing(qtype):
    assert score_answer(qtype, {7}, {7}) == 1
    assert score_answer(qtype, {7}, {8}) == 0
    assert score_answer(qtype, {7}, set()) == 0


def test_selecting_several_choices_on_single_answer_question_scores_zero():
    assert score_answer("single", {7}, {7, 8}) == 0
