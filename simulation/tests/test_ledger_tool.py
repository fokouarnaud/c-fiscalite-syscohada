"""US-93, US-84, US-85, US-89 : le livre officiel d'un parcours est l'unique source de vérité ; balances, déclarations
du 15 et passerelle fiscale en sont calculées, jamais saisies (S2, S12)."""
import datetime
from decimal import Decimal

from tools.simulation import ledger

ACCOUNTS = {"101", "521", "5521", "6011", "4452", "401", "411", "7011", "4431", "4492", "4472", "661", "422", "571"}


def line(account, side, amount):
    return {"account": account, "side": side, "amount": amount}


def entry(date, piece, *lines):
    return {"date": date, "piece": piece, "lines": list(lines)}


CAPITAL = entry("2026-01-02", "S-A-01-001", line("521", "debit", 5000000), line("101", "credit", 5000000))
PURCHASE = entry("2026-01-05", "S-A-01-002",
                 line("6011", "debit", 1000000), line("4452", "debit", 192500), line("401", "credit", 1192500))
PRECOMPTE = entry("2026-01-05", "S-A-01-002", line("4492", "debit", 20000), line("521", "credit", 20000))
SALE = entry("2026-01-20", "S-A-01-003",
             line("5521", "debit", 2385000), line("7011", "credit", 2000000), line("4431", "credit", 385000))
PAYROLL = entry("2026-01-31", "S-A-01-004",
                line("661", "debit", 300000), line("4472", "credit", 25000), line("422", "credit", 275000))
FEBRUARY_SALE = entry("2026-02-03", "S-A-02-001",
                      line("571", "debit", 119250), line("7011", "credit", 100000), line("4431", "credit", 19250))
BOOK = [CAPITAL, PURCHASE, PRECOMPTE, SALE, PAYROLL, FEBRUARY_SALE]
PIECES = {"S-A-01-001", "S-A-01-002", "S-A-01-003", "S-A-01-004", "S-A-02-001"}


def test_a_coherent_book_has_no_error():
    assert ledger.entry_errors(BOOK, ACCOUNTS, PIECES) == []


def test_an_unbalanced_entry_is_reported_with_its_piece():
    wrong = entry("2026-01-06", "S-A-01-002", line("6011", "debit", 100), line("401", "credit", 99))

    assert any("S-A-01-002" in error and "équilibr" in error for error in ledger.entry_errors([wrong], ACCOUNTS, PIECES))


def test_an_unknown_account_or_piece_is_reported():
    wrong = entry("2026-01-06", "S-A-09-999", line("6099", "debit", 100), line("401", "credit", 100))

    errors = ledger.entry_errors([wrong], ACCOUNTS, PIECES)

    assert any("6099" in error for error in errors)
    assert any("S-A-09-999" in error for error in errors)


def test_amounts_are_positive_whole_fcfa():
    wrong = entry("2026-01-06", "S-A-01-002", line("6011", "debit", 100.5), line("401", "credit", 100.5))

    assert any("FCFA" in error for error in ledger.entry_errors([wrong], ACCOUNTS, PIECES))


def test_pieces_never_used_by_the_book_or_a_question_are_listed():
    assert ledger.unused_pieces(BOOK, PIECES | {"S-A-01-099", "S-A-01-100"}, question_pieces={"S-A-01-100"}) == ["S-A-01-099"]


def test_the_balance_at_the_start_of_a_month_only_counts_earlier_entries():
    """US-84 : la balance d'ouverture de février reprend janvier, pas février."""
    balance = ledger.trial_balance(BOOK, before=datetime.date(2026, 2, 1))

    assert balance["7011"] == -2000000
    assert balance["521"] == 4980000
    assert "571" not in balance
    assert sum(balance.values()) == 0


