"""DoD-Parcours (parcours B2, Ets Essomba Boissons, établissement individuel à l'IGS, puis Essomba Boissons SARL au réel ;
profil validé le 2026-11-02, S41, qui amende S13) : SMT et questions numériques ou à choix toute l'année 2026 (S14) ;
CA 2026 sous le seuil de 50 millions (CGI art. C 39 (2)) ; déclaration préalable de cessation au moins trois mois
avant le 31 décembre (art. 95 (1)) ; apport du fonds à une SARL au réel au 1er janvier 2027, bilan d'ouverture
équilibré, apports en nature sous 5 millions (AUSCGIE art. 312) ; frais de constitution en charges (S6) ; déclaration
de clôture dans les trois mois (art. 95 (2)) avec l'IGS (art. 96)."""
import json

import pytest

from assessments.models import Assessment, Question
from courses.models import Section
from simulation.tests.test_parcours_a_content import CONTENT, parcours_a  # noqa: F401 (fixture)

B2 = CONTENT / "simulation" / "b2"
FORMATION = CONTENT / "simulation" / "formation.json"


@pytest.fixture
def ledger_b2():
    return json.loads((B2 / "ledger.json").read_text(encoding="utf-8"))


@pytest.fixture
def pieces_b2():
    return json.loads((B2 / "pieces.json").read_text(encoding="utf-8"))


@pytest.fixture
def partie_b2():
    manifest = json.loads(FORMATION.read_text(encoding="utf-8"))
    return next(p for p in manifest["parties"] if p["slug"] == "b2")


def _lines(entries, prefix, side=None, before=None, on=None):
    return [l for e in entries for l in e["lines"] if l["account"].startswith(prefix)
            and (side is None or l["side"] == side) and (before is None or e["date"] < before)
            and (on is None or e["date"] == on)]


def test_parcours_b2_closes_the_delivery_order_with_seven_modules(parcours_a, partie_b2):  # noqa: F811
    """US-80 (S20) : A → E → B3 → C → D → B1 → B2 ; 7 modules, 4 questions tirées par module."""
    assert list(parcours_a.parties.order_by("order").values_list("slug", flat=True)) == \
        ["a", "e", "b3", "c", "d", "b1", "b2"]
    partie = parcours_a.parties.get(slug="b2")
    assert partie.modules.count() == 7
    assert Assessment.exam_for(partie).questions_per_module == 4
    assert partie_b2["regime"] == "igs_puis_reel" and partie_b2["systeme_comptable"] == "smt"
    assert partie_b2["forme"] == "individuelle" and partie_b2["centre_impots"] == "cfl"


def test_parcours_b2_has_numeric_and_choice_questions_only(parcours_a):  # noqa: F811
    """US-90 (S14) : à l'IGS et au SMT, aucune question `journal` ; au moins une question à choix par module."""
    questions = Question.objects.filter(module__partie__slug="b2", module__partie__formation=parcours_a)
    assert questions.count() >= 140
    assert not questions.filter(qtype="journal").exists()
    for order in range(1, 8):
        assert questions.filter(module__order=order, qtype__in=["single", "multiple", "truefalse"]).exists(), order


def test_the_2026_turnover_stays_below_the_igs_threshold(ledger_b2):
    """S41 (CGI art. C 39 (2)) : un dépassement de 50 millions en cours d'exercice entraînerait le reclassement d'office
    au réel ; le CA de l'Ets reste sous le seuil, dans la classe 10 de l'IGS (30 à moins de 50 millions)."""
    turnover = sum(l["amount"] for l in _lines(ledger_b2, "70", "credit", before="2027-01-01"))
    assert 30000000 <= turnover < 50000000


def test_the_depot_keeps_igs_rules_in_2026(ledger_b2):
    """S40 : TVA et précompte dans le coût d'achat ; prélèvements au compte de l'exploitant, jamais en charge."""
    assert not _lines(ledger_b2, "445", before="2027-01-01") and not _lines(ledger_b2, "4492")
    assert len(_lines(ledger_b2, "1042", "debit")) >= 12
    assert not _lines(ledger_b2, "66")


