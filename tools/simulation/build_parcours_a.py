"""Génère le parcours A de la simulation (Ngono Mode SARL, exercice 2026) dans content/simulation/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_a

Tout est calculé, rien n'est saisi à la main : taux de content/referentiel/parametres.csv, formules de
referentiel/calculs.py, balances et déclarations de tools/simulation/ledger.py. La sortie est déterministe ; les
contrôles bloquants de courses/tests/content_rules.py la vérifient à chaque `pytest` (US-93, DoD-Parcours).
"""
import calendar
import csv
import datetime
import json
from decimal import Decimal as D
from pathlib import Path

from referentiel import calculs
from tools.simulation import ledger, narrative_a

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content" / "simulation"
YEAR = 2026
MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
             "novembre", "décembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
# Module de chaque mois (S11) : M1 création et janvier, M2 à M5 trimestres, M6 inventaire, M7 passerelle et DSF.
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}


def load_parameters():
    with open(ROOT / "content" / "referentiel" / "parametres.csv", encoding="utf-8", newline="") as handle:
        return {row["key"]: D(row["value"]) for row in csv.DictReader(handle, delimiter=";") if row["exercice"] == "2026"}


def load_labels():
    with open(ROOT / "content" / "referentiel" / "syscohada.csv", encoding="utf-8", newline="") as handle:
        return {row["code"]: {"fr": row["label_fr"], "en": row["label_en"]}
                for row in csv.DictReader(handle, delimiter=";")}


P = load_parameters()
LABELS = load_labels()
SELLER = {"name": "Ngono Mode SARL", "niu": "M012600008421K", "rccm": "RC/DLA/2026/B/0117", "regime": "réel",
          "centre": "CIME Douala", "address": "Boulevard de la Liberté, Akwa, Douala"}
SUPPLIER = {"name": "Sawa Textiles SARL", "niu": "M011900004517T", "rccm": "RC/DLA/2019/B/0458", "regime": "réel",
            "centre": "CIME Douala", "address": "Zone portuaire, Bonabéri, Douala"}
NOTARY = {"name": "Étude de Maître Ekambi, notaire", "niu": "P011500002203M", "rccm": "Office notarial n° 12",
          "regime": "réel", "centre": "CIME Douala", "address": "Rue Joss, Bonanjo, Douala"}
GARAGE = {"name": "Auto Wouri SARL", "niu": "M011700003391B", "rccm": "RC/DLA/2017/B/0912", "regime": "réel",
          "centre": "CIME Douala", "address": "Ndokoti, Douala"}
CUSTOMER = {"name": SELLER["name"], "niu": SELLER["niu"]}
# Familles d'articles et leur compte de stock (S18) ; quantités achetées par mois et coût unitaire de base.
FAMILIES = [("chemises", "shirts", "3111", 120, 9000), ("pantalons", "trousers", "3112", 80, 14000),
            ("robes", "dresses", "3121", 60, 18000)]
UNSOLD = {"chemises": 70, "pantalons": 45, "robes": 30}  # quantités en stock au 31 décembre (inventaire physique)
SALES_HT = {"cash": 4000000, "orange": 2000000, "mtn": 1500000}  # ventes HT mensuelles par moyen d'encaissement
STAFF = [("Gérant salarié", "Salaried manager", 400000), ("Vendeuse 1", "Sales assistant 1", 150000),
         ("Vendeuse 2", "Sales assistant 2", 150000)]
RENT = 300000


def fcfa(value):
    return f"{int(value):,}".replace(",", " ")


def text(fr, en):
    return {"fr": fr, "en": en}


def d(month, day, year=YEAR):
    return datetime.date(year, month, day).isoformat()


def workday(month, day, year=YEAR):
    """Date d'une pièce émise par un commerce, une banque ou un bailleur : un dimanche, elle passe au lundi."""
    date = datetime.date(year, month, day)
    return (date + datetime.timedelta(days=1 if date.weekday() == 6 else 0)).isoformat()


def last_day(month):
    return calendar.monthrange(YEAR, month)[1]


def line(account, side, amount, label=None):
    item = {"account": account, "side": side, "amount": int(amount)}
    if label:
        item["label"] = label
    return item


class Book:
    def __init__(self, code="A"):
        self.code = code
        self.pieces, self.entries, self.counters = [], [], {}
        self.questions = {m: [] for m in range(1, 8)}
        self.qcount = {m: 0 for m in range(1, 8)}

    def piece(self, month, kind, date, title_fr, title_en, payload, year=YEAR):
        key = (year, month)
        self.counters[key] = self.counters.get(key, 0) + 1
        prefix = f"{month:02d}" if year == YEAR else f"{12 + month:02d}"
        ref = f"S-{self.code}-{prefix}-{self.counters[key]:03d}"
        self.pieces.append({"ref": ref, "kind": kind, "date": date, "title": text(title_fr, title_en),
                            "payload": payload})
        return ref

    def entry(self, date, piece, *lines):
        self.entries.append({"date": date, "piece": piece, "lines": list(lines)})

    def lines_of(self, piece):
        return [l for e in self.entries if e["piece"] == piece for l in e["lines"]]

    def question(self, module, data):
        self.qcount[module] += 1
        data = {"id": f"S-{self.code}-M{module}-{self.qcount[module]:03d}", "reviewed": {"fr": True, "en": True}, **data}
        self.questions[module].append(data)
        return data["id"]

    def journal(self, module, usage, piece, fr, en, why_fr, why_en):
        return self.question(module, {
            "type": "journal", "usage": usage, "exercice": YEAR,
            "prompt": text(f"{fr}\n\n[[piece:{piece}]]", f"{en}\n\n[[piece:{piece}]]"),
            "explanation": text(why_fr, why_en),
            "journal": [{"account": l["account"], "side": l["side"], "amount": l["amount"]}
                        for l in self.lines_of(piece)]})

    def numeric(self, module, usage, value, fr, en, why_fr, why_en, piece=None, **extra):
        tag = f"\n\n[[piece:{piece}]]" if piece else ""
        return self.question(module, {
            "type": "numeric", "usage": usage, "exercice": YEAR,
            "prompt": text(f"{fr}{tag}", f"{en}{tag}"), "explanation": text(why_fr, why_en),
            "numeric": {"value": int(value), "unit": "FCFA"}, **extra})

    def choice(self, module, usage, piece, fr, en, choices, why_fr, why_en, qtype="single", **extra):
        tag = f"\n\n[[piece:{piece}]]" if piece else ""
        return self.question(module, {
            "type": qtype, "usage": usage, "prompt": text(f"{fr}{tag}", f"{en}{tag}"),
            "explanation": text(why_fr, why_en),
            "choices": [{"text": text(c_fr, c_en), "correct": ok} for c_fr, c_en, ok in choices], **extra})


def tva(ht):
    return calculs.tva_depuis_ht(D(ht), P["tva.taux_principal"], P["cac.taux"])


def invoice_payload(issuer, number, einvoice, lines, ht, extra_totals=()):
    taxes = tva(ht)
    totals = [{"label": text("Total HT", "Total excl. tax"), "role": "ht", "amount": int(ht)},
              {"label": text("TVA 17,5 %", "VAT 17.5%"), "role": "tax", "amount": int(taxes["tva"])},
              {"label": text("CAC 10 % de la TVA", "Council cents 10% of VAT"), "role": "tax", "amount": int(taxes["cac"])}]
    totals += list(extra_totals)
    totals.append({"label": text("Net à payer", "Amount due"), "role": "ttc",
                   "amount": int(ht + taxes["taxes"] + sum(t["amount"] for t in extra_totals))})
    return {"issuer": issuer, "customer": CUSTOMER, "number": number, "einvoice": einvoice, "lines": lines,
            "totals": totals}


def payroll(staff=STAFF):
    """Paie mensuelle : IRPP (barème annuel par douzièmes, CAC), RAV, TDL, CFC ; CNPS pension 4,2 % salariale et
    4,2 % patronale (décret n° 2016/072, montants portés sur le bulletin, S15)."""
    bareme = [(P["irpp.tranche1_plafond"], P["irpp.tranche1_taux"]), (P["irpp.tranche2_plafond"], P["irpp.tranche2_taux"]),
              (P["irpp.tranche3_plafond"], P["irpp.tranche3_taux"]), (None, P["irpp.tranche4_taux"])]
    rav = [(P.get(f"rav.tranche{i}_plafond"), P[f"rav.tranche{i}_montant"]) for i in range(1, 13)]
    tdl = [(P.get(f"tdl.tranche{i}_plafond"), P[f"tdl.tranche{i}_montant"]) for i in range(1, 11)]
    rows = []
    for name_fr, name_en, gross in staff:
        gross = D(gross)
        cnps = calculs.franc(gross * D("4.2") / 100)
        irpp = calculs.irpp_salaire(gross * 12, cnps * 12, P["irpp.taux_frais_professionnels"],
                                    P["irpp.plafond_frais_professionnels"], P["irpp.abattement_salaires"], bareme,
                                    P["cac.taux"])
        taxes = {"irpp": calculs.franc(irpp["total"] / 12), "rav": calculs.forfait_par_tranche(gross, rav),
                 "tdl": calculs.franc(calculs.forfait_par_tranche(gross, tdl) / 12),
                 "cfc": calculs.credit_foncier(gross, P["cfc.taux_salarie"])}
        withheld = sum(taxes.values())
        rows.append({"name": text(name_fr, name_en), "gross": gross, "cnps": cnps, **taxes,
                     "net": gross - withheld - cnps, "cfc_pat": calculs.credit_foncier(gross, P["cfc.taux_employeur"]),
                     "cnps_pat": cnps})
    return rows


