"""US-16 à US-18, US-20 : questions numériques, d'appariement et sur schéma, de la publication à la note ; temps passé."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from assessments.models import Assessment, Question
from assessments.services import save_answer, start_attempt, submit_attempt

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><rect width="100" height="50"/></svg>'


def reviewed(module, qtype, **fields):
    return Question.objects.create(
        module=module, qtype=qtype, prompt_fr="Q ?", prompt_en="Q?", reviewed_fr=True, reviewed_en=True, **fields
    )


@pytest.fixture
def numeric_q(module):
    q = reviewed(module, "numeric", numeric_value=Decimal("1250000"), unit="FCFA", exercice=2026)
    q.publish()
    return q


@pytest.fixture
def matching_q(module):
    q = reviewed(module, "matching")
    for i, (left, right) in enumerate([("R", "Résistance"), ("C", "Condensateur"), ("L", "Bobine"), ("D", "Diode")]):
        q.pairs.create(left_fr=left, left_en=left, right_fr=right, right_en=right, order=i)
    q.publish()
    return q


@pytest.fixture
def hotspot_q(module):
    q = reviewed(module, "hotspot", hotspot_svg=SVG)
    q.choices.create(text_fr="Base", text_en="Base", is_correct=True, shape={"x": 0, "y": 0, "w": 20, "h": 20}, order=0)
    q.choices.create(text_fr="Émetteur", text_en="Emitter", shape={"x": 50, "y": 0, "w": 20, "h": 20}, order=1)
    q.publish()
    return q


def quiz_attempt(learner, module):
    return start_attempt(learner, Assessment.quiz_for(module))


# --- Publication ------------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_numeric_question_needs_an_expected_value(module):
    with pytest.raises(ValidationError):
        reviewed(module, "numeric", unit="FCFA").publish()


@pytest.mark.django_db
def test_numeric_question_has_no_choices(module):
    q = reviewed(module, "numeric", numeric_value=Decimal("12"), unit="%")
    q.choices.create(text_fr="12 %", text_en="12%", is_correct=True)

    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_numeric_question_defaults_to_one_fcfa_and_no_relative_tolerance(numeric_q):
    """C11 : 1 FCFA d'écart absorbe les arrondis ; la tolérance relative n'est qu'une option."""
    assert (numeric_q.tolerance_abs, numeric_q.tolerance_pct) == (1, 0)


@pytest.mark.django_db
def test_matching_question_needs_at_least_two_pairs(module):
    q = reviewed(module, "matching")
    q.pairs.create(left_fr="R", left_en="R", right_fr="Résistance", right_en="Resistor", order=0)

    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_hotspot_question_needs_a_schematic(module):
    q = reviewed(module, "hotspot")
    q.choices.create(text_fr="Base", text_en="Base", is_correct=True, shape={"x": 0, "y": 0, "w": 9, "h": 9})

    with pytest.raises(ValidationError):
        q.publish()



@pytest.mark.django_db
def test_hotspot_schematic_with_script_is_refused(module):
    q = reviewed(module, "hotspot", hotspot_svg=SVG.replace("<rect", "<rect onload=\"alert(1)\""))
    q.choices.create(text_fr="Base", text_en="Base", is_correct=True, shape={"x": 0, "y": 0, "w": 9, "h": 9})

    with pytest.raises(ValidationError):
        q.publish()

@pytest.mark.django_db
def test_hotspot_question_has_exactly_one_right_zone(module):
    q = reviewed(module, "hotspot", hotspot_svg=SVG)
    for i in range(2):
        q.choices.create(text_fr=f"Z{i}", text_en=f"Z{i}", is_correct=True, shape={"x": i * 30, "y": 0, "w": 9, "h": 9})

    with pytest.raises(ValidationError):
        q.publish()


@pytest.mark.django_db
def test_every_hotspot_zone_needs_a_shape(module):
    q = reviewed(module, "hotspot", hotspot_svg=SVG)
    q.choices.create(text_fr="Base", text_en="Base", is_correct=True, shape={"x": 0, "y": 0, "w": 9, "h": 9})
    q.choices.create(text_fr="Sans zone", text_en="No zone")

    with pytest.raises(ValidationError):
        q.publish()


# --- Réponses et notes ------------------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_numeric_answer_is_scored_with_the_tolerance(learner, module, numeric_q):
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, numeric_q.public_id, [], text="1 250 001 FCFA")
    submit_attempt(attempt)

    attempt.refresh_from_db()
    assert attempt.score_pct == 100
    assert attempt.attempt_questions.get().answer_text == "1 250 001 FCFA"


@pytest.mark.django_db
def test_wrong_numeric_answer_scores_zero(learner, module, numeric_q):
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, numeric_q.public_id, [], text="125 000")
    submit_attempt(attempt)

    attempt.refresh_from_db()
    assert attempt.score_pct == 0


@pytest.mark.django_db
def test_matching_answer_earns_the_share_of_right_pairs(learner, module, matching_q):
    r, c, l, d = (str(p.public_id) for p in matching_q.pairs.all())
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, matching_q.public_id, [], pairs={r: r, c: l, l: c, d: d})
    submit_attempt(attempt)

    attempt.refresh_from_db()
    assert attempt.score_pct == 50


