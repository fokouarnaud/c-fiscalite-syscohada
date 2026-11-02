"""US-93, US-96, DoD-Parcours : garde-fous bloquants d'un parcours de la simulation dans content/, appliqués par
scan_content comme pour les autres formations."""
import json

from courses.tests.content_rules import scan_content
from simulation.tests.test_real_world_pieces import CUSTOMER, ISSUER


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False), encoding="utf-8")


def line(account, side, amount):
    return {"account": account, "side": side, "amount": amount}


INVOICE = {"ref": "S-A-01-001", "kind": "facture_achat", "date": "2026-01-05",
           "title": {"fr": "Facture", "en": "Invoice"},
           "payload": {"issuer": ISSUER, "customer": CUSTOMER, "number": "FA-2026-0001", "einvoice": "DGI-SFE-2026-000001",
                       "lines": [{"label": {"fr": "Chemises", "en": "Shirts"}, "amount": 100000}],
                       "totals": [{"label": {"fr": "HT", "en": "Net"}, "role": "ht", "amount": 100000}]}}
ENTRY = {"date": "2026-01-05", "piece": "S-A-01-001",
         "lines": [line("6011", "debit", 100000), line("401", "credit", 100000)]}
BALANCE = {"ref": "S-A-02-000", "kind": "balance", "date": "2026-02-01",
           "title": {"fr": "Balance au 31 janvier", "en": "Trial balance at 31 January"},
           "payload": {"lines": [{"label": {"fr": "401 Fournisseurs", "en": "401 Suppliers"}, "credit": 100000},
                                 {"label": {"fr": "6011 Achats", "en": "6011 Purchases"}, "debit": 100000}]}}
JOURNAL_Q = {"id": "S-A-M1-001", "type": "journal", "usage": "quiz",
             "prompt": {"fr": "Passez l'écriture.\n\n[[piece:S-A-01-001]]", "en": "Record it.\n\n[[piece:S-A-01-001]]"},
             "explanation": {"fr": "Achat.", "en": "Purchase."},
             "journal": [line("6011", "debit", 100000), line("401", "credit", 100000)]}


COMPANY_FILE = "Ngono Mode SARL. Plan : [[syscohada:6011]]. TVA : [[param:tva.taux_global]]."
COMPANY_FILE_EN = "Ngono Mode SARL. Chart: [[syscohada:6011]]. VAT: [[param:tva.taux_global]]."
IGS_FILE = "Ets Fouda. Plan : [[syscohada:6011]]. Précompte : [[param:precompte.taux_igs]] [[cgi:art. 93 quater]]."
IGS_FILE_EN = "Ets Fouda. Chart: [[syscohada:6011]]. Withholding: [[param:precompte.taux_igs]] [[cgi:art. 93 quater]]."
RATES = ("key;exercice;value;unit;label_fr;label_en;source_article\ntva.taux_global;2026;19.25;%;TVA;VAT;CGI art. 142\n"
         "precompte.taux_igs;2026;5;%;Précompte IGS;IGS withholding;CGI art. 21 (3)\n"
         "igs.seuil_comptabilite;2026;10000000;FCFA;Seuil du SMT et de la DSF à l'IGS;IGS bookkeeping threshold;"
         "CGI art. C 44\n")
DESCRIPTION = {"fr": "SARL au réel, boutique de vêtements à Douala.", "en": "LLC under the actual regime, clothing shop."}
IGS_DESCRIPTION = {"fr": "Établissement à l'IGS, dépôt de boissons à Yaoundé.", "en": "Sole trader under IGS, drinks depot."}
IGS = {"slug": "b1", "body": IGS_FILE, "body_en": IGS_FILE_EN, "description": IGS_DESCRIPTION}


def tree(tmp_path, pieces=(INVOICE, BALANCE), entries=(ENTRY,), questions=(JOURNAL_Q,), body=COMPANY_FILE,
         icon="briefcase", regime=None, cash_vat=False, slug="a", body_en=COMPANY_FILE_EN, description=DESCRIPTION,
         inventory_questions=(), centre="cime", suspense="471"):
    write(tmp_path / "referentiel" / "syscohada.csv",
          "code;label_fr;label_en\n6011;Achats;Purchases\n401;Fournisseurs;Suppliers\n")
    write(tmp_path / "referentiel" / "parametres.csv", RATES)
    modules = [{"order": 1, "dir": "a/m1", "sections": [{"order": 1, "file": "01-janvier", "kind": "content"}]}]
    modules += [{"order": n, "dir": f"a/m{n}", "sections": []} for n in range(2, 8)]
    partie = {"slug": slug, "pieces": "a/pieces.json", "ledger": "a/ledger.json", "description": description,
              "exam": {"questions_per_module": 4}, "modules": modules, "centre_impots": centre}
    write(tmp_path / "simulation" / "a" / "m6" / "questions.json", list(inventory_questions))
    if regime:
        partie["regime"] = regime
        if regime != "reel":
            partie["systeme_comptable"] = "smt"
    if cash_vat:
        partie["tva_encaissement"] = True
        if suspense:
            partie["compte_tva_attente"] = suspense
    manifest = {"slug": "simulation", "prefix": "S", "icon": icon,
                "prerequisite_note": {"fr": "Après Form 1 et 2.", "en": "After Forms 1 and 2."},
                "parties": [partie]}
    write(tmp_path / "simulation" / "formation.json", manifest)
    write(tmp_path / "simulation" / "a" / "pieces.json", list(pieces))
    write(tmp_path / "simulation" / "a" / "ledger.json", list(entries))
    write(tmp_path / "simulation" / "a" / "m1" / "01-janvier.fr.md", body)
    write(tmp_path / "simulation" / "a" / "m1" / "01-janvier.en.md", body_en)
    write(tmp_path / "simulation" / "a" / "m1" / "questions.json", list(questions))
    return tmp_path