def build():
    book = Book()
    staff = payroll()
    totals = {k: sum(r[k] for r in staff) for k in ("gross", "cnps", "irpp", "rav", "tdl", "cfc", "net", "cfc_pat",
                                                     "cnps_pat")}
    salary_taxes = totals["irpp"] + totals["rav"] + totals["tdl"] + totals["cfc"] + totals["cfc_pat"]
    lots = {f[0]: [] for f in FAMILIES}
    special = {}

    # Jour 1 : démarches (S28), sources officielles (US-97).
    procedures = [
        ("Création de la SARL au CFCE de Douala", "Creating the LLC at the Douala business centre",
         text("Centre de formalités de création d'entreprises (CFCE) de Douala", "Douala business formalities centre"),
         text("Créer la SARL et obtenir registre de commerce, carte de contribuable et attestation de création",
              "Create the LLC and obtain trade register, taxpayer card and creation certificate"),
         [text("5 + N exemplaires des statuts sous seing privé (N associés)", "5 + N copies of the articles"),
          text("5 + N déclarations de régularité et de conformité", "5 + N declarations of regularity and conformity"),
          text("Extraits de casier judiciaire des associés et du gérant, ou déclaration sur l'honneur",
               "Criminal records of partners and manager, or sworn statement"),
          text("Photocopie de la CNI de chaque associé, 2 pour le gérant associé", "ID copies of partners and manager"),
          text("Plan de localisation, boîte postale, contact téléphonique", "Location map, PO box, phone number"),
          text("Frais de création 41 500 FCFA et annonce légale 13 125 FCFA (à vérifier au CFCE)",
               "Creation fee 41,500 and legal notice 13,125 FCFA (check at the CFCE)")],
         text("Registre de commerce, carte de contribuable (NIU), attestation de création, sous 72 heures",
              "Trade register, taxpayer card (NIU), creation certificate, within 72 hours"),
         "[[source:minfi-cfce]]"),
        ("Rattachement fiscal au CIME", "Tax office attachment (medium-sized taxpayers)",
         text("Direction générale des impôts, CIME de Douala", "Directorate General of Taxation, Douala MTO"),
         text("Suivi fiscal d'une entreprise dont le CA visé (90 millions) est compris entre 50 millions et 3 milliards",
              "Tax follow-up of a company with a target turnover between 50 million and 3 billion"),
         [text("Carte de contribuable délivrée au CFCE", "Taxpayer card issued by the CFCE"),
          text("Statuts et registre de commerce", "Articles and trade register")],
         text("Rattachement au CIME et accès à la télédéclaration", "Attachment to the MTO and e-filing access"),
         "[[cgi:art. L 1]] [[source:dgi-cime]]"),
        ("Immatriculation à la CNPS", "Registration with the CNPS",
         text("Agence régionale de la CNPS", "Regional CNPS office"),
         text("Immatriculer l'employeur, puis chaque salarié dans les 8 jours de l'embauche",
              "Register the employer, then each employee within 8 days of hiring"),
         [text("Demande d'immatriculation sur imprimé CNPS", "Registration form (CNPS)"),
          text("Copie du registre de commerce ou des statuts, patente, carte de contribuable",
               "Copy of trade register or articles, business licence, taxpayer card"),
          text("Plan de localisation et liste du personnel", "Location map and staff list"),
          text("Pour chaque salarié : avis d'embauche et copie certifiée de l'acte de naissance ou de la CNI",
               "For each employee: hiring notice and certified birth certificate or ID")],
         text("Numéro d'employeur et numéros d'assurés", "Employer number and employee numbers"),
         "[[source:cnps-faq]]"),
        ("Ouverture du compte bancaire de l'entreprise", "Opening the company bank account",
         text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
         text("Ouvrir le compte de l'entreprise", "Open the company account"),
         [text("Demande d'ouverture de compte", "Account opening request"),
          text("Registre de commerce, carte de contribuable, plan de localisation", "Trade register, taxpayer card, map"),
          text("Pièces d'identité du gérant, statuts, procès-verbal de nomination du gérant",
               "Manager's ID, articles, minutes appointing the manager"),
          text("Extrait du journal d'annonces légales", "Legal notice extract")],
         text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
        ("Compte marchand Orange Money", "Orange Money merchant account",
         text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
         text("Encaisser les ventes par Orange Money", "Collect sales through Orange Money"),
         [text("Registre de commerce, carte de contribuable, patente", "Trade register, taxpayer card, licence"),
          text("Statuts, CNI du gérant ou d'un mandataire", "Articles, ID of the manager or proxy"),
          text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)")],
         text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
    ]
    procedure_refs = []
    for title_fr, title_en, body, purpose, documents, obtained, source in procedures:
        procedure_refs.append(book.piece(1, "demarche", d(1, 2), f"Démarche : {title_fr}", f"Procedure: {title_en}",
                                         {"organisme": body, "objet": purpose, "documents_a_fournir": documents,
                                          "document_obtenu": obtained, "source": source}))

    capital = book.piece(1, "releve_bancaire", d(1, 2), "Attestation de dépôt du capital (Banque X)",
                         "Capital deposit certificate (Bank X)",
                         {"fields": [{"label": text("Déposant", "Depositor"), "value": SELLER["name"]}],
                          "totals": [{"label": text("Capital libéré", "Paid-up capital"), "amount": 5000000}]})
    book.entry(d(1, 2), capital, line("521", "debit", 5000000), line("1013", "credit", 5000000))
    notary_ht = 225000
    notary = book.piece(1, "facture_achat", d(1, 6), "Facture du notaire (statuts)", "Notary's invoice (articles)",
                        invoice_payload(NOTARY, "N-2026-0004", "DGI-SFE-2026-000214",
                                        [{"label": text("Honoraires de rédaction des statuts", "Drafting fees"),
                                          "amount": 200000},
                                         {"label": text("Débours : droits d'enregistrement", "Registration duties"),
                                          "amount": 25000}], notary_ht))
    notary_tax = tva(200000)["taxes"]
    # Les débours ne portent pas de TVA : la facture la calcule sur les seuls honoraires.
    for total in book.pieces[-1]["payload"]["totals"]:
        if total["role"] == "tax":
            total["amount"] = int(tva(200000)["tva"] if total["label"]["fr"].startswith("TVA") else tva(200000)["cac"])
        if total["role"] == "ttc":
            total["amount"] = int(notary_ht + notary_tax)
    book.entry(d(1, 6), notary, line("6324", "debit", 200000), line("4454", "debit", notary_tax),
               line("646", "debit", 25000), line("521", "credit", notary_ht + notary_tax))
    special["notary"] = notary

    for month in range(1, 13):
        module = MODULE_OF_MONTH[month]
        end = last_day(month)
        refs = {}
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {MONTHS_FR[month - 1]} (Banque X)",
                                  f"{MONTHS_EN[month - 1]} bank statement (Bank X)", {})
        bank_piece = book.pieces[-1]
        # Loyer (précompte de 10 % retenu par le locataire au réel, CGI art. 87).
        withheld = calculs.franc(D(RENT) * P["precompte.taux_loyer"] / 100)
        refs["rent"] = book.piece(month, "recu_caisse", workday(month, 6 if month == 1 else 2), f"Quittance de loyer de {MONTHS_FR[month - 1]}",
                                  f"{MONTHS_EN[month - 1]} rent receipt",
                                  {"fields": [{"label": text("Bailleur", "Landlord"), "value": "M. Tchoua (fictif)"}],
                                   "totals": [{"label": text("Loyer brut", "Gross rent"), "amount": RENT},
                                              {"label": text("Précompte sur loyer 10 % retenu", "10% rent withholding"),
                                               "amount": int(withheld)},
                                              {"label": text("Net versé par virement", "Net paid by transfer"),
                                               "amount": int(RENT - withheld)}]})
        book.entry(workday(month, 6 if month == 1 else 2), refs["rent"], line("6222", "debit", RENT), line("4478", "credit", withheld),
                   line("521", "credit", RENT - withheld))
        # Achats du mois (S18 : trois familles, coût unitaire variable, précompte de 2 %).
        lines_, ht = [], 0
        for name_fr, name_en, _account, qty, base in FAMILIES:
            unit = base + 250 * ((month - 1) % 4)
            lots[name_fr].append((qty, unit))
            lines_.append({"label": text(name_fr.capitalize(), name_en.capitalize()), "qty": qty, "unit_price": unit,
                           "amount": qty * unit})
            ht += qty * unit
        precompte = calculs.franc(D(ht) * P["precompte.taux_reel"] / 100)
        refs["purchase"] = book.piece(month, "facture_achat", workday(month, 5), f"Facture Sawa Textiles de {MONTHS_FR[month - 1]}",
                                      f"Sawa Textiles {MONTHS_EN[month - 1]} invoice",
                                      invoice_payload(SUPPLIER, f"FA-2026-{month:04d}", f"DGI-SFE-2026-{1000 + month:06d}",
                                                      lines_, ht, [{"label": text("Précompte sur achats 2 %",
                                                                                  "2% purchase withholding"),
                                                                    "role": "tax", "amount": int(precompte)}]))
        taxes = tva(ht)
        due = ht + taxes["taxes"] + precompte
        book.entry(workday(month, 5), refs["purchase"], line("6011", "debit", ht), line("4452", "debit", taxes["taxes"]),
                   line("4492", "debit", precompte), line("401", "credit", due))
        book.entry(d(month, 12), refs["bank"], line("401", "debit", due), line("521", "credit", due))
        # Règlement de la déclaration du mois précédent, le 15 (US-85).
        if month > 1:
            refs["settlement"] = settle(book, month - 1, d(month, 15), month)
        # Ventes du mois.
        sales = {k: tva(v) for k, v in SALES_HT.items()}
        refs["cash"] = book.piece(month, "recu_caisse", d(month, end), f"Récapitulatif des ventes au comptant de {MONTHS_FR[month - 1]}",
                                  f"{MONTHS_EN[month - 1]} cash sales summary",
                                  {"totals": [{"label": text("Ventes HT", "Sales excl. tax"), "role": "ht",
                                               "amount": SALES_HT["cash"]},
                                              {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                               "amount": int(sales["cash"]["taxes"])},
                                              {"label": text("Ventes TTC encaissées", "Sales incl. tax collected"),
                                               "role": "ttc", "amount": int(sales["cash"]["ttc"])}]})
        book.entry(d(month, end), refs["cash"], line("5711", "debit", sales["cash"]["ttc"]),
                   line("7011", "credit", SALES_HT["cash"]), line("4431", "credit", sales["cash"]["taxes"]))
        for key, account, operator_fr, operator_en, fee in (("orange", "5522", "Orange Money", "Orange Money", 9500),
                                                            ("mtn", "5521", "MTN MoMo", "MTN MoMo", 7200)):
            refs[key] = book.piece(month, "releve_momo", d(month, end), f"Relevé {operator_fr} de {MONTHS_FR[month - 1]}",
                                   f"{operator_en} statement, {MONTHS_EN[month - 1]}",
                                   {"totals": [{"label": text("Encaissements HT", "Receipts excl. tax"), "role": "ht",
                                                "amount": SALES_HT[key]},
                                               {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                                "amount": int(sales[key]["taxes"])},
                                               {"label": text("Encaissements TTC", "Receipts incl. tax"), "role": "ttc",
                                                "amount": int(sales[key]["ttc"])},
                                               {"label": text("Frais de l'opérateur", "Operator fees"), "amount": fee}]})
            book.entry(d(month, end), refs[key], line(account, "debit", sales[key]["ttc"]),
                       line("7011", "credit", SALES_HT[key]), line("4431", "credit", sales[key]["taxes"]),
                       line("631", "debit", fee), line(account, "credit", fee))
        # Paie et virement des salaires.
        refs["payroll"] = book.piece(month, "bulletin_paie", d(month, end), f"Journal de paie de {MONTHS_FR[month - 1]}",
                                     f"{MONTHS_EN[month - 1]} payroll journal",
                                     {"lines": [{"label": r["name"], "amount": int(r["gross"])} for r in staff],
                                      "totals": [{"label": text("Salaires bruts", "Gross pay"), "role": "ht",
                                                  "amount": int(totals["gross"])},
                                                 {"label": text("IRPP et CAC", "PIT and council cents"), "amount": int(totals["irpp"])},
                                                 {"label": text("RAV", "Audiovisual fee"), "amount": int(totals["rav"])},
                                                 {"label": text("TDL", "Local development tax"), "amount": int(totals["tdl"])},
                                                 {"label": text("CFC salariale", "Employee housing levy"), "amount": int(totals["cfc"])},
                                                 {"label": text("CNPS salariale (pension 4,2 %)", "Employee CNPS (pension 4.2%)"),
                                                  "amount": int(totals["cnps"])},
                                                 {"label": text("Nets à payer", "Net pay"), "amount": int(totals["net"])},
                                                 {"label": text("CFC patronale", "Employer housing levy"), "amount": int(totals["cfc_pat"])},
                                                 {"label": text("CNPS patronale (pension 4,2 %)", "Employer CNPS (pension 4.2%)"),
                                                  "amount": int(totals["cnps_pat"])}]})
        book.entry(d(month, end), refs["payroll"], line("6611", "debit", totals["gross"]),
                   line("6413", "debit", totals["cfc_pat"]), line("6641", "debit", totals["cnps_pat"]),
                   line("4472", "credit", salary_taxes), line("431", "credit", totals["cnps"] + totals["cnps_pat"]),
                   line("422", "credit", totals["net"]))
        book.entry(d(month, end), refs["bank"], line("422", "debit", totals["net"]), line("521", "credit", totals["net"]))
        special.setdefault("months", {})[month] = refs
        events(book, month, special)
        # Versements hebdomadaires des espèces, récapitulés le dernier jour du mois (S19 : virement interne par 585).
        cash_left = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, end))
        refs["cash_out"] = book.piece(month, "recu_caisse", d(month, end),
                                      f"Bordereaux de versement des espèces de {MONTHS_FR[month - 1]}",
                                      f"{MONTHS_EN[month - 1]} cash deposit slips",
                                      {"totals": [{"label": text("Espèces versées", "Cash deposited"),
                                                   "amount": int(cash_left)}]})
        book.entry(d(month, end), refs["cash_out"], line("585", "debit", cash_left), line("5711", "credit", cash_left))
        # Transfert des encaissements Mobile Money vers la banque, puis relevé bancaire du mois (frais de tenue 3 500).
        transfer = sales["orange"]["ttc"] - 9500 + sales["mtn"]["ttc"] - 7200
        book.entry(d(month, end), refs["bank"], line("585", "debit", transfer),
                   line("5522", "credit", sales["orange"]["ttc"] - 9500), line("5521", "credit", sales["mtn"]["ttc"] - 7200))
        bank_in = transfer + cash_left
        book.entry(d(month, end), refs["bank"], line("521", "debit", bank_in), line("585", "credit", bank_in),
                   line("631", "debit", 3500), line("521", "credit", 3500))
        instalment = [{"label": text("Échéance réglée à Auto Wouri", "Instalment paid to Auto Wouri"),
                       "amount": 4770000}] if month in (5, 6, 7) else []
        bank_piece["payload"] = {"totals": instalment + [
            {"label": text("Virement à Sawa Textiles", "Transfer to Sawa Textiles"), "amount": int(due)},
            {"label": text("Salaires nets virés", "Net pay transferred"), "amount": int(totals["net"])},
            {"label": text("Virements internes reçus (espèces et Mobile Money)", "Internal transfers received"),
             "amount": int(bank_in)},
            {"label": text("Frais de tenue de compte", "Account fees"), "amount": 3500}]}

    year_end(book, special, lots)
    return book, special, staff


