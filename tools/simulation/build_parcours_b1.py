"""Génère le parcours B1 de la simulation (Ets Bilounga Boissons, exercice 2026) dans content/simulation/b1/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_b1

Établissement individuel de Mme Thérèse Bilounga à Yaoundé-Ekounou, à l'IGS (CGI art. C 38 à C 44), qui tient le
système minimal de trésorerie (AUDCIF art. 13 et 28) ; profil validé le 2026-11-02 (S39). Le dépôt achète la bière à
la brasserie fictive du parcours B3 et la revend au casier, au comptant et par Orange Money, casier plein contre casier
vide. Pas de TVA collectée ni déductible ; le précompte de 5 % subi reste dans le coût d'achat (S40) ; le loyer est
payé brut ; les prélèvements de l'exploitante passent au compte de l'exploitant. En 2027 : déclaration de l'art. 74
au 15 mars, IGS au 15 avril (art. C 41), DSF du SMT au 15 mai (art. C 44) (S38). Questions numériques ou à choix,
sans écriture `journal` (S14). Les contrôles bloquants de courses/tests/content_rules.py vérifient la sortie.
"""
import calendar
import datetime
from decimal import Decimal as D

from referentiel import calculs
from tools.simulation import ledger, narrative_b1
from tools.simulation.build_parcours_a import (
    MONTHS_EN, MONTHS_FR, OUT, P, YEAR, Book, balances, d, fcfa, line, piece_list, split_usage, text, tva, workday,
    write, write_manifest,
)
from tools.simulation.build_parcours_b3 import ascii_name

SELLER = {"name": "Ets Bilounga Boissons", "niu": "P012600025517B", "rccm": "RC/YAO/2026/A/1407", "regime": "IGS",
          "centre": "Centre de fiscalité locale de Yaoundé IV", "address": "Ekounou, Yaoundé"}
BREWERY = {"name": "Brasseries de la Sanaga SA (fictive)", "niu": "M019800000731S", "rccm": "RC/YAO/1998/B/0071",
           "regime": "réel", "centre": "DGE", "address": "Zone industrielle de Nsam, Yaoundé"}
OWN = {"name": SELLER["name"], "niu": SELLER["niu"]}
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}

PRICE = (6100, 6160)            # casier de 12 bouteilles de 65 cl, HT, au premier puis au second semestre (comme B3)
SELL = 8400                     # prix de vente du casier plein, contre un casier vide (700 F la bouteille)
SOLD = [230, 245, 255, 250, 255, 245, 250, 255, 260, 265, 280, 340]  # casiers vendus ; fêtes de fin d'année
OPENING_BUFFER = 30             # casiers d'avance achetés en janvier, toujours en stock au 31 décembre
MOMO_SHARE = 3                  # un casier sur trois est payé par Orange Money
CAPITAL, RENT, WITHDRAWAL = 3000000, 50000, 100000
TRIP, CRATES_PER_TRIP = 1500, 10  # livraison en pousse-pousse : 1 500 F la course de 10 casiers
OM_FEE, BANK_FEE = 4000, 2500


def last(month):
    return calendar.monthrange(YEAR, month)[1]


def price(month):
    return PRICE[0 if month <= 6 else 1]


