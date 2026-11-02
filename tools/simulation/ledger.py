"""Livre officiel d'un parcours de la simulation (US-93) : seule source de vérité comptable du parcours.

Balances, déclarations du 15 et passerelle fiscale en sont calculées (US-84, US-85, US-89), jamais saisies à la main.
Python standard uniquement (NFR-10) ; une écriture = {date, piece, lines: [{account, side, amount}]}.
"""
import datetime
from collections import Counter
from decimal import Decimal

from referentiel.calculs import franc


def _date(entry):
    return datetime.date.fromisoformat(entry["date"])


def _is_fcfa(amount):
    return isinstance(amount, int) and not isinstance(amount, bool) and amount > 0


def entry_errors(entries, accounts, pieces):
    """Écritures déséquilibrées, montants non entiers, comptes absents du plan, pièces inconnues."""
    errors = []
    for entry in entries:
        ref = entry.get("piece", "?")
        if ref not in pieces:
            errors.append(f"{entry['date']} : pièce inconnue {ref}")
        totals = Counter()
        for line in entry["lines"]:
            if line["account"] not in accounts:
                errors.append(f"{ref} : compte {line['account']} absent du plan SYSCOHADA")
            if not _is_fcfa(line["amount"]):
                errors.append(f"{ref} : montant {line['amount']} non entier en FCFA")
                continue
            totals[line["side"]] += line["amount"]
        if totals["debit"] != totals["credit"]:
            errors.append(f"{ref} : écriture non équilibrée ({totals['debit']} au débit, {totals['credit']} au crédit)")
    return errors


def unused_pieces(entries, pieces, question_pieces=()):
    """Pièces qui ne servent ni à une écriture du livre ni à une question (DoD-Parcours 2)."""
    used = {entry["piece"] for entry in entries} | set(question_pieces)
    return sorted(set(pieces) - used)


def _net(line):
    return line["amount"] if line["side"] == "debit" else -line["amount"]


def trial_balance(entries, before=None):
    """{compte: solde (débit − crédit)} des écritures datées avant `before` ; les comptes soldés sont omis."""
    balance = Counter()
    for entry in entries:
        if before is None or _date(entry) < before:
            for line in entry["lines"]:
                balance[line["account"]] += _net(line)
    return {account: amount for account, amount in sorted(balance.items()) if amount}


def balance_piece(entries, before, labels=None):
    """Contenu d'une pièce « balance » (US-84) : une ligne par compte, solde au débit ou au crédit."""
    labels = labels or {}
    lines = []
    for account, amount in trial_balance(entries, before).items():
        label = labels.get(account, {})
        text = {lang: f"{account} {label[lang]}" if label.get(lang) else account for lang in ("fr", "en")}
        lines.append({"label": text, **({"debit": amount} if amount > 0 else {"credit": -amount})})
    return {"lines": lines}


def account_balance(entries, prefix, upto):
    """US-86 : solde comptable (débit − crédit) des comptes commençant par `prefix`, écritures du jour `upto` comprises."""
    return sum(_net(line) for entry in entries if _date(entry) <= upto
               for line in entry["lines"] if line["account"].startswith(prefix))


def reconciliation_gap(entries, prefix, upto, statement):
    """US-86 : écart à expliquer entre le solde comptable et le solde du relevé (banque ou Mobile Money)."""
    return account_balance(entries, prefix, upto) - statement


def _movement(entries, prefix, year, month, side):
    """Total du mois, sur un seul sens (`debit` ou `credit`), des comptes commençant par `prefix` : le règlement d'une
    déclaration passé dans le mois (sens opposé) ne modifie pas la déclaration du mois."""
    return sum(line["amount"] for entry in entries if (_date(entry).year, _date(entry).month) == (year, month)
               for line in entry["lines"] if line["account"].startswith(prefix) and line["side"] == side)