def previous_deposit(book, month):
    """Espèces versées le 25 du mois (bordereau de sortie de caisse), reçues sur le relevé bancaire du mois."""
    return sum(l["amount"] for e in book.entries if e["date"].startswith(f"{YEAR}-{month:02d}-25")
               for l in e["lines"] if l["account"] == "585" and l["side"] == "debit")


def declaration_of(book, month, credit_in):
    return ledger.monthly_declaration(book.entries, YEAR, month, minimum_rate=P["is.taux_minimum_perception"],
                                      cac_rate=P["cac.taux"], credit_reporte=credit_in)


def settle(book, month, date, settled_in):
    """Déclaration du 15 pour `month` et son règlement : TVA, acompte d'IS net du précompte imputé, retenues."""
    credit_in = book.__dict__.setdefault("credit", 0)
    decl = declaration_of(book, month, credit_in)
    book.credit = decl["credit_tva"]
    deductible = {acc: sum(l["amount"] for e in book.entries
                           if e["date"].startswith(f"{YEAR}-{month:02d}") for l in e["lines"]
                           if l["account"] == acc and l["side"] == "debit") for acc in ("4451", "4452", "4454")}
    withheld = {acc: sum(l["amount"] for e in book.entries
                         if e["date"].startswith(f"{YEAR}-{month:02d}") for l in e["lines"]
                         if l["account"] == acc and l["side"] == "credit") for acc in ("4472", "4478", "431")}
    imputed = min(decl["precompte_impute"], decl["acompte_is"])
    year, mm = (YEAR, settled_in) if settled_in <= 12 else (YEAR + 1, settled_in - 12)
    ref = book.piece(mm, "declaration", date, f"Déclaration du 15 : période de {MONTHS_FR[month - 1]} {YEAR}",
                     f"15th return: {MONTHS_EN[month - 1]} {YEAR}",
                     {"fields": [{"label": text("Chiffre d'affaires HT", "Turnover excl. tax"),
                                  "value": fcfa(decl["chiffre_affaires"])},
                                 {"label": text("TVA collectée", "VAT charged"), "value": fcfa(decl["tva_collectee"])},
                                 {"label": text("TVA déductible", "Recoverable VAT"), "value": fcfa(decl["tva_deductible"])},
                                 {"label": text("Crédit de TVA reporté", "VAT credit brought forward"), "value": fcfa(credit_in)},
                                 {"label": text("Crédit de TVA à reporter", "VAT credit carried forward"),
                                  "value": fcfa(decl["credit_tva"])}],
                      "totals": [{"label": text("TVA due", "VAT due"), "amount": decl["tva_due"]},
                                 {"label": text("Acompte d'IS (2 % + CAC)", "CIT instalment (2% + council cents)"),
                                  "amount": decl["acompte_is"]},
                                 {"label": text("Précompte imputé", "Withholding credited"), "amount": int(imputed)},
                                 {"label": text("Retenues et cotisations reversées", "Withholdings and contributions paid over"),
                                  "amount": sum(withheld.values())}]}, year=year)
    lines = [line("4431", "debit", decl["tva_collectee"])]
    lines += [line(acc, "credit", amount) for acc, amount in deductible.items() if amount]
    if credit_in:
        lines.append(line("4449", "credit", credit_in))
    if decl["credit_tva"]:
        lines.append(line("4449", "debit", decl["credit_tva"]))
    lines += [line("441", "debit", decl["acompte_is"])]
    if imputed:
        lines.append(line("4492", "credit", imputed))
    lines += [line(acc, "debit", amount) for acc, amount in withheld.items() if amount]
    paid = decl["tva_due"] + decl["acompte_is"] - imputed + sum(withheld.values())
    lines.append(line("521", "credit", paid))
    book.entry(date, ref, *lines)
    book.__dict__.setdefault("declarations", {})[month] = (ref, decl, credit_in)
    return ref


