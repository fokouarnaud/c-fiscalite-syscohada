"""Génère le parcours C de la simulation (Tech Clim Bonamoussadi SARL, exercice 2026) dans content/simulation/c/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_c

SARL au réel rattachée au CIME de Douala (profil validé le 2026-11-02, S35) : vente d'appareils (7011) et pose de
climatiseurs (706) ; un fonctionnaire associé à 80 %, payé en honoraires quand il forme les techniciens (632, sans
retenue de l'art. 92 bis) ; gérance confiée à un tiers salarié ; outillage amorti, provision pour garantie (192) ;
IS au taux réduit ; assemblée de juin 2027 : réserve légale, dividendes et IRCM (AUSCGIE art. 346 et 348, CGI art. 70).
Tout est calculé par referentiel/calculs.py et tools/simulation/ledger.py ; les contrôles bloquants de
courses/tests/content_rules.py vérifient la sortie.
"""
import calendar
import datetime
from decimal import Decimal as D

from referentiel import calculs
from tools.simulation import ledger, narrative_c
from tools.simulation.build_parcours_a import (
    MONTHS_EN, MONTHS_FR, OUT, P, YEAR, Book, balances, d, fcfa, line, payroll, piece_list, settle, split_usage, text,
    tva, workday, write, write_manifest,
)
from tools.simulation.build_parcours_b3 import ascii_name, piece_of, taxes_totals

SELLER = {"name": "Tech Clim Bonamoussadi SARL", "niu": "M012600014407T", "rccm": "RC/DLA/2026/B/0519",
          "regime": "réel", "centre": "CIME Douala", "address": "Bonamoussadi, Douala"}
SUPPLIER = {"name": "Électro Import Wouri SARL (fictive)", "niu": "M010700005518H", "rccm": "RC/DLA/2007/B/0866",
            "regime": "réel", "centre": "DGE", "address": "Boulevard du Port, Douala"}
TOOLS_SUPPLIER = {"name": "Froid Équipement Akwa SARL", "niu": "M011300006124W", "rccm": "RC/DLA/2013/B/0402",
                  "regime": "réel", "centre": "CIME Douala", "address": "Akwa, Douala"}
NOTARY = {"name": "Étude de Maître Moukoko, notaire", "niu": "P010900003318C", "rccm": "Office notarial n° 21",
          "regime": "réel", "centre": "CIME Douala", "address": "Bonanjo, Douala"}
CLIENTS = [{"name": "Clinique de Bonamoussadi (fictive)", "niu": "M011000007731D"},
           {"name": "Hôtel Les Palmiers de Kotto (fictif)", "niu": "M011500008842F"}]
OWN = {"name": SELLER["name"], "niu": SELLER["niu"]}
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}

# Familles d'appareils : compte de stock, quantités achetées et vendues par mois, prix d'achat (hausse trimestrielle) et
# prix de vente HT (inchangé).
FAMILIES = [("téléviseurs", "TV sets", "3111", 20, 18, 180000, 230000),
            ("climatiseurs", "air conditioners", "3112", 15, 14, 250000, 320000),
            ("petit électroménager", "small appliances", "3121", 40, 36, 25000, 33000)]
CASH_SHARE = {"téléviseurs": 10, "climatiseurs": 6, "petit électroménager": 24}  # ventes au comptoir ; le reste par Orange Money
POSE = 35000                     # pose d'un climatiseur, HT
STAFF = [("Gérant salarié", "Salaried manager", 300000), ("Technicien poseur 1", "Installer 1", 150000),
         ("Technicien poseur 2", "Installer 2", 150000), ("Vendeuse", "Sales assistant", 120000)]
RENT, CAPITAL, TOOLS_HT, FEES, WARRANTY = 250000, 2000000, 1600000, 100000, 450000
FEE_MONTHS = (3, 6, 9, 11)       # formations des techniciens par le fonctionnaire associé
OM_FEE, BANK_FEE = 9000, 3500
DIVIDENDS, IRCM_RATE = 6000000, D("16.5")  # 15 % (CGI art. 70) majorés de 10 % de CAC


def last(month):
    return calendar.monthrange(YEAR, month)[1]