def simulation_problems(root):
    # Volume (US-72) et ordre des parcours (US-80) ont leurs propres tests ; un arbre d'essai n'a qu'un parcours.
    return [problem for problem in scan_content(root) if "questions d'examen" not in problem
            and "questions de quiz" not in problem and "ordre des parcours" not in problem]


def test_a_coherent_parcours_has_no_problem(tmp_path):
    assert simulation_problems(tree(tmp_path)) == []


def test_the_scan_applies_the_simulation_manifest_rules(tmp_path):
    """US-80 : la structure du manifeste fait partie des garde-fous bloquants."""
    assert any("icône" in p for p in simulation_problems(tree(tmp_path, icon="ledger")))


def test_the_company_file_shows_its_rates_through_parameters(tmp_path):
    """US-81 : la première section d'un parcours (dossier d'entreprise) affiche ses taux par [[param:]]."""
    problems = simulation_problems(tree(tmp_path, body="Plan : [[syscohada:6011]]. TVA à 19,25 %."))

    assert any("dossier d'entreprise" in p and "[[param:]]" in p for p in problems)


def test_the_company_file_lists_its_chart_of_accounts(tmp_path):
    problems = simulation_problems(tree(tmp_path, body="Taux : [[param:tva.taux_global]] [[cgi:art. 142]]."))

    assert any("dossier d'entreprise" in p and "[[syscohada:]]" in p for p in problems)


def test_an_unbalanced_official_entry_is_reported(tmp_path):
    wrong = {**ENTRY, "lines": [line("6011", "debit", 100000), line("401", "credit", 90000)]}

    assert any("S-A-01-001" in p and "équilibr" in p for p in simulation_problems(tree(tmp_path, entries=[wrong])))


def test_an_incoherent_piece_is_reported(tmp_path):
    wrong = {**INVOICE, "payload": {**INVOICE["payload"], "totals": [
        {"label": {"fr": "HT", "en": "Net"}, "role": "ht", "amount": 99000}]}}

    assert any("S-A-01-001" in p and "HT" in p for p in simulation_problems(tree(tmp_path, pieces=[wrong, BALANCE])))


def test_a_piece_used_nowhere_is_reported(tmp_path):
    orphan = {**INVOICE, "ref": "S-A-01-099"}

    assert any("S-A-01-099" in p for p in simulation_problems(tree(tmp_path, pieces=[INVOICE, BALANCE, orphan])))


def test_a_journal_question_that_differs_from_the_book_is_reported(tmp_path):
    wrong = {**JOURNAL_Q, "journal": [line("6011", "debit", 100000), line("401", "credit", 100000),
                                      line("401", "credit", 1)]}

    assert any("S-A-M1-001" in p and "livre officiel" in p for p in simulation_problems(tree(tmp_path, questions=[wrong])))


def test_a_stale_balance_piece_is_reported(tmp_path):
    """US-84 : la balance publiée doit être celle que l'outil calcule à partir du livre officiel."""
    stale = {**BALANCE, "payload": {"lines": [{"label": {"fr": "401 Fournisseurs", "en": "401 Suppliers"}, "credit": 1},
                                              {"label": {"fr": "6011 Achats", "en": "6011 Purchases"}, "debit": 1}]}}

    assert any("S-A-02-000" in p and "balance" in p for p in simulation_problems(tree(tmp_path, pieces=[INVOICE, stale])))


SALE = {"ref": "S-A-01-002", "kind": "facture_vente", "date": "2026-01-20",
        "title": {"fr": "Facture de vente", "en": "Sales invoice"},
        "payload": {"issuer": ISSUER, "customer": CUSTOMER, "number": "FA-2026-0001", "einvoice": "DGI-SFE-2026-000001", "totals": [{"label": {"fr": "TTC", "en": "Total"}, "amount": 238500}]}}
SALE_ENTRY = {"date": "2026-01-20", "piece": "S-A-01-002",
              "lines": [line("5711", "debit", 238500), line("7011", "credit", 200000), line("4431", "credit", 38500)]}


def declaration_question(field, value):
    return {"id": f"S-A-M1-{field}", "type": "numeric", "usage": "quiz", "exercice": 2026,
            "prompt": {"fr": "Montant ?", "en": "Amount?"}, "explanation": {"fr": "Calcul.", "en": "Computation."},
            "numeric": {"value": value, "unit": "FCFA"}, "declaration": {"period": "2026-01", "field": field}}


def declaration_tree(tmp_path, *questions):
    root = tree(tmp_path, pieces=[INVOICE, SALE], entries=[ENTRY, SALE_ENTRY], questions=[JOURNAL_Q, *questions])
    write(root / "referentiel" / "syscohada.csv", "code;label_fr;label_en\n6011;Achats;Purchases\n"
          "401;Fournisseurs;Suppliers\n5711;Caisse;Cash\n7011;Ventes;Sales\n4431;TVA facturée;VAT charged\n")
    write(root / "referentiel" / "parametres.csv", RATES +
          "is.taux_minimum_perception;2026;2;%;Minimum;Minimum;CGI art. 21\ncac.taux;2026;10;%;CAC;CAC;CGI art. C 83\n")
    return root