def events(book, month, special):
    """Événements ponctuels de l'année, chacun sur une pièce (passerelle S21, S23)."""
    if month == 3:
        ref = book.piece(3, "recu_caisse", d(3, 10), "Mise en demeure du propriétaire voisin (litige)",
                         "Formal notice from the neighbouring owner (dispute)",
                         {"fields": [{"label": text("Réclamation", "Claim"), "value": text("Remise en état des locaux",
                                                                                            "Restoring the premises")}],
                          "totals": [{"label": text("Montant réclamé", "Amount claimed"), "amount": 500000}]})
        book.entry(d(3, 10), ref, line("6911", "debit", 500000), line("191", "credit", 500000))
        special["provision"] = ref
    if month == 4:
        ht = 12000000
        ref = book.piece(4, "facture_achat", d(4, 1), "Facture Auto Wouri : voiture de livraison légère",
                         "Auto Wouri invoice: light delivery car",
                         invoice_payload(GARAGE, "AW-2026-0331", "DGI-SFE-2026-004417",
                                         [{"label": text("Voiture légère, usage en ville", "Light car, town use"),
                                           "qty": 1, "unit_price": ht, "amount": ht}], ht))
        book.entry(d(4, 1), ref, line("2451", "debit", ht), line("4451", "debit", tva(ht)["taxes"]),
                   line("4812", "credit", tva(ht)["ttc"]))
        special["vehicle"] = ref
    if month in (5, 6, 7):
        bank = special["months"][month]["bank"]
        book.entry(d(month, 20), bank, line("4812", "debit", 4770000), line("521", "credit", 4770000))
    if month == 7:
        ref = book.piece(7, "recu_caisse", d(7, 22), "Quittance de pénalité de retard (recette des impôts, fictive)",
                         "Late-filing penalty receipt (tax office, fictitious)",
                         {"totals": [{"label": text("Pénalité payée", "Penalty paid"), "amount": 50000}]})
        book.entry(d(7, 22), ref, line("6471", "debit", 50000), line("521", "credit", 50000))
        special["penalty"] = ref
    if month == 9:
        ref = book.piece(9, "recu_caisse", d(9, 18), "Bon de caisse interne sans justificatif externe",
                         "Internal cash voucher without external receipt",
                         {"totals": [{"label": text("Dépense en espèces", "Cash expense"), "amount": 40000}]})
        book.entry(d(9, 18), ref, line("6588", "debit", 40000), line("5711", "credit", 40000))
        special["no_receipt"] = ref
    if month == 10:
        ref = book.piece(10, "recu_caisse", d(10, 8), "Reçu de don d'une association d'intérêt général (fictive)",
                         "Donation receipt from a public-interest association (fictitious)",
                         {"totals": [{"label": text("Don versé", "Donation paid"), "amount": 600000}]})
        book.entry(d(10, 8), ref, line("6582", "debit", 600000), line("521", "credit", 600000))
        special["donation"] = ref
    if month == 11:
        ref = book.piece(11, "recu_caisse", d(11, 10), "Accord transactionnel avec le propriétaire voisin",
                         "Settlement agreement with the neighbouring owner",
                         {"totals": [{"label": text("Litige clos sans paiement", "Dispute closed without payment"),
                                      "amount": 0}]})
        book.entry(d(11, 10), ref, line("191", "debit", 500000), line("7911", "credit", 500000))
        special["reversal"] = ref