PROCEDURES = [
    ("Immatriculation de l'établissement au CFCE de Yaoundé", "Registering the sole proprietorship at the Yaoundé "
     "business centre",
     text("Centre de formalités de création d'entreprises (CFCE) de Yaoundé", "Yaoundé business formalities centre"),
     text("Immatriculer l'établissement individuel de Mme Bilounga au registre du commerce",
          "Register Mrs Bilounga's sole proprietorship in the trade register"),
     [text("CNI de l'exploitante, extrait de casier judiciaire ou déclaration sur l'honneur",
           "Owner's ID, criminal record extract or sworn statement"),
      text("Plan de localisation du dépôt, contact téléphonique", "Depot location map, phone"),
      text("Frais de création (à vérifier au CFCE)", "Creation fees (check at the CFCE)")],
     text("Registre de commerce, carte de contribuable (NIU), attestation de création",
          "Trade register, taxpayer card, creation certificate"),
     "[[source:minfi-cfce]] [[source:minfi-formalites]]"),
    ("Rattachement à l'IGS au centre de fiscalité locale", "IGS attachment at the local tax office",
     text("Centre de fiscalité locale de Yaoundé IV", "Yaoundé IV local tax office"),
     text("Suivi à l'IGS : chiffre d'affaires prévisionnel de 28 millions, sous le seuil de 50 millions du négoce",
          "IGS follow-up: forecast turnover of 28 million, below the 50 million trading threshold"),
     [text("Carte de contribuable délivrée au CFCE", "Taxpayer card issued by the CFCE"),
      text("Déclaration du chiffre d'affaires prévisionnel", "Forecast turnover statement")],
     text("Suivi à l'IGS : déclaration et paiement avant le 15 avril, DSF du SMT avant le 15 mai",
          "IGS follow-up: return and payment by 15 April, cash-basis return by 15 May"),
     "[[cgi:art. C 39]] [[cgi:art. C 41]] [[cgi:art. C 44]]"),
    ("Ouverture du compte bancaire", "Opening the bank account",
     text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
     text("Payer la brasserie par virement et verser la recette chaque semaine",
          "Pay the brewery by transfer and deposit the takings every week"),
     [text("Demande d'ouverture, registre de commerce, carte de contribuable", "Request, trade register, taxpayer card"),
      text("CNI de l'exploitante, plan de localisation", "Owner's ID, location map")],
     text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
    ("Compte marchand Orange Money", "Orange Money merchant account",
     text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
     text("Encaisser les ventes par Orange Money", "Collect sales through Orange Money"),
     [text("Registre de commerce, carte de contribuable", "Trade register, taxpayer card"),
      text("CNI de l'exploitante, RIB", "Owner's ID, bank details")],
     text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
]


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
    book, special = Book("B1"), {"months": {}, "buys": {}}
    special["procedures"] = [book.piece(1, "demarche", d(1, 2), f"Démarche : {fr}", f"Procedure: {en}",
                                        {"organisme": body, "objet": purpose, "documents_a_fournir": docs,
                                         "document_obtenu": got, "source": source})
                             for fr, en, body, purpose, docs, got, source in PROCEDURES]
    special["capital"] = book.piece(1, "releve_bancaire", d(1, 2), "Avis de crédit : apport de l'exploitante (Banque X)",
                                    "Credit notice: owner's contribution (Bank X)",
                                    {"fields": [{"label": text("Déposante", "Depositor"), "value": "Thérèse Bilounga"}],
                                     "totals": [{"label": text("Économies versées au compte du dépôt",
                                                               "Savings paid into the depot account"),
                                                 "amount": CAPITAL}]})
    book.entry(d(1, 2), special["capital"], line("521", "debit", CAPITAL), line("103", "credit", CAPITAL))
    lots, number = [], 0
    for month in range(1, 13):
        end, refs = last(month), {}
        mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
        sold = SOLD[month - 1]
        bought = sold + (OPENING_BUFFER if month == 1 else 0)
        buys = []
        for i, (day, qty) in enumerate(((workday(month, 5), bought // 2), (workday(month, 19), bought - bought // 2))):
            number += 1
            refs[f"purchase{i}"], info = purchase(book, month, day, qty, f"BS-2026-{4100 + number:05d}",
                                                  f"DGI-SFE-2026-{8100 + number:06d}")
            buys.append(info)
        lots.append((bought, price(month)))
        special["buys"][month] = buys
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
        # La recette se reporte au brouillard chaque soir ; le livre la regroupe au 15 et en fin de mois.
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
        rent_day = d(month, 15)  # le bail prévoit le paiement au 15, sur la recette de la quinzaine
        refs["rent"] = book.piece(month, "recu_caisse", rent_day, f"Quittance de loyer du dépôt, {mfr}",
                                  f"{men} depot rent receipt",
                                  {"fields": [{"label": text("Bailleur", "Landlord"), "value": "M. Owona (fictif)"},
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
        # Versements des espèces : le 15 et en fin de mois, la caisse ne garde que le fonds de 20 000.
        mid = d(month, 15)
        first = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, 15))
        first_deposit = max(int(first) - 20000, 0) // 1000 * 1000
        if first_deposit:
            book.entry(mid, None, line("585", "debit", first_deposit), line("5711", "credit", first_deposit))
        cash_end = ledger.account_balance(book.entries, "5711", datetime.date(YEAR, month, end))
        second = int(cash_end) - 20000
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
                (text("Virement personnel de l'exploitante (prélèvement)", "Owner's personal transfer (drawings)"),
                 WITHDRAWAL), (text("Frais de tenue de compte", "Account fees"), BANK_FEE)]
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {mfr} (Banque X)",
                                  f"{men} bank statement (Bank X)",
                                  {"totals": [{"label": label, "amount": amount} for label, amount in rows]})
        book.entry(d(month, end), refs["bank"], line("521", "debit", deposits + transfer),
                   line("585", "credit", deposits + transfer), line("1042", "debit", WITHDRAWAL),
                   line("631", "debit", BANK_FEE), line("521", "credit", WITHDRAWAL + BANK_FEE))
        refs["sold"], refs["momo_qty"], refs["trips"], refs["deposit_total"] = sold, momo, trips, deposits
        special["months"][month] = refs
    special["lots"] = lots
    year_end(book, special)
    return book, special


def year_end(book, special):
    lots = [(D(q), D(u)) for q, u in special["lots"]]
    bought = sum(q for q, _ in special["lots"])
    sold = sum(SOLD)
    result = calculs.sortie_cmup(lots, D(sold))
    special["sheet"] = book.piece(12, "fiche_stock", d(12, 31), "Fiche de stock des casiers (inventaire du 31 décembre)",
                                  "Crate stock card (31 December count)",
                                  {"fields": [{"label": text("Achetés / vendus / comptés au 31/12",
                                                             "Bought / sold / counted at 31/12"),
                                               "value": f"{bought} / {sold} / {bought - sold}"}],
                                   "lines": [{"label": text(f"Lot de {MONTHS_FR[i]}", f"{MONTHS_EN[i]} lot"), "qty": q,
                                              "unit_price": u, "amount": q * u}
                                             for i, (q, u) in enumerate(special["lots"])]})
    entries = book.entries
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
    assert cash + stock == CAPITAL - withdrawals + smt_result, "bilan du SMT déséquilibré"
    special.update(turnover=turnover, igs=igs, igs_cga=igs_cga, classes=[[int(c), int(m)] for c, m in classes],
                   stock=(lots, sold, result), stock_value=stock, expenses=expenses, cash=int(cash),
                   smt_result=smt_result, withdrawals=withdrawals,
                   precompte=sum(b["withheld"] for b in buys), vat_paid=sum(b["tax"] for b in buys),
                   purchases=total("6011"), rent=total("6222"), transport=total("612"), fees=total("631"),
                   cash_margin=turnover - total("6011"))
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
    special["igs_return"] = book.piece(4, "declaration", d(4, 9, YEAR + 1), "Déclaration annuelle de l'IGS 2026",
                                       "2026 yearly IGS return",
                                       {"fields": [{"label": text("Chiffre d'affaires HT 2026", "2026 turnover"),
                                                    "value": fcfa(turnover)},
                                                   {"label": text("Classe du tarif", "Tariff class"),
                                                    "value": text("Classe 9 : de 20 à moins de 30 millions",
                                                                  "Class 9: 20 to under 30 million")},
                                                   {"label": text("Échéance", "Deadline"),
                                                    "value": text("15 avril 2027, paiement compris (CGI art. C 41)",
                                                                  "15 April 2027, payment included")}],
                                        "totals": [{"label": text("IGS annuel (CGI art. C 40)", "Yearly IGS"),
                                                    "amount": igs}]}, year=YEAR + 1)
    for table, fr, en, rows in (
        ("compte_resultat_smt", "DSF du SMT 2026 : compte de résultat", "2026 cash-basis return: income statement",
         [("Recettes de l'exercice (ventes au casier)", "Receipts of the year (crate sales)", turnover),
          ("Dépenses de l'exercice (achats, loyer, transport, frais)", "Payments of the year", expenses),
          ("Variation des stocks (stock final)", "Change in inventories (closing stock)", stock),
          ("Résultat de l'exercice", "Profit for the year", smt_result)]),
        ("bilan_smt", "DSF du SMT 2026 : bilan", "2026 cash-basis return: balance sheet",
         [("Trésorerie : banque, caisse et Orange Money", "Cash: bank, till and Orange Money", cash),
          ("Stock de casiers", "Crate stock", stock),
          ("Capital personnel", "Personal capital", CAPITAL),
          ("Prélèvements de l'exploitante (à déduire)", "Owner's drawings (deducted)", withdrawals),
          ("Résultat de l'exercice", "Profit for the year", smt_result)]),
    ):
        book.piece(5, "declaration", d(5, 7, YEAR + 1), fr, en,
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
         f"5% withholding on the first {men} delivery?", "5 % du HT : Mme Bilounga est à l'IGS (CGI art. 21 (3))."),
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
         "Le 15 et en fin de mois, la caisse ne garde que son fonds de 20 000 ; virement interne par 585."),
    ]
    for piece, value, fr, en, why in asks:
        book.numeric(module, "exam", value, fr, en, why, why, piece=piece)
    receipts = refs["sold"] * SELL
    book.numeric(module, "exam", receipts, f"Total des recettes de {mfr} au cahier du SMT ?",
                 f"Total {men} receipts in the cash book?", "Espèces et Orange Money : tous les casiers vendus × 8 400.",
                 "Cash and Orange Money.", piece=refs["cash"])
    payments = first["due"] + second["due"] + RENT + refs["trips"] * TRIP + OM_FEE + BANK_FEE
    book.numeric(module, "exam", payments, f"Total des dépenses de {mfr} au cahier du SMT (hors prélèvement) ?",
                 f"Total {men} payments (drawings excluded)?",
                 "Brasserie, loyer, pousse-pousse et frais ; le prélèvement de l'exploitante n'est pas une dépense de "
                 "l'activité.", "Brewery, rent, carts and fees; drawings are not a business payment.", piece=refs["bank"])
    end = datetime.date(YEAR, month, last(month))
    book.numeric(module, "exam", ledger.account_balance(book.entries, "521", end),
                 f"Solde du compte bancaire au {last(month)} {mfr} ?", f"Bank balance at {men} {last(month)}?",
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
    ("Que délivre le CFCE à Mme Bilounga ?", "What does the CFCE give Mrs Bilounga?",
     ("Registre de commerce, carte de contribuable et attestation de création", "Trade register, taxpayer card"),
     ("Des statuts", "Articles of association")),
    ("Pourquoi le dépôt relève-t-il de l'IGS ?", "Why is the depot under the IGS?",
     ("CA prévisionnel sous 50 millions, activité de négoce", "Forecast turnover below 50 million, trading"),
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
    book.numeric(1, "exam", CAPITAL, "Économies apportées par Mme Bilounga au démarrage ?", "Owner's start-up savings?",
                 "Capital personnel (103) : un établissement individuel n'a ni capital social ni associés.",
                 "Personal capital (103).", piece=special["capital"])
    book.choice(1, "quiz", special["capital"], "Un établissement individuel a-t-il un capital social (101) ?",
                "Does a sole proprietorship have share capital (101)?",
                [("Non : capital personnel de l'exploitante (103)", "No: owner's personal capital (103)", True),
                 ("Oui", "Yes", False)], "Pas d'associés, pas de parts.", "No partners, no shares.")
    jan = special["months"][1]
    first, second = special["buys"][1]
    for piece, value, fr, en, why in (
        (jan["purchase0"], first["qty"] + second["qty"], "Casiers achetés en janvier, les deux livraisons ensemble ?",
         "Crates bought in January, both deliveries?", "Ventes du mois et 30 casiers d'avance pour ne jamais manquer."),
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
        (1, special["months"][1]["purchase0"], "Mme Bilounga récupère la TVA payée à la brasserie.",
         "Mrs Bilounga recovers the VAT paid to the brewery.", False,
         "Faux : à l'IGS, on ne facture ni ne déduit la TVA ; elle reste dans le coût (CGI art. C 38)."),
        (1, special["months"][1]["rent"], "Le dépôt retient 10 % de précompte sur le loyer.",
         "The depot withholds 10% on the rent.", False,
         "Faux : un locataire à l'IGS paie le loyer brut ; le précompte de l'art. 87 vise les locataires au réel."),
        (2, special["months"][2]["purchase0"], "Le précompte de 5 % s'impute sur l'IGS de l'année.",
         "The 5% withholding is credited against the year's IGS.", False,
         "Faux : le CGI n'en prévoit l'imputation que sur l'IS ou l'IRPP (art. 21 (3)) ; il reste dans le coût (S40)."),
        (3, special["months"][4]["bank"], "Le virement personnel de Mme Bilounga est une dépense du dépôt.",
         "Mrs Bilounga's personal transfer is a depot expense.", False,
         "Faux : c'est un prélèvement de l'exploitante (1042), pas une charge."),
        (4, special["months"][8]["orange"], "Un client qui paie par Orange Money doit une TVA en plus du prix.",
         "A customer paying by Orange Money owes VAT on top.", False, "Faux : le dépôt est à l'IGS, il ne facture pas de TVA."),
        (5, special["months"][12]["cash"], "En décembre, les ventes montent avec les fêtes : le dépôt peut quitter l'IGS "
         "en cours d'année s'il dépasse 50 millions.", "December sales rise: could the depot leave the IGS mid-year above "
         "50 million?", True, "Vrai en principe : un dépassement en cours d'exercice entraîne le reclassement d'office au "
         "réel (CGI art. C 39 (2)) ; ici le dépôt reste loin du seuil."),
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
    inventory_questions(book, special)
    igs_questions(book, special)
    for module in book.questions:
        split_usage(book.questions[module])


def inventory_questions(book, special):
    sheet = special["sheet"]
    lots, sold, result = special["stock"]
    args = [[[int(q), int(u)] for q, u in lots], int(sold)]
    for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré du casier", "weighted average crate cost"),
                        ("valeur_sortie", "coût des casiers vendus au CMUP", "cost of crates sold at WAC")):
        book.numeric(6, "exam", result[key], f"Inventaire : {fr} (prix HT de la brasserie) ?", f"Count: {en} (brewery HT price)?",
                     "CMUP sur les prix HT des lots de l'année, arrondi au franc ; calculateur stock.", "Period WAC.",
                     piece=sheet, calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
    # Au SMT, aucune écriture d'inventaire : la valeur du stock final ne corrige que la DSF du SMT (AUDCIF art. 28).
    book.numeric(6, "exam", result["valeur_stock"], "Inventaire : valeur du stock final au CMUP, portée à la DSF du SMT ?",
                 "Count: closing stock at WAC, carried to the cash-basis return?",
                 "Casiers comptés × coût moyen pondéré ; pas d'écriture au SMT, la valeur va à la DSF.",
                 "Crates counted × WAC; no entry under the cash basis.", piece=sheet)
    peps = calculs.sortie_peps(lots, D(sold))
    book.numeric(6, "exam", peps["valeur_sortie"], "Inventaire : coût des casiers vendus en PEPS (contraste) ?",
                 "Count: cost of crates sold under FIFO?", "Les lots les plus anciens, moins chers, sortent d'abord.",
                 "Oldest, cheaper lots go first.", piece=sheet,
                 calcul={"fonction": "sortie_peps", "args": args, "resultat": ["valeur_sortie"]})
    book.numeric(6, "exam", peps["valeur_stock"], "Inventaire : valeur du stock final en PEPS (contraste) ?",
                 "Count: closing stock under FIFO?", "Les casiers en stock sont les derniers achetés, au prix de juillet.",
                 "The crates left are the last bought.", piece=sheet)
    momo_total = sum(special["months"][m]["momo_qty"] for m in range(1, 13)) * SELL
    book.numeric(6, "exam", momo_total, "Encaissements Orange Money de l'année ?", "Year's Orange Money receipts?",
                 "Un casier sur trois, payé par téléphone (5522).", "One crate in three, paid by phone.", piece=sheet)
    book.numeric(6, "exam", special["turnover"] - momo_total, "Recettes en espèces de l'année ?", "Year's cash receipts?",
                 "Recettes totales moins Orange Money.", "Total receipts less Orange Money.", piece=sheet)
    book.numeric(6, "exam", sum(q for q, _ in special["lots"]) - sold, "Casiers comptés au 31 décembre ?",
                 "Crates counted on 31 December?", "Achetés moins vendus : les 30 casiers d'avance de janvier.",
                 "Bought less sold.", piece=sheet)
    for value, fr, en, why in (
        (special["turnover"], "Recettes de l'année (ventes au casier) ?", "Year's receipts?", "Compte 7011, espèces et "
         "Orange Money."),
        (special["purchases"], "Coût total des achats de bière de l'année ?", "Year's beer purchases, full cost?",
         "HT, TVA et précompte : tout reste dans le coût à l'IGS (6011)."),
        (special["precompte"], "Précomptes de 5 % subis sur l'année ?", "Withholdings suffered over the year?",
         "Vingt-quatre livraisons ; ils ne s'imputent pas sur l'IGS (S40)."),
        (special["vat_paid"], "TVA et CAC payées à la brasserie sur l'année, non récupérables ?",
         "Non-recoverable VAT paid to the brewery?", "À l'IGS, la TVA payée est un coût."),
        (special["cash_margin"], "Marge de l'année : recettes moins coût des achats ?", "Year's margin: receipts less "
         "purchases?", "Environ 800 F par casier : le métier de dépôt vit de petites marges."),
        (special["rent"], "Loyers payés sur l'année ?", "Rent paid over the year?", "Douze loyers bruts de 50 000."),
        (special["transport"], "Courses de pousse-pousse de l'année ?", "Year's push-cart costs?", "Compte 612."),
        (special["fees"], "Frais bancaires et Orange Money de l'année ?", "Year's bank and Orange Money fees?",
         "Compte 631."),
        (special["withdrawals"], "Prélèvements de Mme Bilounga sur l'année ?", "Mrs Bilounga's drawings over the year?",
         "Douze virements personnels de 100 000 (1042)."),
    ):
        book.numeric(6, "exam", value, fr, en, why, why, piece=sheet)
    for fr, en, choices, why in (
        ("Pourquoi compter le stock à l'IGS, sans écritures d'inventaire ?", "Why count stock under the IGS?",
         [("La DSF du SMT corrige le résultat de la variation des stocks", "The cash-basis return adjusts for stock",
           True), ("Ce n'est pas utile", "It is not useful", False)], "AUDCIF art. 28."),
        ("Quel est le coût unitaire le plus élevé au 31 décembre ?", "Which unit cost is higher on 31 December?",
         [("Le PEPS (derniers prix)", "FIFO (latest prices)", True), ("Le CMUP", "WAC", False)],
         "Les prix ont monté en juillet : le PEPS garde les derniers casiers, les plus chers."),
        ("La TVA payée à la brasserie est-elle une créance sur l'État ?", "Is the VAT paid a receivable on the State?",
         [("Non : un coût, à l'IGS", "No: a cost under the IGS", True), ("Oui (445)", "Yes (445)", False)],
         "L'IGS est libératoire de la TVA (CGI art. C 38)."),
    ):
        book.choice(6, "exam", sheet, fr, en, choices, why, why)
    book.choice(6, "quiz", sheet, "Les prélèvements de l'exploitante réduisent le résultat du SMT.",
                "The owner's drawings reduce the cash-basis profit.", [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : ils réduisent ses capitaux, pas le résultat.", "False: they reduce equity, not profit.",
                qtype="truefalse")


def igs_questions(book, special):
    igs_ref, smt_ref, art74 = special["igs_return"], special["smt_return"], special["art74"]
    book.numeric(7, "exam", special["igs"], "IGS annuel 2026 du dépôt ?", "2026 yearly IGS of the depot?",
                 "Tarif de la classe 9 (de 20 à moins de 30 millions) (CGI art. C 40 (1)).", "Class 9 tariff.",
                 piece=igs_ref, calcul={"fonction": "igs_annuel", "args": [special["turnover"], special["classes"]],
                                        "resultat": []})
    book.numeric(7, "exam", special["igs_cga"], "IGS 2026 si Mme Bilounga adhère à un Centre de Gestion Agréé ?",
                 "2026 IGS with a registered management centre?", "Tarif réduit de moitié (CGI art. C 40 (4)).",
                 "Halved tariff.", piece=igs_ref,
                 calcul={"fonction": "igs_annuel", "args": [special["turnover"], special["classes"], True], "resultat": []})
    book.numeric(7, "exam", int(calculs.igs_annuel(D(30000000), [(D(c), D(m)) for c, m in special["classes"]])),
                 "Contraste : IGS dû si le chiffre d'affaires avait atteint 30 millions ?",
                 "Contrast: IGS due had turnover reached 30 million?",
                 "Classe 10 (de 30 à moins de 50 millions) : le tarif double d'une classe à l'autre (art. C 40).",
                 "Class 10: the tariff doubles.", piece=igs_ref,
                 calcul={"fonction": "igs_annuel", "args": [30000000, special["classes"]], "resultat": []})
    for value, fr, en, why, ref in (
        (int(P["igs.seuil_comptabilite"]), "Chiffre d'affaires à partir duquel la DSF du SMT est obligatoire ?",
         "Turnover from which the cash-basis return is compulsory?", "10 millions (CGI art. C 44).", smt_ref),
        (50000000, "Seuil de chiffre d'affaires du négoce au-delà duquel le dépôt passerait au réel ?",
         "Trading turnover threshold above which the depot would move to the actual regime?",
         "50 millions pour le négoce, 30 pour les professions libérales (CGI art. C 39).", igs_ref),
        (special["turnover"], "Chiffre d'affaires déclaré pour l'IGS 2026 ?", "Turnover declared for the 2026 IGS?",
         "Total des recettes de l'année.", igs_ref),
        (special["igs"] - special["igs_cga"], "Économie d'IGS procurée par un Centre de Gestion Agréé ?",
         "IGS saving with a management centre?", "La moitié du tarif.", igs_ref),
        (special["igs"], "Montant à payer avec la déclaration de l'IGS, au plus tard le 15 avril 2027 ?",
         "Amount due with the IGS return by 15 April 2027?", "Paiement en une fois avec la déclaration (art. C 41).",
         igs_ref),
        (special["igs"] // 4, "Quotité trimestrielle si Mme Bilounga opte pour le paiement fractionné ?",
         "Quarterly instalment under the split-payment option?", "Un quart de l'IGS annuel, dans les 15 jours qui "
         "suivent chaque trimestre (art. C 41, circulaire LF 2026).", igs_ref),
        (special["smt_result"], "DSF du SMT : résultat de l'exercice 2026 ?", "Cash-basis return: 2026 profit?",
         "Recettes moins dépenses, plus le stock final (AUDCIF art. 28).", smt_ref),
        (special["cash"], "DSF du SMT : trésorerie au 31 décembre ?", "Cash-basis return: cash at 31 December?",
         "Banque, caisse et Orange Money.", smt_ref),
        (special["stock_value"], "DSF du SMT : stock de casiers au 31 décembre ?", "Cash-basis return: crate stock?",
         "Stock final au CMUP.", smt_ref),
        (special["expenses"], "DSF du SMT : dépenses de l'exercice ?", "Cash-basis return: payments of the year?",
         "Achats, loyer, pousse-pousse et frais (classes 6).", smt_ref),
        (special["smt_result"] - special["igs"], "Résultat 2026 après l'IGS dû en 2027 ?", "2026 profit after the IGS?",
         "L'IGS pèse lourd sur une petite marge : d'où l'intérêt d'un Centre de Gestion Agréé.", igs_ref),
        (special["turnover"], "Chiffre d'affaires porté sur la déclaration de l'art. 74 ?",
         "Turnover on the art. 74 return?", "Une personne physique à l'IGS dépose aussi sa déclaration annuelle de "
         "revenus (CGI art. C 39 (4) et 74).", art74),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref)
    for fr, en, choices, why, ref in (
        ("Date limite de la déclaration et du paiement de l'IGS 2026 ?", "Deadline of the 2026 IGS return?",
         [("15 avril 2027", "15 April 2027", True), ("15 mars 2027", "15 March 2027", False)],
         "CGI art. C 41, modifié par la LF 2026.", igs_ref),
        ("Date limite de la DSF du SMT ?", "Deadline of the cash-basis return?",
         [("15 mai 2027", "15 May 2027", True), ("15 avril 2027", "15 April 2027", False)],
         "CGI art. C 44 : dès 10 millions de chiffre d'affaires.", smt_ref),
        ("Date limite de la déclaration de revenus de l'art. 74 ?", "Deadline of the art. 74 income return?",
         [("15 mars 2027", "15 March 2027", True), ("15 mai 2027", "15 May 2027", False)],
         "CGI art. 74, rendu applicable aux personnes physiques à l'IGS par l'art. C 39 (4).", art74),
        ("Mme Bilounga dépose-t-elle une DSF du système normal ?", "Does Mrs Bilounga file the standard return?",
         [("Non : la DSF du SMT", "No: the cash-basis return", True), ("Oui", "Yes", False)],
         "À l'IGS, SMT et DSF du SMT (art. C 44, S14, S38).", smt_ref),
        ("L'IGS dépend-il du bénéfice du dépôt ?", "Does the IGS depend on the depot's profit?",
         [("Non : de la classe de chiffre d'affaires", "No: on the turnover class", True), ("Oui", "Yes", False)],
         "Tarif forfaitaire par classe (art. C 40).", igs_ref),
        ("L'IGS libère-t-il Mme Bilounga de la TVA et de l'IRPP sur ses bénéfices ?", "Does the IGS discharge VAT and "
         "income tax on profits?", [("Oui (art. C 38)", "Yes (art. C 38)", True), ("Non", "No", False)],
         "Impôt synthétique, libératoire de la patente, de la TVA et de l'IRPP (BIC).", igs_ref),
    ):
        book.choice(7, "quiz", ref, fr, en, choices, why, why)


MODULES = [
    ("Création et janvier", "Set-up and January", "Ouvrir le dépôt et tenir le premier mois au SMT.",
     "Open the depot and keep the first month on a cash basis."),
    ("Premier trimestre (février et mars)", "First quarter (February and March)", "Tenir recettes et dépenses.",
     "Keep receipts and payments."),
    ("Deuxième trimestre", "Second quarter", "Rapprocher caisse, Orange Money et banque.",
     "Reconcile till, Orange Money and bank."),
    ("Troisième trimestre", "Third quarter", "Suivre la hausse du prix de la brasserie.", "Follow the brewery's price rise."),
    ("Quatrième trimestre", "Fourth quarter", "Préparer la clôture des fêtes.", "Prepare the festive year end."),
    ("Clôture et inventaire", "Year-end and count", "Compter les casiers et faire les totaux de l'année.",
     "Count crates and total the year."),
    ("IGS et DSF du SMT", "IGS and cash-basis return", "Déclarer l'art. 74, l'IGS et la DSF du SMT à leurs échéances.",
     "File the art. 74 return, the IGS and the cash-basis return on time."),
]


def sections(book, special):
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    kinds = {p["ref"]: p["kind"] for p in book.pieces}
    out = {m: [] for m in range(1, 8)}
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file", narrative_b1.company_file("fr"),
                   narrative_b1.company_file("en")))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   "Chaque démarche précise l'organisme, les documents et ce que l'on obtient [[cgi:art. C 39]].\n\n"
                   f"{proc}\n", f"Each procedure gives the body, documents and outcome [[cgi:art. C 39]].\n\n{proc}\n"))
    for month in range(1, 13):
        module = MODULE_OF_MONTH[month]
        opening = [ref for ref in by_month[month] if kinds[ref] == "balance"]
        scenes = narrative_b1.month_scenes(book, special, month)
        told = {s["ref"] for s in scenes}
        others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
        out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}",
                            narrative_b1.month_section(month, scenes, opening, others, "fr"),
                            narrative_b1.month_section(month, scenes, opening, others, "en")))
    told = narrative_b1.year_end_sections(book, special)
    out[6].append(("01-cloture", "Clôture et inventaire", "Year-end and count", told["close"]["fr"], told["close"]["en"]))
    out[7].append(("01-declarations", "Déclarations de 2027", "2027 returns", told["returns"]["fr"], told["returns"]["en"]))
    return out