def buy_price(base, month):
    return base + 2500 * ((month - 1) // 3)


PROCEDURES = [
    ("Création de la SARL au CFCE de Douala", "Creating the LLC at the Douala business centre",
     text("Centre de formalités de création d'entreprises (CFCE) de Douala", "Douala business formalities centre"),
     text("Créer la SARL ; capital de 2 000 000 FCFA, au-delà d'un million : statuts notariés",
          "Create the LLC; 2,000,000 FCFA capital, above one million: notarised articles"),
     [text("Statuts notariés et déclaration de souscription et de versement", "Notarised articles and declaration of "
           "subscription and payment"),
      text("Casiers judiciaires ou déclarations sur l'honneur, CNI des associés et du gérant", "Criminal records or sworn "
           "statements, IDs of partners and manager"),
      text("Plan de localisation, boîte postale, contact téléphonique", "Location map, PO box, phone"),
      text("Frais de création et d'annonce légale (à vérifier au CFCE)", "Creation and legal notice fees (check)")],
     text("Registre de commerce, carte de contribuable (NIU), attestation de création",
          "Trade register, taxpayer card, creation certificate"),
     "[[source:loi-2016-014]] [[source:minfi-cfce]] [[source:ohada-auscgie]]"),
    ("Rattachement fiscal au CIME de Douala", "Tax office attachment (Douala medium-sized taxpayers)",
     text("Direction générale des impôts, CIME de Douala", "Directorate General of Taxation, Douala MTO"),
     text("Suivi fiscal d'une entreprise dont le CA visé (environ 120 millions) est compris entre 50 millions et "
          "3 milliards", "Tax follow-up of a company with a target turnover between 50 million and 3 billion"),
     [text("Carte de contribuable délivrée au CFCE", "Taxpayer card issued by the CFCE"),
      text("Statuts et registre de commerce", "Articles and trade register")],
     text("Rattachement au CIME et accès à la télédéclaration", "Attachment to the MTO and e-filing access"),
     "[[cgi:art. L 1]] [[source:dgi-cime]]"),
    ("Immatriculation à la CNPS", "Registration with the CNPS",
     text("Agence régionale de la CNPS", "Regional CNPS office"),
     text("Immatriculer l'employeur, puis chaque salarié dans les 8 jours de l'embauche",
          "Register the employer, then each employee within 8 days of hiring"),
     [text("Demande d'immatriculation sur imprimé CNPS", "Registration form (CNPS)"),
      text("Copie du registre de commerce, carte de contribuable, plan de localisation, liste du personnel",
           "Trade register copy, taxpayer card, map, staff list")],
     text("Numéro d'employeur et numéros d'assurés", "Employer number and employee numbers"), "[[source:cnps-faq]]"),
    ("Ouverture du compte bancaire de l'entreprise", "Opening the company bank account",
     text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
     text("Ouvrir le compte de l'entreprise", "Open the company account"),
     [text("Demande d'ouverture, registre de commerce, carte de contribuable", "Request, trade register, taxpayer card"),
      text("Pièces d'identité du gérant, statuts, procès-verbal de nomination du gérant", "Manager's ID, articles, "
           "minutes appointing the manager")],
     text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
    ("Compte marchand Orange Money", "Orange Money merchant account",
     text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
     text("Encaisser les ventes par Orange Money", "Collect sales through Orange Money"),
     [text("Registre de commerce, carte de contribuable, patente, statuts", "Trade register, taxpayer card, licence, "
           "articles"),
      text("CNI du gérant, RIB", "Manager's ID, bank details")],
     text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
]


def build():
    book, special = Book("C"), {"months": {}}
    staff = payroll(STAFF)
    pay = {k: sum(r[k] for r in staff) for k in ("gross", "cnps", "irpp", "rav", "tdl", "cfc", "net", "cfc_pat", "cnps_pat")}
    salary_taxes = pay["irpp"] + pay["rav"] + pay["tdl"] + pay["cfc"] + pay["cfc_pat"]
    special["procedures"] = [book.piece(1, "demarche", d(1, 2), f"Démarche : {fr}", f"Procedure: {en}",
                                        {"organisme": body, "objet": purpose, "documents_a_fournir": docs,
                                         "document_obtenu": got, "source": source})
                             for fr, en, body, purpose, docs, got, source in PROCEDURES]
    special["capital"] = book.piece(1, "releve_bancaire", d(1, 2), "Attestation de dépôt du capital (Banque X)",
                                    "Capital deposit certificate (Bank X)",
                                    {"fields": [{"label": text("Associés", "Partners"),
                                                 "value": text("Fonctionnaire 80 %, associée 20 %",
                                                               "Civil servant 80%, partner 20%")}],
                                     "totals": [{"label": text("Capital libéré", "Paid-up capital"), "amount": CAPITAL}]})
    book.entry(d(1, 2), special["capital"], line("521", "debit", CAPITAL), line("1013", "credit", CAPITAL))
    fees, duties = 250000, 40000
    fee_tax = tva(fees)
    special["notary"] = book.piece(1, "facture_achat", d(1, 6), "Facture du notaire (statuts)", "Notary's invoice (articles)",
                                   {"issuer": NOTARY, "customer": OWN, "number": "MM-2026-0017",
                                    "einvoice": "DGI-SFE-2026-007117",
                                    "lines": [{"label": text("Honoraires de rédaction des statuts", "Drafting fees"),
                                               "amount": fees},
                                              {"label": text("Débours : droits d'enregistrement", "Registration duties"),
                                               "amount": duties}],
                                    "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht",
                                                "amount": fees + duties},
                                               {"label": text("TVA et CAC sur les honoraires", "VAT on fees"), "role": "tax",
                                                "amount": int(fee_tax["taxes"])},
                                               {"label": text("Net payé par virement", "Net paid by transfer"), "role": "ttc",
                                                "amount": int(fees + duties + fee_tax["taxes"])}]})
    book.entry(d(1, 6), special["notary"], line("6324", "debit", fees), line("4454", "debit", fee_tax["taxes"]),
               line("646", "debit", duties), line("521", "credit", fees + duties + fee_tax["taxes"]))
    tools_tax, tools_totals = taxes_totals(TOOLS_HT)
    special["tools"] = book.piece(1, "facture_achat", workday(1, 7), "Facture d'outillage de pose", "Installation tools invoice",
                                  {"issuer": TOOLS_SUPPLIER, "customer": OWN, "number": "FEA-2026-0044",
                                   "einvoice": "DGI-SFE-2026-007244",
                                   "lines": [{"label": text("Station de récupération de fluide, pompe à vide, perceuses",
                                                            "Refrigerant recovery unit, vacuum pump, drills"),
                                              "qty": 1, "unit_price": TOOLS_HT, "amount": TOOLS_HT}],
                                   "totals": tools_totals + [{"label": text("Net à payer à 30 jours", "Net payable at 30 days"),
                                                              "role": "ttc", "amount": int(tools_tax["ttc"])}]})
    book.entry(workday(1, 7), special["tools"], line("2412", "debit", TOOLS_HT), line("4451", "debit", tools_tax["taxes"]),
               line("4812", "credit", tools_tax["ttc"]))
    special["tools_due"] = int(tools_tax["ttc"])

    lots = {f[0]: [] for f in FAMILIES}
    unpaid = {"supplier": 0, "client": 0}
    for month in range(1, 13):
        end, refs = last(month), {}
        mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {mfr} (Banque X)",
                                  f"{men} bank statement (Bank X)", {})
        rows = []
        withheld = calculs.franc(D(RENT) * P["precompte.taux_loyer"] / 100)
        rent_day = workday(month, 6 if month == 1 else 2)
        refs["rent"] = book.piece(month, "recu_caisse", rent_day, f"Quittance de loyer de la boutique, {mfr}",
                                  f"{men} shop rent receipt",
                                  {"fields": [{"label": text("Bailleur", "Landlord"), "value": "M. Ngando (fictif)"}],
                                   "totals": [{"label": text("Loyer brut", "Gross rent"), "amount": RENT},
                                              {"label": text("Précompte sur loyer 10 % retenu", "10% rent withholding"),
                                               "amount": int(withheld)},
                                              {"label": text("Net versé par virement", "Net paid by transfer"),
                                               "amount": int(RENT - withheld)}]})
        book.entry(rent_day, refs["rent"], line("6222", "debit", RENT), line("4478", "credit", withheld),
                   line("521", "credit", RENT - withheld))
        if month == 2:
            book.entry(workday(2, 9), refs["bank"], line("4812", "debit", special["tools_due"]),
                       line("521", "credit", special["tools_due"]))
            rows.append((text("Virement à Froid Équipement Akwa (outillage)", "Transfer to the tools supplier"),
                         special["tools_due"]))
        if unpaid["supplier"]:
            book.entry(d(month, end), refs["bank"], line("401", "debit", unpaid["supplier"]),
                       line("521", "credit", unpaid["supplier"]))
            rows.append((text("Virement à Électro Import Wouri", "Transfer to the importer"), unpaid["supplier"]))
        if unpaid["client"]:
            book.entry(d(month, 10), refs["bank"], line("521", "debit", unpaid["client"]), line("411", "credit", unpaid["client"]))
            rows.append((text("Virement reçu pour les poses du mois précédent", "Transfer received for last month's "
                              "installations"), unpaid["client"]))
        # Achats chez l'importateur, payés à la fin du mois suivant.
        lines_, ht = [], 0
        for name_fr, name_en, _acc, qty, _sold, base, _sell in FAMILIES:
            unit = buy_price(base, month)
            lots[name_fr].append((qty, unit))
            lines_.append({"label": text(name_fr.capitalize(), name_en.capitalize()), "qty": qty, "unit_price": unit,
                           "amount": qty * unit})
            ht += qty * unit
        taxes, totals = taxes_totals(ht)
        precompte = calculs.franc(D(ht) * P["precompte.taux_reel"] / 100)
        due = ht + taxes["taxes"] + precompte
        totals += [{"label": text("Précompte sur achats 2 %", "2% purchase withholding"), "role": "tax",
                    "amount": int(precompte)},
                   {"label": text("Net à payer à la fin du mois suivant", "Net payable at the end of next month"),
                    "role": "ttc", "amount": int(due)}]
        purchase_day = workday(month, 5)
        refs["purchase"] = book.piece(month, "facture_achat", purchase_day, f"Facture d'Électro Import Wouri, {mfr}",
                                      f"Importer's invoice, {men}",
                                      {"issuer": SUPPLIER, "customer": OWN, "number": f"EIW-2026-{700 + month:04d}",
                                       "einvoice": f"DGI-SFE-2026-{7300 + month:06d}", "lines": lines_, "totals": totals})
        book.entry(purchase_day, refs["purchase"], line("6011", "debit", ht), line("4452", "debit", taxes["taxes"]),
                   line("4492", "debit", precompte), line("401", "credit", due))
        unpaid["supplier"] = int(due)
        # Pose des climatiseurs vendus, facturée à un client entreprise, payée le 10 du mois suivant.
        poses = next(f[4] for f in FAMILIES if f[0] == "climatiseurs")
        client = CLIENTS[month % 2]
        pose_ht = poses * POSE
        pose_tax, pose_totals = taxes_totals(pose_ht)
        invoice_day = workday(month, 20)
        refs["pose"] = book.piece(month, "facture_vente", invoice_day, f"Facture de pose de climatiseurs, {mfr}",
                                  f"Air-conditioner installation invoice, {men}",
                                  {"issuer": SELLER, "customer": client, "number": f"TCB-2026-{month:04d}",
                                   "einvoice": f"DGI-SFE-2026-{7400 + month:06d}",
                                   "lines": [{"label": text("Pose de climatiseur split, fourniture de tuyauterie comprise",
                                                            "Split unit installation, piping included"),
                                              "qty": poses, "unit_price": POSE, "amount": pose_ht}],
                                   "totals": pose_totals + [{"label": text("Net à payer le 10 du mois suivant",
                                                                           "Payable on the 10th of next month"),
                                                             "role": "ttc", "amount": int(pose_tax["ttc"])}]})
        book.entry(invoice_day, refs["pose"], line("411", "debit", pose_tax["ttc"]), line("706", "credit", pose_ht),
                   line("4431", "credit", pose_tax["taxes"]))
        unpaid["client"] = int(pose_tax["ttc"])
        # Ventes d'appareils : au comptoir (espèces) et par Orange Money.
        for key, share in (("cash", True), ("orange", False)):
            qty = {f[0]: (CASH_SHARE[f[0]] if share else f[4] - CASH_SHARE[f[0]]) for f in FAMILIES}
            sale_ht = sum(qty[f[0]] * f[6] for f in FAMILIES)
            sale_tax = tva(sale_ht)
            lines_sale = [{"label": text(f[0].capitalize(), f[1].capitalize()), "qty": qty[f[0]], "unit_price": f[6],
                           "amount": qty[f[0]] * f[6]} for f in FAMILIES]
            if share:
                refs["cash"] = book.piece(month, "recu_caisse", d(month, end), f"Récapitulatif des ventes au comptoir de {mfr}",
                                          f"{men} counter sales summary",
                                          {"lines": lines_sale,
                                           "totals": [{"label": text("Ventes HT", "Sales excl. tax"), "role": "ht",
                                                       "amount": sale_ht},
                                                      {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                                       "amount": int(sale_tax["taxes"])},
                                                      {"label": text("Ventes TTC encaissées", "Sales incl. tax collected"),
                                                       "role": "ttc", "amount": int(sale_tax["ttc"])}]})
                book.entry(d(month, end), refs["cash"], line("5711", "debit", sale_tax["ttc"]),
                           line("7011", "credit", sale_ht), line("4431", "credit", sale_tax["taxes"]))
            else:
                om_ttc = int(sale_tax["ttc"])
                refs["orange"] = book.piece(month, "releve_momo", d(month, end), f"Relevé Orange Money de {mfr}",
                                            f"Orange Money statement, {men}",
                                            {"lines": lines_sale,
                                             "totals": [{"label": text("Encaissements HT", "Receipts excl. tax"),
                                                         "role": "ht", "amount": sale_ht},
                                                        {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                                         "amount": int(sale_tax["taxes"])},
                                                        {"label": text("Encaissements TTC", "Receipts incl. tax"),
                                                         "role": "ttc", "amount": om_ttc},
                                                        {"label": text("Frais de l'opérateur", "Operator fees"),
                                                         "amount": OM_FEE},
                                                        {"label": text("Transfert vers la banque", "Transfer to the bank"),
                                                         "amount": om_ttc - OM_FEE}]})
                book.entry(d(month, end), refs["orange"], line("5522", "debit", om_ttc), line("7011", "credit", sale_ht),
                           line("4431", "credit", sale_tax["taxes"]), line("631", "debit", OM_FEE),
                           line("5522", "credit", OM_FEE), line("585", "debit", om_ttc - OM_FEE),
                           line("5522", "credit", om_ttc - OM_FEE))
        refs["payroll"] = book.piece(month, "bulletin_paie", d(month, end), f"Journal de paie de {mfr}",
                                     f"{men} payroll journal",
                                     {"lines": [{"label": r["name"], "amount": int(r["gross"])} for r in staff],
                                      "totals": [{"label": text("Salaires bruts", "Gross pay"), "role": "ht",
                                                  "amount": int(pay["gross"])},
                                                 {"label": text("IRPP et CAC", "PIT and council cents"), "amount": int(pay["irpp"])},
                                                 {"label": text("RAV", "Audiovisual fee"), "amount": int(pay["rav"])},
                                                 {"label": text("TDL", "Local development tax"), "amount": int(pay["tdl"])},
                                                 {"label": text("CFC salariale", "Employee housing levy"), "amount": int(pay["cfc"])},
                                                 {"label": text("CNPS salariale (pension 4,2 %)", "Employee CNPS (pension 4.2%)"),
                                                  "amount": int(pay["cnps"])},
                                                 {"label": text("Nets à payer", "Net pay"), "amount": int(pay["net"])},
                                                 {"label": text("CFC patronale", "Employer housing levy"), "amount": int(pay["cfc_pat"])},
                                                 {"label": text("CNPS patronale (pension 4,2 %)", "Employer CNPS (pension 4.2%)"),
                                                  "amount": int(pay["cnps_pat"])}]})
        book.entry(d(month, end), refs["payroll"], line("6611", "debit", pay["gross"]),
                   line("6413", "debit", pay["cfc_pat"]), line("6641", "debit", pay["cnps_pat"]),
                   line("4472", "credit", salary_taxes), line("431", "credit", pay["cnps"] + pay["cnps_pat"]),
                   line("422", "credit", pay["net"]))
        book.entry(d(month, end), refs["bank"], line("422", "debit", pay["net"]), line("521", "credit", pay["net"]))
        rows.append((text("Salaires nets virés", "Net pay transferred"), int(pay["net"])))
        if month > 1:
            refs["settlement"] = settle(book, month - 1, d(month, 15), month)
        if month in FEE_MONTHS:
            fee_day = workday(month, 23)
            refs["fees"] = book.piece(month, "recu_caisse", fee_day, f"Note d'honoraires de formation des techniciens, {mfr}",
                                      f"Technician training fee note, {men}",
                                      {"fields": [{"label": text("Intervenant", "Provider"),
                                                   "value": text("Fonctionnaire associé, formateur occasionnel",
                                                                 "Civil servant partner, occasional trainer")},
                                                  {"label": text("Retenue de l'art. 92 bis", "Art. 92 bis withholding"),
                                                   "value": text("Non applicable : la SARL n'est pas sur la liste",
                                                                 "Not applicable: the company is not on the list")}],
                                       "totals": [{"label": text("Honoraires payés par virement", "Fees paid by transfer"),
                                                   "amount": FEES}]})
            book.entry(fee_day, refs["fees"], line("632", "debit", FEES), line("521", "credit", FEES))
            rows.append((text("Honoraires du formateur", "Trainer's fees"), FEES))
        cash_left = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, end))
        refs["cash_out"] = book.piece(month, "recu_caisse", d(month, end), f"Bordereaux de versement des espèces de {mfr}",
                                      f"{men} cash deposit slips",
                                      {"totals": [{"label": text("Espèces versées", "Cash deposited"),
                                                   "amount": int(cash_left)}]})
        book.entry(d(month, end), refs["cash_out"], line("585", "debit", cash_left), line("5711", "credit", cash_left))
        transfers = cash_left + piece_of(book, refs["orange"])["payload"]["totals"][-1]["amount"]
        book.entry(d(month, end), refs["bank"], line("521", "debit", transfers), line("585", "credit", transfers),
                   line("631", "debit", BANK_FEE), line("521", "credit", BANK_FEE))
        rows += [(text("Virements internes reçus (espèces et Orange Money)", "Internal transfers received"),
                  int(transfers)), (text("Frais de tenue de compte", "Account fees"), BANK_FEE)]
        piece_of(book, refs["bank"])["payload"] = {"totals": [{"label": label, "amount": amount} for label, amount in rows]}
        special["months"][month] = refs
    year_end(book, special, lots)
    special["staff"] = staff
    return book, special