def year_end(book, special, lots):
    """Inventaire (S18), amortissement, déclaration de décembre, passerelle (S21, S23), IS et DSF (S12, S22)."""
    stock_entry, stock = [], {}
    sheet_lines, sheet_fields = [], []
    for name_fr, _name_en, _account, _qty, _base in FAMILIES:
        bought = sum(q for q, _ in lots[name_fr])
        sheet_fields.append({"label": text(f"{name_fr.capitalize()} : achetées, inventaire physique",
                                           f"{name_fr.capitalize()}: bought, physical count"),
                             "value": f"{bought} / {UNSOLD[name_fr]}"})
        sheet_lines += [{"label": text(f"{name_fr.capitalize()}, lot {i}", f"{name_fr.capitalize()}, lot {i}"),
                         "qty": q, "unit_price": u, "amount": q * u} for i, (q, u) in enumerate(lots[name_fr], start=1)]
    sheet = book.piece(12, "fiche_stock", d(12, 31), "Fiches de stock CMUP des trois familles", "WAC stock cards",
                       {"fields": sheet_fields, "lines": sheet_lines})
    for name_fr, name_en, account, _qty, _base in FAMILIES:
        family_lots = [(D(q), D(u)) for q, u in lots[name_fr]]
        bought = sum(q for q, _ in lots[name_fr])
        sold = bought - UNSOLD[name_fr]
        result = calculs.sortie_cmup(family_lots, D(sold))
        stock[name_fr] = (sheet, family_lots, sold, result, account)
        stock_entry.append((account, int(result["valeur_stock"])))
    first_ref = stock["chemises"][0]
    book.entry(d(12, 31), first_ref, *[line(account, "debit", value) for account, value in stock_entry],
               line("6031", "credit", sum(v for _, v in stock_entry)))
    plan = calculs.amortissement_lineaire(D(12000000), 3, 4)
    dotation = int(plan[0]["dotation"])
    schedule = book.piece(12, "fiche_stock", d(12, 31), "Tableau d'amortissement de la voiture (3 ans, depuis avril)",
                          "Car depreciation schedule (3 years, from April)",
                          {"totals": [{"label": text("Dotation 2026 (9 mois)", "2026 charge (9 months)"), "amount": dotation}]})
    book.entry(d(12, 31), schedule, line("6813", "debit", dotation), line("2845", "credit", dotation))
    special.update(stock=stock, schedule=schedule, dotation=dotation)
    # Déclaration de décembre, réglée le 15 janvier 2027.
    special["months"][12]["settlement_next"] = settle(book, 12, d(1, 15, YEAR + 1), 13)
    # Passerelle et IS.
    entries_2026 = [e for e in book.entries if e["date"] < f"{YEAR + 1}"]
    accounting = ledger.accounting_result(entries_2026)
    turnover = sum(l["amount"] for e in entries_2026 for l in e["lines"] if l["account"].startswith("70")
                   and l["side"] == "credit")
    excess_depreciation = int(calculs.reintegration_amortissement(D(dotation), D(12000000),
                                                                  P["amortissement.taux_max_auto_leger_ville"], 9))
    excess_gift = int(calculs.reintegration_dons(D(600000), D(turnover), P["dons.plafond_interet_general"]))
    add_backs = {"amendes": 50000, "amortissement_excedentaire": excess_depreciation,
                 "dons_excedentaires": excess_gift, "charge_sans_piece": 40000, "provision": 500000}
    deductions = {"reprise_provision_taxee": 500000}
    tax_result = ledger.tax_result(accounting, add_backs.values(), deductions.values())
    rate = P["is.taux_reduit"] if turnover <= P["is.seuil_taux_reduit"] else P["is.taux"]
    prepaid = sum(l["amount"] for e in book.entries for l in e["lines"] if l["account"] == "441" and l["side"] == "debit")
    tax = ledger.corporate_tax(tax_result, turnover, prepaid, rate, P["is.taux_minimum_perception"], P["cac.taux"])
    liquidation = book.piece(4, "declaration", d(4, 10, YEAR + 1), "DSF 2026 : liquidation de l'IS", "2026 return: CIT",
                             {"fields": [{"label": text("Résultat fiscal", "Taxable profit"), "value": fcfa(tax_result)},
                                         {"label": text("Taux de l'IS", "CIT rate"), "value": f"{rate.normalize()} %"}],
                              "totals": [{"label": text("IS calculé (CAC compris)", "CIT computed"), "amount": tax["is_total"]},
                                         {"label": text("Minimum de perception", "Minimum tax"), "amount": tax["minimum_total"]},
                                         {"label": text("IS dû", "CIT due"), "amount": tax["du"]},
                                         {"label": text("Acomptes versés", "Instalments paid"), "amount": prepaid},
                                         {"label": text("Solde à payer", "Balance due"), "amount": tax["solde"]}]},
                             year=YEAR + 1)
    book.pieces[-1]["dsf"] = "liquidation_is"
    book.entry(d(12, 31), liquidation, line("891", "debit", tax["du"]), line("441", "credit", tax["du"]))
    net = accounting - tax["du"]
    for table, fr, en, rows in (
        ("passage", "DSF 2026 : tableau de passage", "2026 return: reconciliation",
         [("Résultat comptable avant impôt", "Accounting profit before tax", accounting),
          ("Réintégrations", "Add-backs", sum(add_backs.values())),
          ("Déductions", "Deductions", sum(deductions.values())), ("Résultat fiscal", "Taxable profit", tax_result)]),
        ("compte_resultat", "DSF 2026 : compte de résultat", "2026 return: income statement",
         [("Chiffre d'affaires", "Turnover", turnover), ("Résultat avant impôt", "Profit before tax", accounting),
          ("Impôt sur le résultat", "Income tax", tax["du"]), ("Résultat net", "Net profit", net)]),
        ("bilan", "DSF 2026 : bilan (extrait)", "2026 return: balance sheet (extract)",
         [("Capital", "Share capital", 5000000), ("Résultat net de l'exercice", "Net profit for the year", net),
          ("Stocks de marchandises", "Goods inventory", sum(v for _, v in stock_entry)),
          ("Voiture, valeur nette", "Car, net book value", 12000000 - dotation)]),
    ):
        ref = book.piece(4, "declaration", d(4, 10, YEAR + 1), fr, en,
                         {"totals": [{"label": text(a, b), "amount": int(v)} for a, b, v in rows]}, year=YEAR + 1)
        book.pieces[-1]["dsf"] = table
    special.update(accounting=accounting, turnover=turnover, add_backs=add_backs, deductions=deductions,
                   tax_result=tax_result, tax=tax, rate=rate, prepaid=prepaid, liquidation=liquidation,
                   excess_gift=excess_gift, excess_depreciation=excess_depreciation)


def balances(book):
    for month in range(2, 13):
        date = d(month, 1)
        book.piece(month, "balance", date, f"Balance au {last_day(month - 1)} {MONTHS_FR[month - 2]} {YEAR}",
                   f"Trial balance at {MONTHS_EN[month - 2]} {last_day(month - 1)}, {YEAR}",
                   ledger.balance_piece(book.entries, before=datetime.date.fromisoformat(date), labels=LABELS))


