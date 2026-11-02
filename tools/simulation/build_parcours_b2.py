"""Génère le parcours B2 de la simulation (Ets Essomba Boissons, puis Essomba Boissons SARL) dans content/simulation/b2/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_b2

Établissement individuel de M. Paul Essomba à Douala-Bépanda, à l'IGS et au SMT toute l'année 2026 (CGI art. C 38 à
C 44), profil validé le 2026-11-02 (S41, qui amende S13). Son CA reste sous le seuil de 50 millions : un dépassement en
cours d'exercice entraînerait le reclassement d'office au réel (art. C 39 (2)). En septembre, un contrat signé pour
2027 porte le CA prévisionnel au-delà du seuil : Paul déclare la cessation de l'Ets au 31 décembre au moins trois mois
avant (art. 95 (1)) et apporte son fonds à une SARL unipersonnelle au réel, rattachée au CIME, au 1er janvier 2027 :
stock au CMUP et tricycle en nature (sous 5 millions, sans commissaire aux apports, AUSCGIE art. 312), numéraire
déposé en compte bloqué (art. 313), statuts notariés (loi n° 2016/014 art. 4) et droits dégressifs de 2 % (CGI
art. 346 et 544). Le livre officiel s'arrête au bilan d'ouverture de la SARL. En 2027 : déclaration de l'art. 74,
déclaration de clôture avec l'IGS (art. 95 (2) et 96) et DSF du SMT. Questions numériques ou à choix, sans `journal`
(S14). Les contrôles bloquants de courses/tests/content_rules.py vérifient la sortie.
"""
import calendar
import datetime
from decimal import Decimal as D

from referentiel import calculs
from tools.simulation import ledger, narrative_b2
from tools.simulation.build_parcours_a import (
    MONTHS_EN, MONTHS_FR, OUT, P, YEAR, Book, balances, d, fcfa, line, piece_list, split_usage, text, tva, workday,
    write, write_manifest,
)
from tools.simulation.build_parcours_b3 import ascii_name

SELLER = {"name": "Ets Essomba Boissons", "niu": "P012600031842K", "rccm": "RC/DLA/2026/A/2216", "regime": "IGS",
          "centre": "Centre de fiscalité locale de Douala V", "address": "Bépanda, Douala"}
BREWERY = {"name": "Brasseries de la Sanaga SA (fictive)", "niu": "M019800000731S", "rccm": "RC/YAO/1998/B/0071",
           "regime": "réel", "centre": "DGE", "address": "Dépôt régional de Douala-Bassa"}
DEALER = {"name": "Moto Plus Bépanda SARL (fictive)", "niu": "M011900052204T", "rccm": "RC/DLA/2019/B/0522",
          "regime": "réel", "centre": "CIME de Douala", "address": "Bépanda, Douala"}
NOTARY = {"name": "Étude de Maître Ngo Bassa, notaire (fictive)", "niu": "P010800047719N",
          "rccm": "Charge notariale n° 47 (fictive)", "regime": "réel", "centre": "CIME de Douala",
          "address": "Bonanjo, Douala"}
OWN = {"name": SELLER["name"], "niu": SELLER["niu"]}
SARL = "Essomba Boissons SARL"
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}

PRICE = (6100, 6160)            # casier de 12 bouteilles de 65 cl, HT, au premier puis au second semestre (comme B3)
SELL = 8400                     # prix de vente du casier plein, contre un casier vide (700 F la bouteille)
SOLD = [440, 450, 455, 455, 460, 455, 460, 465, 470, 470, 480, 520]  # casiers vendus : CA de 46,9 millions
OPENING_BUFFER = 60             # casiers d'avance achetés en janvier, toujours en stock au 31 décembre
MOMO_SHARE = 3                  # un casier sur trois est payé par Orange Money
CAPITAL, RENT, WITHDRAWAL = 9000000, 75000, 120000
TRIP, CRATES_PER_TRIP = 1500, 10  # livraison en pousse-pousse : 1 500 F la course de 10 casiers
OM_FEE, BANK_FEE = 6000, 2500
FORECAST_2027 = 75000000        # CA prévisionnel 2027 avec le contrat de l'hôtel (S41)
SARL_CAPITAL, PART = 5000000, 10000
TRICYCLE_HT, TRICYCLE_VALUE = 1216000, 1450000  # prix HT ; valeur d'apport retenue aux statuts
NOTARY_FEES = 250000
REGISTRATION_RATE = 2           # droits dégressifs de 2 % sur le capital (CGI art. 346 et 544 A), jusqu'à 750 millions


def last(month):
    return calendar.monthrange(YEAR, month)[1]


def price(month):
    return PRICE[0 if month <= 6 else 1]


def lots():
    """Lots de l'année [(casiers achetés, prix HT)], connus d'avance : ils fixent le CMUP du stock apporté."""
    return [(sold + (OPENING_BUFFER if month == 1 else 0), price(month)) for month, sold in enumerate(SOLD, start=1)]


STOCK = calculs.sortie_cmup([(D(q), D(u)) for q, u in lots()], D(sum(SOLD)))
STOCK_VALUE = int(STOCK["valeur_stock"])
CASH_CONTRIBUTION = SARL_CAPITAL - STOCK_VALUE - TRICYCLE_VALUE