def test_a_declaration_answer_equal_to_the_tool_is_accepted(tmp_path):
    """US-85 : TVA due de janvier = 38 500 ; acompte d'IS = 200 000 × 2 % × 1,10 = 4 400."""
    root = declaration_tree(tmp_path, declaration_question("tva_due", 38500), declaration_question("acompte_is", 4400))

    assert simulation_problems(root) == []


def test_a_declaration_answer_that_differs_from_the_tool_is_reported(tmp_path):
    root = declaration_tree(tmp_path, declaration_question("tva_due", 38000))

    assert any("S-A-M1-tva_due" in p and "38500" in p for p in simulation_problems(root))


def test_an_unknown_declaration_box_is_reported(tmp_path):
    root = declaration_tree(tmp_path, declaration_question("vsd_du", 1))

    assert any("S-A-M1-vsd_du" in p and "case" in p for p in simulation_problems(root))


def test_the_vsd_acronym_is_refused(tmp_path):
    """US-96 (S7) : les obligations du 15 portent leur nom du CGI."""
    assert any("VSD" in p for p in simulation_problems(tree(tmp_path, body="Payer le VSD. " + COMPANY_FILE)))


def test_the_simplified_regime_is_refused_unless_its_abolition_is_explained(tmp_path):
    """US-96 (S9) : la LF 2026 a remplacé le régime simplifié par l'IGS."""
    wrong = tree(tmp_path, body="L'entreprise relève du régime simplifié. " + COMPANY_FILE)
    assert any("régime simplifié" in p for p in simulation_problems(wrong))

    explained = tree(tmp_path, body="Le régime simplifié a été supprimé par la LF 2026 et remplacé par l'IGS. "
                                    + COMPANY_FILE)
    assert simulation_problems(explained) == []


def reconciliation_question(value, statement=None):
    rule = {"account": "5711", "date": "2026-01-31"}
    if statement is not None:
        rule["releve"] = statement
    return {"id": f"S-A-M1-rapp-{value}", "type": "numeric", "usage": "quiz", "exercice": 2026,
            "prompt": {"fr": "Écart ?", "en": "Gap?"}, "explanation": {"fr": "Rapprochement.", "en": "Reconciliation."},
            "numeric": {"value": value, "unit": "FCFA"}, "rapprochement": rule}


def test_a_reconciliation_answer_equal_to_the_book_is_accepted(tmp_path):
    """US-86 : solde comptable de la caisse au 31 janvier = 238 500 ; écart avec un relevé de 230 000 = 8 500."""
    root = declaration_tree(tmp_path, reconciliation_question(238500), reconciliation_question(8500, statement=230000))

    assert simulation_problems(root) == []


def test_a_reconciliation_answer_that_differs_from_the_book_is_reported(tmp_path):
    root = declaration_tree(tmp_path, reconciliation_question(8000, statement=230000))

    assert any("S-A-M1-rapp-8000" in p and "8500" in p for p in simulation_problems(root))


TRAP_Q = {"id": "S-A-M1-002", "type": "truefalse", "usage": "quiz", "piege": "frais_etablissement",
          "prompt": {"fr": "Les frais de constitution s'immobilisent ?", "en": "Are set-up costs capitalised?"},
          "explanation": {"fr": "Non : charges par nature.", "en": "No: expenses by nature."},
          "choices": [{"text": {"fr": "Vrai", "en": "True"}}, {"text": {"fr": "Faux", "en": "False"}, "correct": True}]}


ARTICLES = {"ref": "S-A-01-000", "kind": "statuts", "date": "2026-01-02",
            "title": {"fr": "Frais d'acte et d'enregistrement des statuts", "en": "Deed and registration costs"},
            "payload": {"totals": [{"label": {"fr": "Total", "en": "Total"}, "amount": 350000}]}}


def set_up_tree(tmp_path, debit_account, questions=(JOURNAL_Q, TRAP_Q)):
    entry = {"date": "2026-01-02", "piece": "S-A-01-000",
             "lines": [line(debit_account, "debit", 350000), line("401", "credit", 350000)]}
    root = tree(tmp_path, pieces=[INVOICE, BALANCE, ARTICLES], entries=[ENTRY, entry], questions=questions)
    write(root / "referentiel" / "syscohada.csv", "code;label_fr;label_en\n6011;Achats;Purchases\n"
          "401;Fournisseurs;Suppliers\n6324;Honoraires;Fees\n2181;Immobilisations diverses;Sundry assets\n")
    return root


def test_set_up_costs_are_expensed(tmp_path):
    """US-87 (S6) : frais d'acte et d'enregistrement en charges par nature."""
    problems = simulation_problems(set_up_tree(tmp_path, "6324"))

    assert not any("S-A-01-000" in p for p in problems)


def test_set_up_costs_are_never_capitalised(tmp_path):
    """US-87 (S6) : le SYSCOHADA révisé n'immobilise plus les frais d'établissement."""
    problems = simulation_problems(set_up_tree(tmp_path, "2181"))

    assert any("S-A-01-000" in p and "charges" in p for p in problems)


def calculation_question(qid, value, function, args, result):
    return {"id": qid, "type": "numeric", "usage": "exam", "exercice": 2026,
            "prompt": {"fr": "Montant ?", "en": "Amount?"}, "explanation": {"fr": "Calcul.", "en": "Computation."},
            "numeric": {"value": value, "unit": "FCFA"},
            "calcul": {"fonction": function, "args": args, "resultat": result}}