def test_the_balance_piece_is_generated_from_the_book():
    piece = ledger.balance_piece(BOOK, before=datetime.date(2026, 2, 1), labels={"521": {"fr": "Banque", "en": "Bank"}})

    debit = sum(row.get("debit", 0) for row in piece["lines"])
    credit = sum(row.get("credit", 0) for row in piece["lines"])
    assert debit == credit == 5000000 + 1000000 + 192500 + 20000 + 2385000 + 300000 - 20000
    labels = [row["label"] for row in piece["lines"]]
    assert labels[0] == {"fr": "101", "en": "101"}  # comptes dans l'ordre du plan ; libellé fourni ou code seul
    assert {"fr": "521 Banque", "en": "521 Bank"} in labels


def test_the_declaration_of_the_15th_is_computed_from_the_month():
    """US-85 : TVA, précompte imputé, acompte d'IS (2 % + 10 % de CAC) et retenues sur salaires de janvier."""
    declaration = ledger.monthly_declaration(BOOK, 2026, 1, minimum_rate=Decimal("2"), cac_rate=Decimal("10"))

    assert declaration["chiffre_affaires"] == 2000000
    assert (declaration["tva_collectee"], declaration["tva_deductible"]) == (385000, 192500)
    assert (declaration["tva_due"], declaration["credit_tva"]) == (192500, 0)
    assert declaration["acompte_is"] == 44000  # 2 000 000 × 2 % × 1,10
    assert declaration["precompte_impute"] == 20000
    assert declaration["acompte_is_net"] == 24000
    assert declaration["retenues_salaires"] == 25000


def test_a_vat_credit_is_carried_forward_not_paid():
    purchase_only = [PURCHASE]

    declaration = ledger.monthly_declaration(purchase_only, 2026, 1, minimum_rate=Decimal("2"), cac_rate=Decimal("10"))

    assert (declaration["tva_due"], declaration["credit_tva"]) == (0, 192500)
    later = ledger.monthly_declaration([FEBRUARY_SALE], 2026, 2, minimum_rate=Decimal("2"), cac_rate=Decimal("10"),
                                       credit_reporte=declaration["credit_tva"])
    assert (later["tva_due"], later["credit_tva"]) == (0, 192500 - 19250)


def test_the_accounting_result_is_products_minus_charges():
    assert ledger.accounting_result(BOOK[:5]) == 2000000 - 1000000 - 300000


def test_the_tax_bridge_adds_back_and_deducts():
    """US-89 : résultat fiscal = résultat comptable + réintégrations − déductions."""
    assert ledger.tax_result(700000, reintegrations=[150000, 50000], deductions=[30000]) == 870000


def test_a_journal_question_must_match_the_official_entry_of_its_piece():
    """US-93 : la clé de correction d'une question journal est l'écriture officielle de sa pièce."""
    good = ("S-A-M1-001", "S-A-01-003", [("7011", "credit", 2000000), ("5521", "debit", 2385000), ("4431", "credit", 385000)])
    bad = ("S-A-M1-002", "S-A-01-003", [("5521", "debit", 2385000), ("7011", "credit", 2385000)])

    assert ledger.journal_mismatches(BOOK, [good, bad]) == ["S-A-M1-002"]


def test_the_book_balance_of_a_treasury_account_at_a_date():
    """US-86 : solde comptable (débit − crédit) du compte et de ses sous-comptes, écritures du jour comprises."""
    assert ledger.account_balance(BOOK, "52", upto=datetime.date(2026, 1, 31)) == 4980000
    assert ledger.account_balance(BOOK, "552", upto=datetime.date(2026, 1, 19)) == 0
    assert ledger.account_balance(BOOK, "552", upto=datetime.date(2026, 1, 20)) == 2385000


def test_the_reconciliation_gap_is_the_book_balance_minus_the_statement():
    """US-86 : un relevé à 2 380 000 face à un solde comptable de 2 385 000 laisse 5 000 à expliquer."""
    assert ledger.reconciliation_gap(BOOK, "5521", upto=datetime.date(2026, 1, 31), statement=2380000) == 5000


RATES_IS = {"taux_is": Decimal("30"), "taux_minimum": Decimal("2"), "taux_cac": Decimal("10")}


