"""Génère le parcours B3 de la simulation (Ateba Boissons SARL, exercice 2026) dans content/simulation/b3/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_b3

Dépôt de boissons, SARL au réel rattachée au CIME de Yaoundé (profil validé le 2026-11-01, S32). Achats auprès d'une
brasserie fictive, accises comprises dans le prix (CGI art. 142 (9)), TVA déductible et précompte de 2 % (art. 21 (3)) ;
consignes d'emballages reçues (4094) et facturées (4194), mali (6224) et boni (7074) au retour des vides (Guide
SYSCOHADA, 1re partie, ch. 2, § 4.2) ; casiers propres immobilisés en 243 ; camion 2451 financé par un emprunt de
12 000 000 (162) ; IS comparé au minimum de perception. Tout est calculé par referentiel/calculs.py et
tools/simulation/ledger.py ; les contrôles bloquants de courses/tests/content_rules.py vérifient la sortie.
"""
import calendar
import datetime
from decimal import Decimal as D

from referentiel import calculs
from tools.simulation import ledger, narrative_b3
from tools.simulation.build_parcours_a import (
    MONTHS_EN, MONTHS_FR, OUT, P, YEAR, Book, balances, d, fcfa, line, payroll, piece_list, settle, split_usage, text,
    tva, workday, write, write_manifest,
)

SELLER = {"name": "Ateba Boissons SARL", "niu": "M012600011582R", "rccm": "RC/YAO/2026/B/0342", "regime": "réel",
          "centre": "CIME Yaoundé", "address": "Mvog-Ada, Yaoundé"}
BREWERY = {"name": "Brasseries de la Sanaga SA (fictive)", "niu": "M019800000731S", "rccm": "RC/YAO/1998/B/0071",
           "regime": "réel", "centre": "DGE", "address": "Zone industrielle de Nsam, Yaoundé"}
CRATES = {"name": "Plasti-Centre SARL", "niu": "M011500003318K", "rccm": "RC/YAO/2015/B/0629", "regime": "réel",
          "centre": "CIME Yaoundé", "address": "Mvan, Yaoundé"}
NOTARY = {"name": "Étude de Maître Abena, notaire", "niu": "P011100004472N", "rccm": "Office notarial n° 7",
          "regime": "réel", "centre": "CIME Yaoundé", "address": "Avenue Kennedy, Yaoundé"}
GARAGE = {"name": "Centre Poids Lourds du Mfoundi SARL", "niu": "M010800002956G", "rccm": "RC/YAO/2008/B/1144",
          "regime": "réel", "centre": "CIME Yaoundé", "address": "Olembé, Yaoundé"}
CLIENT = {"name": "Snack-Bar Le Rond-Point SARL", "niu": "M011400007265B"}
OWN = {"name": SELLER["name"], "niu": SELLER["niu"]}
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}

# Formats : casier de 12 bouteilles de 65 cl et casier de 24 bouteilles de 33 cl ; accises par casier (art. 142 (9)).
FORMATS = {"65": {"fr": "Bière 65 cl, casier de 12", "en": "65 cl beer, crate of 12", "bottles": 12,
                  "excise": "accises.biere_65cl", "stock": "3111", "buy": (6100, 6160), "sell": 6580, "deposit": 3600},
           "33": {"fr": "Bière 33 cl, casier de 24", "en": "33 cl beer, crate of 24", "bottles": 24,
                  "excise": "accises.biere_33cl", "stock": "3112", "buy": (7500, 7560), "sell": 8200, "deposit": 4800}}
BUY_QTY = {"65": 3050, "33": 520}
SALES_QTY = {"credit": {"65": 120, "33": 30}, "cash": {"65": 1800, "33": 300}, "orange": {"65": 1080, "33": 170}}
STAFF = [("Gérant salarié", "Salaried manager", 350000), ("Magasinier", "Storekeeper", 150000),
         ("Chauffeur-livreur", "Delivery driver", 180000)]
RENT, CAPITAL, LOAN, TRUCK_HT, CRATES_QTY, CRATE_PRICE = 250000, 10000000, 12000000, 18000000, 400, 2500
LOAN_MONTHS, LOAN_RATE = 36, D(12)  # emprunt sur 3 ans, 12 % l'an, capital constant, premier remboursement en mars
MALI = (6, "65", 20, 3000)   # juin : 20 casiers de 65 cl abîmés repris 3 000 au lieu de 3 600 par la brasserie
BONI = (9, "65", 30, 3000)   # septembre : 30 casiers abîmés repris 3 000 au lieu de 3 600 au snack-bar
FINE, NO_RECEIPT, DONATION = 25000, 60000, 1500000
OM_FEE, BANK_FEE = 8500, 3500


def last(month):
    return calendar.monthrange(YEAR, month)[1]


def buy_price(fmt, month):
    return FORMATS[fmt]["buy"][0 if month <= 6 else 1]


def excise(fmt):
    return int(P[FORMATS[fmt]["excise"]] * FORMATS[fmt]["bottles"])


def sale_lines(qty):
    return [{"label": text(FORMATS[f]["fr"], FORMATS[f]["en"]), "qty": q, "unit_price": FORMATS[f]["sell"],
             "amount": q * FORMATS[f]["sell"]} for f, q in qty.items()]


def piece_of(book, ref):
    return next(p for p in book.pieces if p["ref"] == ref)


def taxes_totals(ht):
    taxes = tva(ht)
    return taxes, [{"label": text("Total HT", "Total excl. tax"), "role": "ht", "amount": int(ht)},
                   {"label": text("TVA 17,5 %", "VAT 17.5%"), "role": "tax", "amount": int(taxes["tva"])},
                   {"label": text("CAC 10 % de la TVA", "Council cents 10% of VAT"), "role": "tax",
                    "amount": int(taxes["cac"])}]