def year_end(book, special, lots):
    sold = {f[0]: 12 * f[4] for f in FAMILIES}
    fields, sheet_lines = [], []
    for name_fr, name_en, *_ in FAMILIES:
        bought = sum(q for q, _ in lots[name_fr])
        fields.append({"label": text(f"{name_fr.capitalize()} : achetés, vendus, en stock",
                                     f"{name_en.capitalize()}: bought, sold, in stock"),
                       "value": f"{bought} / {sold[name_fr]} / {bought - sold[name_fr]}"})
        sheet_lines += [{"label": text(f"{name_fr.capitalize()}, lot {i}", f"{name_en.capitalize()}, lot {i}"), "qty": q,
                         "unit_price": u, "amount": q * u} for i, (q, u) in enumerate(lots[name_fr], start=1)]
    sheet = book.piece(12, "fiche_stock", d(12, 31), "Fiches de stock CMUP des trois familles", "WAC stock cards",
                       {"fields": fields, "lines": sheet_lines})
    stock = {}
    for name_fr, _en, account, *_ in FAMILIES:
        family = [(D(q), D(u)) for q, u in lots[name_fr]]
        stock[name_fr] = (family, sold[name_fr], calculs.sortie_cmup(family, D(sold[name_fr])), account)
    book.entry(d(12, 31), sheet, *[line(v[3], "debit", v[2]["valeur_stock"]) for v in stock.values()],
               line("6031", "credit", sum(v[2]["valeur_stock"] for v in stock.values())))
    dotation = int(calculs.amortissement_lineaire(D(TOOLS_HT), 5, 1)[0]["dotation"])
    schedule = book.piece(12, "fiche_stock", d(12, 31), "Amortissements et provision pour garantie 2026",
                          "2026 depreciation and warranty provision",
                          {"fields": [{"label": text("Pannes déclarées sous garantie au 31 décembre",
                                                     "Warranty failures reported at 31 December"),
                                       "value": text("9 climatiseurs posés en novembre et décembre",
                                                     "9 units installed in November and December")}],
                           "lines": [{"label": text("Outillage (5 ans, depuis janvier)", "Tools (5 years, from January)"),
                                      "amount": dotation},
                                     {"label": text("Provision pour garantie : 9 réparations à 50 000",
                                                    "Warranty provision: 9 repairs at 50,000"), "amount": WARRANTY}],
                           "totals": [{"label": text("Charges de clôture", "Year-end charges"), "role": "ht",
                                       "amount": dotation + WARRANTY}]})
    book.entry(d(12, 31), schedule, line("6813", "debit", dotation), line("2841", "credit", dotation),
               line("6911", "debit", WARRANTY), line("192", "credit", WARRANTY))
    special.update(sheet=sheet, stock=stock, schedule=schedule, dotation=dotation)
    special["months"][12]["settlement_next"] = settle(book, 12, d(1, 15, YEAR + 1), 13)
    entries_2026 = [e for e in book.entries if e["date"] < f"{YEAR + 1}"]
    accounting = ledger.accounting_result(entries_2026)
    turnover = sum(l["amount"] for e in entries_2026 for l in e["lines"] if l["account"].startswith("70")
                   and l["side"] == "credit")
    tax_result = ledger.tax_result(accounting)
    rate = P["is.taux_reduit"] if turnover <= P["is.seuil_taux_reduit"] else P["is.taux"]
    prepaid = sum(l["amount"] for e in book.entries for l in e["lines"] if l["account"] == "441" and l["side"] == "debit")
    tax = ledger.corporate_tax(tax_result, turnover, prepaid, rate, P["is.taux_minimum_perception"], P["cac.taux"])
    liquidation = book.piece(4, "declaration", d(4, 9, YEAR + 1), "DSF 2026 : liquidation de l'IS", "2026 return: CIT",
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
    closing_stock = sum(v[2]["valeur_stock"] for v in stock.values())
    for table, fr, en, rows in (
        ("passage", "DSF 2026 : tableau de passage", "2026 return: reconciliation",
         [("Résultat comptable avant impôt", "Accounting profit before tax", accounting),
          ("Réintégrations", "Add-backs", 0), ("Résultat fiscal", "Taxable profit", tax_result)]),
        ("compte_resultat", "DSF 2026 : compte de résultat", "2026 return: income statement",
         [("Chiffre d'affaires", "Turnover", turnover), ("Résultat avant impôt", "Profit before tax", accounting),
          ("Impôt sur le résultat", "Income tax", tax["du"]), ("Résultat net", "Net profit", net)]),
        ("bilan", "DSF 2026 : bilan (extrait)", "2026 return: balance sheet (extract)",
         [("Capital", "Share capital", CAPITAL), ("Résultat net de l'exercice", "Net profit for the year", net),
          ("Provision pour garantie", "Warranty provision", WARRANTY),
          ("Stocks de marchandises", "Goods inventory", closing_stock),
          ("Outillage, valeur nette", "Tools, net book value", TOOLS_HT - dotation)]),
    ):
        book.piece(4, "declaration", d(4, 9, YEAR + 1), fr, en,
                   {"totals": [{"label": text(a, b), "amount": int(v)} for a, b, v in rows]}, year=YEAR + 1)
        book.pieces[-1]["dsf"] = table
    # Assemblée de juin 2027 (AUSCGIE art. 346 et 348) : réserve légale, dividendes ; IRCM à la mise en paiement.
    reserve = min(int(calculs.franc(D(net) / 10)), CAPITAL // 5)
    retained = net - reserve - DIVIDENDS
    special["meeting"] = book.piece(6, "statuts", d(6, 25, YEAR + 1), "Procès-verbal de l'assemblée ordinaire du 25 juin 2027",
                                    "Minutes of the ordinary meeting of 25 June 2027",
                                    {"fields": [{"label": text("Ordre du jour", "Agenda"),
                                                 "value": text("Approbation des comptes 2026 et affectation du résultat",
                                                               "Approval of the 2026 accounts and appropriation of profit")}],
                                     "totals": [{"label": text("Bénéfice net 2026", "2026 net profit"), "amount": int(net)},
                                                {"label": text("Réserve légale", "Legal reserve"), "amount": int(reserve)},
                                                {"label": text("Dividendes", "Dividends"), "amount": DIVIDENDS},
                                                {"label": text("Report à nouveau", "Retained earnings"), "amount": int(retained)}]},
                                    year=YEAR + 1)
    book.entry(d(6, 25, YEAR + 1), special["meeting"], line("131", "debit", net), line("111", "credit", reserve),
               line("465", "credit", DIVIDENDS), line("121", "credit", retained))
    ircm = int(calculs.franc(D(DIVIDENDS) * IRCM_RATE / 100))
    special["payout"] = book.piece(7, "releve_bancaire", d(7, 9, YEAR + 1), "Avis de virement des dividendes",
                                   "Dividend transfer notice",
                                   {"fields": [{"label": text("Répartition", "Split"),
                                                "value": text("80 % au fonctionnaire associé, 20 % à l'associée",
                                                              "80% to the civil servant, 20% to the other partner")}],
                                    "totals": [{"label": text("Dividendes bruts", "Gross dividends"), "amount": DIVIDENDS},
                                               {"label": text("IRCM retenu (15 % + CAC)", "Withholding tax (15% + council cents)"),
                                                "amount": ircm},
                                               {"label": text("Dividendes nets versés", "Net dividends paid"),
                                                "amount": DIVIDENDS - ircm}]}, year=YEAR + 1)
    book.entry(d(7, 9, YEAR + 1), special["payout"], line("465", "debit", DIVIDENDS), line("4478", "credit", ircm),
               line("521", "credit", DIVIDENDS - ircm))
    special["ircm_paid"] = book.piece(8, "recu_caisse", d(8, 13, YEAR + 1), "Quittance de reversement de l'IRCM",
                                      "Withholding tax payment receipt",
                                      {"totals": [{"label": text("IRCM reversé", "Withholding tax paid over"),
                                                   "amount": ircm}]}, year=YEAR + 1)
    book.entry(d(8, 13, YEAR + 1), special["ircm_paid"], line("4478", "debit", ircm), line("521", "credit", ircm))
    special.update(accounting=accounting, turnover=turnover, tax_result=tax_result, tax=tax, rate=rate, prepaid=prepaid,
                   liquidation=liquidation, net=net, closing_stock=closing_stock, reserve=reserve, retained=retained,
                   ircm=ircm)


# ---------------------------------------------------------------------------------------------------------- questions

def month_questions(book, special, month):
    module, refs = MODULE_OF_MONTH[month], special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    asks = [
        ("purchase", f"Passez l'écriture de la facture de l'importateur de {mfr} (précompte compris).",
         f"Record the importer's {men} invoice (withholding included).",
         "Achats 6011, TVA et CAC 4452, précompte de 2 % en 4492 (CGI art. 21 (3)), fournisseur 401.",
         "Purchases 6011, VAT 4452, 2% withholding 4492, supplier 401."),
        ("pose", f"Passez l'écriture de la facture de pose de {mfr}.", f"Record the {men} installation invoice.",
         "Client 411, services vendus 706, TVA facturée 4431 : une prestation, pas une vente de marchandises.",
         "Customer 411, services sold 706, VAT charged 4431: a service, not a sale of goods."),
        ("cash", f"Passez l'écriture des ventes au comptoir de {mfr}.", f"Record the {men} counter sales.",
         "Caisse 5711 au TTC, ventes de marchandises 7011, TVA 4431.", "Cash 5711, sales 7011, VAT 4431."),
        ("orange", f"Passez l'écriture du relevé Orange Money de {mfr}.", f"Record the {men} Orange Money statement.",
         "Sous-compte 5522 : ventes et TVA, frais 631, transfert vers la banque par 585 (S19).",
         "Sub-account 5522: sales and VAT, fees 631, transfer through 585."),
        ("payroll", f"Passez l'écriture du journal de paie de {mfr}.", f"Record the {men} payroll journal.",
         "Salaires 6611, CFC patronale 6413, CNPS patronale 6641 ; retenues 4472 et 431, nets 422.",
         "Gross 6611, employer levies 6413 and 6641; withholdings 4472 and 431, net 422."),
        ("bank", f"Passez les écritures du relevé bancaire de {mfr}.", f"Record the {men} bank statement entries.",
         "Fournisseur 401, client 411, salaires 422, virements internes 585, frais 631.",
         "Supplier 401, customer 411, salaries 422, internal transfers 585, fees 631."),
        ("rent", f"Passez l'écriture de la quittance de loyer de {mfr}.", f"Record the {men} rent receipt.",
         "Loyer brut 6222, précompte de 10 % en 4478 (CGI art. 87), net payé par la banque.",
         "Gross rent 6222, 10% withholding 4478, net paid by bank."),
        ("cash_out", f"Passez l'écriture des versements d'espèces de {mfr}.", f"Record the {men} cash deposits.",
         "Virement interne : 585 au débit, caisse 5711 au crédit.", "Internal transfer: 585 debit, cash 5711 credit."),
        ("settlement", f"Passez l'écriture du règlement de la déclaration du 15 {mfr}.",
         f"Record the payment of the {men} 15th return.",
         "TVA soldée, acompte d'IS en 441 net du précompte, retenues et CNPS reversées.",
         "VAT settled, CIT instalment net of withholding, withholdings and CNPS paid over."),
        ("fees", f"Passez l'écriture de la note d'honoraires de {mfr}.", f"Record the {men} fee note.",
         "Honoraires 632 payés par la banque ; ni salaire ni retenue de l'art. 92 bis, la SARL n'étant pas sur la liste.",
         "Fees 632 paid by bank; neither wages nor art. 92 bis withholding, the company not being on the list."),
    ]
    for key, fr, en, why_fr, why_en in asks:
        if key in refs:
            book.journal(module, "exam", refs[key], fr, en, why_fr, why_en)
    _ref, decl, _credit = book.declarations[month]
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
    end = datetime.date(YEAR, month, last(month))
    book.numeric(module, "exam", ledger.account_balance(book.entries, "521", end),
                 f"Solde comptable du compte 521 au {last(month)} {mfr} {YEAR} ?",
                 f"Book balance of account 521 at {men} {last(month)}, {YEAR}?",
                 "Débits moins crédits de 521 jusqu'à cette date : le solde à rapprocher du relevé.",
                 "Debits less credits of 521 up to that date.", piece=refs["bank"],
                 rapprochement={"account": "521", "date": end.isoformat()})
    pose = piece_of(book, refs["pose"])
    book.numeric(module, "exam", pose["payload"]["totals"][0]["amount"], f"Chiffre d'affaires HT des poses de {mfr} ?",
                 f"{men} installation revenue excluding tax?", "Nombre de poses × prix de la pose, hors TVA (706).",
                 "Number of installations × price, excluding VAT.", piece=refs["pose"])


PROCEDURE_QUESTIONS = [
    ("Pourquoi les statuts passent-ils chez le notaire ?", "Why are the articles notarised?",
     "Le capital dépasse un million de FCFA (loi n° 2016/014)", "Capital above one million FCFA",
     "Parce qu'un associé est fonctionnaire", "Because a partner is a civil servant"),
    ("Quel centre des impôts suit la SARL ?", "Which tax office follows the company?",
     "Le CIME (CA compris entre 50 millions et 3 milliards)", "The MTO", "La DGE", "The LTO"),
    ("Dans quel délai faut-il immatriculer un salarié à la CNPS ?", "Within how long must an employee be registered?",
     "8 jours après l'embauche", "8 days after hiring", "Trois mois", "Three months"),
    ("Que remet la banque à l'ouverture du compte ?", "What does the bank give?", "Un RIB", "Bank details (RIB)",
     "Une patente", "A licence"),
    ("Quelle pièce Orange exige-t-il en plus des documents légaux ?", "Which extra document does Orange require?",
     "Le RIB", "Bank details (RIB)", "Un bilan certifié", "A certified balance sheet"),
]


def build_questions(book, special):
    for ref, (fr, en, right_fr, right_en, wrong_fr, wrong_en) in zip(special["procedures"], PROCEDURE_QUESTIONS):
        book.choice(1, "quiz", ref, fr, en, [(right_fr, right_en, True), (wrong_fr, wrong_en, False)],
                    "Voir la démarche et sa source officielle.", "See the procedure and its official source.")
    book.choice(1, "quiz", special["notary"], "Les frais de constitution s'inscrivent à l'actif en frais d'établissement.",
                "Set-up costs are capitalised as formation expenses.", [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : le SYSCOHADA révisé les passe en charges par nature (6324, 646).",
                "False: revised SYSCOHADA expenses them by nature.", qtype="truefalse", piege="frais_etablissement")
    book.choice(1, "quiz", special["capital"], "Le fonctionnaire associé à 80 % peut-il être le gérant de la SARL ?",
                "May the 80% civil-servant partner manage the company?",
                [("Non : la gérance est confiée à un tiers", "No: a third party manages it", True),
                 ("Oui, s'il détient la majorité", "Yes, if he holds the majority", False)],
                "S35 : il est associé, jamais gérant ni salarié ; la gérance est confiée à un tiers non fonctionnaire.",
                "He is a partner, never manager or employee.")
    for ref, fr, en, why_fr, why_en in (
        (special["capital"], "Passez l'écriture du dépôt du capital.", "Record the capital deposit.",
         "Banque 521, capital 1013.", "Bank 521, capital 1013."),
        (special["notary"], "Passez l'écriture de la facture du notaire.", "Record the notary's invoice.",
         "Honoraires 6324, droits 646, TVA 4454 : des charges (S6).", "Fees 6324, duties 646, VAT 4454."),
        (special["tools"], "Passez l'écriture de la facture d'outillage.", "Record the tools invoice.",
         "Outillage industriel 2412 (au-delà du seuil de 500 000 HT, CGI art. 7), TVA sur immobilisations 4451, "
         "fournisseur d'immobilisations 4812 : payé à 30 jours.",
         "Industrial tools 2412 (above the 500,000 threshold), VAT on fixed assets 4451."),
    ):
        book.journal(1, "exam", ref, fr, en, why_fr, why_en)
    for month in range(1, 13):
        month_questions(book, special, month)
    for module, piece, fr, en, ok, why in (
        (2, special["months"][3]["fees"], "Les honoraires du fonctionnaire supportent la retenue de 5 % de l'art. 92 bis.",
         "The civil servant's fees bear the 5% art. 92 bis withholding.", False,
         "Faux ici : la retenue ne s'applique que si le payeur figure sur la liste réglementaire (CGI art. 92 bis)."),
        (3, special["months"][6]["fees"], "Le fonctionnaire associé peut être salarié de sa SARL.",
         "The civil-servant partner may be an employee of his company.", False,
         "Faux : il intervient comme formateur occasionnel, payé en honoraires (632)."),
        (4, special["months"][9]["pose"], "La pose d'un climatiseur est une vente de marchandises (7011).",
         "Installing a unit is a sale of goods (7011).", False, "Faux : c'est une prestation de services (706)."),
        (5, special["months"][11]["fees"], "Les honoraires du formateur sont soumis aux cotisations CNPS.",
         "The trainer's fees bear CNPS contributions.", False, "Faux : pas de contrat de travail, pas de bulletin de paie."),
    ):
        book.choice(module, "quiz", piece, fr, en, [("Vrai", "True", ok), ("Faux", "False", not ok)], why, why,
                    qtype="truefalse")
    inventory_questions(book, special)
    bridge_questions(book, special)
    for module in book.questions:
        split_usage(book.questions[module])


def inventory_questions(book, special):
    sheet = special["sheet"]
    for name, (family, sold, result, _account) in special["stock"].items():
        args = [[[int(q), int(u)] for q, u in family], int(sold)]
        for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré", "weighted average unit cost"),
                            ("valeur_sortie", "coût des sorties au CMUP", "cost of goods sold at WAC"),
                            ("valeur_stock", "valeur du stock final au CMUP", "closing stock at WAC")):
            book.numeric(6, "exam", result[key], f"{name.capitalize()} : {fr} ?", f"{name}: {en}?",
                         "CMUP de l'exercice, arrondi au franc ; calculateur stock.", "Period WAC, rounded.",
                         piece=sheet, calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
        peps = calculs.sortie_peps(family, D(sold))
        book.numeric(6, "exam", peps["valeur_sortie"], f"{name.capitalize()} : coût des sorties en PEPS (contraste) ?",
                     f"{name}: cost of goods sold under FIFO?", "Les lots les plus anciens sortent d'abord.",
                     "Oldest lots go first.", piece=sheet,
                     calcul={"fonction": "sortie_peps", "args": args, "resultat": ["valeur_sortie"]})
    book.journal(6, "exam", sheet, "Passez l'écriture du stock final.", "Record the closing stock.",
                 "Stocks 3111, 3112 et 3121 au débit, variation 6031 au crédit.", "Stock accounts debited, 6031 credited.")
    book.journal(6, "exam", special["schedule"], "Passez l'écriture des charges de clôture.", "Record the year-end charges.",
                 "Dotation 6813 et amortissement 2841 ; provision pour garantie : 6911 au débit, 192 au crédit.",
                 "Charge 6813 and depreciation 2841; warranty provision: 6911 debit, 192 credit.")
    book.numeric(6, "exam", special["dotation"], "Dotation 2026 de l'outillage (1 600 000 HT, 5 ans, depuis janvier) ?",
                 "2026 depreciation of the tools (1,600,000, 5 years, from January)?",
                 "Linéaire sur douze mois ; 20 %, le taux fiscal maximal des machines-outils légers (CGI art. 7).",
                 "Straight-line over twelve months; 20%, the maximum tax rate for light machine tools.",
                 piece=special["schedule"],
                 calcul={"fonction": "amortissement_lineaire", "args": [TOOLS_HT, 5, 1], "resultat": [0, "dotation"]})
    book.numeric(6, "exam", WARRANTY, "Montant de la provision pour garantie au 31 décembre ?",
                 "Warranty provision at 31 December?", "Neuf réparations déclarées, estimées à 50 000 chacune.",
                 "Nine reported repairs, estimated at 50,000 each.", piece=special["schedule"])
    book.numeric(6, "exam", special["closing_stock"], "Montant de la variation des stocks (6031) au 31 décembre ?",
                 "Change in inventories (6031) at 31 December?", "Premier exercice : égale au stock final.",
                 "First year: equals the closing stock.", piece=sheet)
    book.numeric(6, "exam", TOOLS_HT - special["dotation"], "Valeur nette comptable de l'outillage au 31 décembre ?",
                 "Net book value of the tools at 31 December?", "Coût HT moins amortissements.",
                 "Cost less depreciation.", piece=special["schedule"])
    for fr, en, choices, why in (
        ("Compte de la provision pour garantie ?", "Account for the warranty provision?",
         [("192", "192", True), ("191", "191", False), ("6911", "6911", False)],
         "192 Provisions pour garanties données aux clients ; 191 vise les litiges."),
        ("La provision pour garantie est-elle déductible ?", "Is the warranty provision deductible?",
         [("Oui : charge nettement précisée, probable et comptabilisée", "Yes: precise, probable and booked", True),
          ("Non, jamais", "No, never", False)], "CGI art. 7 E : conditions de déduction des provisions."),
        ("Taux fiscal maximal des machines-outils légers ?", "Maximum tax rate for light machine tools?",
         [("20 %", "20%", True), ("33,33 %", "33.33%", False)], "CGI art. 7 : 20 %."),
    ):
        book.choice(6, "exam", special["schedule"], fr, en, choices, why, why)
    book.choice(6, "quiz", sheet, "En période de hausse des prix, le PEPS donne un stock final plus élevé que le CMUP.",
                "When prices rise, FIFO gives a higher closing stock than WAC.",
                [("Vrai", "True", True), ("Faux", "False", False)], "Vrai.", "True.", qtype="truefalse")


def bridge_questions(book, special):
    tax, liq = special["tax"], special["liquidation"]
    book.numeric(7, "exam", tax["du"], "IS dû pour 2026 (le plus élevé de l'IS et du minimum) ?", "2026 CIT due?",
                 "IS au taux de 25 % (art. 17 bis), CAC compris, supérieur au minimum de perception.",
                 "CIT at 25%, above the minimum tax.", piece=liq, passerelle="impot_societes",
                 calcul={"fonction": "impot_societes", "args": [special["tax_result"], special["turnover"],
                                                                float(special["rate"]), 2, 10], "resultat": ["du"]})
    for value, fr, en, why, ref in (
        (special["accounting"], "Résultat comptable avant impôt 2026 ?", "2026 profit before tax?",
         "Produits moins charges des classes 6, 7 et 8.", liq),
        (special["tax_result"], "Résultat fiscal 2026 ?", "2026 taxable profit?",
         "Aucune réintégration : la provision pour garantie remplit les conditions de l'art. 7.", liq),
        (tax["minimum_total"], "Minimum de perception 2026, CAC compris ?", "2026 minimum tax?",
         "2 % du CA arrondi au millier inférieur, majoré de 10 %.", liq),
        (special["prepaid"], "Acomptes d'IS versés au titre de 2026 ?", "2026 CIT instalments?",
         "Somme des acomptes des douze déclarations.", liq),
        (tax["solde"], "Solde d'IS à payer avec la DSF ?", "CIT balance due with the return?",
         "IS dû moins acomptes versés.", liq),
        (special["turnover"], "Chiffre d'affaires HT 2026 (ventes et poses) ?", "2026 turnover?", "Comptes 7011 et 706.", liq),
        (special["net"], "Résultat net 2026 ?", "2026 net profit?", "Résultat avant impôt moins IS dû.", liq),
        (special["reserve"], "Dotation à la réserve légale décidée en juin 2027 ?", "Legal reserve allocation in June 2027?",
         "Un dixième au moins du bénéfice, plafonné au cinquième du capital (AUSCGIE art. 346).", special["meeting"]),
        (special["retained"], "Report à nouveau décidé en juin 2027 ?", "Retained earnings decided in June 2027?",
         "Bénéfice net moins réserve légale et dividendes.", special["meeting"]),
        (special["ircm"], "IRCM retenu sur les dividendes ?", "Withholding tax on dividends?",
         "15 % majorés de 10 % de CAC, soit 16,5 % des dividendes bruts (CGI art. 70).", special["payout"]),
        (DIVIDENDS - special["ircm"], "Dividendes nets versés aux associés ?", "Net dividends paid?",
         "Dividendes bruts moins IRCM.", special["payout"]),
        (int((DIVIDENDS - special["ircm"]) * 0.8), "Part nette du fonctionnaire associé (80 %) ?",
         "Net share of the civil-servant partner (80%)?", "80 % des dividendes nets.", special["payout"]),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref)
    for ref, fr, en, why_fr, why_en in (
        (liq, "Passez l'écriture de l'IS de l'exercice.", "Record the CIT for the year.", "Impôt 891, État 441.",
         "Tax 891, State 441."),
        (special["meeting"], "Passez l'écriture d'affectation du résultat.", "Record the appropriation of profit.",
         "Bénéfice 131 au débit ; réserve légale 111, dividendes à payer 465 et report à nouveau 121 au crédit.",
         "Profit 131 debit; legal reserve 111, dividends payable 465 and retained earnings 121 credit."),
        (special["payout"], "Passez l'écriture de la mise en paiement des dividendes.", "Record the dividend payment.",
         "Dividendes à payer 465 au débit ; IRCM retenu en 4478, banque 521 pour le net.",
         "Dividends payable 465 debit; withholding 4478, bank 521 for the net."),
        (special["ircm_paid"], "Passez l'écriture du reversement de l'IRCM.", "Record paying over the withholding tax.",
         "4478 soldé par la banque.", "4478 cleared by the bank."),
    ):
        book.journal(7, "exam", ref, fr, en, why_fr, why_en)
    for fr, en, qtype, choices, why in (
        ("Date limite de dépôt de la DSF 2026 (CIME) ?", "Filing deadline (MTO)?", "single",
         [("15 avril 2027", "15 April 2027", True), ("15 mars 2027", "15 March 2027", False)], "CGI art. 18 (1)."),
        ("Délai de réunion de l'assemblée annuelle d'une SARL ?", "Deadline for the annual meeting of an LLC?", "single",
         [("Six mois après la clôture", "Six months after year end", True), ("Un an", "One year", False)],
         "AUSCGIE art. 348."),
        ("Les dividendes sont une charge déductible.", "Dividends are a deductible expense.", "truefalse",
         [("Vrai", "True", False), ("Faux", "False", True)], "Faux : ils répartissent le bénéfice après impôt."),
        ("L'IRCM est exigible à la mise à disposition des dividendes.", "The withholding tax is due when dividends are "
         "made available.", "truefalse", [("Vrai", "True", True), ("Faux", "False", False)], "Vrai (CGI art. 70)."),
        ("La réserve légale reste obligatoire au-delà du cinquième du capital.", "The legal reserve stays compulsory "
         "above one fifth of capital.", "truefalse", [("Vrai", "True", False), ("Faux", "False", True)],
         "Faux : la dotation cesse d'être obligatoire à ce seuil (AUSCGIE art. 346)."),
        ("Ici, l'IS l'emporte sur le minimum de perception.", "Here CIT exceeds the minimum tax.", "truefalse",
         [("Vrai", "True", True), ("Faux", "False", False)], "Vrai : la marge est suffisante, contrairement au dépôt B3."),
    ):
        book.choice(7, "quiz", liq, fr, en, choices, why, why, qtype=qtype)


MODULES = [
    ("Création et janvier", "Set-up and January", "Créer la SARL, s'équiper et tenir le premier mois.",
     "Create the company, equip it and keep the first month."),
    ("Premier trimestre (février et mars)", "First quarter (February and March)", "Tenir ventes, poses et déclarations.",
     "Keep sales, installations and returns."),
    ("Deuxième trimestre", "Second quarter", "Rémunérer le formateur fonctionnaire.", "Pay the civil-servant trainer."),
    ("Troisième trimestre", "Third quarter", "Suivre la hausse des prix d'achat.", "Follow rising purchase prices."),
    ("Quatrième trimestre", "Fourth quarter", "Préparer la clôture.", "Prepare the year end."),
    ("Inventaire", "Year-end inventory", "Valoriser le stock, amortir, provisionner la garantie.",
     "Value stock, depreciate, provide for warranties."),
    ("Passerelle, DSF et dividendes", "Tax bridge, return and dividends", "Liquider l'IS et affecter le résultat.",
     "Compute CIT and appropriate profit."),
]


def sections(book, special):
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    kinds = {p["ref"]: p["kind"] for p in book.pieces}
    out = {m: [] for m in range(1, 8)}
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file", narrative_c.company_file("fr"),
                   narrative_c.company_file("en")))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   "Chaque démarche précise l'organisme, les documents et ce que l'on obtient [[cgi:art. L 1]].\n\n"
                   f"{proc}\n", f"Each procedure gives the body, documents and outcome [[cgi:art. L 1]].\n\n{proc}\n"))
    special["why"] = {}
    for month in range(1, 13):
        module = MODULE_OF_MONTH[month]
        opening = [ref for ref in by_month[month] if kinds[ref] == "balance"]
        scenes = narrative_c.month_scenes(book, special, month)
        told = {s["ref"] for s in scenes}
        others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
        special["why"].update({s["ref"]: s["why"] for s in scenes})
        out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}",
                            narrative_c.month_section(month, scenes, opening, others, "fr"),
                            narrative_c.month_section(month, scenes, opening, others, "en")))
    told, why = narrative_c.year_end_sections(book, special)
    special["why"].update(why)
    out[6].append(("01-inventaire", "Inventaire au 31 décembre", "Year-end inventory", told["inventory"]["fr"],
                   told["inventory"]["en"]))
    out[7].append(("01-passerelle", "Passerelle fiscale", "Tax bridge", told["bridge"]["fr"], told["bridge"]["en"]))
    out[7].append(("02-dsf", "DSF 2026", "2026 return", told["dsf"]["fr"], told["dsf"]["en"]))
    out[7].append(("03-dividendes", "Assemblée et dividendes 2027", "2027 meeting and dividends",
                   told["dividends"]["fr"], told["dividends"]["en"]))
    return out


