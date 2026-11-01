"""Critères d'acceptation restants du PRD (E9) : ordre et ouverture des parcours (US-80), calculateurs du module
Inventaire (US-88), six éléments de la passerelle de A et tableaux de la DSF (US-89)."""
import pytest

from courses.tests.content_rules import manifest_problems
from simulation.tests.test_simulation_content_rules import (
    BALANCE, INVOICE, JOURNAL_Q, simulation_problems, tree, write,
)
from simulation.tests.test_simulation_manifest import manifest


def parcours(slug):
    partie = manifest()["parties"][0]
    return {**partie, "slug": slug, "description": {"fr": "Parcours au réel.", "en": "Actual regime."},
            "centre_impots": "cime"}


def test_the_parcours_follow_the_delivery_order():
    """US-80 (S20, S29) : A → E → B3 → C → D → B1 → B2, sans saut ni inversion."""
    assert manifest_problems(manifest(parties=[parcours("a"), parcours("e"), parcours("b3")])) == []
    assert any("ordre" in p for p in manifest_problems(manifest(parties=[parcours("a"), parcours("c")])))
    assert any("ordre" in p for p in manifest_problems(manifest(parties=[parcours("b3")])))


def test_the_simulation_opens_only_with_parcours_a():
    """US-80 (S1, S20) : la formation reste fermée tant que le parcours A n'est pas livré."""
    assert any("ouverte" in p for p in manifest_problems(manifest(open=True, parties=[])))
    assert manifest_problems(manifest(open=True)) == []


def inventory_section_tree(tmp_path, body):
    root = tree(tmp_path, pieces=[INVOICE, BALANCE])
    formation = root / "simulation" / "formation.json"
    import json

    data = json.loads(formation.read_text(encoding="utf-8"))
    data["parties"][0]["modules"][5]["sections"] = [{"order": 1, "file": "01-inventaire", "kind": "content"}]
    write(formation, data)
    for lang in ("fr", "en"):
        write(root / "simulation" / "a" / "m6" / f"01-inventaire.{lang}.md", body)
    return root


def test_the_inventory_module_offers_the_stock_and_depreciation_calculators(tmp_path):
    """US-88 : le module Inventaire d'un parcours au réel propose [[calc:stock]] et [[calc:amortissement]]."""
    body = "Inventaire [[syscohada:6011]].\n\n[[calc:stock]]\n\n[[calc:amortissement]]\n"
    assert simulation_problems(inventory_section_tree(tmp_path, body)) == []

    problems = simulation_problems(inventory_section_tree(tmp_path, "Inventaire [[syscohada:6011]].\n\n[[calc:stock]]\n"))
    assert any("calc:amortissement" in p for p in problems)


BRIDGE = ("amendes", "amortissement_excedentaire", "dons_excedentaires", "charge_sans_piece",
          "impot_societes", "reprise_provision_taxee")


def bridge_question(key):
    return {"id": f"S-A-M7-{key}", "type": "numeric", "usage": "exam", "exercice": 2026, "passerelle": key,
            "prompt": {"fr": "Montant ?\n\n[[piece:S-A-01-001]]", "en": "Amount?\n\n[[piece:S-A-01-001]]"},
            "explanation": {"fr": "Passerelle.", "en": "Tax bridge."}, "numeric": {"value": 1, "unit": "FCFA"}}


def test_parcours_a_stages_the_six_bridge_items(tmp_path):
    """US-89 (S21, S23) : les six éléments de la passerelle de A, chacun sur une pièce de l'année."""
    complete = [JOURNAL_Q] + [bridge_question(key) for key in BRIDGE]
    assert simulation_problems(tree(tmp_path, questions=complete)) == []

    missing = [JOURNAL_Q] + [bridge_question(key) for key in BRIDGE[:-1]]
    assert any("reprise_provision_taxee" in p for p in simulation_problems(tree(tmp_path, questions=missing)))


def test_a_bridge_item_rests_on_a_piece(tmp_path):
    questions = [JOURNAL_Q] + [bridge_question(key) for key in BRIDGE]
    questions[1] = {**questions[1], "prompt": {"fr": "Montant ?", "en": "Amount?"}}

    assert any("amendes" in p and "pièce" in p for p in simulation_problems(tree(tmp_path, questions=questions)))


def test_the_tax_return_is_limited_to_its_four_key_tables(tmp_path):
    """US-89 (S12) : bilan, compte de résultat, tableau de passage et liquidation de l'IS."""
    def return_piece(table):
        return {"ref": f"S-A-13-{table[:3]}", "kind": "declaration", "date": "2027-04-15", "dsf": table,
                "title": {"fr": "DSF", "en": "Tax return"},
                "payload": {"totals": [{"label": {"fr": "Total", "en": "Total"}, "amount": 1}]}}

    good = [INVOICE, BALANCE] + [return_piece(t) for t in ("bilan", "compte_resultat", "passage", "liquidation_is")]
    assert simulation_problems(tree(tmp_path, pieces=good)) == []

    extra = [INVOICE, BALANCE, return_piece("tafire")]
    assert any("tafire" in p and "DSF" in p for p in simulation_problems(tree(tmp_path, pieces=extra)))


def test_an_igs_parcours_files_no_standard_tax_return(tmp_path):
    """US-90 (S14) : un parcours à l'IGS tient le SMT, sans DSF normale (bilan, compte de résultat…)."""
    from simulation.tests.test_simulation_content_rules import IGS, SMT_Q

    dsf = {"ref": "S-A-13-bil", "kind": "declaration", "date": "2027-03-15", "dsf": "bilan",
           "title": {"fr": "DSF", "en": "Tax return"},
           "payload": {"totals": [{"label": {"fr": "Total", "en": "Total"}, "amount": 1}]}}

    problems = simulation_problems(tree(tmp_path, pieces=[INVOICE, BALANCE, dsf], questions=[SMT_Q], regime="igs",
                                        **IGS))

    assert any("S-A-13-bil" in p and "IGS" in p for p in problems)