def test_the_cessation_is_declared_three_months_ahead(pieces_b2):
    """CGI art. 95 (1) : la déclaration de cessation précède d'au moins trois mois la date de cessation (31 décembre)."""
    notice = next(p for p in pieces_b2 if p["kind"] == "demarche" and "cessation" in p["title"]["fr"].lower())
    assert notice["date"] <= "2026-09-30"
    assert "[[cgi:art. 95]]" in notice["payload"]["source"]


def test_the_depot_accounts_are_settled_at_year_end(ledger_b2):
    """L'Ets cesse au 31 décembre : banque, caisse et Orange Money soldées ; la SARL ouvre ses propres comptes."""
    for account in ("521", "5711", "5522", "585"):
        movements = _lines(ledger_b2, account, before="2027-01-01")
        balance = sum(l["amount"] if l["side"] == "debit" else -l["amount"] for l in movements)
        assert balance == 0, account


def test_the_opening_balance_sheet_of_the_sarl_is_balanced(ledger_b2, pieces_b2):
    """DoD-Parcours point 5 et US-91 : au 1er janvier 2027, capital (1013) égal aux apports (stock, tricycle,
    numéraire) ; apports en nature sous 5 millions, sans commissaire aux apports (AUSCGIE art. 312)."""
    opening = [e for e in ledger_b2 if e["date"] == "2027-01-01"]
    assert opening and all(e["date"] == "2027-01-01" for e in ledger_b2 if e["date"] >= "2027-01-01")
    capital = sum(l["amount"] for l in _lines(opening, "1013", "credit"))
    stock = sum(l["amount"] for l in _lines(opening, "311", "debit"))
    vehicle = sum(l["amount"] for l in _lines(opening, "2458", "debit"))
    cash = sum(l["amount"] for l in _lines(opening, "521", "debit"))
    assert stock and vehicle and cash and capital == stock + vehicle + cash
    assert stock + vehicle <= 5000000
    assert capital % 10000 == 0 and capital > 1000000  # parts de 10 000 ; statuts notariés (loi 2016/014 art. 4)
    statuts = next(p for p in pieces_b2 if p["kind"] == "statuts")
    assert any(e["piece"] == statuts["ref"] for e in opening)


def test_the_formation_costs_are_expensed_by_the_sarl(ledger_b2):
    """S6 : honoraires du notaire (6324) et droits d'enregistrement de 2 % (6468, CGI art. 346 et 544) en charges,
    jamais en immobilisation ; dette envers l'associé qui les a avancés (4621)."""
    opening = [e for e in ledger_b2 if e["date"] == "2027-01-01"]
    capital = sum(l["amount"] for l in _lines(opening, "1013", "credit"))
    assert _lines(opening, "6324", "debit")
    assert sum(l["amount"] for l in _lines(opening, "6468", "debit")) == capital * 2 // 100
    assert _lines(opening, "4621", "credit")
    assert not _lines(opening, "20")


def test_the_closing_returns_follow_their_deadlines(pieces_b2):
    """CGI art. 95 (2) et 96 : déclaration de clôture dans les trois mois, IGS payé avec ; art. 74 au 15 mars ;
    DSF du SMT (art. C 44) au plus tard avec la clôture."""
    returns = [p for p in pieces_b2 if p["kind"] == "declaration" and p["date"] >= "2027-01-01"]
    closing = next(p for p in returns if "clôture" in p["title"]["fr"])
    art74 = next(p for p in returns if "art. 74" in p["title"]["fr"])
    smt = [p for p in returns if p.get("dsf") in ("bilan_smt", "compte_resultat_smt")]
    assert closing["date"] <= "2027-03-31" and art74["date"] <= "2027-03-15"
    assert any(t["label"]["fr"].startswith("IGS") for t in closing["payload"]["totals"])
    assert len(smt) == 2 and all(p["date"] <= "2027-03-31" for p in smt)
    assert not [p for p in returns if p.get("dsf") in ("bilan", "compte_resultat", "passage", "liquidation_is")]


def test_every_section_of_parcours_b2_renders_without_unknown_tag(parcours_a):  # noqa: F811
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__slug="b2", module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