PROCEDURES = [
    ("Création de la SARL au CFCE de Yaoundé", "Creating the LLC at the Yaoundé business centre",
     text("Centre de formalités de création d'entreprises (CFCE) de Yaoundé", "Yaoundé business formalities centre"),
     text("Créer la SARL ; capital de 10 000 000 FCFA, au-delà du seuil d'un million : statuts notariés",
          "Create the LLC; 10,000,000 FCFA capital, above one million: notarised articles"),
     [text("Statuts établis par le notaire et déclarations de régularité et de conformité",
           "Notarised articles and declarations of regularity and conformity"),
      text("Extraits de casier judiciaire des associés et du gérant, ou déclaration sur l'honneur",
           "Criminal records of partners and manager, or sworn statement"),
      text("Photocopie de la CNI de chaque associé et du gérant", "ID copies of partners and manager"),
      text("Plan de localisation, boîte postale, contact téléphonique", "Location map, PO box, phone number"),
      text("Frais de création et d'annonce légale (à vérifier au CFCE)", "Creation and legal notice fees (check)")],
     text("Registre de commerce, carte de contribuable (NIU), attestation de création",
          "Trade register, taxpayer card (NIU), creation certificate"),
     "[[source:loi-2016-014]] [[source:minfi-cfce]]"),
    ("Rattachement fiscal au CIME de Yaoundé", "Tax office attachment (Yaoundé medium-sized taxpayers)",
     text("Direction générale des impôts, CIME de Yaoundé", "Directorate General of Taxation, Yaoundé MTO"),
     text("Suivi fiscal d'une entreprise dont le CA visé (environ 280 millions) est compris entre 50 millions et "
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
      text("Copie du registre de commerce ou des statuts, patente, carte de contribuable",
           "Copy of trade register or articles, business licence, taxpayer card"),
      text("Plan de localisation et liste du personnel", "Location map and staff list"),
      text("Pour chaque salarié : avis d'embauche et copie certifiée de l'acte de naissance ou de la CNI",
           "For each employee: hiring notice and certified birth certificate or ID")],
     text("Numéro d'employeur et numéros d'assurés", "Employer number and employee numbers"), "[[source:cnps-faq]]"),
    ("Ouverture du compte bancaire de l'entreprise", "Opening the company bank account",
     text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
     text("Ouvrir le compte de l'entreprise, puis y recevoir l'emprunt du camion", "Open the account, then receive the truck loan"),
     [text("Demande d'ouverture de compte", "Account opening request"),
      text("Registre de commerce, carte de contribuable, plan de localisation", "Trade register, taxpayer card, map"),
      text("Pièces d'identité du gérant, statuts, procès-verbal de nomination du gérant",
           "Manager's ID, articles, minutes appointing the manager")],
     text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
    ("Compte marchand Orange Money", "Orange Money merchant account",
     text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
     text("Encaisser les ventes des bars par Orange Money", "Collect bar sales through Orange Money"),
     [text("Registre de commerce, carte de contribuable, patente", "Trade register, taxpayer card, licence"),
      text("Statuts, CNI du gérant ou d'un mandataire", "Articles, ID of the manager or proxy"),
      text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)")],
     text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
]


def build():
    book, special = Book("B3"), {"months": {}}
    staff = payroll(STAFF)
    pay = {k: sum(r[k] for r in staff) for k in ("gross", "cnps", "irpp", "rav", "tdl", "cfc", "net", "cfc_pat", "cnps_pat")}
    salary_taxes = pay["irpp"] + pay["rav"] + pay["tdl"] + pay["cfc"] + pay["cfc_pat"]
    special["procedures"] = [book.piece(1, "demarche", d(1, 2), f"Démarche : {fr}", f"Procedure: {en}",
                                        {"organisme": body, "objet": purpose, "documents_a_fournir": docs,
                                         "document_obtenu": got, "source": source})
                             for fr, en, body, purpose, docs, got, source in PROCEDURES]

    # Jour 1 : capital, frais de constitution en charges (S6), casiers propres immobilisés (243).
    special["capital"] = book.piece(1, "releve_bancaire", d(1, 2), "Attestation de dépôt du capital (Banque X)",
                                    "Capital deposit certificate (Bank X)",
                                    {"fields": [{"label": text("Déposant", "Depositor"), "value": SELLER["name"]}],
                                     "totals": [{"label": text("Capital libéré", "Paid-up capital"), "amount": CAPITAL}]})
    book.entry(d(1, 2), special["capital"], line("521", "debit", CAPITAL), line("1013", "credit", CAPITAL))
    fees, duties = 300000, 50000
    fee_tax = tva(fees)
    special["notary"] = book.piece(1, "facture_achat", d(1, 6), "Facture du notaire (statuts)", "Notary's invoice (articles)",
                                   {"issuer": NOTARY, "customer": OWN, "number": "AB-2026-0009",
                                    "einvoice": "DGI-SFE-2026-003109",
                                    "lines": [{"label": text("Honoraires de rédaction des statuts", "Drafting fees"),
                                               "amount": fees},
                                              {"label": text("Débours : droits d'enregistrement", "Registration duties"),
                                               "amount": duties}],
                                    "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht",
                                                "amount": fees + duties},
                                               {"label": text("TVA et CAC sur les honoraires", "VAT and council cents on fees"),
                                                "role": "tax", "amount": int(fee_tax["taxes"])},
                                               {"label": text("Net payé par virement", "Net paid by transfer"), "role": "ttc",
                                                "amount": int(fees + duties + fee_tax["taxes"])}]})
    book.entry(d(1, 6), special["notary"], line("6324", "debit", fees), line("4454", "debit", fee_tax["taxes"]),
               line("646", "debit", duties), line("521", "credit", fees + duties + fee_tax["taxes"]))
    crates_ht = CRATES_QTY * CRATE_PRICE
    crates_tax, crates_totals = taxes_totals(crates_ht)
    special["crates"] = book.piece(1, "facture_achat", d(1, 6), "Facture Plasti-Centre : casiers propres",
                                   "Plasti-Centre invoice: own crates",
                                   {"issuer": CRATES, "customer": OWN, "number": "PC-2026-0031",
                                    "einvoice": "DGI-SFE-2026-003131",
                                    "lines": [{"label": text("Casiers vides marqués Ateba Boissons", "Empty crates marked "
                                                             "Ateba Boissons"), "qty": CRATES_QTY,
                                               "unit_price": CRATE_PRICE, "amount": crates_ht}],
                                    "totals": crates_totals + [{"label": text("Net payé par virement", "Net paid by transfer"),
                                                                "role": "ttc", "amount": int(crates_tax["ttc"])}]})
    book.entry(d(1, 6), special["crates"], line("243", "debit", crates_ht), line("4451", "debit", crates_tax["taxes"]),
               line("521", "credit", crates_tax["ttc"]))

    lots = {f: [] for f in FORMATS}
    unpaid = {"brewery": 0, "client": 0}
    outstanding = LOAN
    for month in range(1, 13):
        end, refs = last(month), {}
        mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {mfr} (Banque X)",
                                  f"{men} bank statement (Bank X)", {})
        bank_rows = []
        if month == 2:
            special["loan"] = book.piece(2, "releve_bancaire", workday(2, 1), "Avis de crédit : déblocage de l'emprunt du camion",
                                         "Credit notice: truck loan drawdown",
                                         {"fields": [{"label": text("Durée et taux", "Term and rate"),
                                                      "value": text("36 mois, 12 % l'an, capital constant",
                                                                    "36 months, 12% a year, equal principal")}],
                                          "totals": [{"label": text("Montant prêté", "Amount lent"), "amount": LOAN}]})
            book.entry(workday(2, 1), special["loan"], line("521", "debit", LOAN), line("162", "credit", LOAN))
            truck_tax, truck_totals = taxes_totals(TRUCK_HT)
            special["truck"] = book.piece(2, "facture_achat", d(2, 3), "Facture du camion de livraison",
                                          "Delivery truck invoice",
                                          {"issuer": GARAGE, "customer": OWN, "number": "CPL-2026-0058",
                                           "einvoice": "DGI-SFE-2026-003258",
                                           "lines": [{"label": text("Camion porteur 10 t, mise en service le 3 février",
                                                                    "10 t truck, in service from 3 February"),
                                                      "qty": 1, "unit_price": TRUCK_HT, "amount": TRUCK_HT}],
                                           "totals": truck_totals + [{"label": text("Net à payer", "Amount due"),
                                                                      "role": "ttc", "amount": int(truck_tax["ttc"])}]})
            book.entry(d(2, 3), special["truck"], line("2451", "debit", TRUCK_HT), line("4451", "debit", truck_tax["taxes"]),
                       line("4812", "credit", truck_tax["ttc"]))
            book.entry(d(2, 6), refs["bank"], line("4812", "debit", truck_tax["ttc"]), line("521", "credit", truck_tax["ttc"]))
            bank_rows.append((text("Virement au Centre Poids Lourds du Mfoundi", "Transfer to the truck dealer"),
                              int(truck_tax["ttc"])))
        # Loyer de l'entrepôt (précompte de 10 % retenu, CGI art. 87).
        withheld = calculs.franc(D(RENT) * P["precompte.taux_loyer"] / 100)
        refs["rent"] = book.piece(month, "recu_caisse", workday(month, 6 if month == 1 else 2), f"Quittance de loyer de l'entrepôt, {mfr}",
                                  f"{men} warehouse rent receipt",
                                  {"fields": [{"label": text("Bailleur", "Landlord"), "value": "Mme Owona (fictive)"}],
                                   "totals": [{"label": text("Loyer brut", "Gross rent"), "amount": RENT},
                                              {"label": text("Précompte sur loyer 10 % retenu", "10% rent withholding"),
                                               "amount": int(withheld)},
                                              {"label": text("Net versé par virement", "Net paid by transfer"),
                                               "amount": int(RENT - withheld)}]})
        book.entry(workday(month, 6 if month == 1 else 2), refs["rent"], line("6222", "debit", RENT), line("4478", "credit", withheld),
                   line("521", "credit", RENT - withheld))
        # Règlements : la facture de la brasserie du mois précédent en fin de mois, celle du snack-bar le 10.
        if unpaid["brewery"]:
            book.entry(d(month, end), refs["bank"], line("401", "debit", unpaid["brewery"]),
                       line("521", "credit", unpaid["brewery"]))
            bank_rows.append((text("Virement aux Brasseries de la Sanaga", "Transfer to the brewery"), unpaid["brewery"]))
        if unpaid["client"]:
            book.entry(d(month, 10), refs["bank"], line("521", "debit", unpaid["client"]),
                       line("411", "credit", unpaid["client"]))
            bank_rows.append((text("Virement reçu du Snack-Bar Le Rond-Point", "Transfer from the snack bar"),
                              unpaid["client"]))
        # Facture de la brasserie : accises comprises, précompte 2 %, consigne des casiers livrés, déconsigne des vides.
        lines_, ht = [], 0
        for f, qty in BUY_QTY.items():
            unit = buy_price(f, month)
            lots[f].append((qty, unit))
            lines_.append({"label": text(FORMATS[f]["fr"], FORMATS[f]["en"]), "qty": qty, "unit_price": unit,
                           "amount": qty * unit})
            ht += qty * unit
        taxes, totals = taxes_totals(ht)
        precompte = calculs.franc(D(ht) * P["precompte.taux_reel"] / 100)
        consign = sum(q * FORMATS[f]["deposit"] for f, q in BUY_QTY.items())
        returned = {f: sum(SALES_QTY[c][f] for c in SALES_QTY) for f in FORMATS} if month > 1 else {}
        deconsign = sum(q * FORMATS[f]["deposit"] for f, q in returned.items())
        mali = MALI[2] * (FORMATS[MALI[1]]["deposit"] - MALI[3]) if month == MALI[0] else 0
        due = ht + taxes["taxes"] + precompte + consign - deconsign + mali
        excises = sum(q * excise(f) for f, q in BUY_QTY.items())
        totals += [{"label": text("Précompte sur achats 2 %", "2% purchase withholding"), "role": "tax",
                    "amount": int(precompte)},
                   {"label": text("Total TTC et précompte", "Total incl. tax and withholding"), "role": "ttc",
                    "amount": int(ht + taxes["taxes"] + precompte)},
                   {"label": text("Consigne des casiers livrés", "Deposit on crates delivered"), "amount": int(consign)}]
        if deconsign:
            totals.append({"label": text("Déconsigne des vides rendus", "Deposit refunded on empties returned"),
                           "amount": int(deconsign)})
        if mali:
            totals.append({"label": text("Retenue pour 20 casiers abîmés (600 par casier)",
                                         "Withheld for 20 damaged crates (600 each)"), "amount": int(mali)})
        totals.append({"label": text("Net à payer à la fin du mois suivant", "Net payable at the end of next month"),
                       "amount": int(due)})
        refs["purchase"] = book.piece(month, "facture_achat", workday(month, 5), f"Facture des Brasseries de la Sanaga, {mfr}",
                                      f"Brewery invoice, {men}",
                                      {"issuer": BREWERY, "customer": OWN, "number": f"BS-2026-{4000 + month:05d}",
                                       "einvoice": f"DGI-SFE-2026-{5100 + month:06d}",
                                       "fields": [{"label": text("Dont droit d'accises spécifique additionnel compris dans le prix (CGI art. 142 (9)), en FCFA",
                                                                 "Of which additional specific excise included in the price, FCFA"),
                                                   "value": fcfa(excises)},
                                                  {"label": text("Vides rendus (casiers 65 cl / 33 cl)",
                                                                 "Empties returned (65 cl / 33 cl crates)"),
                                                   "value": f"{returned.get('65', 0)} / {returned.get('33', 0)}"}],
                                       "lines": lines_, "totals": totals})
        purchase_lines = [line("6011", "debit", ht), line("4452", "debit", taxes["taxes"]),
                          line("4492", "debit", precompte), line("4094", "debit", consign)]
        if deconsign:
            purchase_lines.append(line("4094", "credit", deconsign))
        if mali:
            purchase_lines.append(line("6224", "debit", mali))
        purchase_lines.append(line("401", "credit", due))
        book.entry(workday(month, 5), refs["purchase"], *purchase_lines)
        unpaid["brewery"] = int(due)
        refs["excises"] = excises
        # Facture du snack-bar : vente à crédit, consigne facturée (4194), déconsigne des vides rendus, boni éventuel.
        qty = SALES_QTY["credit"]
        sale_ht = sum(q * FORMATS[f]["sell"] for f, q in qty.items())
        sale_tax, sale_totals = taxes_totals(sale_ht)
        consign_out = sum(q * FORMATS[f]["deposit"] for f, q in qty.items())
        back = consign_out if month > 1 else 0
        boni = BONI[2] * (FORMATS[BONI[1]]["deposit"] - BONI[3]) if month == BONI[0] else 0
        client_due = sale_ht + sale_tax["taxes"] + consign_out - back + boni
        sale_totals += [{"label": text("Total TTC", "Total incl. tax"), "role": "ttc", "amount": int(sale_tax["ttc"])},
                        {"label": text("Consigne des casiers livrés", "Deposit on crates delivered"),
                         "amount": int(consign_out)}]
        if back:
            sale_totals.append({"label": text("Déconsigne des vides rendus", "Deposit refunded on empties returned"),
                                "amount": int(back)})
        if boni:
            sale_totals.append({"label": text("Retenue pour 30 casiers abîmés (600 par casier)",
                                              "Withheld for 30 damaged crates (600 each)"), "amount": int(boni)})
        sale_totals.append({"label": text("Net à payer à 30 jours", "Net payable at 30 days"), "amount": int(client_due)})
        refs["sale"] = book.piece(month, "facture_vente", workday(month, 20), f"Facture au Snack-Bar Le Rond-Point, {mfr}",
                                  f"Invoice to the snack bar, {men}",
                                  {"issuer": SELLER, "customer": CLIENT, "number": f"AB-2026-{month:04d}",
                                   "einvoice": f"DGI-SFE-2026-{6200 + month:06d}", "lines": sale_lines(qty),
                                   "totals": sale_totals})
        sale_entry = [line("411", "debit", client_due), line("7011", "credit", sale_ht),
                      line("4431", "credit", sale_tax["taxes"]), line("4194", "credit", consign_out)]
        if back:
            sale_entry.append(line("4194", "debit", back))
        if boni:
            sale_entry.append(line("7074", "credit", boni))
        book.entry(workday(month, 20), refs["sale"], *sale_entry)
        unpaid["client"] = int(client_due)
        # Ventes au comptant (échange des vides, sans consigne) et par Orange Money.
        cash_ht = sum(q * FORMATS[f]["sell"] for f, q in SALES_QTY["cash"].items())
        cash_tax = tva(cash_ht)
        refs["cash"] = book.piece(month, "recu_caisse", d(month, end), f"Récapitulatif des ventes au comptant de {mfr}",
                                  f"{men} cash sales summary",
                                  {"lines": sale_lines(SALES_QTY["cash"]),
                                   "totals": [{"label": text("Ventes HT", "Sales excl. tax"), "role": "ht", "amount": cash_ht},
                                              {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                               "amount": int(cash_tax["taxes"])},
                                              {"label": text("Ventes TTC encaissées", "Sales incl. tax collected"),
                                               "role": "ttc", "amount": int(cash_tax["ttc"])}]})
        book.entry(d(month, end), refs["cash"], line("5711", "debit", cash_tax["ttc"]), line("7011", "credit", cash_ht),
                   line("4431", "credit", cash_tax["taxes"]))
        om_ht = sum(q * FORMATS[f]["sell"] for f, q in SALES_QTY["orange"].items())
        om_tax = tva(om_ht)
        refs["orange"] = book.piece(month, "releve_momo", d(month, end), f"Relevé Orange Money de {mfr}",
                                    f"Orange Money statement, {men}",
                                    {"totals": [{"label": text("Encaissements HT", "Receipts excl. tax"), "role": "ht",
                                                 "amount": om_ht},
                                                {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                                 "amount": int(om_tax["taxes"])},
                                                {"label": text("Encaissements TTC", "Receipts incl. tax"), "role": "ttc",
                                                 "amount": int(om_tax["ttc"])},
                                                {"label": text("Frais de l'opérateur", "Operator fees"), "amount": OM_FEE},
                                                {"label": text("Transfert vers la banque", "Transfer to the bank"),
                                                 "amount": int(om_tax["ttc"] - OM_FEE)}]})
        book.entry(d(month, end), refs["orange"], line("5522", "debit", om_tax["ttc"]), line("7011", "credit", om_ht),
                   line("4431", "credit", om_tax["taxes"]), line("631", "debit", OM_FEE), line("5522", "credit", OM_FEE),
                   line("585", "debit", om_tax["ttc"] - OM_FEE), line("5522", "credit", om_tax["ttc"] - OM_FEE))
        # Paie du mois, virée par la banque.
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
        bank_rows.append((text("Salaires nets virés", "Net pay transferred"), int(pay["net"])))
        # Déclaration du 15 du mois précédent (US-85).
        if month > 1:
            refs["settlement"] = settle(book, month - 1, d(month, 15), month)
        # Remboursement de l'emprunt (capital constant, intérêts sur le capital restant dû), de mars à décembre.
        if month >= 3:
            principal = LOAN // LOAN_MONTHS
            interest = int(calculs.franc(D(outstanding) * LOAN_RATE / 100 / 12))
            outstanding -= principal
            book.entry(d(month, 28), refs["bank"], line("162", "debit", principal), line("6712", "debit", interest),
                       line("521", "credit", principal + interest))
            bank_rows.append((text("Échéance de l'emprunt (capital et intérêts)", "Loan instalment (principal and interest)"),
                              principal + interest))
            special.setdefault("interest", 0)
            special["interest"] += interest
        events(book, month, special)
        # Versement des espèces du mois en banque (S19 : virements internes par 585), puis relevé bancaire.
        cash_left = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, end))
        refs["cash_out"] = book.piece(month, "recu_caisse", d(month, end), f"Bordereau de versement des espèces de {mfr}",
                                      f"{men} cash deposit slip",
                                      {"totals": [{"label": text("Espèces versées à la banque", "Cash deposited"),
                                                   "amount": int(cash_left)}]})
        book.entry(d(month, end), refs["cash_out"], line("585", "debit", cash_left), line("5711", "credit", cash_left))
        transfers = cash_left + om_tax["ttc"] - OM_FEE
        book.entry(d(month, end), refs["bank"], line("521", "debit", transfers), line("585", "credit", transfers),
                   line("631", "debit", BANK_FEE), line("521", "credit", BANK_FEE))
        bank_rows += [(text("Virements internes reçus (espèces et Orange Money)", "Internal transfers received"),
                       int(transfers)), (text("Frais de tenue de compte", "Account fees"), BANK_FEE)]
        piece_of(book, refs["bank"])["payload"] = {"totals": [{"label": label, "amount": amount}
                                                              for label, amount in bank_rows]}
        special["months"][month] = refs
    special["outstanding"] = outstanding
    year_end(book, special, lots)
    special["staff"] = staff
    return book, special


