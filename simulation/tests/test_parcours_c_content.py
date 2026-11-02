"""DoD-Parcours (parcours C, Tech Clim Bonamoussadi SARL au réel, profil validé le 2026-11-02, S35) : le contenu
s'importe après A, E et B3, se publie et se rend sans balise inconnue ; honoraires du fonctionnaire sans retenue de
l'art. 92 bis, provision pour garantie, IS au taux réduit supérieur au minimum, dividendes de 2027 avec réserve
légale et IRCM (US-80, US-83, US-88, US-89, US-93)."""
import json

import pytest

from assessments.models import Assessment, Question
from courses.models import Section
from simulation.tests.test_parcours_a_content import CONTENT, parcours_a  # noqa: F401 (fixture)

C = CONTENT / "simulation" / "c"


@pytest.fixture
def ledger_c():
    return json.loads((C / "ledger.json").read_text(encoding="utf-8"))


@pytest.fixture
def pieces_c():
    return json.loads((C / "pieces.json").read_text(encoding="utf-8"))


def _lines(entries, prefix, side=None):
    return [l for e in entries for l in e["lines"] if l["account"].startswith(prefix) and (side is None or l["side"] == side)]


def test_parcours_c_follows_b3_with_seven_modules(parcours_a):  # noqa: F811
    """US-80 (S20, S35) : C est la quatrième partie ; examen à 4 questions tirées par module."""
    assert list(parcours_a.parties.order_by("order").values_list("slug", flat=True))[:4] == ["a", "e", "b3", "c"]
    partie = parcours_a.parties.get(slug="c")
    assert partie.modules.count() == 7
    assert Assessment.exam_for(partie).questions_per_module == 4


def test_parcours_c_questions_are_published_with_journal_entries(parcours_a):  # noqa: F811
    questions = Question.objects.filter(module__partie__slug="c", module__partie__formation=parcours_a)

    assert questions.count() >= 140
    assert questions.filter(qtype="journal").count() >= 60
    assert set(questions.values_list("status", flat=True)) == {Question.Status.PUBLISHED}


def test_the_civil_servant_is_paid_fees_without_withholding(ledger_c, pieces_c):
    """S35 : honoraires en 632, sans salaire ni retenue de l'art. 92 bis (la SARL n'est pas sur la liste)."""
    fees = {p["ref"] for p in pieces_c if "honoraires" in p["title"]["fr"].lower()}
    assert len(fees) >= 4
    for entry in (e for e in ledger_c if e["piece"] in fees):
        assert {l["account"] for l in entry["lines"]} == {"632", "521"}


def test_c_books_sales_services_and_a_deductible_warranty_provision(ledger_c):
    """Ventes 7011 et poses 706 ; provision pour garanties données aux clients (192) au 31 décembre."""
    assert _lines(ledger_c, "7011", "credit") and _lines(ledger_c, "706", "credit")
    year_end = [l for e in ledger_c if e["date"] == "2026-12-31" for l in e["lines"]]
    assert any(l["account"] == "192" and l["side"] == "credit" for l in year_end)


def test_c_pays_the_cit_above_the_minimum_tax(pieces_c):
    """US-89 : au taux réduit de 25 %, l'IS dépasse le minimum de perception ; DSF au plus tard le 15 avril 2027."""
    liquidation = next(p for p in pieces_c if p.get("dsf") == "liquidation_is")
    totals = {t["label"]["fr"]: t["amount"] for t in liquidation["payload"]["totals"]}

    assert totals["IS dû"] == totals["IS calculé (CAC compris)"] > totals["Minimum de perception"]
    assert liquidation["date"] <= "2027-04-15"


def test_the_2027_meeting_funds_the_legal_reserve_and_withholds_the_ircm(ledger_c):
    """AUSCGIE art. 346 et 348, CGI art. 70 : assemblée avant le 30 juin 2027 ; réserve légale (111) d'un dixième du
    bénéfice au moins, plafonnée au cinquième du capital ; IRCM de 15 % + CAC retenu sur les dividendes (465)."""
    meeting = [e for e in ledger_c if "2027-01-01" <= e["date"] <= "2027-06-30" and any(l["account"] == "465" for l in e["lines"])]
    assert meeting
    reserve = sum(l["amount"] for e in meeting for l in e["lines"] if l["account"] == "111" and l["side"] == "credit")
    assert 0 < reserve <= 400000  # un cinquième du capital de 2 000 000
    dividends = sum(l["amount"] for e in meeting for l in e["lines"] if l["account"] == "465" and l["side"] == "credit")
    withheld = sum(l["amount"] for e in ledger_c if e["date"] >= "2027-06-30"
                   for l in e["lines"] if l["account"] == "4478" and l["side"] == "credit")
    assert withheld == round(dividends * 0.165)


def test_every_section_of_parcours_c_renders_without_unknown_tag(parcours_a):  # noqa: F811
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__slug="c", module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