def test_inventory_answers_equal_to_the_reference_formulas_are_accepted(tmp_path):
    """US-88 : dotation au prorata temporis (6 000 000 sur 5 ans, mise en service en avril : 9 mois = 900 000), sortie
    au CMUP (coût unitaire 5 667 arrondi au franc, × 15 = 85 005) ; US-92 : retenue de 5,5 % sur 1 000 000."""
    root = inventory_tree(tmp_path, [ENTRY, DEPRECIATION])
    write(root / "simulation" / "a" / "m1" / "questions.json", [
        JOURNAL_Q,
        calculation_question("S-A-M6-001", 900000, "amortissement_lineaire", [6000000, 5, 4], [0, "dotation"]),
        calculation_question("S-A-M6-002", 85005, "sortie_cmup", [[[10, 5000], [20, 6000]], 15], ["valeur_sortie"]),
        calculation_question("S-D-M2-001", 55000, "retenue_source", [1000000, 5, 10], ["retenue"]),
    ])

    assert simulation_problems(root) == []


def test_an_inventory_answer_that_differs_from_the_formula_is_reported(tmp_path):
    root = tree(tmp_path, questions=[JOURNAL_Q, calculation_question(
        "S-A-M6-003", 1200000, "amortissement_lineaire", [6000000, 5, 4], [0, "dotation"])])

    assert any("S-A-M6-003" in p and "900000" in p for p in simulation_problems(root))


def test_only_the_reference_formulas_can_be_called(tmp_path):
    root = tree(tmp_path, questions=[JOURNAL_Q, calculation_question("S-A-M6-004", 1, "__import__", ["os"], [])])

    assert any("S-A-M6-004" in p and "formule inconnue" in p for p in simulation_problems(root))


SMT_Q = {"id": "S-B1-M2-001", "type": "numeric", "usage": "quiz", "exercice": 2026,
         "prompt": {"fr": "Total des dépenses de janvier ?\n\n[[piece:S-A-01-001]]",
                    "en": "Total January expenses?\n\n[[piece:S-A-01-001]]"},
         "explanation": {"fr": "SMT.", "en": "Cash-basis system."}, "numeric": {"value": 100000, "unit": "FCFA"}}


def test_an_igs_parcours_uses_numeric_questions_only(tmp_path):
    """US-90 (S14) : B1 tient le SMT ; pas de question journal."""
    assert simulation_problems(tree(tmp_path, questions=[SMT_Q], regime="igs", **IGS)) == []
    problems = simulation_problems(tree(tmp_path, questions=[SMT_Q, JOURNAL_Q], regime="igs", **IGS))
    assert any("S-A-M1-001" in p and "IGS" in p for p in problems)


def test_an_igs_business_never_records_vat(tmp_path):
    """US-90 : un contribuable à l'IGS ne facture ni ne déduit la TVA."""
    with_vat = {**ENTRY, "lines": [line("6011", "debit", 90000), line("4452", "debit", 10000),
                                   line("401", "credit", 100000)]}
    root = tree(tmp_path, pieces=[INVOICE], entries=[with_vat], questions=[SMT_Q], regime="igs", **IGS)
    write(root / "referentiel" / "syscohada.csv",
          "code;label_fr;label_en\n6011;Achats;Purchases\n401;Fournisseurs;Suppliers\n4452;TVA récupérable;VAT\n")

    assert any("4452" in p and "IGS" in p for p in simulation_problems(root))


def test_the_switch_to_the_actual_regime_happens_on_1_january_2027_only(tmp_path):
    """US-91 (S13) : B2 bascule au 1er janvier 2027 (bilan d'ouverture), jamais en cours d'année."""
    opening = {"date": "2027-01-01", "piece": "S-A-01-001",
               "lines": [line("6011", "debit", 1), line("401", "credit", 1)]}
    later = {**opening, "date": "2027-03-01"}

    assert simulation_problems(tree(tmp_path, pieces=[INVOICE], entries=[ENTRY, opening], questions=[SMT_Q],
                                    regime="igs_puis_reel", **IGS)) == []
    problems = simulation_problems(tree(tmp_path, pieces=[INVOICE], entries=[ENTRY, later], questions=[SMT_Q],
                                        regime="igs_puis_reel", **IGS))
    assert any("2027-03-01" in p and "1er janvier 2027" in p for p in problems)


def test_an_unknown_regime_is_reported(tmp_path):
    assert any("régime" in p for p in simulation_problems(tree(tmp_path, regime="simplifie")))


SERVICE_INVOICE = {"ref": "S-D-03-001", "kind": "facture_vente", "date": "2026-03-10",
                   "title": {"fr": "Facture d'entretien", "en": "Maintenance invoice"},
                   "payload": {"issuer": ISSUER, "customer": CUSTOMER, "number": "FA-2026-0001", "einvoice": "DGI-SFE-2026-000001", "totals": [{"label": {"fr": "HT", "en": "Net"}, "amount": 1000000}]}}
SERVICE_PAYMENT = {"ref": "S-D-04-002", "kind": "releve_bancaire", "date": "2026-04-05",
                   "title": {"fr": "Relevé d'avril", "en": "April statement"},
                   "payload": {"totals": [{"label": {"fr": "Crédit", "en": "Credit"}, "amount": 1192500}]}}


def cash_vat_tree(tmp_path, invoice_lines, payment_lines, suspense="471"):
    entries = [ENTRY, {"date": "2026-03-10", "piece": "S-D-03-001", "lines": invoice_lines},
               {"date": "2026-04-05", "piece": "S-D-04-002", "lines": payment_lines}]
    root = tree(tmp_path, pieces=[INVOICE, SERVICE_INVOICE, SERVICE_PAYMENT], entries=entries, cash_vat=True,
                suspense=suspense)
    write(root / "referentiel" / "syscohada.csv", "code;label_fr;label_en\n6011;Achats;Purchases\n"
          "401;Fournisseurs;Suppliers\n411;Clients;Customers\n706;Services vendus;Services\n"
          "4432;TVA sur prestations;VAT on services\n521;Banque;Bank\n471;Débiteurs et créditeurs divers;Sundry debtors and creditors\n")
    return root