PROCEDURES = [
    ("Immatriculation de l'établissement au CFCE de Douala", "Registering the sole proprietorship at the Douala "
     "business centre",
     text("Centre de formalités de création d'entreprises (CFCE) de Douala", "Douala business formalities centre"),
     text("Immatriculer l'établissement individuel de M. Essomba au registre du commerce",
          "Register Mr Essomba's sole proprietorship in the trade register"),
     [text("CNI de l'exploitant, extrait de casier judiciaire ou déclaration sur l'honneur",
           "Owner's ID, criminal record extract or sworn statement"),
      text("Plan de localisation du dépôt, contact téléphonique", "Depot location map, phone"),
      text("Frais de création (à vérifier au CFCE)", "Creation fees (check at the CFCE)")],
     text("Registre de commerce, carte de contribuable (NIU), attestation de création",
          "Trade register, taxpayer card, creation certificate"),
     "[[source:minfi-cfce]] [[source:minfi-formalites]]"),
    ("Rattachement à l'IGS au centre de fiscalité locale", "IGS attachment at the local tax office",
     text("Centre de fiscalité locale de Douala V", "Douala V local tax office"),
     text("Suivi à l'IGS : chiffre d'affaires prévisionnel de 46 millions, sous le seuil de 50 millions du négoce",
          "IGS follow-up: forecast turnover of 46 million, below the 50 million trading threshold"),
     [text("Carte de contribuable délivrée au CFCE", "Taxpayer card issued by the CFCE"),
      text("Déclaration du chiffre d'affaires prévisionnel", "Forecast turnover statement")],
     text("Suivi à l'IGS : déclaration et paiement avant le 15 avril, DSF du SMT avant le 15 mai",
          "IGS follow-up: return and payment by 15 April, cash-basis return by 15 May"),
     "[[cgi:art. C 39]] [[cgi:art. C 41]] [[cgi:art. C 44]]"),
    ("Ouverture du compte bancaire", "Opening the bank account",
     text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
     text("Payer la brasserie par virement et verser la recette chaque quinzaine",
          "Pay the brewery by transfer and deposit the takings every fortnight"),
     [text("Demande d'ouverture, registre de commerce, carte de contribuable", "Request, trade register, taxpayer card"),
      text("CNI de l'exploitant, plan de localisation", "Owner's ID, location map")],
     text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
    ("Compte marchand Orange Money", "Orange Money merchant account",
     text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
     text("Encaisser les ventes par Orange Money", "Collect sales through Orange Money"),
     [text("Registre de commerce, carte de contribuable", "Trade register, taxpayer card"),
      text("CNI de l'exploitant, RIB", "Owner's ID, bank details")],
     text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
]

CESSATION = (
    "Déclaration préalable de cessation de l'établissement", "Advance notice of the sole proprietorship's cessation",
    text("Centre de fiscalité locale de Douala V (déclaration en ligne)", "Douala V local tax office (online return)"),
    text("Annoncer la cessation définitive de l'Ets au 31 décembre 2026 et l'apport du fonds à Essomba Boissons SARL, "
         "en formation : le contrat signé avec l'hôtel porte le CA prévisionnel 2027 à 75 millions",
         "Announce the final cessation on 31 December 2026 and the transfer of the business to Essomba Boissons SARL, "
         "being formed: the hotel contract lifts the 2027 forecast turnover to 75 million"),
    [text("NIU, adresse et activité de l'établissement", "Taxpayer number, address and activity"),
     text("Date de cessation envisagée (31 décembre 2026) et nature : cessation définitive",
          "Planned cessation date (31 December 2026) and nature: final"),
     text("Identité et adresse du cessionnaire : Essomba Boissons SARL, en formation, Bépanda",
          "Transferee: Essomba Boissons SARL, being formed, Bépanda")],
    text("Accusé de réception ; ouverture d'un contrôle de la situation fiscale (art. 95 bis)",
         "Acknowledgement; review of the tax position opened (art. 95 bis)"),
    "[[cgi:art. 95]] [[cgi:art. 95 bis]] [[cgi:art. C 39]]")

SARL_PROCEDURES = [
    ("Dépôt des fonds de la SARL en formation", "Depositing the funds of the company being formed",
     text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
     text("Déposer l'apport en numéraire sur un compte bloqué au nom de la SARL en formation",
          "Pay the cash contribution into a blocked account in the name of the company being formed"),
     [text("Liste des souscripteurs et des sommes versées", "List of subscribers and amounts paid"),
      text("Projet de statuts, CNI de l'associé unique", "Draft articles, sole partner's ID")],
     text("Certificat du dépositaire ; fonds bloqués jusqu'à l'immatriculation",
          "Depositary's certificate; funds blocked until registration"),
     "[[source:ohada-auscgie]] [[source:sg-cm-compte-entreprise]]"),
    ("Statuts notariés de la SARL", "Notarised articles of the LLC",
     text("Étude de notaire (Maître Ngo Bassa, fictive)", "Notary's office (Maître Ngo Bassa, fictitious)"),
     text("Signer les statuts : capital de 5 000 000, au-delà du seuil d'un million, donc acte notarié ; évaluer "
          "chaque apport en nature ; faire enregistrer l'acte",
          "Sign the articles: 5,000,000 of capital, above one million, hence a notarised deed; value each "
          "contribution in kind; register the deed"),
     [text("CNI de l'associé unique et du gérant", "ID of the sole partner and manager"),
      text("Certificat du dépositaire des fonds", "Depositary's certificate"),
      text("Évaluation des apports en nature : fiche de stock, facture du tricycle", "Valuation of contributions in "
           "kind: stock card, tricycle invoice")],
     text("Statuts enregistrés (droits de 2 % du capital), déclaration de souscription et de versement",
          "Registered articles (2% duty on the capital), subscription and payment statement"),
     "[[source:loi-2016-014]] [[source:ohada-auscgie]] [[cgi:art. 346]] [[cgi:art. 544]]"),
    ("Immatriculation de la SARL au CFCE de Douala", "Registering the LLC at the Douala business centre",
     text("Centre de formalités de création d'entreprises (CFCE) de Douala", "Douala business formalities centre"),
     text("Immatriculer Essomba Boissons SARL, début d'activité au 1er janvier 2027",
          "Register Essomba Boissons SARL, trading from 1 January 2027"),
     [text("Statuts enregistrés et certificat du dépositaire", "Registered articles and depositary's certificate"),
      text("Déclaration de régularité et de conformité, CNI du gérant", "Statement of compliance, manager's ID"),
      text("Plan de localisation du siège", "Location map of the registered office")],
     text("Registre de commerce, carte de contribuable (NIU) de la SARL, attestation de création",
          "Trade register, the LLC's taxpayer card, creation certificate"),
     "[[source:minfi-cfce]] [[source:minfi-formalites]]"),
    ("Rattachement de la SARL au CIME de Douala", "Attaching the LLC to the Douala medium-sized taxpayer office",
     text("Centre des impôts des moyennes entreprises (CIME) de Douala", "Douala medium-sized taxpayer office"),
     text("Suivi au réel : chiffre d'affaires prévisionnel de 75 millions, entre 50 millions et 3 milliards",
          "Actual regime: forecast turnover of 75 million, between 50 million and 3 billion"),
     [text("Carte de contribuable de la SARL", "The LLC's taxpayer card"),
      text("Déclaration du chiffre d'affaires prévisionnel 2027", "2027 forecast turnover statement")],
     text("Suivi au réel : déclarations mensuelles dès février 2027, DSF de l'exercice 2027",
          "Actual regime: monthly returns from February 2027, 2027 financial statements"),
     "[[source:dgi-cime]] [[cgi:art. 93 quater]]"),
]


def demarche(book, month, day, item):
    fr, en, body, purpose, docs, got, source = item
    return book.piece(month, "demarche", d(month, day), f"Démarche : {fr}", f"Procedure: {en}",
                      {"organisme": body, "objet": purpose, "documents_a_fournir": docs, "document_obtenu": got,
                       "source": source})


def purchase(book, month, day, qty, number, einvoice):
    """Livraison de la brasserie : TVA facturée par le fournisseur au réel et précompte de 5 % (CGI art. 21 (3)),
    tous deux dans le coût d'achat d'un contribuable à l'IGS (S40) ; payée par virement avant le chargement."""
    unit = price(month)
    ht = qty * unit
    taxes = tva(ht)
    withheld = int(calculs.franc(D(ht) * P["precompte.taux_igs"] / 100))
    due = int(taxes["ttc"]) + withheld
    ref = book.piece(month, "facture_achat", day, f"Facture de la brasserie, livraison du {int(day[8:])} {MONTHS_FR[month - 1]}",
                     f"Brewery invoice, delivery of {MONTHS_EN[month - 1]} {int(day[8:])}",
                     {"issuer": BREWERY, "customer": OWN, "number": number, "einvoice": einvoice,
                      "fields": [{"label": text("Régime du client", "Customer's regime"),
                                  "value": text("Contribuable à l'IGS : précompte de 5 %", "IGS taxpayer: 5% withholding")}],
                      "lines": [{"label": text("Bière 65 cl, casier de 12 (accises comprises)",
                                               "65 cl beer, crate of 12 (excise included)"),
                                 "qty": qty, "unit_price": unit, "amount": ht}],
                      "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht", "amount": ht},
                                 {"label": text("TVA et CAC (19,25 %)", "VAT and council cents (19.25%)"), "role": "tax",
                                  "amount": int(taxes["taxes"])},
                                 {"label": text("Précompte sur achats 5 %", "5% purchase withholding"), "role": "tax",
                                  "amount": withheld},
                                 {"label": text("Net payé par virement", "Net paid by transfer"), "role": "ttc",
                                  "amount": due}]})
    book.entry(day, ref, line("6011", "debit", due), line("521", "credit", due))
    return ref, {"qty": qty, "unit": unit, "ht": ht, "tax": int(taxes["taxes"]), "withheld": withheld, "due": due}


def build():
    book, special = Book("B2"), {"months": {}, "buys": {}}
    special["procedures"] = [demarche(book, 1, 2, item) for item in PROCEDURES]
    special["capital"] = book.piece(1, "releve_bancaire", d(1, 2), "Avis de crédit : apport de l'exploitant (Banque X)",
                                    "Credit notice: owner's contribution (Bank X)",
                                    {"fields": [{"label": text("Déposant", "Depositor"), "value": "Paul Essomba"}],
                                     "totals": [{"label": text("Économies versées au compte du dépôt",
                                                               "Savings paid into the depot account"),
                                                 "amount": CAPITAL}]})
    book.entry(d(1, 2), special["capital"], line("521", "debit", CAPITAL), line("103", "credit", CAPITAL))
    special["cessation"] = demarche(book, 9, 25, CESSATION)
    special["sarl_procedures"] = [demarche(book, month, day, item)
                                  for (month, day), item in zip(((11, 9), (12, 28), (12, 29), (12, 30)), SARL_PROCEDURES)]
    number = 0
    for month in range(1, 13):
        end, refs = last(month), {}
        mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
        sold = SOLD[month - 1]
        bought = sold + (OPENING_BUFFER if month == 1 else 0)
        buys = []
        for i, (day, qty) in enumerate(((workday(month, 5), bought // 2), (workday(month, 19), bought - bought // 2))):
            number += 1
            refs[f"purchase{i}"], info = purchase(book, month, day, qty, f"BS-2026-{6200 + number:05d}",
                                                  f"DGI-SFE-2026-{9300 + number:06d}")
            buys.append(info)
        special["buys"][month] = buys
        if month == 11:
            special_november(book, special, refs)
        if month == 12:
            special_december(book, special, refs)
        # Ventes au casier : deux tiers en espèces, un tiers par Orange Money ; aucune TVA (IGS).
        momo = sold // MOMO_SHARE
        cash = sold - momo
        refs["cash"] = book.piece(month, "recu_caisse", d(month, end), f"Brouillard de caisse de {mfr} : ventes au comptant",
                                  f"{men} cash book: cash sales",
                                  {"lines": [{"label": text("Casiers de bière 65 cl vendus (casier vide rendu)",
                                                            "65 cl beer crates sold (empty crate returned)"),
                                              "qty": cash, "unit_price": SELL, "amount": cash * SELL}],
                                   "totals": [{"label": text("Recettes en espèces", "Cash receipts"), "role": "ht",
                                               "amount": cash * SELL}]})
        half = cash // 2 * SELL
        book.entry(d(month, 15), refs["cash"], line("5711", "debit", half), line("7011", "credit", half))
        book.entry(d(month, end), refs["cash"], line("5711", "debit", cash * SELL - half),
                   line("7011", "credit", cash * SELL - half))
        om_total = momo * SELL
        transfer = om_total - OM_FEE
        refs["orange"] = book.piece(month, "releve_momo", d(month, end), f"Relevé Orange Money de {mfr}",
                                    f"{men} Orange Money statement",
                                    {"lines": [{"label": text("Casiers payés par Orange Money", "Crates paid by Orange Money"),
                                                "qty": momo, "unit_price": SELL, "amount": om_total}],
                                     "totals": [{"label": text("Encaissements", "Receipts"), "role": "ht", "amount": om_total},
                                                {"label": text("Frais de l'opérateur", "Operator fees"), "amount": OM_FEE},
                                                {"label": text("Transfert vers la banque", "Transfer to the bank"),
                                                 "amount": transfer}]})
        book.entry(d(month, end), refs["orange"], line("5522", "debit", om_total), line("7011", "credit", om_total),
                   line("631", "debit", OM_FEE), line("585", "debit", transfer), line("5522", "credit", om_total))
        rent_day = d(month, 15)
        refs["rent"] = book.piece(month, "recu_caisse", rent_day, f"Quittance de loyer du dépôt, {mfr}",
                                  f"{men} depot rent receipt",
                                  {"fields": [{"label": text("Bailleur", "Landlord"), "value": "M. Kotto (fictif)"},
                                              {"label": text("Précompte sur loyer", "Rent withholding"),
                                               "value": text("Aucun : locataire à l'IGS, loyer payé brut",
                                                             "None: IGS tenant, rent paid gross")}],
                                   "totals": [{"label": text("Loyer payé en espèces", "Rent paid in cash"),
                                               "amount": RENT}]})
        book.entry(rent_day, refs["rent"], line("6222", "debit", RENT), line("5711", "credit", RENT))
        trips = -(-sold // CRATES_PER_TRIP)
        refs["transport"] = book.piece(month, "recu_caisse", d(month, end), f"Courses de pousse-pousse de {mfr}",
                                       f"{men} push-cart deliveries",
                                       {"lines": [{"label": text("Livraisons aux clients, 10 casiers par course",
                                                                 "Deliveries to customers, 10 crates a trip"),
                                                   "qty": trips, "unit_price": TRIP, "amount": trips * TRIP}],
                                        "totals": [{"label": text("Payé en espèces aux pousseurs", "Paid in cash"),
                                                    "role": "ht", "amount": trips * TRIP}]})
        book.entry(d(month, end), refs["transport"], line("612", "debit", trips * TRIP),
                   line("5711", "credit", trips * TRIP))
        # Versements des espèces : le 15 et en fin de mois, la caisse ne garde que le fonds de 20 000 ; en décembre,
        # l'établissement cesse : toute la caisse part à la banque.
        float_ = 0 if month == 12 else 20000
        mid = d(month, 15)
        first = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, 15))
        first_deposit = max(int(first) - 20000, 0) // 1000 * 1000
        if first_deposit:
            book.entry(mid, None, line("585", "debit", first_deposit), line("5711", "credit", first_deposit))
        cash_end = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, end))
        second = int(cash_end) - float_
        book.entry(d(month, end), None, line("585", "debit", second), line("5711", "credit", second))
        refs["deposits"] = book.piece(month, "recu_caisse", d(month, end), f"Bordereaux de versement d'espèces de {mfr}",
                                      f"{men} cash deposit slips",
                                      {"totals": [{"label": text("Versement du 15", "Deposit on the 15th"),
                                                   "amount": first_deposit},
                                                  {"label": text("Versement de fin de mois", "Month-end deposit"),
                                                   "amount": second}]})
        for entry in book.entries[-2:] if first_deposit else book.entries[-1:]:
            entry["piece"] = refs["deposits"]
        deposits = first_deposit + second
        rows = [(text("Versements d'espèces reçus", "Cash deposits received"), deposits),
                (text("Transfert reçu d'Orange Money", "Transfer received from Orange Money"), transfer),
                (text("Virements à la brasserie", "Transfers to the brewery"), sum(b["due"] for b in buys)),
                (text("Virement personnel de l'exploitant (prélèvement)", "Owner's personal transfer (drawings)"),
                 WITHDRAWAL), (text("Frais de tenue de compte", "Account fees"), BANK_FEE)]
        rows += [(label, amount) for label, amount in special.get("bank_extra", {}).get(month, [])]
        end_date = datetime.date(YEAR, month, end)
        lines = [line("521", "debit", deposits + transfer), line("585", "credit", deposits + transfer),
                 line("1042", "debit", WITHDRAWAL), line("631", "debit", BANK_FEE),
                 line("521", "credit", WITHDRAWAL + BANK_FEE)]
        if month == 12:
            # Cessation au 31 décembre : le solde du compte du dépôt passe sur le compte personnel de Paul.
            remaining = int(ledger.account_balance(book.entries, "521", end_date)) + deposits + transfer \
                - WITHDRAWAL - BANK_FEE
            special["closing_transfer"] = remaining
            rows.append((text("Clôture : solde viré au compte personnel de M. Essomba",
                              "Closing: balance transferred to Mr Essomba's personal account"), remaining))
            lines += [line("1042", "debit", remaining), line("521", "credit", remaining)]
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {mfr} (Banque X)",
                                  f"{men} bank statement (Bank X)",
                                  {"totals": [{"label": label, "amount": amount} for label, amount in rows]})
        book.entry(d(month, end), refs["bank"], *lines)
        refs["sold"], refs["momo_qty"], refs["trips"], refs["deposit_total"] = sold, momo, trips, deposits
        special["months"][month] = refs
    year_end(book, special)
    return book, special