def test_parcours_d_explains_the_eleven_percent_contrast(tmp_path):
    """US-92 (S10) : le parcours D contient la retenue de 5,5 % et le contraste à 11 % (entreprise hors fichier)."""
    from simulation.tests.test_simulation_content_rules import calculation_question

    def d_tree(rates):
        questions = [JOURNAL_Q] + [calculation_question(f"S-D-M2-{rate}", value, "retenue_source", [1000000, rate, 10],
                                                        ["retenue"]) for rate, value in rates]
        return tree(tmp_path, questions=questions, slug="d", body="Ets Froid. [[syscohada:6011]] [[param:tva.taux_global]]",
                    body_en="Ets Froid. [[syscohada:6011]] [[param:tva.taux_global]]")

    assert not any("11 %" in p for p in simulation_problems(d_tree([(5, 55000), (10, 110000)])))
    assert any("11 %" in p for p in simulation_problems(d_tree([(5, 55000)])))


def momo_tree(tmp_path, sub_accounts):
    """S19 : un sous-compte par moyen de paiement, créé par l'entité sous un compte du plan (552)."""
    import json

    from simulation.tests.test_simulation_content_rules import ENTRY, line

    sale = {"date": "2026-01-31", "piece": "S-A-01-001",
            "lines": [line("5521", "debit", 100000), line("401", "credit", 100000)]}
    root = tree(tmp_path, pieces=[INVOICE], entries=[ENTRY, sale], questions=[JOURNAL_Q])
    write(root / "referentiel" / "syscohada.csv",
          "code;label_fr;label_en\n6011;Achats;Purchases\n401;Fournisseurs;Suppliers\n552;Monnaie électronique;E-money\n")
    path = root / "simulation" / "formation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if sub_accounts is not None:
        data["parties"][0]["sous_comptes"] = sub_accounts
    write(path, data)
    return root


def test_a_parcours_may_open_its_own_sub_accounts_under_a_chart_account(tmp_path):
    """S19 : 5521 « MTN MoMo » subdivise 552 ; une écriture sur 5521 est alors admise."""
    assert not any("5521" in p for p in simulation_problems(
        momo_tree(tmp_path, {"5521": {"fr": "MTN MoMo", "en": "MTN MoMo"}})))
    assert any("5521" in p for p in simulation_problems(momo_tree(tmp_path, None)))


def test_a_sub_account_must_subdivide_an_account_of_the_chart(tmp_path):
    problems = simulation_problems(momo_tree(tmp_path, {"5521": {"fr": "MoMo", "en": "MoMo"},
                                                        "9999": {"fr": "Inventé", "en": "Made up"}}))

    assert any("9999" in p and "sous-compte" in p for p in problems)


def test_a_journal_question_may_use_a_declared_sub_account(tmp_path):
    """S19 : la clé d'une question journal peut porter sur un sous-compte déclaré par le parcours."""
    import json

    from simulation.tests.test_simulation_content_rules import line

    root = momo_tree(tmp_path, {"5521": {"fr": "MTN MoMo", "en": "MTN MoMo"}})
    question = {**JOURNAL_Q, "journal": [line("6011", "debit", 100000), line("401", "credit", 100000)]}
    momo_q = {**JOURNAL_Q, "id": "S-A-M1-009", "journal": [line("5521", "debit", 1), line("401", "credit", 1)]}
    write(root / "simulation" / "a" / "m1" / "questions.json", [question, momo_q])

    assert not any("compte inconnu 5521" in p for p in simulation_problems(root))


def test_each_month_of_a_complete_parcours_has_eight_to_twelve_pieces():
    """DoD-Parcours point 1 (S4) : 8 à 12 pièces comptables datées par mois ; les démarches ne comptent pas, et la règle
    vise un parcours qui couvre les douze mois."""
    from courses.tests.content_rules import pieces_per_month_problems

    def pieces(per_month):
        return [{"ref": f"S-A-{m:02d}-{i:03d}", "kind": "facture_achat", "date": f"2026-{m:02d}-05"}
                for m, count in per_month.items() for i in range(count)]

    assert pieces_per_month_problems(pieces({m: 10 for m in range(1, 13)})) == []
    assert pieces_per_month_problems(pieces({1: 30})) == []  # parcours incomplet : pas encore contrôlé
    problems = pieces_per_month_problems(pieces({**{m: 10 for m in range(1, 13)}, 3: 13, 7: 7}))
    assert any("2026-03" in p and "13" in p for p in problems) and any("2026-07" in p and "7" in p for p in problems)
    procedures = [{"ref": f"S-A-01-9{i:02d}", "kind": "demarche", "date": "2026-01-02"} for i in range(5)]
    assert pieces_per_month_problems(pieces({m: 10 for m in range(1, 13)}) + procedures) == []


def test_parcours_e_comes_right_after_a():
    """S29 : la SARL à l'IGS du gérant (20 %) et du fonctionnaire (80 %) est livrée juste après A."""
    assert manifest_problems(manifest(parties=[parcours("a"), {**parcours("e"), "regime": "igs",
                                                                "systeme_comptable": "smt",
                                                                "description": {"fr": "SARL à l'IGS.",
                                                                                "en": "LLC under IGS."}}])) == []
    assert any("ordre" in p for p in manifest_problems(manifest(parties=[parcours("a"), parcours("b3")])))
