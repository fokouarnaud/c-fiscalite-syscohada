"""DoD-Parcours (parcours B1, Ets Bilounga Boissons, établissement individuel à l'IGS, profil validé le 2026-11-02,
S39) : SMT et questions numériques ou à choix (S14) ; précompte de 5 % dans le coût d'achat (S40) ; loyer payé brut
par un locataire à l'IGS ; prélèvements de l'exploitante ; déclaration de l'art. 74 au 15 mars, IGS au 15 avril
(art. C 41) et DSF du SMT au 15 mai (art. C 44, S38)."""
import json

import pytest

from assessments.models import Assessment, Question
from courses.models import Section
from simulation.tests.test_parcours_a_content import CONTENT, parcours_a  # noqa: F401 (fixture)

B1 = CONTENT / "simulation" / "b1"


@pytest.fixture
def ledger_b1():
    return json.loads((B1 / "ledger.json").read_text(encoding="utf-8"))


@pytest.fixture
def pieces_b1():
    return json.loads((B1 / "pieces.json").read_text(encoding="utf-8"))


def _lines(entries, prefix, side=None):
    return [l for e in entries for l in e["lines"] if l["account"].startswith(prefix) and (side is None or l["side"] == side)]


def test_parcours_b1_follows_d_with_seven_modules(parcours_a):  # noqa: F811
    assert list(parcours_a.parties.order_by("order").values_list("slug", flat=True))[:6] == ["a", "e", "b3", "c", "d", "b1"]
    partie = parcours_a.parties.get(slug="b1")
    assert partie.modules.count() == 7
    assert Assessment.exam_for(partie).questions_per_module == 4


def test_parcours_b1_has_numeric_and_choice_questions_only(parcours_a):  # noqa: F811
    """US-90 (S14) : à l'IGS et au SMT, aucune question `journal` ; au moins une question à choix par module."""
    questions = Question.objects.filter(module__partie__slug="b1", module__partie__formation=parcours_a)
    assert questions.count() >= 140
    assert not questions.filter(qtype="journal").exists()
    for order in range(1, 8):
        assert questions.filter(module__order=order, qtype__in=["single", "multiple", "truefalse"]).exists(), order


def test_the_owner_brings_personal_capital_and_withdraws_without_expense(ledger_b1):
    """Exploitante individuelle : capital personnel (103), prélèvements au compte de l'exploitant (1042), jamais en
    charge ni en salaire."""
    assert _lines(ledger_b1, "103", "credit")
    assert len(_lines(ledger_b1, "1042", "debit")) >= 12
    assert not _lines(ledger_b1, "66")


def test_the_purchase_withholding_stays_in_the_cost_of_beer(ledger_b1, pieces_b1):
    """S40 (CGI art. 21 (3)) : le précompte de 5 % et la TVA payés à la brasserie entrent dans le coût (6011)."""
    assert not _lines(ledger_b1, "4492") and not _lines(ledger_b1, "445")
    invoices = [p for p in pieces_b1 if p["kind"] == "facture_achat"]
    assert len(invoices) >= 24
    for invoice in invoices:
        totals = {t["label"]["fr"]: t["amount"] for t in invoice["payload"]["totals"]}
        assert any(k.startswith("Précompte sur achats 5 %") for k in totals)
        debit = sum(l["amount"] for e in ledger_b1 if e["piece"] == invoice["ref"] for l in e["lines"]
                    if l["account"] == "6011" and l["side"] == "debit")
        assert debit == invoice["payload"]["totals"][-1]["amount"]


def test_the_rent_is_paid_gross_by_an_igs_tenant(ledger_b1):
    """Un locataire à l'IGS n'opère pas le précompte sur loyer (CGI art. 87, circulaire LF 2026)."""
    assert len(_lines(ledger_b1, "6222", "debit")) == 12
    assert not _lines(ledger_b1, "4478")


def test_the_yearly_returns_follow_their_deadlines(pieces_b1):
    """S38 : déclaration de l'art. 74 au 15 mars (C 39 (4)), IGS au 15 avril (C 41), DSF du SMT au 15 mai (C 44)."""
    returns = [p for p in pieces_b1 if p["kind"] == "declaration" and p["date"] >= "2027-01-01"]
    igs = next(p for p in returns if "IGS" in p["title"]["fr"])
    art74 = next(p for p in returns if "art. 74" in p["title"]["fr"])
    smt = [p for p in returns if p.get("dsf") in ("bilan_smt", "compte_resultat_smt")]
    assert art74["date"] <= "2027-03-15" and igs["date"] <= "2027-04-15"
    assert len(smt) == 2 and all(p["date"] <= "2027-05-15" for p in smt)
    assert not [p for p in returns if p.get("dsf") in ("bilan", "compte_resultat", "passage", "liquidation_is")]


def test_every_section_of_parcours_b1_renders_without_unknown_tag(parcours_a):  # noqa: F811
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__slug="b1", module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
