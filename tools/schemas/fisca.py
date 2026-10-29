"""Schémas de la formation Fiscalité CGI Cameroun (C13) : python -m tools.schemas fisca."""
from .common import ACCENT, Drawing, block, tr

SLUG = "fisca"
EN = {
    "Cycle déclaratif de l'entreprise": "The company's filing cycle",
    "Chaque mois, au plus tard le 15": "Every month, by the 15th",
    "Déclaration et paiement : TVA, acomptes d'IS, retenues sur salaires":
        "Return and payment: VAT, CIT instalments, payroll withholdings",
    "Clôture de l'exercice": "Year-end closing",
    "Déclaration statistique et fiscale (DSF), solde de l'IS": "Statistical and tax return (DSF), CIT balance",
    "Contrôle et contentieux (Livre des procédures fiscales)": "Audit and disputes (Tax procedures book)",
}


def s_cycle_declaratif():
    d = Drawing(640, 320, tr("Cycle déclaratif de l'entreprise"))
    d.text(320, 32, "Cycle déclaratif de l'entreprise", size=15, weight="700")
    block(d, 30, 70, 270, 60, tr("Chaque mois, au plus tard le 15"))
    d.text(165, 150, "Déclaration et paiement : TVA, acomptes d'IS, retenues sur salaires", size=11, anchor="start")
    block(d, 340, 70, 270, 60, tr("Clôture de l'exercice"))
    d.text(475, 175, "Déclaration statistique et fiscale (DSF), solde de l'IS", size=11)
    block(d, 140, 220, 360, 60, tr("Contrôle et contentieux (Livre des procédures fiscales)"), size=11)
    d.arrow((300, 100), (340, 100), color=ACCENT)
    d.arrow((475, 130), (420, 220), color=ACCENT)
    return d


SECTION_DIAGRAMS = {7: [s_cycle_declaratif]}
QUESTION_DIAGRAMS = {}


def question_dir(module):
    raise ValueError(f"Aucun schéma de question pour le module {module}.")