def events(book, month, special):
    """Pièces ponctuelles de la passerelle (S32) : amende de circulation, charge sans pièce, don."""
    if month == 5:
        ref = book.piece(5, "recu_caisse", d(5, 14), "Quittance d'amende de circulation du camion (fictive)",
                         "Traffic fine receipt for the truck (fictitious)",
                         {"fields": [{"label": text("Motif", "Reason"), "value": text("Surcharge à l'essieu",
                                                                                       "Axle overload")}],
                          "totals": [{"label": text("Amende payée par virement", "Fine paid by transfer"), "amount": FINE}]})
        book.entry(d(5, 14), ref, line("6478", "debit", FINE), line("521", "credit", FINE))
        special["fine"] = ref
    if month == 8:
        ref = book.piece(8, "recu_caisse", d(8, 19), "Bon de caisse interne sans justificatif externe",
                         "Internal cash voucher without external receipt",
                         {"totals": [{"label": text("Dépense en espèces", "Cash expense"), "amount": NO_RECEIPT}]})
        book.entry(d(8, 19), ref, line("6588", "debit", NO_RECEIPT), line("5711", "credit", NO_RECEIPT))
        special["no_receipt"] = ref
    if month == 10:
        ref = book.piece(10, "recu_caisse", d(10, 9), "Reçu de don d'une association d'intérêt général (fictive)",
                         "Donation receipt from a public-interest association (fictitious)",
                         {"totals": [{"label": text("Don versé par virement", "Donation paid by transfer"),
                                      "amount": DONATION}]})
        book.entry(d(10, 9), ref, line("6582", "debit", DONATION), line("521", "credit", DONATION))
        special["donation"] = ref