def special_november(book, special, refs):
    """Le numéraire de la SARL en formation part sur un compte bloqué (AUSCGIE art. 313) ; Paul achète, à titre
    personnel, le tricycle qu'il apportera en nature. Les deux sommes sortent du dépôt comme des prélèvements."""
    day = workday(11, 16)
    refs["deposit_sarl"] = book.piece(11, "releve_bancaire", day, "Certificat du dépositaire : fonds de la SARL en formation",
                                      "Depositary's certificate: funds of the company being formed",
                                      {"fields": [{"label": text("Déposant", "Depositor"),
                                                   "value": text("Paul Essomba, associé unique", "Paul Essomba, sole partner")},
                                                  {"label": text("Compte", "Account"),
                                                   "value": text(f"{SARL}, en formation : compte bloqué jusqu'à "
                                                                 "l'immatriculation", f"{SARL}, being formed: blocked "
                                                                 "until registration")}],
                                       "totals": [{"label": text("Apport en numéraire versé", "Cash contribution paid"),
                                                   "amount": CASH_CONTRIBUTION}]})
    book.entry(day, refs["deposit_sarl"], line("1042", "debit", CASH_CONTRIBUTION), line("521", "credit", CASH_CONTRIBUTION))
    day = workday(11, 23)
    taxes = tva(TRICYCLE_HT)
    refs["tricycle"] = book.piece(11, "facture_achat", day, "Facture du tricycle de livraison (achat personnel)",
                                  "Delivery tricycle invoice (personal purchase)",
                                  {"issuer": DEALER, "customer": {"name": "M. Paul Essomba (à titre personnel)",
                                                                   "niu": SELLER["niu"]},
                                   "number": "MP-2026-00871", "einvoice": "DGI-SFE-2026-117403",
                                   "lines": [{"label": text("Tricycle de livraison neuf, benne 1 tonne",
                                                            "New delivery tricycle, 1-tonne box"),
                                              "qty": 1, "unit_price": TRICYCLE_HT, "amount": TRICYCLE_HT}],
                                   "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht",
                                               "amount": TRICYCLE_HT},
                                              {"label": text("TVA et CAC (19,25 %)", "VAT and council cents (19.25%)"),
                                               "role": "tax", "amount": int(taxes["taxes"])},
                                              {"label": text("Net payé par virement", "Net paid by transfer"),
                                               "role": "ttc", "amount": int(taxes["ttc"])}]})
    book.entry(day, refs["tricycle"], line("1042", "debit", int(taxes["ttc"])), line("521", "credit", int(taxes["ttc"])))
    special["tricycle_ttc"], special["tricycle_tax"] = int(taxes["ttc"]), int(taxes["taxes"])
    special.setdefault("bank_extra", {})[11] = [
        (text("Virement au compte bloqué de la SARL en formation", "Transfer to the blocked account of the company"),
         CASH_CONTRIBUTION),
        (text("Virement à Moto Plus (tricycle, achat personnel)", "Transfer to Moto Plus (tricycle)"), int(taxes["ttc"]))]


def special_december(book, special, refs):
    """Statuts du 28 décembre : apports évalués (stock au CMUP de l'année, tricycle) ; facture du notaire avancée par
    Paul. Au 1er janvier 2027, la SARL ouvre son bilan et reprend les frais de constitution (AUSCGIE art. 110)."""
    parts = SARL_CAPITAL // PART
    unit = int(STOCK["cout_unitaire"])
    refs["statuts"] = book.piece(12, "statuts", d(12, 28), f"Statuts de {SARL} : apports et capital",
                                 f"Articles of {SARL}: contributions and capital",
                                 {"fields": [{"label": text("Forme", "Form"),
                                              "value": text("SARL unipersonnelle, associé unique et gérant : Paul Essomba",
                                                            "Single-member LLC; sole partner and manager: Paul Essomba")},
                                             {"label": text("Parts sociales", "Shares"),
                                              "value": text(f"{parts} parts de {fcfa(PART)}", f"{parts} shares of {PART:,} F")},
                                             {"label": text("Commissaire aux apports", "Contributions auditor"),
                                              "value": text("Non requis : apports en nature de 5 000 000 au plus "
                                                            "(AUSCGIE art. 312)", "Not required: contributions in kind "
                                                            "of 5,000,000 at most")},
                                             {"label": text("Début d'activité", "Start of trading"),
                                              "value": text("1er janvier 2027, reprise du fonds de l'Ets Essomba Boissons",
                                                            "1 January 2027, takeover of Ets Essomba Boissons")}],
                                  "lines": [{"label": text(f"Apport en nature : stock de {OPENING_BUFFER} casiers au "
                                                           "coût moyen pondéré de l'année",
                                                           f"In kind: {OPENING_BUFFER} crates at the year's weighted "
                                                           "average cost"),
                                             "qty": OPENING_BUFFER, "unit_price": unit, "amount": STOCK_VALUE},
                                            {"label": text("Apport en nature : tricycle de livraison", "In kind: delivery "
                                                           "tricycle"), "qty": 1, "unit_price": TRICYCLE_VALUE,
                                             "amount": TRICYCLE_VALUE},
                                            {"label": text("Apport en numéraire (compte bloqué)", "Cash (blocked account)"),
                                             "qty": 1, "unit_price": CASH_CONTRIBUTION, "amount": CASH_CONTRIBUTION}],
                                  "totals": [{"label": text("Capital social", "Share capital"), "role": "ht",
                                              "amount": SARL_CAPITAL}]})
    book.entry(d(1, 1, YEAR + 1), refs["statuts"], line("311", "debit", STOCK_VALUE), line("2458", "debit", TRICYCLE_VALUE),
               line("521", "debit", CASH_CONTRIBUTION), line("1013", "credit", SARL_CAPITAL))
    fees = tva(NOTARY_FEES)
    duty = SARL_CAPITAL * REGISTRATION_RATE // 100
    due = int(fees["ttc"]) + duty
    refs["notary"] = book.piece(12, "facture_achat", d(12, 28), "Facture du notaire : statuts et enregistrement",
                                "Notary's invoice: articles and registration",
                                {"issuer": NOTARY, "customer": {"name": f"{SARL} (en formation)", "niu": "en cours d'attribution (CFCE)"},
                                 "number": "NB-2026-0412", "einvoice": "DGI-SFE-2026-121877",
                                 "fields": [{"label": text("Avancé par", "Paid in advance by"),
                                             "value": text("M. Paul Essomba, associé unique", "Mr Paul Essomba")}],
                                 "lines": [{"label": text("Honoraires : rédaction et dépôt des statuts",
                                                          "Fees: drafting and filing the articles"),
                                            "qty": 1, "unit_price": NOTARY_FEES, "amount": NOTARY_FEES}],
                                 "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht", "amount": NOTARY_FEES},
                                            {"label": text("TVA et CAC (19,25 %)", "VAT and council cents (19.25%)"),
                                             "role": "tax", "amount": int(fees["taxes"])},
                                            {"label": text("Droits d'enregistrement 2 % du capital (débours)",
                                                           "2% registration duty on the capital (disbursement)"),
                                             "role": "tax", "amount": duty},
                                            {"label": text("Net payé", "Net paid"), "role": "ttc", "amount": due}]})
    book.entry(d(12, 28), refs["notary"], line("1042", "debit", due), line("521", "credit", due))
    book.entry(d(1, 1, YEAR + 1), refs["notary"], line("6324", "debit", NOTARY_FEES),
               line("4454", "debit", int(fees["taxes"])), line("6468", "debit", duty), line("4621", "credit", due))
    special.update(notary_due=due, notary_tax=int(fees["taxes"]), duty=duty, parts=parts)
    special.setdefault("bank_extra", {})[12] = [
        (text("Virement à l'étude du notaire (frais de la SARL)", "Transfer to the notary (company's costs)"), due)]


