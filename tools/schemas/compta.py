"""Schémas de la formation Comptabilité SYSCOHADA (C13) : python -m tools.schemas compta.

Les taux viennent de content/referentiel/parametres.csv et les montants de referentiel.calculs : un schéma ne recopie
jamais un chiffre à la main.
"""
from decimal import Decimal

from referentiel import calculs

from . import common
from .common import ACCENT, INK, SOFT, Drawing, block, tr

SLUG = "compta"
EN = {
    "Compte en T : 601 Achats de marchandises": "T-account: 601 Purchases of goods",
    "Débit": "Debit", "Crédit": "Credit",
    "Emplois, charges": "Uses, expenses", "Ressources, produits": "Sources, income",
    "Solde débiteur = total débit − total crédit": "Debit balance = total debits − total credits",
    "Bilan SYSCOHADA (schéma)": "SYSCOHADA balance sheet (outline)",
    "ACTIF": "ASSETS", "PASSIF": "EQUITY AND LIABILITIES",
    "Actif immobilisé (classe 2)": "Fixed assets (class 2)", "Actif circulant (classes 3 et 4)": "Current assets (classes 3 and 4)",
    "Trésorerie-actif (classe 5)": "Cash assets (class 5)",
    "Capitaux propres (classe 1)": "Equity (class 1)", "Dettes financières (classe 1)": "Financial debts (class 1)",
    "Passif circulant (classe 4)": "Current liabilities (class 4)", "Trésorerie-passif (classe 5)": "Cash liabilities (class 5)",
    "Circuit de la TVA": "VAT circuit",
    "TVA facturée au client": "VAT charged to the customer", "443 État, TVA facturée": "443 State, VAT charged",
    "TVA payée au fournisseur": "VAT paid to the supplier", "445 État, TVA récupérable": "445 State, recoverable VAT",
    "TVA à reverser = 443 − 445": "VAT to pay = 443 − 445", "4441 État, TVA due": "4441 State, VAT due",
    "Taux global : {global_} (principal {principal} + CAC {cac})": "Overall rate: {global_} (standard {principal} + council cents {cac})",
    "Plan d'amortissement linéaire": "Straight-line depreciation schedule",
    "Valeur d'origine {valeur}, 5 ans, mise en service en avril": "Cost {valeur}, 5 years, in service from April",
    "Année {n}": "Year {n}",
}
FRISE_VALEUR, FRISE_ANNEES, FRISE_MOIS = Decimal("10000000"), 5, 4


def montant(value):
    """« 1 500 000 » en français, « 1,500,000 » en anglais (texte d'un schéma, hors Django)."""
    grouped = f"{int(value):,}"
    return grouped if common.LANG == "en" else grouped.replace(",", " ")


def taux(value):
    text = f"{value.normalize():f}"
    return f"{text}%" if common.LANG == "en" else f"{text.replace('.', ',')} %"


def parametre(key):
    import csv

    with open(common.ROOT / "content" / "referentiel" / "parametres.csv", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle, delimiter=";") if row["key"] == key]
    return Decimal(max(rows, key=lambda row: int(row["exercice"]))["value"])


def s_compte_en_t():
    d = Drawing(560, 260, tr("Compte en T : 601 Achats de marchandises"))
    d.text(280, 34, "Compte en T : 601 Achats de marchandises", size=15, weight="700")
    d.wire((60, 70), (500, 70), width=3)
    d.wire((280, 70), (280, 210), width=3)
    d.text(170, 60, "Débit", weight="700", color=ACCENT)
    d.text(390, 60, "Crédit", weight="700", color=ACCENT)
    d.text(170, 110, "Emplois, charges", color=SOFT, italic=True)
    d.text(390, 110, "Ressources, produits", color=SOFT, italic=True)
    d.text(280, 240, "Solde débiteur = total débit − total crédit", size=12)
    return d


def s_bilan():
    d = Drawing(620, 330, tr("Bilan SYSCOHADA (schéma)"))
    d.text(310, 32, "Bilan SYSCOHADA (schéma)", size=15, weight="700")
    d.text(160, 62, "ACTIF", weight="700", color=ACCENT)
    d.text(460, 62, "PASSIF", weight="700", color=ACCENT)
    for i, label in enumerate(("Actif immobilisé (classe 2)", "Actif circulant (classes 3 et 4)", "Trésorerie-actif (classe 5)")):
        block(d, 30, 80 + i * 76, 260, 62, tr(label))
    for i, label in enumerate(("Capitaux propres (classe 1)", "Dettes financières (classe 1)", "Passif circulant (classe 4)",
                               "Trésorerie-passif (classe 5)")):
        block(d, 330, 80 + i * 57, 260, 47, tr(label))
    return d


def s_circuit_tva():
    principal, cac = parametre("tva.taux_principal"), parametre("cac.taux")
    global_ = parametre("tva.taux_global")
    d = Drawing(640, 300, tr("Circuit de la TVA"))
    d.text(320, 32, "Circuit de la TVA", size=15, weight="700")
    block(d, 30, 70, 260, 60, tr("443 État, TVA facturée"))
    d.text(160, 150, "TVA facturée au client", size=12, color=SOFT)
    block(d, 350, 70, 260, 60, tr("445 État, TVA récupérable"))
    d.text(480, 150, "TVA payée au fournisseur", size=12, color=SOFT)
    block(d, 190, 190, 260, 60, tr("4441 État, TVA due"))
    d.arrow((160, 130), (260, 190))
    d.arrow((480, 130), (380, 190))
    d.text(320, 278, "TVA à reverser = 443 − 445", size=12)
    d.text(320, 56, tr("Taux global : {global_} (principal {principal} + CAC {cac})").format(
        global_=taux(global_), principal=taux(principal), cac=taux(cac)), size=12, color=INK)
    return d


def s_frise_amortissement():
    plan = calculs.amortissement_lineaire(FRISE_VALEUR, FRISE_ANNEES, mois_debut=FRISE_MOIS)
    d = Drawing(120 + 100 * len(plan), 230, tr("Plan d'amortissement linéaire"))
    d.text(d.w / 2, 32, "Plan d'amortissement linéaire", size=15, weight="700")
    d.text(d.w / 2, 54, tr("Valeur d'origine {valeur}, 5 ans, mise en service en avril").format(valeur=montant(FRISE_VALEUR)),
           size=12, color=SOFT)
    top = max(row["dotation"] for row in plan)
    for i, row in enumerate(plan):
        x, height = 70 + 100 * i, float(row["dotation"] / top) * 110
        d.add(f'<rect x="{x}" y="{190 - height:.1f}" width="60" height="{height:.1f}" rx="6" fill="{ACCENT}"/>')
        d.text(x + 30, 182 - height, montant(row["dotation"]), size=11, weight="600")
        d.text(x + 30, 210, tr("Année {n}").format(n=i + 1), size=11)
    return d


SECTION_DIAGRAMS = {1: [s_compte_en_t, s_bilan], 6: [s_circuit_tva], 20: [s_frise_amortissement]}
QUESTION_DIAGRAMS = {}


def question_dir(module):
    raise ValueError(f"Aucun schéma de question pour le module {module}.")