def year_end(book, special, lots):
    """Inventaire (CMUP par format), amortissements, déclaration de décembre, passerelle, IS et DSF (S12, S22)."""
    sold = {f: 12 * sum(SALES_QTY[c][f] for c in SALES_QTY) for f in FORMATS}
    sheet_lines, fields = [], []
    for f in FORMATS:
        bought = sum(q for q, _ in lots[f])
        fields.append({"label": text(f"{FORMATS[f]['fr']} : achetés, vendus, inventaire physique",
                                     f"{FORMATS[f]['en']}: bought, sold, physical count"),
                       "value": f"{bought} / {sold[f]} / {bought - sold[f]}"})
        sheet_lines += [{"label": text(f"{FORMATS[f]['fr']}, lot {i}", f"{FORMATS[f]['en']}, lot {i}"), "qty": q,
                         "unit_price": u, "amount": q * u} for i, (q, u) in enumerate(lots[f], start=1)]
    sheet = book.piece(12, "fiche_stock", d(12, 31), "Fiche de stock CMUP des deux formats", "WAC stock card, both formats",
                       {"fields": fields, "lines": sheet_lines})
    stock = {}
    for f in FORMATS:
        family = [(D(q), D(u)) for q, u in lots[f]]
        stock[f] = (family, sold[f], calculs.sortie_cmup(family, D(sold[f])))
    book.entry(d(12, 31), sheet, *[line(FORMATS[f]["stock"], "debit", stock[f][2]["valeur_stock"]) for f in FORMATS],
               line("6031", "credit", sum(stock[f][2]["valeur_stock"] for f in FORMATS)))
    truck = int(calculs.amortissement_lineaire(D(TRUCK_HT), 5, 2)[0]["dotation"])
    crates = int(calculs.amortissement_lineaire(D(CRATES_QTY * CRATE_PRICE), 5, 1)[0]["dotation"])
    schedule = book.piece(12, "fiche_stock", d(12, 31), "Tableau des amortissements 2026", "2026 depreciation schedule",
                          {"lines": [{"label": text("Camion (5 ans, depuis février : 11 mois)",
                                                    "Truck (5 years, from February: 11 months)"), "amount": truck},
                                     {"label": text("Casiers propres (5 ans, depuis janvier)",
                                                    "Own crates (5 years, from January)"), "amount": crates}],
                           "totals": [{"label": text("Dotations 2026", "2026 charges"), "role": "ht",
                                       "amount": truck + crates}]})
    book.entry(d(12, 31), schedule, line("6813", "debit", truck), line("2845", "credit", truck),
               line("6813", "debit", crates), line("2843", "credit", crates))
    special.update(sheet=sheet, stock=stock, schedule=schedule, truck_dotation=truck, crates_dotation=crates)
    special["months"][12]["settlement_next"] = settle(book, 12, d(1, 15, YEAR + 1), 13)
    entries_2026 = [e for e in book.entries if e["date"] < f"{YEAR + 1}"]
    accounting = ledger.accounting_result(entries_2026)
    turnover = sum(l["amount"] for e in entries_2026 for l in e["lines"] if l["account"].startswith("70")
                   and l["side"] == "credit")
    excess_gift = int(calculs.reintegration_dons(D(DONATION), D(turnover), P["dons.plafond_interet_general"]))
    add_backs = {"amendes": FINE, "charge_sans_piece": NO_RECEIPT, "dons_excedentaires": excess_gift}
    tax_result = ledger.tax_result(accounting, add_backs.values())
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
    closing_stock = sum(stock[f][2]["valeur_stock"] for f in FORMATS)
    for table, fr, en, rows in (
        ("passage", "DSF 2026 : tableau de passage", "2026 return: reconciliation",
         [("Résultat comptable avant impôt", "Accounting profit before tax", accounting),
          ("Réintégrations", "Add-backs", sum(add_backs.values())), ("Résultat fiscal", "Taxable profit", tax_result)]),
        ("compte_resultat", "DSF 2026 : compte de résultat", "2026 return: income statement",
         [("Chiffre d'affaires", "Turnover", turnover), ("Résultat avant impôt", "Profit before tax", accounting),
          ("Impôt sur le résultat", "Income tax", tax["du"]), ("Résultat net", "Net profit", net)]),
        ("bilan", "DSF 2026 : bilan (extrait)", "2026 return: balance sheet (extract)",
         [("Capital", "Share capital", CAPITAL), ("Résultat net de l'exercice", "Net profit for the year", net),
          ("Emprunt bancaire restant dû", "Bank loan outstanding", special["outstanding"]),
          ("Stocks de marchandises", "Goods inventory", closing_stock),
          ("Camion, valeur nette", "Truck, net book value", TRUCK_HT - truck),
          ("Casiers propres, valeur nette", "Own crates, net book value", CRATES_QTY * CRATE_PRICE - crates)]),
    ):
        book.piece(4, "declaration", d(4, 10, YEAR + 1), fr, en,
                   {"totals": [{"label": text(a, b), "amount": int(v)} for a, b, v in rows]}, year=YEAR + 1)
        book.pieces[-1]["dsf"] = table
    special.update(accounting=accounting, turnover=turnover, add_backs=add_backs, tax_result=tax_result, tax=tax,
                   rate=rate, prepaid=prepaid, liquidation=liquidation, excess_gift=excess_gift, net=net,
                   closing_stock=closing_stock)


# ---------------------------------------------------------------------------------------------------------- questions