def year_end(book, special):
    lots_ = [(D(q), D(u)) for q, u in lots()]
    bought = sum(q for q, _ in lots())
    sold = sum(SOLD)
    result = STOCK
    special["lots"] = lots()
    special["sheet"] = book.piece(12, "fiche_stock", d(12, 31), "Fiche de stock des casiers (inventaire du 31 décembre)",
                                  "Crate stock card (31 December count)",
                                  {"fields": [{"label": text("Achetés / vendus / comptés au 31/12",
                                                             "Bought / sold / counted at 31/12"),
                                               "value": f"{bought} / {sold} / {bought - sold}"}],
                                   "lines": [{"label": text(f"Lot de {MONTHS_FR[i]}", f"{MONTHS_EN[i]} lot"), "qty": q,
                                              "unit_price": u, "amount": q * u}
                                             for i, (q, u) in enumerate(lots())]})
    entries = [e for e in book.entries if e["date"] < f"{YEAR + 1}-01-01"]
    end = datetime.date(YEAR, 12, 31)

    def total(prefix, side="debit"):
        return sum(l["amount"] for e in entries for l in e["lines"] if l["account"].startswith(prefix)
                   and l["side"] == side)

    turnover = total("7011", "credit")
    classes = [(D(P[f"igs.classe{i}_plafond"]), D(P[f"igs.classe{i}_montant"])) for i in range(1, 11)]
    igs = int(calculs.igs_annuel(D(turnover), classes))
    igs_cga = int(calculs.igs_annuel(D(turnover), classes, True))
    buys = [b for month in special["buys"].values() for b in month]
    expenses = sum(l["amount"] for e in entries for l in e["lines"] if l["account"][0] == "6" and l["side"] == "debit")
    cash = sum(ledger.account_balance(entries, acc, end) for acc in ("521", "5711", "5522", "585"))
    stock = int(result["valeur_stock"])
    smt_result = turnover - expenses + stock
    withdrawals = total("1042")
    assert cash == 0, "les comptes de trésorerie de l'Ets sont soldés au 31 décembre"
    assert cash + stock == CAPITAL - withdrawals + smt_result, "bilan du SMT déséquilibré"
    opening = [e for e in book.entries if e["date"] == f"{YEAR + 1}-01-01"]
    assert all(sum(l["amount"] for l in e["lines"] if l["side"] == "debit")
               == sum(l["amount"] for l in e["lines"] if l["side"] == "credit") for e in opening)
    special.update(turnover=turnover, igs=igs, igs_cga=igs_cga, classes=[[int(c), int(m)] for c, m in classes],
                   stock=(lots_, sold, result), stock_value=stock, expenses=expenses, cash=int(cash),
                   smt_result=smt_result, withdrawals=withdrawals,
                   precompte=sum(b["withheld"] for b in buys), vat_paid=sum(b["tax"] for b in buys),
                   purchases=total("6011"), rent=total("6222"), transport=total("612"), fees=total("631"),
                   cash_margin=turnover - total("6011"),
                   monthly_withdrawals=12 * WITHDRAWAL)
    special["art74"] = book.piece(3, "declaration", d(3, 10, YEAR + 1), "Déclaration annuelle de revenus 2026 (art. 74)",
                                  "2026 yearly income return (art. 74)",
                                  {"fields": [{"label": text("Contribuable", "Taxpayer"),
                                               "value": text("Personne physique à l'IGS (CGI art. C 39 (4))",
                                                             "Individual under the IGS")},
                                              {"label": text("Revenus de l'activité", "Business income"),
                                               "value": text("Dépôt de boissons, IGS libératoire de l'IRPP (BIC)",
                                                             "Drinks depot, IGS in full discharge of income tax")}],
                                   "totals": [{"label": text("Chiffre d'affaires déclaré", "Turnover declared"),
                                               "amount": turnover}]}, year=YEAR + 1)
    special["closing_return"] = book.piece(
        3, "declaration", d(3, 26, YEAR + 1), "Déclaration de clôture de l'Ets (art. 95) et IGS 2026",
        "Closing return of the sole proprietorship (art. 95) and 2026 IGS",
        {"fields": [{"label": text("Date de cessation", "Cessation date"), "value": text("31 décembre 2026",
                                                                                         "31 December 2026")},
                    {"label": text("Cessionnaire", "Transferee"), "value": text(f"{SARL}, Bépanda (CIME de Douala)",
                                                                                f"{SARL}, Bépanda")},
                    {"label": text("Classe du tarif", "Tariff class"),
                     "value": text("Classe 10 : de 30 à moins de 50 millions", "Class 10: 30 to under 50 million")},
                    {"label": text("Échéance", "Deadline"),
                     "value": text("31 mars 2027 : trois mois après la cessation, paiement compris (art. 95 et 96)",
                                   "31 March 2027: three months after cessation, payment included")}],
         "totals": [{"label": text("Chiffre d'affaires HT 2026", "2026 turnover"), "amount": turnover},
                    {"label": text("Stock apporté à la SARL", "Stock transferred to the LLC"), "amount": stock},
                    {"label": text("IGS annuel (CGI art. C 40)", "Yearly IGS"), "amount": igs}]}, year=YEAR + 1)
    for table, fr, en, rows in (
        ("compte_resultat_smt", "DSF du SMT 2026 : compte de résultat", "2026 cash-basis return: income statement",
         [("Recettes de l'exercice (ventes au casier)", "Receipts of the year (crate sales)", turnover),
          ("Dépenses de l'exercice (achats, loyer, transport, frais)", "Payments of the year", expenses),
          ("Variation des stocks (stock final)", "Change in inventories (closing stock)", stock),
          ("Résultat de l'exercice", "Profit for the year", smt_result)]),
        ("bilan_smt", "DSF du SMT 2026 : bilan", "2026 cash-basis return: balance sheet",
         [("Trésorerie : comptes soldés à la cessation", "Cash: accounts settled at cessation", cash),
          ("Stock de casiers (apporté à la SARL le 1er janvier)", "Crate stock (transferred on 1 January)", stock),
          ("Capital personnel", "Personal capital", CAPITAL),
          ("Prélèvements de l'exploitant, apports à la SARL compris (à déduire)", "Owner's drawings, LLC "
           "contributions included (deducted)", withdrawals),
          ("Résultat de l'exercice", "Profit for the year", smt_result)]),
    ):
        book.piece(3, "declaration", d(3, 26, YEAR + 1), fr, en,
                   {"totals": [{"label": text(a, b), "amount": int(v)} for a, b, v in rows]}, year=YEAR + 1)
        book.pieces[-1]["dsf"] = table
    special["smt_return"] = book.pieces[-1]["ref"]


# ---------------------------------------------------------------------------------------------------------- questions