def split_usage(questions):
    """Au moins 8 questions de quiz et 12 d'examen par module (US-72), réparties sur tout le module."""
    total = len(questions)
    quiz = max(8, total // 3)
    picks = {round(j * total / quiz) for j in range(quiz)}
    for i, question in enumerate(questions):
        question["usage"] = "quiz" if i in picks else "exam"


def month_questions(book, special, month):
    module, refs = MODULE_OF_MONTH[month], special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    asks = [
        ("purchase", f"Passez l'écriture de la facture d'achat de {mfr} (précompte de 2 % compris).",
         f"Record the {men} purchase invoice (2% withholding included).",
         "Achats en 6011, TVA et CAC récupérables en 4452, précompte en 4492, dette fournisseur en 401 (CGI art. 21 et 143).",
         "Purchases in 6011, recoverable VAT in 4452, withholding in 4492, supplier debt in 401."),
        ("cash", f"Passez l'écriture des ventes au comptant de {mfr}.", f"Record the {men} cash sales.",
         "Caisse 5711 au TTC, ventes 7011 au HT, TVA facturée 4431.", "Cash 5711 incl. tax, sales 7011, VAT charged 4431."),
        ("orange", f"Passez l'écriture du relevé Orange Money de {mfr}.", f"Record the {men} Orange Money statement.",
         "Sous-compte 5522, ventes et TVA ; frais de l'opérateur en 631 (S19).",
         "Sub-account 5522, sales and VAT; operator fees in 631."),
        ("payroll", f"Passez l'écriture du journal de paie de {mfr}.", f"Record the {men} payroll journal.",
         "Salaires 6611, CFC patronale 6413, CNPS patronale 6641 ; retenues fiscales 4472, CNPS 431, nets 422.",
         "Gross pay 6611, employer levies 6413 and 6641; tax withholdings 4472, CNPS 431, net pay 422."),
        ("bank", f"Passez les écritures du relevé bancaire de {mfr}.", f"Record the {men} bank statement entries.",
         "Virement au fournisseur (401), salaires nets (422), virements internes via 585 (S19), frais en 631.",
         "Supplier transfer (401), net pay (422), internal transfers through 585, fees in 631."),
        ("mtn", f"Passez l'écriture du relevé MTN MoMo de {mfr}.", f"Record the {men} MTN MoMo statement.",
         "Sous-compte 5521, ventes et TVA ; frais de l'opérateur en 631 (S19).",
         "Sub-account 5521, sales and VAT; operator fees in 631."),
        ("rent", f"Passez l'écriture de la quittance de loyer de {mfr}.", f"Record the {men} rent receipt.",
         "Loyer brut en 6222 ; précompte de 10 % retenu en 4478 (CGI art. 87) ; net payé par la banque.",
         "Gross rent in 6222; 10% withholding in 4478; net paid by bank."),
        ("settlement", f"Passez l'écriture du règlement de la déclaration du 15 {mfr}.",
         f"Record the payment of the {men} 15th return.",
         "Solde de la TVA (4431, 445, 4449), acompte d'IS en 441 net du précompte imputé, retenues et CNPS reversées.",
         "VAT settled, CIT instalment in 441 net of withholding, withholdings and CNPS paid over."),
    ]
    for key, fr, en, why_fr, why_en in asks:
        if key in refs:
            book.journal(module, "exam", refs[key], fr, en, why_fr, why_en)
    _ref, decl, _credit_in = book.declarations[month]
    period = f"{YEAR}-{month:02d}"
    for field, fr, en in (("tva_due" if decl["tva_due"] else "credit_tva", "TVA due (ou crédit à reporter)",
                           "VAT due (or credit carried forward)"),
                          ("acompte_is_net", "Acompte d'IS net du précompte imputé", "CIT instalment net of withholding"),
                          ("retenues_salaires", "Retenues à la source du mois (salaires et loyer)",
                           "Withholdings of the month (pay and rent)")):
        book.numeric(module, "exam", decl[field], f"Déclaration du 15 pour {mfr} {YEAR} : {fr} ?",
                     f"15th return for {men} {YEAR}: {en}?",
                     "Calcul sur les écritures du mois : TVA facturée moins TVA déductible et crédit reporté ; acompte de "
                     "2 % du CA majoré de 10 % de CAC, moins le précompte (CGI art. 21) ; retenues portées en 447.",
                     "Computed from the month's entries (CGI art. 21).", declaration={"period": period, "field": field})
    purchase = next(p for p in book.pieces if p["ref"] == refs["purchase"])
    withheld = next(t["amount"] for t in purchase["payload"]["totals"] if t["label"]["fr"].startswith("Précompte"))
    book.numeric(module, "exam", withheld, f"Précompte sur achats subi en {mfr} (taux du réel) ?",
                 f"Purchase withholding suffered in {men} (actual regime rate)?",
                 "2 % du montant HT de la facture, sans CAC, imputable sur l'acompte d'IS (CGI art. 21 (3)).",
                 "2% of the invoice amount excluding tax, credited against the CIT instalment.", piece=refs["purchase"])
    balance = ledger.account_balance(book.entries, "521", datetime.date(YEAR, month, last_day(month)))
    book.numeric(module, "exam", balance, f"Solde comptable du compte 521 au {last_day(month)} {mfr} {YEAR} ?",
                 f"Book balance of account 521 at {men} {last_day(month)}, {YEAR}?",
                 "Débits moins crédits de 521 jusqu'à cette date : c'est le solde à rapprocher du relevé bancaire.",
                 "Debits less credits of 521 up to that date, to reconcile with the bank statement.",
                 piece=refs["bank"], rapprochement={"account": "521", "date": d(month, last_day(month))})


PROCEDURE_QUESTIONS = [
    ("Quels documents le CFCE délivre-t-il à la création ?", "What does the CFCE issue on creation?",
     "Registre de commerce, carte de contribuable et attestation de création",
     "Trade register, taxpayer card and creation certificate", "Une attestation de non-redevance seule",
     "A tax clearance only"),
    ("Quel centre des impôts suit Ngono Mode SARL ?", "Which tax office follows Ngono Mode SARL?",
     "Le CIME (CA compris entre 50 millions et 3 milliards)", "The MTO (turnover between 50 million and 3 billion)",
     "La DGE", "The LTO"),
    ("Dans quel délai faut-il immatriculer un salarié à la CNPS ?", "Within how long must an employee be registered?",
     "8 jours après l'embauche", "8 days after hiring", "Trois mois après l'embauche", "Three months after hiring"),
    ("Que remet la banque à l'ouverture du compte ?", "What does the bank give when opening the account?",
     "Un relevé d'identité bancaire (RIB)", "Bank details (RIB)", "Une carte de contribuable", "A taxpayer card"),
    ("Quelle pièce Orange exige-t-il en plus des documents légaux ?",
     "Which document does Orange require besides legal papers?", "Le relevé d'identité bancaire (RIB)",
     "Bank details (RIB)", "Un bilan certifié", "A certified balance sheet"),
]


def build_questions(book, special):
    for ref, (fr, en, right_fr, right_en, wrong_fr, wrong_en) in zip(special["procedures"], PROCEDURE_QUESTIONS):
        book.choice(1, "quiz", ref, fr, en, [(right_fr, right_en, True), (wrong_fr, wrong_en, False)],
                    "Voir la démarche et sa source officielle.", "See the procedure and its official source.")
    book.choice(1, "quiz", special["notary"], "Les frais de constitution de la SARL s'inscrivent à l'actif en frais "
                "d'établissement.", "The LLC's set-up costs are capitalised as formation expenses.",
                [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : le SYSCOHADA révisé n'immobilise plus les frais d'établissement ; honoraires (6324) et droits "
                "d'enregistrement (646) sont des charges par nature (S6).",
                "False: revised SYSCOHADA no longer capitalises formation expenses; they are expenses by nature.",
                qtype="truefalse", piege="frais_etablissement")
    book.journal(1, "exam", special["capital"], "Passez l'écriture du dépôt du capital.", "Record the capital deposit.",
                 "Banque 521 au débit, capital souscrit, appelé, versé 1013 au crédit.",
                 "Bank 521 debit, capital 1013 credit.")
    book.journal(1, "exam", special["notary"], "Passez l'écriture de la facture du notaire.",
                 "Record the notary's invoice.",
                 "Honoraires 6324, droits d'enregistrement 646, TVA récupérable sur services 4454 : des charges, jamais "
                 "une immobilisation (S6).", "Fees 6324, registration duties 646, recoverable VAT 4454: expenses (S6).")
    for month in range(1, 13):
        month_questions(book, special, month)
    events = [
        (2, "provision", "Passez l'écriture de la provision pour litige.", "Record the litigation provision.",
         "Dotation 6911, provision pour litiges 191 ; non déductible fiscalement (réintégrée).",
         "Charge 6911, provision 191; not tax-deductible (added back)."),
        (3, "vehicle", "Passez l'écriture de la facture de la voiture.", "Record the car invoice.",
         "Matériel automobile 2451, TVA sur immobilisations 4451, fournisseur d'immobilisations 4812.",
         "Vehicles 2451, VAT on fixed assets 4451, fixed-asset supplier 4812."),
        (4, "penalty", "Passez l'écriture de la pénalité.", "Record the penalty.",
         "Pénalités d'assiette 6471 ; non déductibles (CGI art. 7).", "Assessment penalties 6471; not deductible."),
        (4, "no_receipt", "Passez l'écriture du bon de caisse.", "Record the cash voucher.",
         "Charge diverse 6588 sans justificatif externe : non déductible.", "Sundry expense 6588 without receipt."),
        (5, "donation", "Passez l'écriture du don.", "Record the donation.",
         "Dons 6582 ; déductibles dans la limite de 0,5 % du CA (CGI art. 7).", "Donations 6582; deductible up to 0.5%."),
        (5, "reversal", "Passez l'écriture de la reprise de provision.", "Record the provision reversal.",
         "Provision 191 soldée par 7911 ; la reprise d'une provision déjà taxée se déduit.",
         "Provision 191 reversed through 7911; deducted for tax."),
    ]
    for module, key, fr, en, why_fr, why_en in events:
        book.journal(module, "exam", special[key], fr, en, why_fr, why_en)
    inventory_questions(book, special)
    bridge_questions(book, special)
    for module in book.questions:
        split_usage(book.questions[module])


def inventory_questions(book, special):
    for name, (ref, lots, sold, result, _account) in special["stock"].items():
        args = [[[int(q), int(u)] for q, u in lots], int(sold)]
        for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré", "weighted average unit cost"),
                            ("valeur_sortie", "coût des sorties au CMUP", "cost of goods sold at WAC"),
                            ("valeur_stock", "valeur du stock final au CMUP", "closing stock at WAC")):
            book.numeric(6, "exam", result[key], f"{name.capitalize()} : {fr} ?", f"{name.capitalize()}: {en}?",
                         "CMUP de l'exercice (inventaire intermittent, S18), arrondi au franc ; calculateur stock.",
                         "Period weighted average cost, rounded to the franc.", piece=ref,
                         calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
        peps = calculs.sortie_peps([(D(q), D(u)) for q, u in lots], D(sold))
        book.numeric(6, "exam", peps["valeur_sortie"], f"{name.capitalize()} : coût des sorties en PEPS (contraste) ?",
                     f"{name.capitalize()}: cost of goods sold under FIFO (contrast)?",
                     "En PEPS, les lots les plus anciens sortent d'abord : l'écart avec le CMUP change la marge.",
                     "Under FIFO the oldest lots go first; the gap with WAC changes the margin.", piece=ref,
                     calcul={"fonction": "sortie_peps", "args": args, "resultat": ["valeur_sortie"]})
    book.journal(6, "exam", special["stock"]["chemises"][0], "Passez l'écriture du stock final des trois familles.",
                 "Record the closing stock of the three families.",
                 "Stocks 3111, 3112 et 3121 au débit, variation des stocks 6031 au crédit (inventaire intermittent).",
                 "Stock accounts debited, change in inventories 6031 credited.")
    book.numeric(6, "exam", special["dotation"],
                 "Dotation 2026 de la voiture (12 000 000 HT, 3 ans, mise en service en avril) ?",
                 "2026 depreciation of the car (12,000,000, 3 years, in use from April)?",
                 "Linéaire au prorata : 12 000 000 / 36 × 9 mois ; calculateur amortissement.",
                 "Straight-line pro rata: 12,000,000 / 36 × 9 months.", piece=special["schedule"],
                 calcul={"fonction": "amortissement_lineaire", "args": [12000000, 3, 4], "resultat": [0, "dotation"]})
    book.journal(6, "exam", special["schedule"], "Passez l'écriture de la dotation aux amortissements.",
                 "Record the depreciation charge.", "Dotations 6813, amortissements du matériel de transport 2845.",
                 "Charge 6813, accumulated depreciation 2845.")
    total_stock = sum(v[3]["valeur_stock"] for v in special["stock"].values())
    book.numeric(6, "exam", total_stock, "Montant total de la variation des stocks de marchandises (6031) au 31 décembre ?",
                 "Total change in goods inventory (6031) at 31 December?",
                 "Premier exercice : pas de stock initial, la variation égale le stock final des trois familles.",
                 "First year: no opening stock, so the change equals the closing stock.",
                 piece=special["stock"]["chemises"][0])
    book.numeric(6, "exam", 12000000 - special["dotation"], "Valeur nette comptable de la voiture au 31 décembre ?",
                 "Net book value of the car at 31 December?", "Coût d'acquisition HT moins amortissements cumulés.",
                 "Cost excluding tax less accumulated depreciation.", piece=special["schedule"])
    shirts = special["stock"]["chemises"]
    peps = calculs.sortie_peps(shirts[1], shirts[2])
    book.numeric(6, "exam", abs(peps["valeur_sortie"] - shirts[3]["valeur_sortie"]),
                 "Chemises : écart entre le coût des sorties au CMUP et en PEPS ?",
                 "Shirts: gap between cost of goods sold at WAC and FIFO?",
                 "Différence des deux coûts des sorties : autant d'écart sur la marge brute.",
                 "Difference between both costs of goods sold: same gap on gross margin.", piece=shirts[0])
    book.choice(6, "exam", special["schedule"], "Taux d'amortissement fiscal maximal d'une voiture légère utilisée en ville ?",
                "Maximum tax depreciation rate of a light car used in town?", 
                [("25 %", "25%", True), ("33,33 %", "33.33%", False), ("20 %", "20%", False)],
                "25 % (CGI art. 7) : au-delà, la dotation comptable est réintégrée.",
                "25% (CGI art. 7): any excess is added back.")
    book.choice(6, "quiz", special["stock"]["robes"][0], "En période de hausse des prix, le PEPS donne un stock final "
                "plus élevé que le CMUP.", "When prices rise, FIFO gives a higher closing stock than WAC.",
                [("Vrai", "True", True), ("Faux", "False", False)],
                "Vrai : le stock final est valorisé aux derniers prix, plus élevés.",
                "True: closing stock is valued at the latest, higher prices.", qtype="truefalse")


def bridge_questions(book, special):
    add, tax = special["add_backs"], special["tax"]
    items = [
        ("amendes", special["penalty"], add["amendes"], None, "Montant de la pénalité à réintégrer ?",
         "Penalty to add back?", "Les amendes et pénalités ne sont pas déductibles (CGI art. 7)."),
        ("amortissement_excedentaire", special["schedule"], add["amortissement_excedentaire"],
         {"fonction": "reintegration_amortissement", "args": [special["dotation"], 12000000, 25, 9], "resultat": []},
         "Part de la dotation à réintégrer (taux fiscal maximal de 25 %) ?", "Depreciation to add back (25% cap)?",
         "Déductible : 12 000 000 × 25 % × 9/12 ; le surplus est réintégré (CGI art. 7)."),
        ("dons_excedentaires", special["donation"], add["dons_excedentaires"],
         {"fonction": "reintegration_dons", "args": [600000, special["turnover"], 0.5], "resultat": []},
         "Part du don à réintégrer (limite de 0,5 % du CA) ?", "Donation to add back (0.5% of turnover cap)?",
         "Déductible dans la limite de 0,5 % du chiffre d'affaires (CGI art. 7)."),
        ("charge_sans_piece", special["no_receipt"], add["charge_sans_piece"], None,
         "Charge à réintégrer faute de justificatif ?", "Expense to add back for lack of receipt?",
         "Une charge sans pièce justificative n'est pas déductible (CGI art. 7)."),
        ("impot_societes", special["liquidation"], tax["du"],
         {"fonction": "impot_societes", "args": [special["tax_result"], special["turnover"], float(special["rate"]), 2, 10],
          "resultat": ["du"]},
         "IS dû pour 2026 (le plus élevé de l'IS et du minimum de perception) ?",
         "2026 CIT due (higher of CIT and minimum tax)?",
         "IS au taux de 25 % (CA inférieur à 3 milliards, art. 17 bis) comparé au minimum de 2 % du CA, CAC compris."),
        ("reprise_provision_taxee", special["reversal"], special["deductions"]["reprise_provision_taxee"], None,
         "Montant à déduire au titre de la reprise de provision ?", "Amount deducted for the provision reversal?",
         "La provision a été réintégrée à sa dotation : sa reprise se déduit."),
    ]
    for key, ref, value, calc, fr, en, why in items:
        extra = {"passerelle": key}
        if calc:
            extra["calcul"] = calc
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref, **extra)
    for value, fr, en, why, ref in (
        (add["provision"], "Dotation à la provision pour litige à réintégrer ?", "Litigation provision to add back?",
         "Provision pour un risque non déductible : réintégrée.", special["provision"]),
        (special["accounting"], "Résultat comptable avant impôt 2026 ?", "2026 accounting profit before tax?",
         "Produits moins charges des classes 6, 7 et 8.", special["liquidation"]),
        (special["tax_result"], "Résultat fiscal 2026 ?", "2026 taxable profit?",
         "Résultat comptable + réintégrations − déductions.", special["liquidation"]),
        (tax["minimum_total"], "Minimum de perception 2026, CAC compris ?", "2026 minimum tax, council cents included?",
         "2 % du CA arrondi au millier inférieur, majoré de 10 % (CGI art. 21 et 23).", special["liquidation"]),
        (special["prepaid"], "Total des acomptes d'IS versés au titre de 2026 ?", "Total 2026 CIT instalments?",
         "Somme des acomptes bruts des douze déclarations (compte 441).", special["liquidation"]),
        (tax["solde"], "Solde d'IS à payer avec la DSF ?", "CIT balance due with the return?",
         "IS dû moins acomptes versés.", special["liquidation"]),
        (special["turnover"], "Chiffre d'affaires HT 2026 ?", "2026 turnover excl. tax?", "Total des ventes 7011.",
         special["liquidation"]),
        (special["accounting"] - tax["du"], "Résultat net 2026 ?", "2026 net profit?", "Résultat avant impôt − IS dû.",
         special["liquidation"]),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref)
    book.journal(7, "exam", special["liquidation"], "Passez l'écriture de l'IS de l'exercice.",
                 "Record the CIT for the year.", "Impôt sur les bénéfices 891 au débit, État 441 au crédit.",
                 "Income tax 891 debit, State 441 credit.")
    quizzes = [
        ("Date limite de dépôt de la DSF 2026 de Ngono Mode SARL (CIME) ?", "Filing deadline (MTO)?", "single",
         [("15 avril 2027", "15 April 2027", True), ("15 mars 2027", "15 March 2027", False),
          ("15 mai 2027", "15 May 2027", False)], "CIME : 15 avril (CGI art. 18 (1), S22)."),
        ("Quels tableaux de la DSF sont travaillés dans la simulation ?", "Which return tables are covered?", "single",
         [("Bilan, compte de résultat, tableau de passage, liquidation de l'IS",
           "Balance sheet, income statement, reconciliation, CIT", True),
          ("Tous les tableaux de la DSF", "All tables", False)], "Périmètre S12."),
        ("L'IS de l'exercice est une charge déductible.", "The year's CIT is deductible.", "truefalse",
         [("Vrai", "True", False), ("Faux", "False", True)], "Faux : l'IS n'est pas admis en charge (CGI art. 7)."),
        ("Un précompte subi sur achats s'impute sur les acomptes d'IS.",
         "Purchase withholding is credited against CIT instalments.", "truefalse",
         [("Vrai", "True", True), ("Faux", "False", False)], "Vrai (CGI art. 21 (3))."),
        ("Le minimum de perception s'applique même en cas de perte.", "The minimum tax applies even with a loss.",
         "truefalse", [("Vrai", "True", True), ("Faux", "False", False)],
         "Vrai : il est dû sur le chiffre d'affaires (CGI art. 21 et 23)."),
    ]
    for fr, en, qtype, choices, why in quizzes:
        book.choice(7, "quiz", special["liquidation"], fr, en, choices, why, why, qtype=qtype)


MODULES = [
    ("Création et janvier", "Set-up and January", "Créer l'entreprise et tenir son premier mois.",
     "Create the company and keep its first month."),
    ("Premier trimestre (février et mars)", "First quarter (February and March)", "Tenir les opérations courantes.",
     "Keep routine operations."),
    ("Deuxième trimestre", "Second quarter", "Acquérir une immobilisation et tenir les opérations.",
     "Buy a fixed asset and keep operations."),
    ("Troisième trimestre", "Third quarter", "Traiter pénalités et dépenses sans pièce.",
     "Handle penalties and expenses without receipts."),
    ("Quatrième trimestre", "Fourth quarter", "Traiter dons et reprises de provisions.",
     "Handle donations and provision reversals."),
    ("Inventaire", "Year-end inventory", "Valoriser le stock et amortir.", "Value stock and depreciate."),
    ("Passerelle fiscale et DSF", "Tax bridge and return", "Passer du résultat comptable à l'IS et à la DSF.",
     "Move from accounting profit to CIT and the return."),
]


def piece_list(refs):
    return "\n\n".join(f"[[piece:{ref}]]" for ref in refs)


def ascii_name(month):
    return MONTHS_FR[month - 1].replace("é", "e").replace("û", "u")


def sections(book, special):
    """Sections bilingues par module : dossier d'entreprise (US-81), mois (S11), inventaire (US-88), passerelle."""
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    out = {m: [] for m in range(1, 8)}
    company_fr = (
        "## Ngono Mode SARL\n\nBoutique de vêtements à Douala-Akwa, SARL au capital de 5 000 000 FCFA créée le 2 janvier "
        f"{YEAR}, au régime du réel, rattachée au CIME (chiffre d'affaires visé : 90 millions) [[source:dgi-cime]]. Un "
        "gérant salarié et deux vendeuses.\n\n### Plan de comptes de l'entreprise\n\n"
        "[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] (sous-comptes 5521 MTN MoMo et 5522 Orange Money) "
        "[[syscohada:6011]] [[syscohada:7011]] [[syscohada:4452]] [[syscohada:4431]] [[syscohada:4492]] "
        "[[syscohada:4472]] [[syscohada:431]]\n\n### Taux de l'exercice 2026\n\n"
        "- TVA [[param:tva.taux_principal]] et CAC [[param:cac.taux]] de la TVA [[cgi:art. 142]] ;\n"
        "- précompte sur achats [[param:precompte.taux_reel]] [[cgi:art. 21]] ;\n"
        "- acompte d'IS [[param:is.taux_minimum_perception]] du chiffre d'affaires ;\n"
        "- précompte sur loyer [[param:precompte.taux_loyer]] [[cgi:art. 87]].\n")
    company_en = (
        "## Ngono Mode SARL\n\nClothing shop in Douala-Akwa, LLC with 5,000,000 FCFA capital created on 2 January "
        f"{YEAR}, actual regime, attached to the medium-sized taxpayer office [[source:dgi-cime]].\n\n"
        "### Chart of accounts\n\n[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] [[syscohada:6011]] "
        "[[syscohada:7011]] [[syscohada:4452]] [[syscohada:4431]] [[syscohada:4492]]\n\n### 2026 rates\n\n"
        "- VAT [[param:tva.taux_principal]], council cents [[param:cac.taux]] [[cgi:art. 142]];\n"
        "- purchase withholding [[param:precompte.taux_reel]] [[cgi:art. 21]];\n"
        "- rent withholding [[param:precompte.taux_loyer]] [[cgi:art. 87]].\n")
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file", company_fr + "\n" + narrative_a.company_extra("fr"),
                   company_en + "\n" + narrative_a.company_extra("en")))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   "Chaque démarche précise l'organisme, les documents à fournir et ce que l'on obtient, avec sa source "
                   f"officielle [[cgi:art. L 1]].\n\n{proc}\n",
                   f"Each procedure gives the body, the documents and what you obtain [[cgi:art. L 1]].\n\n{proc}\n"))
    kinds = {p["ref"]: p["kind"] for p in book.pieces}
    special["why"] = {}
    for month in range(1, 13):
        # S34 : chaque mois est raconté scène par scène ; la balance d'ouverture suit l'accroche.
        module = MODULE_OF_MONTH[month]
        opening = [ref for ref in by_month[month] if kinds[ref] == "balance"]
        told = {sc["ref"] for sc in narrative_a.month_scenes(book, special, month)}
        others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
        body_fr, why = narrative_a.month_section(book, special, month, opening, others, "fr")
        body_en, _ = narrative_a.month_section(book, special, month, opening, others, "en")
        special["why"].update(why)
        out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}", body_fr, body_en))
    told, why = narrative_a.year_end_sections(book, special)
    special["why"].update(why)
    out[6].append(("01-inventaire", "Inventaire au 31 décembre", "Year-end inventory", told["inventory"]["fr"],
                   told["inventory"]["en"]))
    out[7].append(("01-passerelle", "Passerelle fiscale", "Tax bridge", told["bridge"]["fr"], told["bridge"]["en"]))
    out[7].append(("02-dsf", "DSF 2026", "2026 return", told["dsf"]["fr"], told["dsf"]["en"]))
    return out