def month_questions(book, special, month):
    module, refs = MODULE_OF_MONTH[month], special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    asks = [
        ("purchase", f"Passez l'écriture de la facture de la brasserie de {mfr} (précompte, consigne et vides compris).",
         f"Record the {men} brewery invoice (withholding, deposits and empties included).",
         "Achats 6011 (accises comprises dans le prix), TVA et CAC 4452, précompte de 2 % en 4492 (CGI art. 21 (3)) ; "
         "consigne des casiers livrés en 4094, déconsigne des vides au crédit de 4094, mali éventuel en 6224 (Guide "
         "SYSCOHADA, 1re partie, ch. 2) ; net dû au fournisseur 401.",
         "Purchases 6011 (excise included), VAT 4452, 2% withholding 4492; deposits debited to 4094, empties returned "
         "credited to 4094, any loss in 6224; net payable 401."),
        ("sale", f"Passez l'écriture de la facture au snack-bar de {mfr}.", f"Record the {men} snack-bar invoice.",
         "Client 411 au net, ventes 7011, TVA facturée 4431 ; consigne facturée en 4194 (hors base de TVA, emballages "
         "identifiables, CGI art. 139) ; vides rendus au débit de 4194, boni éventuel en 7074.",
         "Customer 411, sales 7011, VAT 4431; deposit charged to 4194 (outside the VAT base); empties returned debited "
         "to 4194, any gain in 7074."),
        ("cash", f"Passez l'écriture des ventes au comptant de {mfr}.", f"Record the {men} cash sales.",
         "Caisse 5711 au TTC, ventes 7011 au HT, TVA facturée 4431 ; les vides s'échangent, sans consigne.",
         "Cash 5711 incl. tax, sales 7011, VAT charged 4431; empties are swapped, no deposit."),
        ("orange", f"Passez l'écriture du relevé Orange Money de {mfr}.", f"Record the {men} Orange Money statement.",
         "Sous-compte 5522 : ventes et TVA, frais de l'opérateur en 631, transfert vers la banque par 585 (S19).",
         "Sub-account 5522: sales and VAT, operator fees 631, transfer to the bank through 585."),
        ("payroll", f"Passez l'écriture du journal de paie de {mfr}.", f"Record the {men} payroll journal.",
         "Salaires 6611, CFC patronale 6413, CNPS patronale 6641 ; retenues fiscales 4472, CNPS 431, nets 422.",
         "Gross pay 6611, employer levies 6413 and 6641; tax withholdings 4472, CNPS 431, net pay 422."),
        ("bank", f"Passez les écritures du relevé bancaire de {mfr}.", f"Record the {men} bank statement entries.",
         "Règlements à 30 jours (401, 411), salaires nets (422), échéance de l'emprunt (162 et 6712), virements internes "
         "par 585, frais en 631.", "30-day settlements, net pay, loan instalment (162, 6712), internal transfers, fees."),
        ("rent", f"Passez l'écriture de la quittance de loyer de {mfr}.", f"Record the {men} rent receipt.",
         "Loyer brut 6222 ; précompte de 10 % retenu en 4478 (CGI art. 87) ; net payé par la banque.",
         "Gross rent 6222; 10% withholding 4478; net paid by bank."),
        ("cash_out", f"Passez l'écriture du bordereau de versement des espèces de {mfr}.",
         f"Record the {men} cash deposit slip.", "Virement interne : 585 au débit, caisse 5711 au crédit (S19).",
         "Internal transfer: 585 debit, cash 5711 credit."),
        ("settlement", f"Passez l'écriture du règlement de la déclaration du 15 {mfr}.",
         f"Record the payment of the {men} 15th return.",
         "Solde de la TVA (4431, 445, 4449), acompte d'IS en 441 net du précompte imputé, retenues et CNPS reversées.",
         "VAT settled, CIT instalment in 441 net of withholding, withholdings and CNPS paid over."),
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
    book.numeric(module, "exam", refs["excises"], f"Montant du droit d'accises spécifique additionnel compris dans la "
                 f"facture de la brasserie de {mfr} ?",
                 f"Additional specific excise duty included in the {men} brewery invoice?",
                 "Droit spécifique additionnel (CGI art. 142 (9)) : 75 par bouteille de 65 cl et 37,5 par bouteille de "
                 "33 cl, soit 900 par casier dans les deux formats. Il s'ajoute au droit d'accises de 25 % ; la brasserie "
                 "paie les deux et les comprend dans son prix : ils font partie du coût d'achat (6011).",
                 "Additional specific duty: 75 per 65 cl bottle and 37.5 per 33 cl bottle, 900 per crate either way. It "
                 "comes on top of the 25% excise; the brewer pays both and includes them in its price.",
                 piece=refs["purchase"])
    end = datetime.date(YEAR, month, last(month))
    book.numeric(module, "exam", ledger.account_balance(book.entries, "521", end),
                 f"Solde comptable du compte 521 au {last(month)} {mfr} {YEAR} ?",
                 f"Book balance of account 521 at {men} {last(month)}, {YEAR}?",
                 "Débits moins crédits de 521 jusqu'à cette date : c'est le solde à rapprocher du relevé bancaire.",
                 "Debits less credits of 521 up to that date.", piece=refs["bank"],
                 rapprochement={"account": "521", "date": end.isoformat()})
    if month in (3, 6, 9, 12):
        for account, fr, en in (("4094", "consignes à récupérer auprès de la brasserie", "deposits receivable from the brewery"),
                                ("4194", "consignes dues au snack-bar", "deposits owed to the snack bar")):
            balance = ledger.account_balance(book.entries, account, end)
            book.numeric(module, "exam", abs(balance), f"Solde du compte {account} ({fr}) au {last(month)} {mfr} ?",
                         f"Balance of account {account} ({en}) at {men} {last(month)}?",
                         "Consignes facturées moins vides rendus depuis le début de l'exercice.",
                         "Deposits charged less empties returned since the start of the year.",
                         piece=refs["purchase"] if account == "4094" else refs["sale"],
                         rapprochement={"account": account, "date": end.isoformat()}) if balance >= 0 else \
                book.numeric(module, "exam", -balance, f"Solde créditeur du compte {account} ({fr}) au {last(month)} {mfr} ?",
                             f"Credit balance of account {account} ({en}) at {men} {last(month)}?",
                             "Consignes facturées moins vides rendus depuis le début de l'exercice.",
                             "Deposits charged less empties returned since the start of the year.",
                             piece=refs["sale"])


PROCEDURE_QUESTIONS = [
    ("Pourquoi les statuts d'Ateba Boissons SARL passent-ils par un notaire ?",
     "Why are the articles of Ateba Boissons SARL notarised?",
     "Le capital dépasse un million de FCFA (loi n° 2016/014, art. 4)", "Capital above one million FCFA",
     "Toute SARL doit passer par un notaire", "Every LLC must use a notary"),
    ("Quel centre des impôts suit Ateba Boissons SARL ?", "Which tax office follows Ateba Boissons SARL?",
     "Le CIME (CA compris entre 50 millions et 3 milliards)", "The MTO (turnover between 50 million and 3 billion)",
     "Le centre de fiscalité locale", "The local tax office"),
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
                 "Banque 521 au débit, capital souscrit, appelé, versé 1013 au crédit.", "Bank 521 debit, capital 1013 credit.")
    book.journal(1, "exam", special["notary"], "Passez l'écriture de la facture du notaire.", "Record the notary's invoice.",
                 "Honoraires 6324, droits d'enregistrement 646, TVA récupérable sur services 4454 : des charges (S6).",
                 "Fees 6324, registration duties 646, recoverable VAT 4454: expenses (S6).")
    book.journal(1, "exam", special["crates"], "Passez l'écriture de la facture des casiers propres.",
                 "Record the invoice for the company's own crates.",
                 "Casiers marqués au nom de l'entreprise, durables : matériel d'emballage récupérable et identifiable 243 "
                 "(et non 2493, réservé aux immobilisations en cours), TVA sur immobilisations 4451.",
                 "Branded, durable crates: returnable packaging equipment 243 (2493 is for assets in progress), VAT 4451.")
    for month in range(1, 13):
        month_questions(book, special, month)
    book.journal(2, "exam", special["loan"], "Passez l'écriture du déblocage de l'emprunt.", "Record the loan drawdown.",
                 "Banque 521 au débit, emprunts auprès des établissements de crédit 162 au crédit.",
                 "Bank 521 debit, bank borrowings 162 credit.")
    book.journal(2, "exam", special["truck"], "Passez l'écriture de la facture du camion.", "Record the truck invoice.",
                 "Matériel automobile 2451, TVA sur immobilisations 4451, fournisseur d'immobilisations 4812.",
                 "Vehicles 2451, VAT on fixed assets 4451, fixed-asset supplier 4812.")
    book.choice(2, "quiz", special["loan"], "Les intérêts de l'emprunt du camion s'ajoutent au coût du camion.",
                "Loan interest is added to the truck's cost.", [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : ce sont des charges financières (6712) de chaque échéance.",
                "False: they are finance costs (6712) of each instalment.", qtype="truefalse")
    for module, key, fr, en, why_fr, why_en in (
        (3, "fine", "Passez l'écriture de l'amende de circulation.", "Record the traffic fine.",
         "Amendes pénales 6478 ; non déductibles (CGI art. 7), réintégrées à la passerelle.",
         "Fines 6478; not deductible, added back."),
        (4, "no_receipt", "Passez l'écriture du bon de caisse.", "Record the cash voucher.",
         "Charge diverse 6588 sans justificatif externe : non déductible.", "Sundry expense 6588 without receipt."),
        (5, "donation", "Passez l'écriture du don.", "Record the donation.",
         "Dons 6582 ; déductibles dans la limite de 0,5 % du CA (CGI art. 7).", "Donations 6582; deductible up to 0.5%."),
    ):
        book.journal(module, "exam", special[key], fr, en, why_fr, why_en)
    for module, piece, fr, en, ok, why in (
        (3, special["months"][6]["purchase"], "Le mali sur les casiers abîmés rendus à la brasserie est une charge de "
         "location d'emballages (6224).", "The loss on damaged crates returned to the brewery is a packaging charge (6224).",
         True, "Vrai : le Guide l'assimile à une location (1re partie, ch. 2)."),
        (4, special["months"][9]["sale"], "La retenue sur les vides abîmés du snack-bar est un boni (7074).",
         "The amount withheld on the snack bar's damaged empties is a gain (7074).", True,
         "Vrai : boni sur reprise d'emballages, chez le fournisseur."),
        (2, special["months"][2]["sale"], "La consigne de casiers identifiables entre dans la base de la TVA.",
         "Deposits on identifiable crates are in the VAT base.", False,
         "Faux : exclue de la base pour des emballages récupérables, réutilisables et identifiables (CGI art. 139 (2))."),
        (5, special["months"][10]["purchase"], "Le précompte de 2 % sur les achats à la brasserie s'impute sur "
         "l'acompte d'IS.", "The 2% purchase withholding is credited against the CIT instalment.", True,
         "Vrai (CGI art. 21 (3))."),
    ):
        book.choice(module, "quiz", piece, fr, en, [("Vrai", "True", ok), ("Faux", "False", not ok)], why, why,
                    qtype="truefalse")
    inventory_questions(book, special)
    bridge_questions(book, special)
    for module in book.questions:
        split_usage(book.questions[module])


def inventory_questions(book, special):
    sheet = special["sheet"]
    for f, (family, sold, result) in special["stock"].items():
        args = [[[int(q), int(u)] for q, u in family], int(sold)]
        name_fr, name_en = FORMATS[f]["fr"], FORMATS[f]["en"]
        for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré", "weighted average unit cost"),
                            ("valeur_sortie", "coût des sorties au CMUP", "cost of goods sold at WAC"),
                            ("valeur_stock", "valeur du stock final au CMUP", "closing stock at WAC")):
            book.numeric(6, "exam", result[key], f"{name_fr} : {fr} ?", f"{name_en}: {en}?",
                         "CMUP de l'exercice (inventaire intermittent), arrondi au franc ; calculateur stock.",
                         "Period weighted average cost, rounded to the franc.", piece=sheet,
                         calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
        peps = calculs.sortie_peps(family, D(sold))
        book.numeric(6, "exam", peps["valeur_sortie"], f"{name_fr} : coût des sorties en PEPS (contraste) ?",
                     f"{name_en}: cost of goods sold under FIFO (contrast)?",
                     "En PEPS, les lots les plus anciens sortent d'abord ; la hausse de prix de juillet creuse l'écart.",
                     "Under FIFO the oldest lots go first.", piece=sheet,
                     calcul={"fonction": "sortie_peps", "args": args, "resultat": ["valeur_sortie"]})
    book.journal(6, "exam", sheet, "Passez l'écriture du stock final des deux formats.", "Record the closing stock.",
                 "Stocks 3111 et 3112 au débit, variation des stocks 6031 au crédit (inventaire intermittent).",
                 "Stock accounts debited, change in inventories 6031 credited.")
    book.journal(6, "exam", special["schedule"], "Passez l'écriture des dotations aux amortissements.",
                 "Record the depreciation charges.",
                 "Dotations 6813 ; amortissements du matériel de transport 2845 et du matériel d'emballage 2843.",
                 "Charge 6813; accumulated depreciation 2845 and 2843.")
    book.numeric(6, "exam", special["truck_dotation"], "Dotation 2026 du camion (18 000 000 HT, 5 ans, mis en service "
                 "en février) ?", "2026 depreciation of the truck (18,000,000, 5 years, from February)?",
                 "Linéaire au prorata : 18 000 000 / 60 × 11 mois ; calculateur amortissement.",
                 "Straight-line pro rata: 18,000,000 / 60 × 11 months.", piece=special["schedule"],
                 calcul={"fonction": "amortissement_lineaire", "args": [TRUCK_HT, 5, 2], "resultat": [0, "dotation"]})
    book.numeric(6, "exam", special["crates_dotation"], "Dotation 2026 des casiers propres (1 000 000 HT, 5 ans, depuis "
                 "janvier) ?", "2026 depreciation of the own crates (1,000,000, 5 years, from January)?",
                 "Linéaire sur 12 mois : 1 000 000 / 5.", "Straight-line over 12 months.", piece=special["schedule"],
                 calcul={"fonction": "amortissement_lineaire", "args": [CRATES_QTY * CRATE_PRICE, 5, 1],
                         "resultat": [0, "dotation"]})
    book.numeric(6, "exam", special["closing_stock"], "Montant total de la variation des stocks (6031) au 31 décembre ?",
                 "Total change in inventories (6031) at 31 December?",
                 "Premier exercice : pas de stock initial, la variation égale le stock final des deux formats.",
                 "First year: no opening stock.", piece=sheet)
    book.numeric(6, "exam", TRUCK_HT - special["truck_dotation"], "Valeur nette comptable du camion au 31 décembre ?",
                 "Net book value of the truck at 31 December?", "Coût d'acquisition HT moins amortissements cumulés.",
                 "Cost excluding tax less accumulated depreciation.", piece=special["schedule"])
    big = special["stock"]["65"]
    gap = abs(calculs.sortie_peps(big[0], D(big[1]))["valeur_sortie"] - big[2]["valeur_sortie"])
    book.numeric(6, "exam", gap, "Bière 65 cl : écart entre le coût des sorties au CMUP et en PEPS ?",
                 "65 cl beer: gap between cost of goods sold at WAC and FIFO?",
                 "Différence des deux coûts des sorties : autant d'écart sur la marge brute.",
                 "Difference between both costs of goods sold.", piece=sheet)
    end = datetime.date(YEAR, 12, 31)
    book.numeric(6, "exam", -ledger.account_balance(book.entries, "162", end),
                 "Capital de l'emprunt restant dû au 31 décembre ?", "Loan principal outstanding at 31 December?",
                 "12 000 000 moins dix remboursements de capital (mars à décembre).", "12,000,000 less ten repayments.",
                 piece=special["loan"])
    book.numeric(6, "exam", special["interest"], "Total des intérêts de l'emprunt comptabilisés en 2026 (6712) ?",
                 "Total loan interest booked in 2026 (6712)?", "Somme des intérêts des dix échéances, à 1 % par mois du "
                 "capital restant dû.", "Sum of the ten instalments' interest.", piece=special["loan"])
    book.choice(6, "exam", special["schedule"], "Taux d'amortissement fiscal maximal d'un camion (matériel automobile "
                "lourd) ?", "Maximum tax depreciation rate of a truck (heavy vehicle)?",
                [("33,33 %", "33.33%", True), ("25 %", "25%", False), ("10 %", "10%", False)],
                "33,33 % (CGI art. 7) : le taux comptable de 20 % reste en deçà, rien à réintégrer.",
                "33.33% (CGI art. 7): the 20% book rate is below it, nothing to add back.")
    book.choice(6, "exam", special["crates"], "Compte des casiers propres de l'entreprise ?", "Account for own crates?",
                [("243", "243", True), ("2493", "2493", False), ("6082", "6082", False)],
                "243 Matériel d'emballage récupérable et identifiable ; 2493 est la ligne des immobilisations en cours.",
                "243; 2493 is for assets in progress.")
    book.choice(6, "quiz", sheet, "En période de hausse des prix, le PEPS donne un stock final plus élevé que le CMUP.",
                "When prices rise, FIFO gives a higher closing stock than WAC.",
                [("Vrai", "True", True), ("Faux", "False", False)],
                "Vrai : le stock final est valorisé aux derniers prix, plus élevés.", "True.", qtype="truefalse")


def bridge_questions(book, special):
    add, tax = special["add_backs"], special["tax"]
    items = [
        ("amendes", special["fine"], add["amendes"], None, "Montant de l'amende à réintégrer ?", "Fine to add back?",
         "Les amendes et pénalités ne sont pas déductibles (CGI art. 7)."),
        ("dons_excedentaires", special["donation"], add["dons_excedentaires"],
         {"fonction": "reintegration_dons", "args": [DONATION, special["turnover"], 0.5], "resultat": []},
         "Part du don à réintégrer (limite de 0,5 % du CA) ?", "Donation to add back (0.5% of turnover cap)?",
         "Déductible dans la limite de 0,5 % du chiffre d'affaires (CGI art. 7)."),
        ("charge_sans_piece", special["no_receipt"], add["charge_sans_piece"], None,
         "Charge à réintégrer faute de justificatif ?", "Expense to add back for lack of receipt?",
         "Une charge sans pièce justificative n'est pas déductible (CGI art. 7)."),
        ("impot_societes", special["liquidation"], tax["du"],
         {"fonction": "impot_societes", "args": [special["tax_result"], special["turnover"], float(special["rate"]), 2, 10],
          "resultat": ["du"]},
         "IS dû pour 2026 (le plus élevé de l'IS et du minimum de perception) ?", "2026 CIT due (higher of CIT and minimum)?",
         "IS au taux de 25 % (art. 17 bis) comparé au minimum de 2 % du CA, CAC compris : le minimum l'emporte."),
    ]
    for key, ref, value, calc, fr, en, why in items:
        extra = {"passerelle": key}
        if calc:
            extra["calcul"] = calc
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref, **extra)
    liq = special["liquidation"]
    for value, fr, en, why in (
        (special["accounting"], "Résultat comptable avant impôt 2026 ?", "2026 accounting profit before tax?",
         "Produits moins charges des classes 6, 7 et 8."),
        (special["tax_result"], "Résultat fiscal 2026 ?", "2026 taxable profit?", "Résultat comptable + réintégrations."),
        (sum(add.values()), "Total des réintégrations ?", "Total add-backs?", "Amende, charge sans pièce et don excédentaire."),
        (tax["is_total"], "IS calculé au taux de 25 %, CAC compris ?", "CIT at 25%, council cents included?",
         "Résultat fiscal × 25 %, majoré de 10 % de CAC (CGI art. 17 bis)."),
        (tax["minimum_total"], "Minimum de perception 2026, CAC compris ?", "2026 minimum tax, council cents included?",
         "2 % du CA arrondi au millier inférieur, majoré de 10 % (CGI art. 21 et 23)."),
        (special["prepaid"], "Total des acomptes d'IS versés au titre de 2026 ?", "Total 2026 CIT instalments?",
         "Somme des acomptes bruts des douze déclarations (compte 441)."),
        (special["turnover"], "Chiffre d'affaires HT 2026 (ventes et bonis sur emballages) ?",
         "2026 turnover excl. tax (sales and packaging gains)?", "Total des comptes 70 (7011 et 7074)."),
        (special["net"], "Résultat net 2026 ?", "2026 net profit?", "Résultat avant impôt − IS dû."),
        (special["closing_stock"], "Stocks de marchandises au bilan 2026 ?", "2026 balance-sheet goods inventory?",
         "Stock final des deux formats au CMUP."),
        (special["outstanding"], "Emprunt restant dû au bilan 2026 ?", "Loan outstanding on the 2026 balance sheet?",
         "Capital emprunté moins les remboursements de l'année."),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=liq)
    if tax["excedent"]:
        book.numeric(7, "exam", tax["excedent"], "Excédent d'acomptes sur l'IS dû ?", "Instalments in excess of CIT due?",
                     "Acomptes versés moins IS dû.", "Instalments less CIT due.", piece=liq)
    else:
        # Un solde nul s'explique : les douze acomptes de 2 % du CA (CAC compris) couvrent exactement le minimum.
        book.numeric(7, "exam", tax["solde"], "Solde d'IS à payer avec la DSF (0 si tout est déjà réglé) ?",
                     "CIT balance due with the return (0 if already paid)?",
                     "IS dû moins acomptes versés. Quand c'est le minimum de perception qui est dû, les douze acomptes de "
                     "2 % du chiffre d'affaires, centimes compris, l'ont déjà payé : le solde est nul.",
                     "CIT due less instalments. When the minimum tax is due, the twelve 2% instalments, council cents "
                     "included, have already paid it: the balance is zero.", piece=liq)
    book.journal(7, "exam", liq, "Passez l'écriture de l'IS de l'exercice.", "Record the CIT for the year.",
                 "Impôt sur les bénéfices 891 au débit, État 441 au crédit.", "Income tax 891 debit, State 441 credit.")
    for fr, en, qtype, choices, why in (
        ("Date limite de dépôt de la DSF 2026 d'Ateba Boissons SARL (CIME) ?", "Filing deadline (MTO)?", "single",
         [("15 avril 2027", "15 April 2027", True), ("15 mars 2027", "15 March 2027", False),
          ("15 mai 2027", "15 May 2027", False)], "CIME : 15 avril (CGI art. 18 (1), S22)."),
        ("La bière est-elle un produit à marge administrée pour l'acompte d'IS ?",
         "Is beer an administered-margin product for the CIT instalment?", "single",
         [("Non : acompte de 2 % du CA, majoré des CAC", "No: 2% of turnover plus council cents", True),
          ("Oui : 14 % de la marge brute", "Yes: 14% of gross margin", False)],
         "Non : l'art. 21 (1) c vise les produits pétroliers, de la minoterie, pharmaceutiques, de la presse et les engrais."),
        ("Quels tableaux de la DSF sont travaillés dans la simulation ?", "Which return tables are covered?", "single",
         [("Bilan, compte de résultat, tableau de passage, liquidation de l'IS",
           "Balance sheet, income statement, reconciliation, CIT", True),
          ("Tous les tableaux de la DSF", "All tables", False)], "Périmètre S12."),
        ("L'IS de l'exercice est une charge déductible.", "The year's CIT is deductible.", "truefalse",
         [("Vrai", "True", False), ("Faux", "False", True)], "Faux : l'IS n'est pas admis en charge (CGI art. 7)."),
        ("Le minimum de perception s'applique même quand l'IS calculé est plus faible.",
         "The minimum tax applies even when the computed CIT is lower.", "truefalse",
         [("Vrai", "True", True), ("Faux", "False", False)], "Vrai : c'est le cas d'Ateba Boissons (CGI art. 21 et 23)."),
        ("Les accises comprises dans le prix d'achat sont déductibles comme la TVA.",
         "Excise included in the purchase price is recoverable like VAT.", "truefalse",
         [("Vrai", "True", False), ("Faux", "False", True)],
         "Faux : payées par la brasserie et comprises dans son prix, elles font partie du coût d'achat (6011)."),
    ):
        book.choice(7, "quiz", liq, fr, en, choices, why, why, qtype=qtype)


# ------------------------------------------------------------------------------------------------------------ sections

MODULES = [
    ("Création et janvier", "Set-up and January", "Créer la SARL, équiper le dépôt et tenir le premier mois.",
     "Create the LLC, equip the depot and keep the first month."),
    ("Premier trimestre (février et mars)", "First quarter (February and March)",
     "Financer et immobiliser le camion ; tenir consignes et déclarations.", "Finance the truck; keep deposits and returns."),
    ("Deuxième trimestre", "Second quarter", "Traiter l'amende et le mali sur emballages.",
     "Handle the fine and the packaging loss."),
    ("Troisième trimestre", "Third quarter", "Traiter la dépense sans pièce et le boni sur emballages.",
     "Handle the unsupported expense and the packaging gain."),
    ("Quatrième trimestre", "Fourth quarter", "Traiter le don et clôturer les opérations courantes.",
     "Handle the donation and close routine operations."),
    ("Inventaire", "Year-end inventory", "Valoriser le stock, amortir camion et casiers.",
     "Value stock, depreciate truck and crates."),
    ("Passerelle fiscale et DSF", "Tax bridge and return", "Comparer l'IS au minimum de perception et remplir la DSF.",
     "Compare CIT with the minimum tax and fill in the return."),
]


def ascii_name(month):
    return MONTHS_FR[month - 1].replace("é", "e").replace("û", "u")


def sections(book, special):
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    out = {m: [] for m in range(1, 8)}
    company_fr = (
        "## Ateba Boissons SARL\n\nDépôt de boissons à Yaoundé-Mvog-Ada, SARL au capital de 10 000 000 FCFA créée le "
        f"2 janvier {YEAR}, au régime du réel, rattachée au CIME de Yaoundé (chiffre d'affaires visé : environ 145 "
        "millions) [[source:dgi-cime]]. Un gérant salarié, un magasinier et un chauffeur-livreur. Fournisseur unique : "
        "Brasseries de la Sanaga SA (fictive) ; principal client à crédit : Snack-Bar Le Rond-Point SARL (fictif).\n\n"
        "### Plan de comptes de l'entreprise\n\n"
        "[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] (sous-compte 5522 Orange Money) [[syscohada:6011]] "
        "[[syscohada:7011]] [[syscohada:4094]] [[syscohada:4194]] [[syscohada:6224]] [[syscohada:7074]] "
        "[[syscohada:243]] [[syscohada:2451]] [[syscohada:162]] [[syscohada:4452]] [[syscohada:4431]] "
        "[[syscohada:4492]] [[syscohada:4472]] [[syscohada:431]]\n\n"
        "### Consignes d'emballages\n\nLa brasserie consigne les casiers livrés (créance en 4094) et rembourse les vides "
        "rendus ; le dépôt consigne à son tour les casiers livrés au snack-bar (dette en 4194). Un casier abîmé repris à "
        "moindre prix donne un mali (6224) chez celui qui le rend et un boni (7074) chez celui qui le reprend "
        "[[guide:1re partie, ch. 2]]. Les consignes de casiers identifiables restent hors de la base de la TVA "
        "[[cgi:art. 139]].\n\n### Taux de l'exercice 2026\n\n"
        "- TVA [[param:tva.taux_principal]] et CAC [[param:cac.taux]] de la TVA [[cgi:art. 142]] ;\n"
        "- droits d'accises compris dans le prix d'achat : [[param:accises.biere_65cl]] par bouteille de 65 cl, "
        "[[param:accises.biere_33cl]] par bouteille de 33 cl [[cgi:art. 142]] ;\n"
        "- précompte sur achats [[param:precompte.taux_reel]] [[cgi:art. 21]] ;\n"
        "- acompte d'IS [[param:is.taux_minimum_perception]] du chiffre d'affaires, IS au taux réduit "
        "[[param:is.taux_reduit]] [[cgi:art. 17 bis]] ;\n"
        "- précompte sur loyer [[param:precompte.taux_loyer]] [[cgi:art. 87]].\n")
    company_en = (
        "## Ateba Boissons SARL\n\nBeverage depot in Yaoundé-Mvog-Ada, LLC with 10,000,000 FCFA capital created on "
        f"2 January {YEAR}, actual regime, attached to the Yaoundé medium-sized taxpayer office [[source:dgi-cime]]. "
        "A salaried manager, a storekeeper and a delivery driver.\n\n### Chart of accounts\n\n"
        "[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] [[syscohada:6011]] [[syscohada:7011]] "
        "[[syscohada:4094]] [[syscohada:4194]] [[syscohada:6224]] [[syscohada:7074]] [[syscohada:243]] "
        "[[syscohada:2451]] [[syscohada:162]]\n\n### Packaging deposits\n\nThe brewery charges deposits on crates "
        "delivered (receivable in 4094); the depot charges deposits to the snack bar (debt in 4194); damaged crates "
        "give a loss (6224) or a gain (7074) [[guide:1re partie, ch. 2]] [[cgi:art. 139]].\n\n### 2026 rates\n\n"
        "- VAT [[param:tva.taux_principal]], council cents [[param:cac.taux]] [[cgi:art. 142]];\n"
        "- excise included in the purchase price: [[param:accises.biere_65cl]] per 65 cl bottle, "
        "[[param:accises.biere_33cl]] per 33 cl bottle;\n"
        "- purchase withholding [[param:precompte.taux_reel]] [[cgi:art. 21]];\n"
        "- CIT instalment [[param:is.taux_minimum_perception]] of turnover, reduced CIT rate [[param:is.taux_reduit]];\n"
        "- rent withholding [[param:precompte.taux_loyer]] [[cgi:art. 87]].\n")
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file",
                   narrative_b3.typeset_fr(company_fr + "\n" + narrative_b3.CAST_FR + "\n" + narrative_b3.ROUTINES_FR),
                   company_en + "\n" + narrative_b3.CAST_EN + "\n" + narrative_b3.ROUTINES_EN))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   "Chaque démarche précise l'organisme, les documents à fournir et ce que l'on obtient, avec sa source "
                   f"officielle [[cgi:art. L 1]].\n\n{proc}\n",
                   f"Each procedure gives the body, the documents and what you obtain [[cgi:art. L 1]].\n\n{proc}\n"))
    for month in range(1, 13):
        module = MODULE_OF_MONTH[month]
        intro_fr = (f"Pièces de {MONTHS_FR[month - 1]} {YEAR}. Passez chaque écriture, suivez les consignes "
                    "[[syscohada:4094]] [[syscohada:4194]], puis préparez la déclaration du 15 du mois suivant "
                    "[[cgi:art. 21]] [[cgi:art. 143]].")
        intro_en = (f"{MONTHS_EN[month - 1]} {YEAR} documents [[syscohada:4094]] [[syscohada:4194]] [[cgi:art. 21]] "
                    "[[cgi:art. 143]].")
        refs = piece_list(by_month[month])
        if month in special.get("scenes", {}):
            # S34 : mois narré ; la balance d'ouverture suit l'accroche, les pièces sans scène (fiches d'inventaire de
            # décembre) suivent le récit.
            scenes = special["scenes"][month]
            told = {s["ref"] for s in scenes}
            kinds = {p["ref"]: p["kind"] for p in book.pieces}
            opening = [ref for ref in by_month[month] if ref not in told and kinds[ref] == "balance"]
            others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
            out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                                f"{MONTHS_EN[month - 1]} {YEAR}",
                                narrative_b3.month_section(scenes, others, "fr", month, opening),
                                narrative_b3.month_section(scenes, others, "en", month, opening)))
            continue
        out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}", f"{intro_fr}\n\n{refs}\n", f"{intro_en}\n\n{refs}\n"))
    # S34 : inventaire, passerelle et DSF racontés comme les mois.
    told = narrative_b3.year_end_sections(book, special)
    out[6].append(("01-inventaire", "Inventaire au 31 décembre", "Year-end inventory",
                   told["inventory"]["fr"], told["inventory"]["en"]))
    out[7].append(("01-passerelle", "Passerelle fiscale", "Tax bridge", told["bridge"]["fr"], told["bridge"]["en"]))
    out[7].append(("02-dsf", "DSF 2026", "2026 return", told["dsf"]["fr"], told["dsf"]["en"]))
    return out