def test_vat_on_services_is_due_when_the_customer_pays(tmp_path):
    """US-92 : prestataire D, TVA exigible à l'encaissement : 4432 est crédité au règlement, pas à la facture."""
    root = cash_vat_tree(
        tmp_path,
        [line("411", "debit", 1192500), line("706", "credit", 1000000), line("471", "credit", 192500)],
        [line("521", "debit", 1192500), line("411", "credit", 1192500),
         line("471", "debit", 192500), line("4432", "credit", 192500)])

    assert not any("4432" in p for p in simulation_problems(root))


def test_vat_on_services_recorded_on_the_invoice_is_reported(tmp_path):
    root = cash_vat_tree(
        tmp_path,
        [line("411", "debit", 1192500), line("706", "credit", 1000000), line("4432", "credit", 192500)],
        [line("521", "debit", 1192500), line("411", "credit", 1192500)])

    assert any("S-D-03-001" in p and "4432" in p and "encaissement" in p for p in simulation_problems(root))


def test_a_piece_cited_only_by_an_explanation_counts_as_used(tmp_path):
    """US-85 : un relevé cité dans la correction d'une question n'est pas une pièce orpheline."""
    statement = {**INVOICE, "ref": "S-A-01-050", "kind": "releve_bancaire"}
    question = {**JOURNAL_Q, "explanation": {"fr": "Voir [[piece:S-A-01-050]]", "en": "See [[piece:S-A-01-050]]"}}

    problems = simulation_problems(tree(tmp_path, pieces=[INVOICE, BALANCE, statement], questions=[question]))

    assert not any("S-A-01-050" in p for p in problems)


def test_set_up_costs_come_with_the_capitalisation_trap_question(tmp_path):
    """US-87 (S6) : quand le parcours a des frais de constitution, une question piège corrige l'ancien réflexe
    d'immobilisation des frais d'établissement."""
    problems = simulation_problems(set_up_tree(tmp_path, "6324", questions=[JOURNAL_Q]))

    assert any("piège" in p and "frais d'établissement" in p for p in problems)


SCHEDULE = {"ref": "S-A-12-001", "kind": "fiche_stock", "date": "2026-12-31",
            "title": {"fr": "Tableau d'amortissement", "en": "Depreciation schedule"},
            "payload": {"totals": [{"label": {"fr": "Dotation", "en": "Charge"}, "amount": 900000}]}}
DEPRECIATION = {"date": "2026-12-31", "piece": "S-A-12-001",
                "lines": [line("6813", "debit", 900000), line("2845", "credit", 900000)]}
DEPRECIATION_Q = {"id": "S-A-M6-010", "type": "numeric", "usage": "exam", "exercice": 2026,
                  "prompt": {"fr": "Dotation 2026 ?", "en": "2026 charge?"},
                  "explanation": {"fr": "Prorata de 9 mois.", "en": "9-month pro rata."},
                  "numeric": {"value": 900000, "unit": "FCFA"},
                  "calcul": {"fonction": "amortissement_lineaire", "args": [6000000, 5, 4], "resultat": [0, "dotation"]}}


def inventory_tree(tmp_path, entries):
    root = tree(tmp_path, pieces=[INVOICE, SCHEDULE], entries=entries, inventory_questions=[DEPRECIATION_Q])
    write(root / "referentiel" / "syscohada.csv", "code;label_fr;label_en\n6011;Achats;Purchases\n"
          "401;Fournisseurs;Suppliers\n6813;Dotations;Depreciation\n2845;Amortissements;Accumulated depreciation\n")
    return root


def test_the_year_end_charge_is_recorded_in_the_official_book(tmp_path):
    """US-88 : la dotation calculée figure au 31 décembre dans le livre officiel (compte 681)."""
    assert simulation_problems(inventory_tree(tmp_path, [ENTRY, DEPRECIATION])) == []


def test_a_year_end_charge_missing_from_the_book_is_reported(tmp_path):
    problems = simulation_problems(inventory_tree(tmp_path, [ENTRY]))

    assert any("S-A-M6-010" in p and "681" in p and "31 décembre" in p for p in problems)


def test_an_igs_company_file_cites_its_regime_and_its_withholding_rate(tmp_path):
    """US-90 : le dossier d'un parcours à l'IGS cite l'article du régime et le précompte de 5 % par [[param:]]."""
    without = tree(tmp_path, questions=[SMT_Q], regime="igs", **{**IGS, "body": "Ets Fouda. [[syscohada:6011]] "
                                                                                  "[[param:tva.taux_global]]"})
    problems = simulation_problems(without)

    assert any("precompte.taux_igs" in p for p in problems)
    assert any("93 quater" in p for p in problems)


def test_cnps_rates_are_never_parameters(tmp_path):
    """US-95 (S15, C28) : les montants CNPS figurent sur le bulletin ; aucun taux CNPS n'est paramétré."""
    root = tree(tmp_path)
    write(root / "referentiel" / "parametres.csv", RATES + "cnps.taux_salarie;2026;4.2;%;CNPS;CNPS;Code social\n")

    assert any("cnps.taux_salarie" in p and "CNPS" in p for p in scan_content(root))


