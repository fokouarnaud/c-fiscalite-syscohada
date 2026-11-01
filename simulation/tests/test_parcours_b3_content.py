"""DoD-Parcours (parcours B3, Ateba Boissons SARL au réel, profil validé le 2026-11-01, S32) : le contenu s'importe
après A et E, se publie et se rend sans balise inconnue ; consignes d'emballages, camion, accises comprises dans le prix
d'achat, précompte de 2 % et IS comparé au minimum de perception (US-80, US-85, US-88, US-89, US-93)."""
import json

import pytest

from assessments.models import Assessment, Question
from courses.models import Section
from simulation.models import Piece
from simulation.tests.test_parcours_a_content import CONTENT, parcours_a  # noqa: F401 (fixture)

B3 = CONTENT / "simulation" / "b3"


@pytest.fixture
def ledger_b3():
    return json.loads((B3 / "ledger.json").read_text(encoding="utf-8"))


@pytest.fixture
def pieces_b3():
    return json.loads((B3 / "pieces.json").read_text(encoding="utf-8"))


def _lines(entries, account, side=None):
    return [l for e in entries for l in e["lines"] if l["account"] == account and (side is None or l["side"] == side)]


def test_parcours_b3_follows_a_and_e_with_seven_modules(parcours_a):  # noqa: F811
    """US-80 (S20, S29) : B3 est la troisième partie ; examen à 4 questions tirées par module."""
    assert list(parcours_a.parties.order_by("order").values_list("slug", flat=True))[:3] == ["a", "e", "b3"]
    partie = parcours_a.parties.get(slug="b3")
    assert partie.modules.count() == 7
    assert Assessment.exam_for(partie).questions_per_module == 4


def test_parcours_b3_questions_are_published_and_include_journal_entries(parcours_a):  # noqa: F811
    """US-72, US-83 : au réel, les pièces se saisissent en `journal` ; tout est publié."""
    questions = Question.objects.filter(module__partie__slug="b3", module__partie__formation=parcours_a)

    assert questions.count() >= 140
    assert questions.filter(qtype="journal").count() >= 60
    assert set(questions.values_list("status", flat=True)) == {Question.Status.PUBLISHED}


def test_b3_records_deposits_with_brewery_and_customers_and_their_mali_and_boni(ledger_b3):
    """Guide SYSCOHADA, 1re partie, ch. 2, § 4.2 : consigne reçue en 4094, consigne facturée en 4194 ; mali 6224 chez
    le client, boni 7074 chez le fournisseur."""
    assert _lines(ledger_b3, "4094", "debit") and _lines(ledger_b3, "4094", "credit")
    assert _lines(ledger_b3, "4194", "credit") and _lines(ledger_b3, "4194", "debit")
    assert _lines(ledger_b3, "6224", "debit") and _lines(ledger_b3, "7074", "credit")


def test_b3_capitalises_its_truck_and_own_crates_and_depreciates_them(ledger_b3):
    """S32 : camion 2451 et casiers propres 243 (2493 est la ligne « en cours » du plan révisé), amortis au 31
    décembre (2845, 2843) ; emprunt bancaire de 12 000 000 en 162."""
    assert _lines(ledger_b3, "2451", "debit") and _lines(ledger_b3, "243", "debit")
    year_end = [l for e in ledger_b3 if e["date"] == "2026-12-31" for l in e["lines"]]
    assert {l["account"] for l in year_end if l["side"] == "credit"} >= {"2845", "2843"}
    assert {"account": "162", "side": "credit", "amount": 12000000} in _lines(ledger_b3, "162")


def test_brewery_invoices_include_excise_in_price_and_bear_the_2_percent_withholding(pieces_b3):
    """CGI art. 142 (9) et 21 (3) : accises comprises dans le prix d'achat, précompte de 2 % sur les achats."""
    brewery = [p for p in pieces_b3 if p["kind"] == "facture_achat" and "Sanaga" in p["payload"]["issuer"]["name"]]

    assert len(brewery) == 12
    for piece in brewery:
        labels = " ".join(f["label"]["fr"] for f in piece["payload"].get("fields", []))
        assert "accises" in labels
        withheld = [t for t in piece["payload"]["totals"] if t["label"]["fr"].startswith("Précompte")]
        ht = next(t["amount"] for t in piece["payload"]["totals"] if t.get("role") == "ht")
        assert withheld and withheld[0]["amount"] == round(ht * 2 / 100)


def test_b3_pays_the_minimum_tax_rather_than_the_cit(pieces_b3):
    """US-89 (S32) : le minimum de perception l'emporte sur l'IS au taux de 25 % ; DSF au plus tard le 15 avril 2027."""
    liquidation = next(p for p in pieces_b3 if p.get("dsf") == "liquidation_is")
    totals = {t["label"]["fr"]: t["amount"] for t in liquidation["payload"]["totals"]}

    assert totals["IS dû"] == totals["Minimum de perception"] > totals["IS calculé (CAC compris)"]
    assert liquidation["date"] <= "2027-04-15"


def test_january_of_b3_tells_one_scene_per_accounting_piece(pieces_b3):
    """S34 (pilote) : chaque pièce comptable de janvier est précédée de sa scène en quatre temps, avec renvoi au cours,
    en FR et en EN ; balances et déclarations ne sont pas racontées."""
    january = [p["ref"] for p in pieces_b3 if p["date"].startswith("2026-01") and p["kind"] not in ("demarche", "balance",
                                                                                                  "declaration")]
    for lang, heads in (("fr", ("**La règle.**", "**Pourquoi ce choix et pas un autre.**", "**Ce que ça change.**", "**Où ça se range.**",
                                "**Revoir :**")),
                        ("en", ("**The rule.**", "**Why this choice and not another.**", "**What it changes.**", "**Where it is filed.**",
                                "**See again:**"))):
        body = (B3 / "m1" / f"03-janvier.{lang}.md").read_text(encoding="utf-8").replace(" ", " ")  # espace fine de la typographie française
        scenes = body.split("\n### ")[1:]
        told = {ref for s in scenes for ref in january if f"[[piece:{ref}]]" in s}
        assert told == set(january), lang
        for s in scenes[:-1]:  # la dernière rubrique est le bilan du mois
            assert all(head in s for head in heads), s[:60]


def test_january_of_b3_shows_its_two_figures_in_both_languages():
    """S33 : les figures du pilote existent en FR et en EN, en SVG statique sans script."""
    from django.conf import settings

    for lang in ("fr", "en"):
        body = (B3 / "m1" / f"03-janvier.{lang}.md").read_text(encoding="utf-8")
        for name in ("circuit-casiers", "trois-caisses"):
            src = f"/static/content/simulation/b3/{name}.{lang}.svg"
            assert f"]({src})" in body
            svg = (settings.BASE_DIR / src.lstrip("/")).read_text(encoding="utf-8")
            assert "<script" not in svg and svg.startswith("<svg")


def test_every_section_of_parcours_b3_renders_without_unknown_tag(parcours_a):  # noqa: F811
    from courses.rendering import render_markdown

    for section in Section.objects.filter(module__partie__slug="b3", module__partie__formation=parcours_a):
        html = render_markdown(section.body_md)
        assert "<mark" not in html and "[[" not in html, section.title
    assert Piece.objects.filter(partie__slug="b3").count() >= 12 * 8