def test_the_minimum_tax_applies_when_it_exceeds_the_corporate_tax():
    """US-89 : bénéfice fiscal 1 000 000 → IS 330 000 ; minimum sur 90 000 000 de CA → 1 980 000, qui l'emporte ;
    les acomptes et précomptes versés (1 500 000) s'imputent : solde 480 000."""
    result = ledger.corporate_tax(1000000, turnover=90000000, prepaid=1500000, **RATES_IS)

    assert (result["is_total"], result["minimum_total"], result["du"]) == (330000, 1980000, 1980000)
    assert result["solde"] == 480000


def test_the_corporate_tax_applies_when_it_exceeds_the_minimum():
    """Bénéfice fiscal 10 000 000 → IS 3 300 000 > minimum 1 980 000 ; acomptes 2 000 000 → solde 1 300 000."""
    result = ledger.corporate_tax(10000000, turnover=90000000, prepaid=2000000, **RATES_IS)

    assert (result["du"], result["solde"]) == (3300000, 1300000)


def test_overpaid_instalments_leave_a_credit_not_a_negative_tax():
    result = ledger.corporate_tax(0, turnover=10000000, prepaid=500000, **RATES_IS)

    assert (result["du"], result["solde"], result["excedent"]) == (220000, 0, 280000)


def test_the_tax_return_deadline_depends_on_the_tax_office():
    """US-89 (CGI art. 18 (1)) : 15 mars à la DGE, 15 avril au CIME, 15 mai au centre de fiscalité locale ; une
    contribuable à l'IGS dépose sa déclaration annuelle et paie l'IGS au plus tard le 15 avril (art. C 41 modifié
    par la LF 2026, circulaire § 671, S38), qu'il soit une société ou une personne physique."""
    assert ledger.tax_return_deadline("dge", 2026) == datetime.date(2027, 3, 15)
    assert ledger.tax_return_deadline("cime", 2026) == datetime.date(2027, 4, 15)
    assert ledger.tax_return_deadline("cfl", 2026) == datetime.date(2027, 5, 15)
    assert ledger.tax_return_deadline("cfl", 2026, regime="igs") == datetime.date(2027, 4, 15)
    assert ledger.tax_return_deadline("cfl", 2026, regime="igs", forme="individuelle") == datetime.date(2027, 4, 15)


def test_the_cash_basis_tax_return_is_due_by_15_may():
    """S38 (CGI art. C 44, circulaire § 677-678) : à l'IGS, dès 10 millions de CA, DSF du SMT au plus tard le
    15 mai."""
    assert ledger.smt_return_deadline(2026) == datetime.date(2027, 5, 15)


def test_an_individual_business_files_its_results_by_15_march_whatever_its_office():
    """US-89 (S37, CGI art. 74 et 91) : un exploitant individuel au réel souscrit la déclaration annuelle de ses
    résultats et paie le solde de l'IRPP au plus tard le 15 mars, même rattaché au CIME ; l'art. 18 (1) vise l'IS."""
    assert ledger.tax_return_deadline("cime", 2026, forme="individuelle") == datetime.date(2027, 3, 15)
    assert ledger.tax_return_deadline("cime", 2026, forme="societe") == datetime.date(2027, 4, 15)


def test_settling_last_month_return_does_not_change_this_month_return():
    """US-85 : le règlement du 15 (débit de 443, crédit de 445 et des retenues 447) solde le mois précédent ; la
    déclaration du mois en cours ne retient que la TVA facturée, la TVA déductible et les retenues du mois."""
    settlement = entry("2026-02-15", "S-A-02-002", line("4431", "debit", 385000), line("4452", "credit", 192500),
                       line("4472", "debit", 25000), line("521", "credit", 217500))

    declaration = ledger.monthly_declaration([FEBRUARY_SALE, settlement], 2026, 2, minimum_rate=Decimal("2"),
                                             cac_rate=Decimal("10"))

    assert (declaration["tva_collectee"], declaration["tva_deductible"]) == (19250, 0)
    assert declaration["retenues_salaires"] == 0