def main():
    from tools.simulation.build_parcours_a import explain

    book, special = build()
    balances(book)
    build_questions(book, special)
    module_sections = sections(book, special)
    explain(book, special["why"])
    modules = []
    for number, (title_fr, title_en, comp_fr, comp_en) in enumerate(MODULES, start=1):
        folder = f"c/m{number}"
        entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": text(comp_fr, comp_en), "sections": entries})
    write(OUT / "c" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "c" / "ledger.json", book.entries)
    partie = {
        "slug": "c", "title": text("Parcours C : électronique et pose de climatiseurs (Tech Clim Bonamoussadi SARL)",
                                   "Track C: electronics and air-conditioner installation (Tech Clim Bonamoussadi SARL)"),
        "description": text("SARL au réel à Douala, rattachée au CIME : ventes d'appareils, poses, associé fonctionnaire, "
                            "dividendes.", "LLC under the actual regime in Douala: appliance sales, installations, "
                            "civil-servant partner, dividends."),
        "centre_impots": "cime", "chiffre_affaires_vise": 120000000,
        "sous_comptes": {"5522": text("Orange Money", "Orange Money")},
        "pieces": "c/pieces.json", "ledger": "c/ledger.json", "exam": {"questions_per_module": 4}, "modules": modules}
    write_manifest({}, partie)
    low = min(ledger.account_balance(book.entries, "521", datetime.date.fromisoformat(e["date"])) for e in book.entries)
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, "
          f"résultat {special['accounting']}, IS {special['tax']}, net {special['net']}, banque au plus bas {low}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