def test_each_parcours_description_summarises_its_regime(tmp_path):
    """US-80 : la description de chaque parcours résume le profil, dont le régime."""
    assert any("description" in p for p in simulation_problems(tree(tmp_path, description={"fr": "", "en": ""})))
    problems = simulation_problems(tree(tmp_path, description={"fr": "Boutique de vêtements à Douala.", "en": "Shop."}))
    assert any("description" in p and "réel" in p for p in problems)


def test_parcours_a_is_ngono_mode_sarl(tmp_path):
    """US-81 (S17) : le dossier du parcours A présente Ngono Mode SARL, en FR et en EN."""
    problems = simulation_problems(tree(tmp_path, body="Mode Akwa SARL. [[syscohada:6011]] [[param:tva.taux_global]]"))

    assert any("Ngono Mode SARL" in p for p in problems)


IGS_CLASSES = [[500000, 20000], [1000000, 30000], [1500000, 40000], [2000000, 50000], [2500000, 60000],
               [5000000, 150000], [10000000, 300000], [20000000, 500000], [30000000, 1000000], [50000000, 2000000]]


def test_an_igs_answer_is_checked_against_the_tariff(tmp_path):
    """US-90 (U19) : 42 000 000 de CA, adhérent d'un Centre de Gestion Agréé : 2 000 000 / 2 = 1 000 000."""
    good = calculation_question("S-B1-M7-001", 1000000, "igs_annuel", [42000000, IGS_CLASSES, True], [])
    wrong = calculation_question("S-B1-M7-002", 2000000, "igs_annuel", [42000000, IGS_CLASSES, True], [])

    problems = simulation_problems(tree(tmp_path, questions=[SMT_Q, good, wrong], regime="igs", **IGS))

    assert not any("S-B1-M7-001" in p for p in problems)
    assert any("S-B1-M7-002" in p and "1000000" in p for p in problems)


def test_the_corporate_tax_answer_is_checked_against_the_minimum_tax(tmp_path):
    """US-89 : bénéfice 1 000 000, CA 90 000 000 : le minimum (1 980 000) l'emporte sur l'IS (330 000)."""
    args = [1000000, 90000000, 30, 2, 10]
    good = calculation_question("S-A-M7-001", 1980000, "impot_societes", args, ["du"])
    wrong = calculation_question("S-A-M7-002", 330000, "impot_societes", args, ["du"])

    problems = simulation_problems(tree(tmp_path, questions=[JOURNAL_Q, good, wrong]))

    assert not any("S-A-M7-001" in p for p in problems)
    assert any("S-A-M7-002" in p and "1980000" in p for p in problems)


CLOSING_STOCK = {"date": "2026-12-31", "piece": "S-A-12-001",
                 "lines": [line("311", "debit", 85005), line("6031", "credit", 85005)]}
STOCK_Q = {"id": "S-A-M6-020", "type": "numeric", "usage": "exam", "exercice": 2026,
           "prompt": {"fr": "Stock final ?", "en": "Closing stock?"}, "explanation": {"fr": "CMUP.", "en": "WAC."},
           "numeric": {"value": 85005, "unit": "FCFA"},
           "calcul": {"fonction": "sortie_cmup", "args": [[[10, 5000], [20, 6000]], 15], "resultat": ["valeur_stock"]}}


def stock_tree(tmp_path, entries):
    root = tree(tmp_path, pieces=[INVOICE, SCHEDULE], entries=entries, inventory_questions=[STOCK_Q])
    write(root / "referentiel" / "syscohada.csv", "code;label_fr;label_en\n6011;Achats;Purchases\n"
          "401;Fournisseurs;Suppliers\n311;Marchandises;Goods\n6031;Variation des stocks;Change in stocks\n")
    return root


def test_the_closing_stock_is_recorded_in_the_official_book(tmp_path):
    """US-88 : le stock final valorisé (CMUP) figure au 31 décembre dans le livre officiel (débit 31)."""
    assert simulation_problems(stock_tree(tmp_path, [ENTRY, CLOSING_STOCK])) == []


def test_a_closing_stock_missing_from_the_book_is_reported(tmp_path):
    problems = simulation_problems(stock_tree(tmp_path, [ENTRY]))

    assert any("S-A-M6-020" in p and "stock" in p and "31 décembre" in p for p in problems)


def test_simulation_modules_meet_the_question_volume_minimum(tmp_path):
    """U16 : la simulation, B1 compris, reste soumise au minimum de US-72 (12 questions d'examen, 8 de quiz)."""
    problems = scan_content(tree(tmp_path))

    assert "simulation/a/m1 : 0 questions d'examen sur 12" in problems
    assert "simulation/a/m1 : 1 questions de quiz sur 8" in problems


def test_the_tax_bridge_add_backs_are_checked_against_article_7(tmp_path):
    """US-89 (S21) : réintégrations de l'amortissement au-delà du taux maximal et des dons au-delà de 0,5 % du CA."""
    good = calculation_question("S-A-M7-010", 750000, "reintegration_amortissement", [3000000, 12000000, 25, 9], [])
    wrong = calculation_question("S-A-M7-011", 600000, "reintegration_dons", [600000, 90000000, 0.5], [])

    problems = simulation_problems(tree(tmp_path, questions=[JOURNAL_Q, good, wrong]))

    assert not any("S-A-M7-010" in p for p in problems)
    assert any("S-A-M7-011" in p and "150000" in p for p in problems)


def test_each_parcours_declares_its_tax_office():
    """US-89 (CGI art. 18 (1)) : l'échéance de la DSF dépend du centre de rattachement, déclaré par le parcours."""
    from courses.tests.content_rules import manifest_problems

    from simulation.tests.test_simulation_manifest import manifest

    data = manifest()
    del data["parties"][0]["centre_impots"]
    assert any("centre_impots attendu parmi" in p for p in manifest_problems(data))
    data["parties"][0]["centre_impots"] = "cdi"
    assert any("centre_impots attendu parmi" in p for p in manifest_problems(data))