def explain(book, why):
    """S34 : l'explication d'une question journal sur une pièce narrée reprend le « pourquoi » de sa scène."""
    for questions in book.questions.values():
        for question in questions:
            if question["type"] != "journal":
                continue
            for ref, (fr, en) in why.items():
                if f"[[piece:{ref}]]" in question["prompt"]["fr"]:
                    question["explanation"] = text(f"{question['explanation']['fr']} Pourquoi pas autre chose : {fr}",
                                                   f"{question['explanation']['en']} Why not something else: {en}")


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8", newline="\n")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


DELIVERY_ORDER = ("a", "e", "b3", "c", "d", "b1", "b2")  # S20, S29 (courses/tests/content_rules.py)


def write_manifest(manifest, partie):
    """Remplace la seule partie générée dans formation.json ; les autres parcours sont gardés, dans l'ordre de livraison."""
    path = OUT / "formation.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        parties = {p["slug"]: p for p in current.get("parties", [])}
        manifest = {**current, **{k: v for k, v in manifest.items() if k != "parties"}}
    else:
        parties = {}
    parties[partie["slug"]] = partie
    manifest["parties"] = [parties[slug] for slug in DELIVERY_ORDER if slug in parties]
    for order, item in enumerate(manifest["parties"], start=1):
        item["order"] = order
    write(path, manifest)