def monthly_questions(book, special, month):
    module, refs = MODULE_OF_MONTH[month], special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    first, second = special["buys"][month]
    asks = [
        (refs["purchase0"], first["withheld"], f"Précompte de 5 % subi sur la première livraison de {mfr} ?",
         f"5% withholding on the first {men} delivery?", "5 % du HT : M. Essomba est à l'IGS (CGI art. 21 (3))."),
        (refs["purchase0"], first["due"], f"Coût de la première livraison de {mfr}, tout compris ?",
         f"Full cost of the first {men} delivery?",
         "HT, TVA et précompte : à l'IGS, rien ne se récupère ; tout entre dans le coût d'achat (S40)."),
        (refs["purchase1"], second["tax"], f"TVA et CAC payées sur la seconde livraison de {mfr}, non récupérables ?",
         f"Non-recoverable VAT on the second {men} delivery?", "19,25 % du HT, facturés par la brasserie au réel."),
        (refs["cash"], (refs["sold"] - refs["momo_qty"]) * SELL, f"Recettes en espèces de {mfr} ?", f"{men} cash receipts?",
         "Casiers vendus au comptant × 8 400 ; aucune TVA facturée à l'IGS."),
        (refs["orange"], refs["momo_qty"] * SELL, f"Encaissements Orange Money de {mfr} ?", f"{men} Orange Money receipts?",
         "Casiers payés par téléphone × 8 400, au sous-compte 5522 (S19)."),
        (refs["transport"], refs["trips"] * TRIP, f"Courses de pousse-pousse payées en {mfr} ?", f"{men} push-cart costs?",
         "Une course de 1 500 F pour 10 casiers livrés ; transport sur ventes (612)."),
        (refs["deposits"], refs["deposit_total"], f"Espèces versées à la banque en {mfr} ?", f"Cash deposited in {men}?",
         "Le 15 et en fin de mois, la caisse ne garde que son fonds de 20 000 (rien en décembre, à la cessation) ; "
         "virement interne par 585."),
    ]
    for piece, value, fr, en, why in asks:
        book.numeric(module, "exam", value, fr, en, why, why, piece=piece)
    receipts = refs["sold"] * SELL
    book.numeric(module, "exam", receipts, f"Total des recettes de {mfr} au cahier du SMT ?",
                 f"Total {men} receipts in the cash book?", "Espèces et Orange Money : tous les casiers vendus × 8 400.",
                 "Cash and Orange Money.", piece=refs["cash"])
    payments = first["due"] + second["due"] + RENT + refs["trips"] * TRIP + OM_FEE + BANK_FEE
    book.numeric(module, "exam", payments, f"Total des dépenses de {mfr} au cahier du SMT (hors prélèvements) ?",
                 f"Total {men} payments (drawings excluded)?",
                 "Brasserie, loyer, pousse-pousse et frais ; les prélèvements de l'exploitant ne sont pas des dépenses de "
                 "l'activité.", "Brewery, rent, carts and fees; drawings are not a business payment.", piece=refs["bank"])
    end = datetime.date(YEAR, month, last(month))
    book.numeric(module, "exam", ledger.account_balance(book.entries, "521", end),
                 f"Solde du compte bancaire du dépôt au {last(month)} {mfr} ?", f"Depot bank balance at {men} {last(month)}?",
                 "Recettes moins dépenses passées par la banque à cette date.", "Bank receipts less payments.",
                 piece=refs["bank"], rapprochement={"account": "521", "date": end.isoformat()})
    if month > 1:
        balance_ref = next(p["ref"] for p in book.pieces if p["kind"] == "balance" and p["date"] == d(month, 1))
        previous = datetime.date(YEAR, month - 1, last(month - 1))
        book.numeric(module, "exam", ledger.account_balance(book.entries, "5711", previous),
                     f"Fonds de caisse au début de {mfr}, d'après la balance ?", f"Cash float at the start of {men}?",
                     "Solde débiteur du compte 5711 : le fonds gardé pour rendre la monnaie.", "Debit balance of 5711.",
                     piece=balance_ref, rapprochement={"account": "5711", "date": previous.isoformat()})


PROCEDURE_QUESTIONS = [
    ("Que délivre le CFCE à M. Essomba ?", "What does the CFCE give Mr Essomba?",
     ("Registre de commerce, carte de contribuable et attestation de création", "Trade register, taxpayer card"),
     ("Des statuts", "Articles of association")),
    ("Pourquoi le dépôt relève-t-il de l'IGS en 2026 ?", "Why is the depot under the IGS in 2026?",
     ("CA prévisionnel de 46 millions, sous 50 millions, activité de négoce", "Forecast of 46 million, below 50 million"),
     ("Parce qu'il n'a pas de salarié", "Because it has no employee")),
    ("Pourquoi un compte bancaire ?", "Why a bank account?",
     ("Pour payer la brasserie par virement et sécuriser la recette", "To pay the brewery and secure the takings"),
     ("La loi interdit les espèces", "The law bans cash")),
    ("Que remet Orange à la fin de la démarche ?", "What does Orange give at the end?",
     ("Un code marchand", "A merchant code"), ("Une patente", "A business licence")),
]


def build_questions(book, special):
    for ref, (fr, en, right, wrong) in zip(special["procedures"], PROCEDURE_QUESTIONS):
        book.choice(1, "quiz", ref, fr, en, [(right[0], right[1], True), (wrong[0], wrong[1], False)],
                    "Voir la démarche et sa source officielle.", "See the procedure and its official source.")
    book.numeric(1, "exam", CAPITAL, "Économies apportées par M. Essomba au démarrage ?", "Owner's start-up savings?",
                 "Capital personnel (103) : un établissement individuel n'a ni capital social ni associés.",
                 "Personal capital (103).", piece=special["capital"])
    book.choice(1, "quiz", special["capital"], "Un établissement individuel a-t-il un capital social (101) ?",
                "Does a sole proprietorship have share capital (101)?",
                [("Non : capital personnel de l'exploitant (103)", "No: owner's personal capital (103)", True),
                 ("Oui", "Yes", False)], "Pas d'associés, pas de parts ; la SARL de 2027 en aura.",
                "No partners, no shares; the 2027 LLC will have them.")
    jan = special["months"][1]
    first, second = special["buys"][1]
    for piece, value, fr, en, why in (
        (jan["purchase0"], first["qty"] + second["qty"], "Casiers achetés en janvier, les deux livraisons ensemble ?",
         "Crates bought in January, both deliveries?", "Ventes du mois et 60 casiers d'avance pour ne jamais manquer."),
        (jan["purchase1"], first["due"] + second["due"], "Coût total des achats de janvier ?", "January purchases, "
         "full cost?", "Les deux factures, TVA et précompte compris."),
        (jan["purchase0"], SELL - first["due"] // first["qty"], "Marge par casier en janvier, au franc près "
         "(prix de vente moins coût complet) ?", "January margin per crate (selling price less full cost)?",
         "8 400 moins le coût d'un casier, TVA et précompte compris (division arrondie à l'unité inférieure)."),
        (jan["orange"], OM_FEE, "Frais Orange Money de janvier ?", "January Orange Money fees?",
         "Frais de l'opérateur en services bancaires (631)."),
    ):
        book.numeric(1, "exam", value, fr, en, why, why, piece=piece)
    for month in range(1, 13):
        monthly_questions(book, special, month)
    for module, piece, fr, en, ok, why in (
        (1, special["months"][1]["purchase0"], "M. Essomba récupère la TVA payée à la brasserie.",
         "Mr Essomba recovers the VAT paid to the brewery.", False,
         "Faux : à l'IGS, on ne facture ni ne déduit la TVA ; elle reste dans le coût (CGI art. C 38)."),
        (1, special["months"][1]["rent"], "Le dépôt retient 10 % de précompte sur le loyer.",
         "The depot withholds 10% on the rent.", False,
         "Faux : un locataire à l'IGS paie le loyer brut ; le précompte de l'art. 87 vise les locataires au réel."),
        (2, special["months"][2]["purchase0"], "Le précompte de 5 % s'impute sur l'IGS de l'année.",
         "The 5% withholding is credited against the year's IGS.", False,
         "Faux : le CGI n'en prévoit l'imputation que sur l'IS ou l'IRPP (art. 21 (3)) ; il reste dans le coût (S40)."),
        (3, special["months"][4]["bank"], "Le virement personnel de M. Essomba est une dépense du dépôt.",
         "Mr Essomba's personal transfer is a depot expense.", False,
         "Faux : c'est un prélèvement de l'exploitant (1042), pas une charge."),
        (4, special["months"][8]["orange"], "Un client qui paie par Orange Money doit une TVA en plus du prix.",
         "A customer paying by Orange Money owes VAT on top.", False, "Faux : le dépôt est à l'IGS, il ne facture pas de TVA."),
        (4, special["cessation"], "Si le dépôt dépassait 50 millions de CA dès novembre 2026, il serait reclassé d'office "
         "au réel en cours d'exercice.", "Above 50 million of turnover by November 2026, the depot would be moved to the "
         "actual regime mid-year.", True, "Vrai : tout dépassement du seuil au cours d'un exercice entraîne le "
         "reclassement d'office (CGI art. C 39 (2)) ; d'où le soin de Paul à rester sous 50 millions en 2026."),
        (5, special["months"][11]["tricycle"], "La SARL pourra déduire la TVA de la facture du tricycle.",
         "The LLC will deduct the VAT on the tricycle invoice.", False,
         "Faux : Paul a acheté le tricycle à titre personnel ; la SARL le reçoit en apport, sans TVA facturée à son nom."),
    ):
        book.choice(module, "quiz", piece, fr, en, [("Vrai", "True", ok), ("Faux", "False", not ok)], why, why,
                    qtype="truefalse")
    for module, piece, fr, en, choices, why in (
        (2, special["months"][3]["deposits"], "Pourquoi verser les espèces deux fois par mois ?",
         "Why deposit the cash twice a month?",
         [("Limiter le risque de vol et suivre la recette", "Limit theft risk and track takings", True),
          ("Parce que la banque l'impose", "Because the bank requires it", False)],
         "Bonne pratique de caisse : la caisse ne garde qu'un fonds de 20 000."),
        (3, special["months"][6]["transport"], "Où classer les courses de pousse-pousse vers les clients ?",
         "Where do push-cart deliveries go?",
         [("Transports sur ventes (612)", "Transport on sales (612)", True), ("Loyer (6222)", "Rent (6222)", False)],
         "Le transport des casiers vendus est un transport sur ventes."),
        (4, special["months"][7]["purchase1"], "Le prix d'achat passe à 6 160 en juillet. Effet sur la marge ?",
         "The price rises to 6,160 in July. Effect on the margin?",
         [("Elle baisse, le prix de vente restant à 8 400", "It falls, the selling price staying at 8,400", True),
          ("Aucun", "None", False)], "Coût du casier plus élevé, prix de vente inchangé."),
        (5, special["months"][10]["bank"], "Que montre le relevé bancaire chaque mois ?", "What does the bank statement "
         "show each month?",
         [("Versements, transfert Orange Money, virements à la brasserie, prélèvement, frais",
           "Deposits, Orange Money transfer, brewery transfers, drawings, fees", True),
          ("Seulement les ventes", "Only sales", False)], "Le cahier du SMT se rapproche de ce relevé."),
    ):
        book.choice(module, "quiz", piece, fr, en, choices, why, why)
    cessation_questions(book, special)
    sarl_questions(book, special)
    inventory_questions(book, special)
    returns_questions(book, special)
    for module in book.questions:
        split_usage(book.questions[module])