def tell(book, special):
    """S34 : récit du pilote (janvier) ; l'explication de chaque question sur une pièce narrée reprend le « pourquoi »."""
    special["scenes"] = {1: narrative_b3.january(book, special)}
    special["scenes"].update({m: narrative_b3.later_month(book, special, m) for m in range(2, 13)})
    why = {s["ref"]: s["why"] for scenes in special["scenes"].values() for s in scenes}
    for questions in book.questions.values():
        for question in questions:
            for ref, (fr, en) in why.items():
                if f"[[piece:{ref}]]" in question["prompt"]["fr"] and question["type"] == "journal":
                    question["explanation"] = text(f"{question['explanation']['fr']} Pourquoi pas autre chose : {fr}",
                                                   f"{question['explanation']['en']} Why not something else: {en}")


def main():
    book, special = build()
    balances(book)
    build_questions(book, special)
    tell(book, special)
    module_sections = sections(book, special)
    modules = []
    for number, (title_fr, title_en, comp_fr, comp_en) in enumerate(MODULES, start=1):
        folder = f"b3/m{number}"
        entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": text(comp_fr, comp_en), "sections": entries})
    write(OUT / "b3" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "b3" / "ledger.json", book.entries)
    partie = {
        "slug": "b3", "title": text("Parcours B3 : dépôt de boissons (Ateba Boissons SARL)",
                                    "Track B3: beverage depot (Ateba Boissons SARL)"),
        "description": text("SARL au réel, dépôt de boissons à Yaoundé-Mvog-Ada, rattachée au CIME : consignes, camion, "
                             "accises.", "LLC under the actual regime, beverage depot in Yaoundé: deposits, truck, excise."),
        "centre_impots": "cime", "chiffre_affaires_vise": 280000000,
        "sous_comptes": {"5522": text("Orange Money", "Orange Money")},
        "pieces": "b3/pieces.json", "ledger": "b3/ledger.json", "exam": {"questions_per_module": 4}, "modules": modules}
    write_manifest({}, partie)
    low = min(ledger.account_balance(book.entries, "521", datetime.date.fromisoformat(e["date"])) for e in book.entries)
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, "
          f"résultat {special['accounting']}, IS {special['tax']}, banque au plus bas {low}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