@pytest.mark.django_db
def test_matching_answer_drops_unknown_identifiers(learner, module, matching_q):
    r = str(matching_q.pairs.first().public_id)
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, matching_q.public_id, [], pairs={r: r, "00000000-0000-0000-0000-000000000000": r})

    assert attempt.attempt_questions.get().answer_json == {r: r}


@pytest.mark.django_db
def test_matching_right_column_order_is_frozen_per_attempt(learner, module, matching_q):
    attempt = quiz_attempt(learner, module)

    aq = attempt.attempt_questions.get()
    assert sorted(p.pk for p in aq.ordered_pairs()) == sorted(matching_q.pairs.values_list("pk", flat=True))


@pytest.mark.django_db
def test_hotspot_answer_is_the_clicked_zone(learner, module, hotspot_q):
    base = hotspot_q.choices.get(is_correct=True)
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, hotspot_q.public_id, [base.public_id])
    submit_attempt(attempt)

    attempt.refresh_from_db()
    assert attempt.score_pct == 100


@pytest.mark.django_db
def test_feedback_gives_the_expected_numeric_value(learner, module, numeric_q):
    attempt = quiz_attempt(learner, module)
    save_answer(attempt, numeric_q.public_id, [], text="125 000")

    [item] = attempt.feedback()

    assert (item["score"], item["answer_text"], item["expected_value"]) == (0, "125 000", "1 250 000 FCFA")


# --- Temps passé (US-20, US-28) ---------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_time_spent_on_a_question_adds_up_across_saves(learner, module, numeric_q):
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, numeric_q.public_id, [], text="1 000", time_spent_s=40)
    save_answer(attempt, numeric_q.public_id, [], text="1 250 000", time_spent_s=25)

    assert attempt.attempt_questions.get().time_spent_s == 65


@pytest.mark.django_db
def test_reported_time_is_clamped_to_a_plausible_range(learner, module, numeric_q):
    attempt = quiz_attempt(learner, module)

    save_answer(attempt, numeric_q.public_id, [], text="1 000", time_spent_s=-30)
    save_answer(attempt, numeric_q.public_id, [], text="1 000", time_spent_s=999999)

    assert attempt.attempt_questions.get().time_spent_s == 3600


# --- Correction lisible (US-15 à US-17) -------------------------------------------------------------------------------


@pytest.mark.parametrize("value, unit, lang, shown", [
    ("1250000", "FCFA", "fr", "1 250 000 FCFA"),   # séparateur de milliers français de Django : espace insécable
    ("1250000", "FCFA", "en", "1,250,000 FCFA"),
    ("240625.5", "FCFA", "fr", "240 625,5 FCFA"),
    ("-15000", "FCFA", "fr", "-15 000 FCFA"),
    ("19.25", "%", "fr", "19,25 %"),                          # espace avant % en français
    ("19.25", "%", "en", "19.25%"),
    ("30", "jours", "fr", "30 jours"),
    ("30", "jours", "en", "30 days"),
    ("6", "mois", "en", "6 months"),
    ("5", "années", "en", "5 years"),
    ("0", "FCFA", "fr", "0 FCFA"),
    ("1500", "", "fr", "1 500"),                        # coefficient sans unité
])
@pytest.mark.django_db
def test_expected_value_is_shown_with_grouped_thousands_and_its_unit(module, value, unit, lang, shown):
    """US-35 : la valeur attendue s'affiche au format de la langue, sans préfixe SI."""
    from django.utils import translation

    q = reviewed(module, "numeric", numeric_value=Decimal(value), unit=unit)
    with translation.override(lang):
        assert q.expected_value_display() == shown


@pytest.mark.django_db
def test_matching_feedback_lists_the_learners_pairs_with_their_verdict(learner, module, matching_q):
    r, c, l, d = (str(p.public_id) for p in matching_q.pairs.all())
    attempt = quiz_attempt(learner, module)
    save_answer(attempt, matching_q.public_id, [], pairs={r: r, c: l})

    [item] = attempt.feedback()

    assert [(row["left"], row["given"], row["expected"], row["ok"]) for row in item["pair_rows"]] == [
        ("R", "Résistance", "Résistance", True),
        ("C", "Bobine", "Condensateur", False),
        ("L", "", "Bobine", False),
        ("D", "", "Diode", False),
    ]


@pytest.mark.django_db
def test_an_amount_question_must_name_its_exercice_to_be_published(module):
    """US-36 : une question chiffrée est datée (« exercice 2026 ») pour rester juste quand les taux changent."""
    q = reviewed(module, "numeric", numeric_value=Decimal("192500"), unit="FCFA")

    with pytest.raises(ValidationError):
        q.publish()

    q.exercice = 2026
    q.publish()
    assert q.status == Question.Status.PUBLISHED


@pytest.mark.django_db
def test_the_amount_hint_explains_the_french_number_format_not_si_prefixes(client, enrolled, module, numeric_q):
    """C11 : plus de préfixes SI ; espaces ou points de milliers et virgule décimale."""
    client.force_login(enrolled)
    html = client.get(f"/fr/tentatives/{quiz_attempt(enrolled, module).public_id}/").content.decode()

    assert "préfixes" not in html
    assert "1 250 000" in html