DSF = {"ref": "S-A-13-001", "kind": "declaration", "date": "2027-04-15",
       "title": {"fr": "DSF 2026", "en": "2026 tax return"},
       "payload": {"totals": [{"label": {"fr": "IS dû", "en": "CIT due"}, "amount": 1980000}]}}


def test_the_tax_return_is_dated_by_its_deadline(tmp_path):
    """US-89 : rattachée au CIME, l'entreprise dépose sa DSF 2026 au plus tard le 15 avril 2027."""
    assert simulation_problems(tree(tmp_path, pieces=[INVOICE, BALANCE, DSF], centre="cime")) == []
    problems = simulation_problems(tree(tmp_path, pieces=[INVOICE, BALANCE, DSF], centre="dge"))
    assert any("S-A-13-001" in p and "2027-03-15" in p for p in problems)


def test_an_individual_business_files_by_15_march_even_under_a_cime(tmp_path):
    """US-89 (S37, CGI art. 74 et 91) : déclaration des résultats d'un exploitant individuel au plus tard le 15 mars."""
    root = tree(tmp_path, pieces=[INVOICE, BALANCE, DSF], centre="cime")
    manifest = json.loads((root / "simulation" / "formation.json").read_text(encoding="utf-8"))
    manifest["parties"][0]["forme"] = "individuelle"
    write(root / "simulation" / "formation.json", manifest)

    assert any("S-A-13-001" in p and "2027-03-15" in p for p in simulation_problems(root))


SMT_RETURN = [{"ref": f"S-A-13-{table[:3]}", "kind": "declaration", "date": "2027-05-15", "dsf": table,
               "title": {"fr": "DSF du SMT", "en": "Cash-basis tax return"},
               "payload": {"totals": [{"label": {"fr": "Total", "en": "Total"}, "amount": 100000}]}}
              for table in ("bilan_smt", "compte_resultat_smt")]
IGS_RETURN = {"ref": "S-A-13-igs", "kind": "declaration", "date": "2027-04-15",
              "title": {"fr": "Déclaration annuelle de l'IGS", "en": "Yearly IGS return"},
              "payload": {"totals": [{"label": {"fr": "IGS", "en": "IGS"}, "amount": 1000000}]}}


def igs_tree(tmp_path, pieces, turnover=18000000, entries=(ENTRY,)):
    root = tree(tmp_path, pieces=pieces, entries=entries, questions=[SMT_Q], regime="igs", centre="cfl", **IGS)
    manifest = json.loads((root / "simulation" / "formation.json").read_text(encoding="utf-8"))
    manifest["parties"][0]["chiffre_affaires_vise"] = turnover
    write(root / "simulation" / "formation.json", manifest)
    return root


def test_the_igs_return_is_due_by_15_april(tmp_path):
    """S38 (CGI art. C 41 modifié par la LF 2026, circulaire § 671) : déclaration et paiement de l'IGS au 15 avril."""
    assert simulation_problems(igs_tree(tmp_path, [INVOICE, BALANCE, IGS_RETURN, *SMT_RETURN])) == []
    late = {**IGS_RETURN, "date": "2027-04-16"}
    problems = simulation_problems(igs_tree(tmp_path, [INVOICE, BALANCE, late, *SMT_RETURN]))
    assert any("S-A-13-igs" in p and "2027-04-15" in p for p in problems)


def test_an_igs_business_files_its_cash_basis_return_by_15_may(tmp_path):
    """S38 (CGI art. C 44) : la DSF du SMT (bilan et compte de résultat, AUDCIF art. 28) est déposée au 15 mai."""
    late = [{**piece, "date": "2027-05-16"} for piece in SMT_RETURN]
    problems = simulation_problems(igs_tree(tmp_path, [INVOICE, BALANCE, IGS_RETURN, *late]))
    assert any("S-A-13-bil" in p and "2027-05-15" in p for p in problems)


def test_an_igs_business_above_10_million_files_a_cash_basis_return(tmp_path):
    """S38 (CGI art. C 44, circulaire § 677-678) : dès 10 millions de CA, SMT obligatoire et DSF du SMT."""
    problems = simulation_problems(igs_tree(tmp_path, [INVOICE, BALANCE, IGS_RETURN], turnover=18000000))
    assert any("DSF du SMT" in p for p in problems)
    assert not any("DSF du SMT" in p for p in simulation_problems(
        igs_tree(tmp_path, [INVOICE, BALANCE, IGS_RETURN], turnover=8000000)))


def test_an_igs_business_bears_its_purchase_withholding_as_a_cost(tmp_path):
    """S40 (CGI art. 21 (3)) : le précompte subi n'est imputable que pour l'IS ou l'IRPP ; à l'IGS il entre dans le
    coût d'achat et ne passe jamais en 4492."""
    with_advance = {**ENTRY, "lines": [line("6011", "debit", 100000), line("4492", "debit", 5000),
                                       line("401", "credit", 105000)]}
    problems = simulation_problems(igs_tree(tmp_path, [INVOICE, BALANCE, IGS_RETURN, *SMT_RETURN],
                                            entries=[with_advance]))
    assert any("4492" in p and "IGS" in p for p in problems)