def cessation_questions(book, special):
    ref = special["cessation"]
    book.numeric(4, "exam", FORECAST_2027, "Chiffre d'affaires prévisionnel 2027 annoncé dans la déclaration de cessation ?",
                 "2027 forecast turnover stated in the cessation notice?",
                 "Le contrat de l'hôtel s'ajoute aux ventes du dépôt : 75 millions, au-delà du seuil de 50 millions.",
                 "The hotel contract adds to the depot's sales.", piece=ref)
    book.numeric(4, "exam", 50000000, "Seuil de chiffre d'affaires du négoce au-delà duquel on relève du réel ?",
                 "Trading turnover threshold above which the actual regime applies?",
                 "50 millions pour le négoce, 30 pour les professions libérales (CGI art. C 39 et 93 quater).",
                 "50 million for trading.", piece=ref)
    for fr, en, choices, why in (
        ("Au plus tard quand Paul doit-il déclarer une cessation prévue le 31 décembre 2026 ?",
         "By when must Paul file notice of a cessation planned for 31 December 2026?",
         [("Le 30 septembre 2026 : trois mois avant", "30 September 2026: three months ahead", True),
          ("Le 31 décembre 2026", "31 December 2026", False), ("Le 15 mars 2027", "15 March 2027", False)],
         "La déclaration préalable précède d'au moins trois mois la cessation (CGI art. 95 (1))."),
        ("Sur quel chiffre d'affaires apprécie-t-on le régime d'une entreprise nouvelle ?",
         "Which turnover sets the regime of a new business?",
         [("Le prévisionnel déclaré à l'immatriculation", "The forecast declared at registration", True),
          ("Celui de l'établissement de 2026", "The 2026 sole proprietorship's", False)],
         "Pour une entreprise nouvelle, le CA prévisionnel, sous réserve de régularisation (circulaire de la LF 2026, "
         "art. C 39) : la SARL, avec 75 millions prévus, relève du réel dès sa création."),
        ("Pourquoi Paul crée-t-il une SARL au 1er janvier plutôt que de garder l'Ets en 2027 ?",
         "Why does Paul set up an LLC on 1 January rather than keep the sole proprietorship in 2027?",
         [("L'Ets dépasserait 50 millions en 2027 et serait reclassé d'office en cours d'année ; la SARL part au réel "
           "dès le premier jour, et sépare son patrimoine", "The sole proprietorship would cross 50 million in 2027 and "
           "be reclassified mid-year; the LLC starts under the actual regime and ring-fences his assets", True),
          ("Parce qu'une SARL ne paie pas d'impôt", "Because an LLC pays no tax", False)],
         "Le changement de régime se fait à une date nette (CGI art. C 39 (2)) ; la SARL limite aussi la responsabilité "
         "de Paul à ses apports."),
        ("Que déclenche la déclaration de cessation ?", "What does the cessation notice trigger?",
         [("Un contrôle de la situation fiscale de l'Ets", "A review of the tax position", True),
          ("Le remboursement des précomptes", "A refund of withholdings", False)], "CGI art. 95 bis."),
    ):
        book.choice(4, "quiz", ref, fr, en, choices, why, why)


SARL_PROCEDURE_QUESTIONS = [
    ("Que remet la banque après le dépôt des fonds de la SARL en formation ?", "What does the bank give after the "
     "deposit?", ("Un certificat du dépositaire", "A depositary's certificate"), ("Une carte de contribuable",
                                                                                 "A taxpayer card")),
    ("Quel acte le notaire fait-il enregistrer ?", "Which deed does the notary register?",
     ("Les statuts, aux droits de 2 % du capital", "The articles, at 2% of the capital"),
     ("Le bail du dépôt", "The depot lease")),
    ("Qu'obtient Paul au CFCE pour la SARL ?", "What does Paul obtain at the CFCE for the LLC?",
     ("Registre de commerce, NIU de la SARL, attestation de création", "Trade register, the LLC's taxpayer number"),
     ("Un code marchand Orange Money", "An Orange Money merchant code")),
    ("Pourquoi la SARL relève-t-elle du CIME ?", "Why does the LLC belong to the CIME?",
     ("CA prévisionnel de 75 millions, entre 50 millions et 3 milliards", "Forecast of 75 million"),
     ("Parce qu'elle a un associé fonctionnaire", "Because a partner is a civil servant")),
]