def main():
    book, special = build()
    balances(book)
    build_questions(book, special)
    module_sections = sections(book, special)
    modules = []
    for number, (title_fr, title_en, comp_fr, comp_en) in enumerate(MODULES, start=1):
        folder = f"b1/m{number}"
        entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": text(comp_fr, comp_en), "sections": entries})
    write(OUT / "b1" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "b1" / "ledger.json", book.entries)
    partie = {
        "slug": "b1", "title": text("Parcours B1 : dépôt de boissons à l'IGS (Ets Bilounga Boissons)",
                                    "Track B1: drinks depot under the IGS (Ets Bilounga Boissons)"),
        "description": text("Établissement individuel à l'IGS, au SMT : dépôt de boissons à Yaoundé-Ekounou.",
                            "Sole proprietorship under the IGS, cash basis: drinks depot in Yaoundé."),
        "regime": "igs", "systeme_comptable": "smt", "forme": "individuelle", "centre_impots": "cfl",
        "chiffre_affaires_vise": 28000000, "sous_comptes": {"5522": text("Orange Money", "Orange Money")},
        "pieces": "b1/pieces.json", "ledger": "b1/ledger.json", "exam": {"questions_per_module": 4}, "modules": modules}
    write_manifest({}, partie)
    low = min(ledger.account_balance(book.entries, "521", datetime.date.fromisoformat(e["date"])) for e in book.entries)
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, IGS {special['igs']}, "
          f"résultat SMT {special['smt_result']}, banque au plus bas {low}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