def test_cash_basis_vat_needs_its_suspense_account(tmp_path):
    """US-92 (U20) : la TVA facturée attend l'encaissement sur le compte déclaré par le parcours ; à l'encaissement,
    ce compte est débité du montant porté au crédit de 4432."""
    lines_invoice = [line("411", "debit", 1192500), line("706", "credit", 1000000), line("471", "credit", 192500)]
    lines_payment = [line("521", "debit", 1192500), line("411", "credit", 1192500),
                     line("471", "debit", 192500), line("4432", "credit", 192500)]
    assert not any("attente" in p for p in simulation_problems(
        cash_vat_tree(tmp_path, lines_invoice, lines_payment, suspense="471")))
    assert any("compte_tva_attente" in p for p in simulation_problems(
        cash_vat_tree(tmp_path, lines_invoice, lines_payment, suspense=None)))
    unbalanced = [line("521", "debit", 1192500), line("411", "credit", 1000000), line("411", "credit", 192500),
                  line("4432", "credit", 192500), line("6011", "debit", 192500)]
    assert any("S-D-04-002" in p and "attente" in p for p in simulation_problems(
        cash_vat_tree(tmp_path, lines_invoice, unbalanced, suspense="471")))


def test_the_vat_suspense_account_exists_in_the_chart(tmp_path):
    """U20 (S24, par défaut 471) : le compte d'attente déclaré par le parcours existe dans le plan SYSCOHADA."""
    lines_invoice = [line("411", "debit", 1192500), line("706", "credit", 1000000), line("4799", "credit", 192500)]
    lines_payment = [line("521", "debit", 1192500), line("411", "credit", 1192500),
                     line("4799", "debit", 192500), line("4432", "credit", 192500)]

    problems = simulation_problems(cash_vat_tree(tmp_path, lines_invoice, lines_payment, suspense="4799"))

    assert any("compte_tva_attente" in p and "4799" in p and "plan" in p for p in problems)


def test_an_invoice_without_its_cameroonian_tax_identity_is_reported(tmp_path):
    """S27 : dans content/, une facture sans NIU, RCCM, numéro ni référence de facturation DGI est signalée."""
    bare = {**INVOICE, "payload": {k: v for k, v in INVOICE["payload"].items() if k != "issuer"}}

    problems = simulation_problems(tree(tmp_path, pieces=[bare, BALANCE]))

    assert any("S-A-01-001" in p and "émetteur" in p for p in problems)


SCENE_FR = ("### Lundi 5 janvier : la facture\n\nLe grossiste livre.\n\n[[piece:S-A-01-001]]\n\n**La règle.** Achats "
            "[[syscohada:6011]].\n\n> **Pourquoi ce choix et pas un autre.** Pas une immobilisation.\n\n**Ce que ça change.** "
            "Dette.\n\n**Où ça se range.** Classeur Achats.\n\n**Revoir :** Comptabilité M1 « Les achats ».\n")
SCENE_EN = ("### Monday 5 January: the invoice\n\nThe wholesaler delivers.\n\n[[piece:S-A-01-001]]\n\n**The rule.** "
            "Purchases [[syscohada:6011]].\n\n> **Why this choice and not another.** Not an asset.\n\n**What it changes.** "
            "Debt.\n\n**Where it is filed.** Purchases binder.\n\n**See again:** Accounting M1 “Purchases”.\n")


def narrated_tree(tmp_path, fr=SCENE_FR, en=SCENE_EN):
    root = tree(tmp_path, body=COMPANY_FILE + "\n\n" + fr, body_en=COMPANY_FILE_EN + "\n\n" + en)
    write(root / "compta" / "formation.json", {"slug": "compta", "prefix": "C", "parties": [
        {"slug": "p1", "modules": [{"order": 1, "dir": "p1/m1", "sections": []}]}]})
    return root


def test_a_month_piece_told_in_a_full_scene_passes(tmp_path):
    """S34 : une pièce comptable d'une section mensuelle racontée dans une scène aux cinq temps ne pose aucun problème."""
    assert not [p for p in simulation_problems(narrated_tree(tmp_path)) if "scène" in p or "Revoir" in p]


def test_a_month_piece_shown_without_its_scene_is_reported(tmp_path):
    """S34 : un parcours muet, qui aligne ses pièces sans les raconter, est refusé."""
    problems = simulation_problems(narrated_tree(tmp_path, fr="[[piece:S-A-01-001]]\n", en="[[piece:S-A-01-001]]\n"))

    assert any("S-A-01-001" in p and "sans scène" in p for p in problems)


def test_a_scene_missing_one_of_its_five_beats_is_reported(tmp_path):
    """S34 : chaque scène dit la règle, le pourquoi, l'effet, le rangement et le renvoi au cours."""
    problems = simulation_problems(narrated_tree(tmp_path, en=SCENE_EN.replace("**Where it is filed.** Purchases binder.\n\n",
                                                                                 "")))

    assert any("S-A-01-001" in p and "Where it is filed" in p for p in problems)


def test_a_course_reference_to_a_missing_module_is_reported(tmp_path):
    """S34 : « Revoir » désigne un module existant de la formation citée."""
    problems = simulation_problems(narrated_tree(tmp_path, fr=SCENE_FR.replace("Comptabilité M1", "Comptabilité M99")))

    assert any("Revoir" in p and "M99" in p for p in problems)


def test_a_cited_figure_must_exist_in_static(tmp_path):
    """S33 : une figure citée par une scène existe dans static/content/."""
    figure = "\n\n![Circuit](/static/content/simulation/a/absente.fr.svg)\n"
    problems = simulation_problems(narrated_tree(tmp_path, fr=SCENE_FR + figure))

    assert any("absente.fr.svg" in p and "figure" in p for p in problems)