def sarl_questions(book, special):
    nov, dec = special["months"][11], special["months"][12]
    for module, piece, value, fr, en, why in (
        (5, nov["deposit_sarl"], CASH_CONTRIBUTION, "Apport en numéraire déposé sur le compte bloqué ?",
         "Cash contribution paid into the blocked account?",
         "Capital moins les apports en nature (stock et tricycle) ; libéré en totalité, alors que la moitié suffisait "
         "(AUSCGIE art. 311-1)."),
        (5, nov["tricycle"], special["tricycle_ttc"], "Prix payé par Paul pour le tricycle, TVA comprise ?",
         "Price paid by Paul for the tricycle, VAT included?", "HT plus TVA et CAC : Paul achète en personne privée, "
                                                               "il ne récupère rien."),
        (5, nov["tricycle"], special["tricycle_tax"], "TVA et CAC comprises dans le prix du tricycle ?",
         "VAT and council cents in the tricycle price?", "19,25 % du HT, facturés par le vendeur au réel."),
        (5, dec["statuts"], SARL_CAPITAL, "Capital social d'Essomba Boissons SARL ?", "Share capital of Essomba Boissons SARL?",
         "Somme des apports : stock, tricycle et numéraire."),
        (5, dec["statuts"], special["parts"], "Nombre de parts sociales de 10 000 ?", "Number of 10,000 shares?",
         "Capital divisé par la valeur nominale (au moins 5 000 au Cameroun, loi n° 2016/014 art. 2)."),
        (5, dec["statuts"], STOCK_VALUE + TRICYCLE_VALUE, "Total des apports en nature ?", "Total contributions in kind?",
         "Stock et tricycle : sous 5 millions, pas de commissaire aux apports (AUSCGIE art. 312)."),
        (5, dec["statuts"], STOCK_VALUE, "Valeur d'apport du stock de casiers ?", "Value of the crate stock contributed?",
         "60 casiers au coût moyen pondéré de l'année."),
        (5, dec["notary"], special["duty"], "Droits d'enregistrement des statuts ?", "Registration duty on the articles?",
         "Droits dégressifs de 2 % du capital pour la tranche jusqu'à 750 millions (CGI art. 346 et 544 A)."),
        (5, dec["notary"], special["notary_due"], "Montant total de la facture du notaire, avancé par Paul ?",
         "Total of the notary's invoice, advanced by Paul?", "Honoraires, TVA et droits d'enregistrement."),
        (5, dec["notary"], special["notary_tax"], "TVA facturée par le notaire sur ses honoraires ?",
         "VAT charged by the notary on the fees?", "19,25 % des honoraires ; la SARL la récupérera (4454)."),
    ):
        book.numeric(module, "exam", value, fr, en, why, why, piece=piece)
    for fr, en, choices, why, piece in (
        ("Pourquoi des statuts notariés ?", "Why notarised articles?",
         [("Le capital dépasse un million de francs", "The capital exceeds one million francs", True),
          ("Parce qu'il y a un apport en numéraire", "Because there is a cash contribution", False)],
         "Le notaire est facultatif jusqu'à un million de capital (loi n° 2016/014 art. 4).", dec["statuts"]),
        ("Faut-il un commissaire aux apports ?", "Is a contributions auditor needed?",
         [("Non : les apports en nature ne dépassent pas 5 millions", "No: contributions in kind do not exceed 5 million",
           True), ("Oui, dès qu'il y a un apport en nature", "Yes, for any contribution in kind", False)],
         "AUSCGIE art. 312 ; l'associé reste responsable cinq ans de la valeur retenue.", dec["statuts"]),
        ("Pourquoi bloquer les fonds jusqu'à l'immatriculation ?", "Why block the funds until registration?",
         [("Pour garantir le capital aux tiers", "To guarantee the capital to third parties", True),
          ("Pour gagner des intérêts", "To earn interest", False)], "AUSCGIE art. 313 et 314.", special["months"][11]["deposit_sarl"]),
        ("Quel compte recevra le tricycle dans la SARL ?", "Which account receives the tricycle in the LLC?",
         [("2458 : autres matériels de transport (vélo, mobylette, moto)", "2458: other transport equipment", True),
          ("6011 : achats de marchandises", "6011: purchases of goods", False)],
         "Un bien durable utilisé pour l'activité est une immobilisation [[syscohada:2458]].", special["months"][11]["tricycle"]),
    ):
        book.choice(5, "quiz", piece, fr, en, choices, why, why)
    for ref, (fr, en, right, wrong) in zip(special["sarl_procedures"], SARL_PROCEDURE_QUESTIONS):
        book.choice(5, "quiz", ref, fr, en, [(right[0], right[1], True), (wrong[0], wrong[1], False)],
                    "Voir la démarche et sa source officielle.", "See the procedure and its official source.")
    book.choice(5, "quiz", dec["notary"], "La SARL inscrit les frais de constitution (notaire, droits d'enregistrement) en "
                "frais d'établissement à l'actif.", "The LLC capitalises its formation costs as set-up costs.",
                [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : le SYSCOHADA révisé les passe en charges par nature (6324 pour le notaire, 6468 pour les droits) ; "
                "l'ancien compte de frais d'établissement a disparu.",
                "False: revised SYSCOHADA expenses them by nature.", qtype="truefalse", piege="frais_etablissement")


def inventory_questions(book, special):
    sheet = special["sheet"]
    lots_, sold, result = special["stock"]
    args = [[[int(q), int(u)] for q, u in lots_], int(sold)]
    for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré du casier", "weighted average crate cost"),
                        ("valeur_sortie", "coût des casiers vendus au CMUP", "cost of crates sold at WAC")):
        book.numeric(6, "exam", result[key], f"Inventaire : {fr} (prix HT de la brasserie) ?", f"Count: {en} (brewery HT price)?",
                     "CMUP sur les prix HT des lots de l'année, arrondi au franc ; calculateur stock.", "Period WAC.",
                     piece=sheet, calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
    book.numeric(6, "exam", result["valeur_stock"], "Inventaire : valeur du stock final au CMUP, apportée à la SARL ?",
                 "Count: closing stock at WAC, contributed to the LLC?",
                 "Casiers comptés × coût moyen pondéré ; pas d'écriture au SMT ; la même valeur figure aux statuts.",
                 "Crates counted × WAC; the same value appears in the articles.", piece=sheet)
    peps = calculs.sortie_peps(lots_, D(sold))
    book.numeric(6, "exam", peps["valeur_sortie"], "Inventaire : coût des casiers vendus en PEPS (contraste) ?",
                 "Count: cost of crates sold under FIFO?", "Les lots les plus anciens, moins chers, sortent d'abord.",
                 "Oldest, cheaper lots go first.", piece=sheet,
                 calcul={"fonction": "sortie_peps", "args": args, "resultat": ["valeur_sortie"]})
    # Au SMT, aucune écriture d'inventaire : le stock final en PEPS reste une question simple, sans calcul contrôlé.
    book.numeric(6, "exam", peps["valeur_stock"], "Inventaire : valeur du stock final en PEPS (contraste) ?",
                 "Count: closing stock under FIFO?", "Les casiers en stock sont les derniers achetés, au prix de juillet.",
                 "The crates left are the last bought.", piece=sheet)
    book.numeric(6, "exam", sum(q for q, _ in special["lots"]) - sold, "Casiers comptés au 31 décembre ?",
                 "Crates counted on 31 December?", "Achetés moins vendus : les 60 casiers d'avance de janvier.",
                 "Bought less sold.", piece=sheet)
    momo_total = sum(special["months"][m]["momo_qty"] for m in range(1, 13)) * SELL
    for value, fr, en, why in (
        (special["turnover"], "Recettes de l'année (ventes au casier) ?", "Year's receipts?",
         "Compte 7011, espèces et Orange Money : sous 50 millions, le dépôt reste à l'IGS toute l'année."),
        (momo_total, "Encaissements Orange Money de l'année ?", "Year's Orange Money receipts?", "Un casier sur trois."),
        (special["purchases"], "Coût total des achats de bière de l'année ?", "Year's beer purchases, full cost?",
         "HT, TVA et précompte : tout reste dans le coût à l'IGS (6011)."),
        (special["precompte"], "Précomptes de 5 % subis sur l'année ?", "Withholdings suffered over the year?",
         "Vingt-quatre livraisons ; ils ne s'imputent pas sur l'IGS (S40)."),
        (special["vat_paid"], "TVA et CAC payées à la brasserie sur l'année, non récupérables ?",
         "Non-recoverable VAT paid to the brewery?", "À l'IGS, la TVA payée est un coût."),
        (special["rent"], "Loyers payés sur l'année ?", "Rent paid over the year?", "Douze loyers bruts de 75 000."),
        (special["transport"], "Courses de pousse-pousse de l'année ?", "Year's push-cart costs?", "Compte 612."),
        (special["fees"], "Frais bancaires et Orange Money de l'année ?", "Year's bank and Orange Money fees?",
         "Compte 631."),
        (special["withdrawals"], "Total des prélèvements de l'exploitant (1042), apports à la SARL et clôture compris ?",
         "Total owner's drawings (1042), LLC contributions and closing included?",
         "Prélèvements mensuels, numéraire, tricycle, notaire et solde de clôture : tout ce qui quitte le dépôt pour Paul."),
        (special["closing_transfer"], "Solde du compte du dépôt viré à Paul le 31 décembre ?",
         "Depot account balance transferred to Paul on 31 December?",
         "L'établissement cesse : la banque est soldée ; Paul garde de quoi payer l'IGS de mars 2027."),
        (special["smt_result"], "Résultat 2026 du SMT : recettes moins dépenses, plus le stock final ?",
         "2026 cash-basis profit: receipts less payments, plus closing stock?", "AUDCIF art. 28."),
    ):
        book.numeric(6, "exam", value, fr, en, why, why, piece=sheet)
    statuts = special["months"][12]["statuts"]
    opening_total = SARL_CAPITAL
    for value, fr, en, why in (
        (opening_total, "Bilan d'ouverture de la SARL au 1er janvier 2027 : total de l'actif ?",
         "LLC opening balance sheet at 1 January 2027: total assets?",
         "Stock, tricycle et banque : exactement le capital, avant toute opération."),
        (CASH_CONTRIBUTION, "Bilan d'ouverture : banque de la SARL (521) ?", "Opening balance sheet: the LLC's bank (521)?",
         "Le numéraire débloqué après l'immatriculation."),
        (TRICYCLE_VALUE, "Bilan d'ouverture : tricycle (2458) ?", "Opening balance sheet: tricycle (2458)?",
         "Valeur d'apport retenue aux statuts, sous le prix payé TVA comprise."),
    ):
        book.numeric(6, "exam", value, fr, en, why, why, piece=statuts)
    for fr, en, choices, why, piece in (
        ("Pourquoi compter le stock au 31 décembre ?", "Why count stock on 31 December?",
         [("Il corrige le résultat du SMT et fixe la valeur apportée à la SARL", "It adjusts the cash-basis profit and "
           "sets the value contributed", True), ("Ce n'est pas utile", "It is not useful", False)],
         "AUDCIF art. 28 ; le même chiffre passe dans les statuts.", sheet),
        ("Pourquoi les comptes de trésorerie du dépôt sont-ils soldés au 31 décembre ?",
         "Why are the depot's cash accounts settled on 31 December?",
         [("L'établissement cesse ; la SARL ouvre ses propres comptes", "The business ceases; the LLC opens its own", True),
          ("Pour éviter l'IGS", "To avoid the IGS", False)], "Deux personnes distinctes : Paul, puis la SARL.",
         special["months"][12]["bank"]),
        ("Quel est le coût unitaire le plus élevé au 31 décembre ?", "Which unit cost is higher on 31 December?",
         [("Le PEPS (derniers prix)", "FIFO (latest prices)", True), ("Le CMUP", "WAC", False)],
         "Les prix ont monté en juillet : le PEPS garde les derniers casiers, les plus chers.", sheet),
    ):
        book.choice(6, "exam", piece, fr, en, choices, why, why)
    book.choice(6, "quiz", sheet, "Les prélèvements de l'exploitant réduisent le résultat du SMT.",
                "The owner's drawings reduce the cash-basis profit.", [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : ils réduisent ses capitaux, pas le résultat.", "False: they reduce equity, not profit.",
                qtype="truefalse")


def returns_questions(book, special):
    closing, smt_ref, art74 = special["closing_return"], special["smt_return"], special["art74"]
    notary = special["months"][12]["notary"]
    book.numeric(7, "exam", special["igs"], "IGS annuel 2026 du dépôt ?", "2026 yearly IGS of the depot?",
                 "Tarif de la classe 10 (de 30 à moins de 50 millions) (CGI art. C 40 (1)).", "Class 10 tariff.",
                 piece=closing, calcul={"fonction": "igs_annuel", "args": [special["turnover"], special["classes"]],
                                        "resultat": []})
    book.numeric(7, "exam", special["igs_cga"], "IGS 2026 si Paul avait adhéré à un Centre de Gestion Agréé ?",
                 "2026 IGS with a registered management centre?", "Tarif réduit de moitié (CGI art. C 40 (4)).",
                 "Halved tariff.", piece=closing,
                 calcul={"fonction": "igs_annuel", "args": [special["turnover"], special["classes"], True], "resultat": []})
    for value, fr, en, why, ref in (
        (special["turnover"], "Chiffre d'affaires déclaré à la clôture ?", "Turnover declared at closing?",
         "Total des recettes de 2026.", closing),
        (special["stock_value"], "Stock déclaré comme apporté au cessionnaire ?", "Stock declared as transferred?",
         "La déclaration de clôture détaille les stocks et le cessionnaire (art. 95 (2)).", closing),
        (special["igs"], "Montant à payer avec la déclaration de clôture, au plus tard le 31 mars 2027 ?",
         "Amount due with the closing return by 31 March 2027?",
         "La déclaration de cessation s'accompagne du paiement des droits (art. 96) : l'IGS 2026 part avant le 15 avril.",
         closing),
        (special["igs"] // 4, "Quotité trimestrielle si l'Ets avait opté pour le paiement fractionné ?",
         "Quarterly instalment under the split-payment option?", "Un quart de l'IGS annuel (art. C 41).", closing),
        (special["smt_result"], "DSF du SMT : résultat de l'exercice 2026 ?", "Cash-basis return: 2026 profit?",
         "Recettes moins dépenses, plus le stock final (AUDCIF art. 28).", smt_ref),
        (special["cash"], "DSF du SMT : trésorerie au 31 décembre ?", "Cash-basis return: cash at 31 December?",
         "Zéro : les comptes du dépôt sont soldés à la cessation.", smt_ref),
        (special["expenses"], "DSF du SMT : dépenses de l'exercice ?", "Cash-basis return: payments of the year?",
         "Achats, loyer, pousse-pousse et frais (classes 6).", smt_ref),
        (special["smt_result"] - special["igs"], "Résultat 2026 après l'IGS ?", "2026 profit after the IGS?",
         "L'IGS de la classe 10 pèse sur une marge de quelques centaines de francs par casier.", closing),
        (special["turnover"], "Chiffre d'affaires porté sur la déclaration de l'art. 74 ?",
         "Turnover on the art. 74 return?", "Une personne physique à l'IGS dépose aussi sa déclaration annuelle de "
         "revenus (CGI art. C 39 (4) et 74).", art74),
        (special["notary_due"], "Dette de la SARL envers Paul au 1er janvier 2027 (4621) ?",
         "The LLC's debt to Paul on 1 January 2027 (4621)?",
         "La SARL reprend les frais avancés pour elle (AUSCGIE art. 110) et les doit à son associé.", notary),
        (special["notary_tax"], "TVA récupérable par la SARL sur la facture du notaire (4454) ?",
         "VAT recoverable by the LLC on the notary's invoice (4454)?",
         "La SARL est au réel : elle déduira cette TVA sur sa première déclaration, en février 2027.", notary),
        (NOTARY_FEES + special["duty"], "Charges de constitution de la SARL au 1er janvier 2027 (6324 et 6468) ?",
         "The LLC's formation expenses on 1 January 2027 (6324 and 6468)?",
         "Honoraires et droits d'enregistrement, en charges par nature (S6).", notary),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref)
    for fr, en, choices, why, ref in (
        ("Date limite de la déclaration de clôture de l'Ets ?", "Deadline of the closing return?",
         [("31 mars 2027 : trois mois après la cessation", "31 March 2027: three months after cessation", True),
          ("15 avril 2027", "15 April 2027", False)], "CGI art. 95 (2) ; plus tôt que l'échéance de l'IGS (art. C 41).",
         closing),
        ("Date limite de la déclaration de revenus de l'art. 74 ?", "Deadline of the art. 74 income return?",
         [("15 mars 2027", "15 March 2027", True), ("15 mai 2027", "15 May 2027", False)],
         "CGI art. 74, rendu applicable aux personnes physiques à l'IGS par l'art. C 39 (4).", art74),
        ("Pourquoi déposer la DSF du SMT avec la déclaration de clôture ?", "Why file the cash-basis return with the "
         "closing return?", [("La clôture liquide les revenus jusqu'à la cessation, états à l'appui", "The closing "
                              "return settles income up to cessation, with statements", True),
                             ("Parce que le 15 mai est supprimé", "Because 15 May was abolished", False)],
         "Art. 95 (2) et C 44 : l'échéance du 15 mai reste la limite, la clôture l'avance.", smt_ref),
        ("Paul dépose-t-il une DSF du système normal pour 2026 ?", "Does Paul file the standard return for 2026?",
         [("Non : la DSF du SMT de l'Ets", "No: the sole proprietorship's cash-basis return", True), ("Oui", "Yes", False)],
         "À l'IGS, SMT et DSF du SMT (art. C 44, S14) ; la DSF normale viendra pour la SARL, sur 2027.", smt_ref),
        ("À quel centre des impôts la SARL est-elle rattachée ?", "Which tax office does the LLC belong to?",
         [("Le CIME de Douala : 75 millions prévus, entre 50 millions et 3 milliards", "Douala CIME: 75 million "
           "forecast", True), ("Le centre de fiscalité locale", "The local tax office", False)],
         "Rattachement selon le chiffre d'affaires (DGI) ; régime du réel dès la création.", notary),
        ("L'IGS dépend-il du bénéfice du dépôt ?", "Does the IGS depend on the depot's profit?",
         [("Non : de la classe de chiffre d'affaires", "No: on the turnover class", True), ("Oui", "Yes", False)],
         "Tarif forfaitaire par classe (art. C 40).", closing),
    ):
        book.choice(7, "quiz", ref, fr, en, choices, why, why)


MODULES = [
    ("Création et janvier", "Set-up and January", "Ouvrir le dépôt et tenir le premier mois au SMT.",
     "Open the depot and keep the first month on a cash basis."),
    ("Premier trimestre (février et mars)", "First quarter (February and March)", "Tenir recettes et dépenses.",
     "Keep receipts and payments."),
    ("Deuxième trimestre", "Second quarter", "Rapprocher caisse, Orange Money et banque.",
     "Reconcile till, Orange Money and bank."),
    ("Troisième trimestre et décision", "Third quarter and decision", "Rester sous le seuil et déclarer la cessation à "
     "temps.", "Stay below the threshold and give notice of cessation in time."),
    ("Quatrième trimestre : naissance de la SARL", "Fourth quarter: the LLC is born",
     "Déposer le numéraire, évaluer les apports, signer les statuts.", "Pay in the cash, value the contributions, "
     "sign the articles."),
    ("Clôture de l'Ets et bilan d'ouverture", "Closing the business and opening balance sheet",
     "Compter le stock, solder les comptes du dépôt, ouvrir le bilan de la SARL.",
     "Count the stock, settle the depot's accounts, open the LLC's balance sheet."),
    ("Déclarations de clôture", "Closing returns", "Déclarer l'art. 74, la clôture avec l'IGS et la DSF du SMT.",
     "File the art. 74 return, the closing return with the IGS and the cash-basis return."),
]


def sections(book, special):
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    kinds = {p["ref"]: p["kind"] for p in book.pieces}
    out = {m: [] for m in range(1, 8)}
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file", narrative_b2.company_file("fr"),
                   narrative_b2.company_file("en")))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   "Chaque démarche précise l'organisme, les documents et ce que l'on obtient [[cgi:art. C 39]].\n\n"
                   f"{proc}\n", f"Each procedure gives the body, documents and outcome [[cgi:art. C 39]].\n\n{proc}\n"))
    for month in range(1, 13):
        module = MODULE_OF_MONTH[month]
        opening = [ref for ref in by_month[month] if kinds[ref] == "balance"]
        scenes = narrative_b2.month_scenes(book, special, month)
        told = {s["ref"] for s in scenes}
        others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
        out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}",
                            narrative_b2.month_section(month, scenes, opening, others, "fr"),
                            narrative_b2.month_section(month, scenes, opening, others, "en")))
        if month == 9:
            told_ = narrative_b2.cessation_section(special)
            out[4].append(("04-cessation", "Déclarer la cessation", "Notice of cessation", told_["fr"], told_["en"]))
        if month == 12:
            told_ = narrative_b2.sarl_procedures_section(special)
            out[5].append(("04-creation-sarl", "Créer la SARL", "Setting up the LLC", told_["fr"], told_["en"]))
    told = narrative_b2.year_end_sections(book, special)
    out[6].append(("01-cloture", "Clôture de l'Ets et bilan d'ouverture de la SARL", "Closing the business and the LLC's "
                   "opening balance sheet", told["close"]["fr"], told["close"]["en"]))
    out[7].append(("01-declarations", "Déclarations de 2027", "2027 returns", told["returns"]["fr"], told["returns"]["en"]))
    return out