def main():
    book, special, _staff = build()
    special["procedures"] = [p["ref"] for p in book.pieces if p["kind"] == "demarche"]
    special["capital"] = next(p["ref"] for p in book.pieces if p["title"]["fr"].startswith("Attestation de dépôt"))
    balances(book)
    build_questions(book, special)
    module_sections = sections(book, special)
    explain(book, special["why"])
    modules = []
    for number, (title_fr, title_en, comp_fr, comp_en) in enumerate(MODULES, start=1):
        folder = f"a/m{number}"
        section_entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            section_entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": text(comp_fr, comp_en), "sections": section_entries})
    write(OUT / "a" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "a" / "ledger.json", book.entries)
    manifest = {
        "slug": "simulation", "prefix": "S", "icon": "briefcase", "open": True, "order": 3,
        "title": text("Simulation Compta et Fisca", "Accounting and Tax Simulation"),
        "description": text("Une année complète d'entreprises camerounaises fictives, sur pièces justificatives.",
                            "A full year of fictitious Cameroonian businesses, from source documents."),
        "legal_reference": text("SYSCOHADA révisé et CGI Cameroun, édition 2026",
                                "Revised SYSCOHADA and Cameroon General Tax Code, 2026 edition"),
        "prerequisite_note": text("Recommandé après les formations Comptabilité et Fiscalité.",
                                  "Recommended after the Accounting and Taxation courses."),
        "parties": [{
            "slug": "a", "order": 1,
            "title": text("Parcours A : boutique de vêtements (Ngono Mode SARL)", "Track A: clothing shop (Ngono Mode SARL)"),
            "description": text("SARL au réel, boutique de vêtements à Douala-Akwa, rattachée au CIME.",
                                "LLC under the actual regime, clothing shop in Douala-Akwa."),
            "centre_impots": "cime", "chiffre_affaires_vise": 90000000,
            "sous_comptes": {"5521": text("MTN MoMo", "MTN MoMo"), "5522": text("Orange Money", "Orange Money")},
            "pieces": "a/pieces.json", "ledger": "a/ledger.json", "exam": {"questions_per_module": 4},
            "modules": modules}],
    }
    write_manifest(manifest, manifest["parties"][0])
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, "
          f"résultat {special['accounting']}, IS {special['tax']['du']}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
