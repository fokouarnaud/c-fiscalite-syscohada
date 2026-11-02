"""DoD-Parcours (parcours D, Ets Tchinda Froid, exploitant individuel au réel, profil validé le 2026-11-02, S36 et S37) :
TVA à l'encaissement (471, 4432), retenues des clients publics (5,5 % d'acompte et TVA retenue à la source, art. 21 (2)
et 149 (2)), contraste à 11 %, IRPP sur les BIC au taux de l'art. 17 comparé au minimum (art. 69 (2)), prélèvements de
l'exploitant, déclaration des résultats au 15 mars 2027 (art. 74) ; événements à choix et récit complet."""
import json

import pytest

from assessments.models import Assessment, Question
from courses.models import Section
from simulation.tests.test_parcours_a_content import CONTENT, parcours_a  # noqa: F401 (fixture)

D = CONTENT / "simulation" / "d"


@pytest.fixture
def ledger_d():
    return json.loads((D / "ledger.json").read_text(encoding="utf-8"))


@pytest.fixture
def pieces_d():
    return json.loads((D / "pieces.json").read_text(encoding="utf-8"))


def _lines(entries, prefix, side=None):
    return [l for e in entries for l in e["lines"] if l["account"].startswith(prefix) and (side is None or l["side"] == side)]


def test_parcours_d_follows_c_with_seven_modules(parcours_a):  # noqa: F811
    assert list(parcours_a.parties.order_by("order").values_list("slug", flat=True))[:5] == ["a", "e", "b3", "c", "d"]
    partie = parcours_a.parties.get(slug="d")
    assert partie.modules.count() == 7
    assert Assessment.exam_for(partie).questions_per_module == 4


def test_parcours_d_has_journal_entries_and_choice_events(parcours_a):  # noqa: F811
    """Événements à choix (demande de l'utilisateur du 2026-11-02) : au moins une question à choix par module."""
    questions = Question.objects.filter(module__partie__slug="d", module__partie__formation=parcours_a)
    assert questions.count() >= 140
    assert questions.filter(qtype="journal").count() >= 50
    for order in range(1, 8):
        assert questions.filter(module__order=order, qtype__in=["single", "multiple", "truefalse"]).exists(), order


def test_the_owner_contributes_personal_capital_and_withdraws_through_his_account(ledger_d):
    """Exploitant individuel : capital personnel (103), prélèvements au compte de l'exploitant (1042), jamais en charge."""
    assert _lines(ledger_d, "103", "credit")
    withdrawals = _lines(ledger_d, "1042", "debit")
    assert len(withdrawals) >= 12
    assert not _lines(ledger_d, "6661")


def test_public_customers_withhold_the_instalment_and_the_vat(ledger_d, pieces_d):
    """Art. 21 (2) et 149 (2) : à chaque paiement public, 5,5 % du HT en 4492 et la TVA retenue en 4458 ; la TVA
    devient exigible (4432) en soldant le compte d'attente 471 du même montant."""
    ars = {p["ref"] for p in pieces_d if "ARS" in p["title"]["fr"]}
    assert len(ars) >= 10
    for entry in (e for e in ledger_d if e["piece"] in ars):
        accounts = {l["account"] for l in entry["lines"]}
        assert {"4492", "4458", "471", "4432", "521", "411"} <= accounts


def test_d_pays_irpp_at_the_corporate_rate_and_files_by_15_march(pieces_d, ledger_d):
    """S37 (CGI art. 69 (2), 74, 91) : IRPP sur les BIC au taux de l'art. 17, au moins 2 % du CA ; déclaration des
    résultats au plus tard le 15 mars 2027 ; l'IRPP de l'exploitant passe au compte de l'exploitant (1043 « impôts et
    autres charges personnelles »), pas en charge."""
    liquidation = next(p for p in pieces_d if p.get("dsf") == "liquidation_is")
    assert liquidation["date"] <= "2027-03-15"
    fields = {f["label"]["fr"]: f["value"] for f in liquidation["payload"]["fields"]}
    assert fields["Taux"] == "30 %"
    assert not _lines(ledger_d, "891")
    year_end = [l for e in ledger_d if e["date"] == "2026-12-31" for l in e["lines"]]
    assert any(l["account"] == "1043" and l["side"] == "debit" for l in year_end)


def test_every_section_of_parcours_d_renders_without_unknown_tag(parcours_a):  # noqa: F811
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__slug="d", module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
