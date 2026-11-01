"""DoD-Parcours (parcours E, Froid Équipe Services SARL à l'IGS) : le contenu s'importe après A, se publie et se rend
sans balise inconnue ; aucune écriture `journal` à l'IGS (S14, S29 à S31)."""
import json

from assessments.models import Assessment, Question
from courses.models import Section
from simulation.models import Piece
from simulation.tests.test_parcours_a_content import CONTENT, parcours_a  # noqa: F401 (fixture)


def test_parcours_e_follows_a_with_seven_modules(parcours_a):  # noqa: F811
    """US-80 (S29) : E est la deuxième partie, juste après A ; examen à 4 questions tirées par module."""
    assert list(parcours_a.parties.order_by("order").values_list("slug", flat=True))[:2] == ["a", "e"]
    partie = parcours_a.parties.get(slug="e")
    assert partie.modules.count() == 7
    assert Assessment.exam_for(partie).questions_per_module == 4


def test_parcours_e_has_only_numeric_and_choice_questions(parcours_a):  # noqa: F811
    """US-90 (S14) : à l'IGS et au SMT, aucune question `journal`."""
    questions = Question.objects.filter(module__partie__slug="e", module__partie__formation=parcours_a)

    assert questions.count() >= 140
    assert not questions.filter(qtype="journal").exists()
    assert set(questions.values_list("status", flat=True)) == {Question.Status.PUBLISHED}


def test_parcours_e_starts_with_minimal_capital_and_a_partner_advance():
    """S31 : capital de 100 000 FCFA (1013) et avance du fonctionnaire en compte courant d'associé (4621)."""
    entries = json.loads((CONTENT / "simulation" / "e" / "ledger.json").read_text(encoding="utf-8"))
    # Dès la première semaine : l'avance, prévue le dimanche 4, est créditée le lundi 5 (pièce bancaire en jour ouvré).
    january = [l for e in entries if e["date"] <= "2026-01-05" for l in e["lines"]]

    assert {"account": "1013", "side": "credit", "amount": 100000} in january
    assert any(l["account"] == "4621" and l["side"] == "credit" for l in january)
    assert not any(l["account"].startswith("66") for e in entries for l in e["lines"])  # vacataire, pas de salaire (S30)


def test_every_section_of_parcours_e_renders_without_unknown_tag(parcours_a):  # noqa: F811
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__slug="e", module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
    assert Piece.objects.filter(partie__slug="e").count() >= 12 * 8