def monthly_declaration(entries, year, month, minimum_rate, cac_rate, credit_reporte=0):
    """Montants de la déclaration du 15 du mois suivant (US-85) : TVA, acompte d'IS au minimum de perception majoré
    des CAC (CGI art. 21), précompte imputé (4492) et retenues sur salaires (447)."""
    chiffre_affaires = _movement(entries, "70", year, month, "credit")
    collectee = _movement(entries, "443", year, month, "credit")
    deductible = _movement(entries, "445", year, month, "debit")
    solde = collectee - deductible - credit_reporte
    acompte = int(franc(Decimal(chiffre_affaires) * minimum_rate / 100 * (1 + cac_rate / 100)))
    precompte = _movement(entries, "4492", year, month, "debit")
    return {
        "chiffre_affaires": chiffre_affaires,
        "tva_collectee": collectee,
        "tva_deductible": deductible,
        "tva_due": max(solde, 0),
        "credit_tva": max(-solde, 0),
        "acompte_is": acompte,
        "precompte_impute": precompte,
        "acompte_is_net": max(acompte - precompte, 0),
        "retenues_salaires": _movement(entries, "447", year, month, "credit"),
    }


def accounting_result(entries):
    """Résultat comptable : produits − charges (classes 6, 7 et 8)."""
    return -sum(_net(line) for entry in entries for line in entry["lines"] if line["account"][0] in "678")


def tax_result(accounting, reintegrations=(), deductions=()):
    """Passerelle (US-89) : résultat fiscal = résultat comptable + réintégrations − déductions."""
    return accounting + sum(reintegrations) - sum(deductions)


def corporate_tax(tax_result, turnover, prepaid, taux_is, taux_minimum, taux_cac):
    """US-89 : IS de l'exercice = le plus élevé de l'IS sur le résultat fiscal et du minimum de perception sur le
    chiffre d'affaires (CGI art. 17, 21, 23 ; referentiel.calculs.impot_societes), sous déduction des acomptes,
    précomptes et retenues déjà versés (`prepaid`) ; un excédent n'est jamais un impôt négatif."""
    from referentiel.calculs import impot_societes

    computed = impot_societes(Decimal(tax_result), Decimal(turnover), taux_is, taux_minimum, taux_cac)
    result = {key: int(value) for key, value in computed.items()}
    result["solde"] = max(result["du"] - prepaid, 0)
    result["excedent"] = max(prepaid - result["du"], 0)
    return result


def tax_office(turnover, seuil_cime, seuil_dge):
    """Centre de rattachement selon le chiffre d'affaires (DGI : CIME de 50 millions à 3 milliards, DGE au-delà) ;
    en deçà, centre de fiscalité locale."""
    if turnover >= seuil_dge:
        return "dge"
    return "cime" if turnover >= seuil_cime else "cfl"


TAX_RETURN_DEADLINES = {"dge": (3, 15), "cime": (4, 15), "cfl": (5, 15)}


def tax_return_deadline(centre, exercice, regime="reel", forme="societe"):
    """Date limite de la déclaration de l'exercice : CGI art. 18 (1) selon le centre de rattachement (DGE, CIME,
    centre de fiscalité locale) pour l'IS ; 15 mars pour la déclaration annuelle d'un contribuable à l'IGS (art. C 41)
    et pour celle des résultats d'un exploitant individuel au réel (art. 74 et 91)."""
    month, day = (3, 15) if regime != "reel" or forme == "individuelle" else TAX_RETURN_DEADLINES[centre]
    return datetime.date(exercice + 1, month, day)


def journal_mismatches(entries, questions):
    """Questions `journal` [(id, pièce, [(compte, sens, montant)])] dont la clé diffère de l'écriture officielle."""
    official = {}
    for entry in entries:
        official.setdefault(entry["piece"], Counter()).update(
            (line["account"], line["side"], line["amount"]) for line in entry["lines"])
    return [question_id for question_id, piece, lines in questions
            if Counter((str(a), s, int(m)) for a, s, m in lines) != official.get(piece, Counter())]