def main():
    book, special = build()
    balances(book)
    build_questions(book, special)
    module_sections = sections(book, special)
    modules = []
    for number, (title_fr, title_en, comp_fr, comp_en) in enumerate(MODULES, start=1):
        folder = f"b2/m{number}"
        entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": text(comp_fr, comp_en), "sections": entries})
    write(OUT / "b2" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "b2" / "ledger.json", book.entries)
    partie = {
        "slug": "b2", "title": text("Parcours B2 : dépôt de boissons, de l'IGS à la SARL (Ets Essomba Boissons)",
                                    "Track B2: drinks depot, from the IGS to an LLC (Ets Essomba Boissons)"),
        "description": text("Établissement individuel à l'IGS, au SMT, à Douala-Bépanda, apporté le 1er janvier 2027 à "
                            "une SARL au réel.", "Sole proprietorship under the IGS, cash basis, in Douala, contributed "
                            "on 1 January 2027 to an LLC under the actual regime."),
        "regime": "igs_puis_reel", "systeme_comptable": "smt", "forme": "individuelle", "centre_impots": "cfl",
        "chiffre_affaires_vise": 46000000, "sous_comptes": {"5522": text("Orange Money", "Orange Money")},
        "pieces": "b2/pieces.json", "ledger": "b2/ledger.json", "exam": {"questions_per_module": 4}, "modules": modules}
    write_manifest({}, partie)
    low = min(ledger.account_balance(book.entries, "521", datetime.date.fromisoformat(e["date"]))
              for e in book.entries if e["date"] < "2027-01-01")
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, IGS {special['igs']}, "
          f"résultat SMT {special['smt_result']}, banque au plus bas {low}, numéraire {CASH_CONTRIBUTION}, "
          f"solde de clôture {special['closing_transfer']}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
