"""Génère le parcours D de la simulation (Ets Tchinda Froid, exercice 2026) dans content/simulation/d/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_d

Établissement individuel au réel rattaché au CIME de Yaoundé (profil validé le 2026-11-02, S36 ; échéance S37) :
Jean-Claude Tchinda, technicien frigoriste, entretient et dépanne des climatiseurs et des chambres froides (706) pour
des clients publics et privés. TVA des services exigible à l'encaissement (CGI art. 134 (1) b, compte d'attente 471,
S24) ; à chaque paiement public, retenue de 5,5 % du HT (art. 21 (2)) et TVA retenue à la source (art. 149 (2)),
attestée par une ARS ; contraste à 11 % ; IRPP sur les BIC au taux de l'art. 17, au moins 2 % du CA (art. 69 (2)),
majoré des CAC (art. 71), porté au compte de l'exploitant ; déclaration des résultats au 15 mars 2027 (art. 74).
Tout est calculé par referentiel/calculs.py et tools/simulation/ledger.py ; les contrôles bloquants de
courses/tests/content_rules.py vérifient la sortie.
"""
import calendar
import datetime
from decimal import Decimal as D

from referentiel import calculs
from tools.simulation import ledger, narrative_d
from tools.simulation.build_parcours_a import (
    MONTHS_EN, MONTHS_FR, OUT, P, YEAR, Book, balances, d, fcfa, line, payroll, piece_list, split_usage, text, tva,
    workday, write, write_manifest,
)
from tools.simulation.build_parcours_b3 import ascii_name, piece_of, taxes_totals

SELLER = {"name": "Ets Tchinda Froid", "niu": "P012600021934R", "rccm": "RC/YAO/2026/A/1288",
          "regime": "réel", "centre": "CIME Yaoundé", "address": "Biyem-Assi, Yaoundé"}
SUPPLIER = {"name": "Frigo Pièces Mvog-Mbi SARL (fictive)", "niu": "M011100006653K", "rccm": "RC/YAO/2011/B/0733",
            "regime": "réel", "centre": "CIME Yaoundé", "address": "Mvog-Mbi, Yaoundé"}
TOOLS_SUPPLIER = {"name": "Quincaillerie du Centre SARL (fictive)", "niu": "M010800004219P",
                  "rccm": "RC/YAO/2008/B/0291", "regime": "réel", "centre": "CIME Yaoundé",
                  "address": "Marché central, Yaoundé"}
PRIVATE = [{"name": "Supermarché Le Panier de Biyem-Assi (fictif)", "niu": "M011400008127L"},
           {"name": "Résidence hôtelière Les Manguiers (fictive)", "niu": "M011800009316S"}]
PUBLIC = [{"name": "Hôpital de district de Biyem-Assi (fictif)", "niu": "M019900000418A"},
          {"name": "Commune d'arrondissement de Yaoundé VI (fictive)", "niu": "M019800000227C"}]
OWN = {"name": SELLER["name"], "niu": SELLER["niu"]}
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}

# Activité mensuelle : interventions facturées aux entreprises privées (dépannage, 60 000 HT), climatiseurs entretenus
# sous contrat public (25 000 HT l'appareil), dépannages à domicile payés par Orange Money (35 000 HT). La saison sèche
# (février à avril) fait monter la demande.
PRIVATE_JOBS = [38, 46, 50, 46, 40, 36, 32, 32, 36, 40, 40, 42]
PUBLIC_UNITS = [80, 96, 100, 96, 84, 80, 72, 72, 80, 84, 84, 88]
HOME_JOBS = [22, 30, 32, 30, 24, 22, 18, 18, 22, 24, 24, 26]
JOB, UNIT, HOME = 60000, 25000, 35000
# Approvisionnements stockés (6041) : quantités achetées et consommées par mois, prix d'achat (hausse trimestrielle).
FAMILIES = [("fluide frigorigène R410A (bouteille)", "R410A refrigerant (cylinder)", "3311", 20, 18, 48000, 1500),
            ("pièces détachées (kit)", "spare parts (kit)", "3312", 40, 37, 55000, 2000)]
STAFF = [("Aide-technicien", "Assistant technician", 130000)]
RENT, CASH_IN, VAN, TOOLS_HT, WITHDRAWAL = 150000, 3000000, 6000000, 450000, 300000
OM_FEE, BANK_FEE = 6000, 3500


def last(month):
    return calendar.monthrange(YEAR, month)[1]


def buy_price(base, rise, month):
    return base + rise * ((month - 1) // 3)


PROCEDURES = [
    ("Immatriculation de l'établissement au CFCE de Yaoundé", "Registering the sole proprietorship at the Yaoundé "
     "business centre",
     text("Centre de formalités de création d'entreprises (CFCE) de Yaoundé", "Yaoundé business formalities centre"),
     text("Immatriculer l'établissement individuel de M. Tchinda au registre du commerce",
          "Register Mr Tchinda's sole proprietorship in the trade register"),
     [text("CNI de l'exploitant, extrait de casier judiciaire ou déclaration sur l'honneur",
           "Owner's ID, criminal record extract or sworn statement"),
      text("Plan de localisation de l'atelier, boîte postale, contact téléphonique", "Workshop location map, PO box, "
           "phone"),
      text("Frais de création (à vérifier au CFCE)", "Creation fees (check at the CFCE)")],
     text("Registre de commerce, carte de contribuable (NIU), attestation de création",
          "Trade register, taxpayer card, creation certificate"),
     "[[source:minfi-cfce]] [[source:minfi-formalites]]"),
    ("Rattachement fiscal au CIME de Yaoundé", "Tax office attachment (Yaoundé medium-sized taxpayers)",
     text("Direction générale des impôts, CIME de Yaoundé", "Directorate General of Taxation, Yaoundé MTO"),
     text("Suivi fiscal d'une entreprise dont le CA visé (environ 65 millions) dépasse 50 millions : régime du réel",
          "Tax follow-up of a business with a target turnover above 50 million: actual regime"),
     [text("Carte de contribuable délivrée au CFCE", "Taxpayer card issued by the CFCE"),
      text("Registre de commerce et plan de localisation", "Trade register and location map")],
     text("Rattachement au CIME, inscription au fichier des contribuables actifs, accès à la télédéclaration",
          "Attachment to the MTO, entry in the active taxpayer file, e-filing access"),
     "[[cgi:art. L 1]] [[source:dgi-cime]]"),
    ("Immatriculation à la CNPS", "Registration with the CNPS",
     text("Agence de la CNPS de Yaoundé", "CNPS Yaoundé office"),
     text("Immatriculer l'employeur, puis l'aide-technicien dans les 8 jours de l'embauche",
          "Register the employer, then the assistant within 8 days of hiring"),
     [text("Demande d'immatriculation sur imprimé CNPS", "Registration form (CNPS)"),
      text("Copie du registre de commerce, carte de contribuable, plan de localisation, contrat de travail",
           "Trade register copy, taxpayer card, map, employment contract")],
     text("Numéro d'employeur et numéro d'assuré", "Employer number and employee number"), "[[source:cnps-faq]]"),
    ("Ouverture du compte bancaire professionnel", "Opening the business bank account",
     text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
     text("Séparer l'argent de l'atelier de celui du ménage", "Keep the workshop's money apart from the household's"),
     [text("Demande d'ouverture, registre de commerce, carte de contribuable", "Request, trade register, taxpayer card"),
      text("CNI de l'exploitant, plan de localisation", "Owner's ID, location map")],
     text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
    ("Compte marchand Orange Money", "Orange Money merchant account",
     text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
     text("Encaisser les dépannages à domicile par Orange Money", "Collect home repairs through Orange Money"),
     [text("Registre de commerce, carte de contribuable, patente", "Trade register, taxpayer card, licence"),
      text("CNI de l'exploitant, RIB", "Owner's ID, bank details")],
     text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
]


def withholding(ht, rate):
    """Retenue d'acompte d'IRPP subie sur un paiement public (CGI art. 21 (2)) : taux principal majoré des CAC."""
    return int(calculs.retenue_source(D(ht), D(rate), P["cac.taux"])["retenue"])


def sale_invoice(book, month, client, number, einvoice, lines_, ht, day, public):
    taxes, totals = taxes_totals(ht)
    due = text("Payable par le Trésor public, retenues à la source déduites", "Payable by the Treasury, withholdings "
               "deducted") if public else text("Payable par virement le 10 du mois suivant", "Payable by transfer on "
                                               "the 10th of next month")
    title = (f"Facture d'entretien sous contrat public, {MONTHS_FR[month - 1]}" if public
             else f"Facture de dépannages aux entreprises, {MONTHS_FR[month - 1]}",
             f"Public maintenance contract invoice, {MONTHS_EN[month - 1]}" if public
             else f"Business repair invoice, {MONTHS_EN[month - 1]}")
    ref = book.piece(month, "facture_vente", day, *title,
                     {"issuer": SELLER, "customer": client, "number": number, "einvoice": einvoice,
                      "fields": [{"label": text("TVA", "VAT"),
                                  "value": text("Exigible à l'encaissement (prestations de services)",
                                                "Due on collection (services)")}],
                      "lines": lines_,
                      "totals": totals + [{"label": due, "role": "ttc", "amount": int(taxes["ttc"])}]})
    book.entry(day, ref, line("411", "debit", taxes["ttc"]), line("706", "credit", ht),
               line("471", "credit", taxes["taxes"]))
    return ref, {"ht": ht, "taxes": int(taxes["taxes"]), "ttc": int(taxes["ttc"]), "client": client["name"]}


def build():
    book, special = Book("D"), {"months": {}, "public": {}}
    staff = payroll(STAFF)
    pay = {k: sum(r[k] for r in staff) for k in ("gross", "cnps", "irpp", "rav", "tdl", "cfc", "net", "cfc_pat", "cnps_pat")}
    salary_taxes = pay["irpp"] + pay["rav"] + pay["tdl"] + pay["cfc"] + pay["cfc_pat"]
    special["procedures"] = [book.piece(1, "demarche", d(1, 2), f"Démarche : {fr}", f"Procedure: {en}",
                                        {"organisme": body, "objet": purpose, "documents_a_fournir": docs,
                                         "document_obtenu": got, "source": source})
                             for fr, en, body, purpose, docs, got, source in PROCEDURES]
    special["apports"] = book.piece(1, "fiche_stock", d(1, 2), "État des apports de l'exploitant au 2 janvier 2026",
                                    "Owner's contributions at 2 January 2026",
                                    {"fields": [{"label": text("Exploitant", "Owner"),
                                                 "value": "Jean-Claude Tchinda"},
                                                {"label": text("Camionnette", "Van"),
                                                 "value": text("Utilitaire de 2023, valeur estimée par un expert",
                                                               "2023 utility van, value estimated by an assessor")}],
                                     "lines": [{"label": text("Camionnette utilitaire", "Utility van"), "qty": 1,
                                                "unit_price": VAN, "amount": VAN},
                                               {"label": text("Espèces déposées à la banque", "Cash deposited at the bank"),
                                                "qty": 1, "unit_price": CASH_IN, "amount": CASH_IN}],
                                     "totals": [{"label": text("Capital personnel apporté", "Personal capital brought in"),
                                                 "role": "ht", "amount": VAN + CASH_IN}]})
    book.entry(d(1, 2), special["apports"], line("2451", "debit", VAN), line("521", "debit", CASH_IN),
               line("103", "credit", VAN + CASH_IN))
    tools_tax, tools_totals = taxes_totals(TOOLS_HT)
    tools_day = workday(1, 5)
    special["tools"] = book.piece(1, "facture_achat", tools_day, "Facture d'outillage (manomètres, pompe à vide)",
                                  "Tools invoice (gauges, vacuum pump)",
                                  {"issuer": TOOLS_SUPPLIER, "customer": OWN, "number": "QC-2026-0031",
                                   "einvoice": "DGI-SFE-2026-009031",
                                   "lines": [{"label": text("Jeu de manomètres, pompe à vide, détecteur de fuites",
                                                            "Gauge set, vacuum pump, leak detector"),
                                              "qty": 1, "unit_price": TOOLS_HT, "amount": TOOLS_HT}],
                                   "totals": tools_totals + [{"label": text("Payé par virement", "Paid by transfer"),
                                                              "role": "ttc", "amount": int(tools_tax["ttc"])}]})
    book.entry(tools_day, special["tools"], line("6056", "debit", TOOLS_HT), line("4454", "debit", tools_tax["taxes"]),
               line("521", "credit", tools_tax["ttc"]))

    lots = {f[0]: [] for f in FAMILIES}
    unpaid = {"supplier": 0, "private": None, "public": None}
    for month in range(1, 13):
        end, refs = last(month), {}
        mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {mfr} (Banque X)",
                                  f"{men} bank statement (Bank X)", {})
        rows = []
        withheld = calculs.franc(D(RENT) * P["precompte.taux_loyer"] / 100)
        rent_day = workday(month, 5 if month == 1 else 2)
        refs["rent"] = book.piece(month, "recu_caisse", rent_day, f"Quittance de loyer de l'atelier, {mfr}",
                                  f"{men} workshop rent receipt",
                                  {"fields": [{"label": text("Bailleur", "Landlord"), "value": "Mme Onana (fictive)"}],
                                   "totals": [{"label": text("Loyer brut", "Gross rent"), "amount": RENT},
                                              {"label": text("Précompte sur loyer 10 % retenu", "10% rent withholding"),
                                               "amount": int(withheld)},
                                              {"label": text("Net versé par virement", "Net paid by transfer"),
                                               "amount": int(RENT - withheld)}]})
        book.entry(rent_day, refs["rent"], line("6222", "debit", RENT), line("4478", "credit", withheld),
                   line("521", "credit", RENT - withheld))
        if unpaid["private"]:
            inv = unpaid["private"]
            day = workday(month, 10)
            book.entry(day, refs["bank"], line("521", "debit", inv["ttc"]), line("411", "credit", inv["ttc"]),
                       line("471", "debit", inv["taxes"]), line("4432", "credit", inv["taxes"]))
            rows.append((text(f"Virement reçu de {inv['client']}", f"Transfer received from {inv['client']}"), inv["ttc"]))
        if unpaid["public"]:
            inv = unpaid["public"]
            retenue = withholding(inv["ht"], P["retenue.commande_publique"])
            net = inv["ttc"] - retenue - inv["taxes"]
            day = workday(month, 20)
            refs["ars"] = book.piece(month, "releve_bancaire", day,
                                     f"Avis de paiement du Trésor et attestation de retenue à la source (ARS), {mfr}",
                                     f"Treasury payment notice and withholding certificate (ARS), {men}",
                                     {"fields": [{"label": text("Payeur", "Payer"), "value": inv["client"]},
                                                 {"label": text("Facture réglée", "Invoice paid"), "value": inv["number"]},
                                                 {"label": text("Attestation", "Certificate"),
                                                  "value": f"ARS-DGI-2026-{40100 + month:06d}"}],
                                      "totals": [{"label": text("Facture TTC", "Invoice incl. tax"), "amount": inv["ttc"]},
                                                 {"label": text("Acompte d'IRPP retenu (5 % + CAC)",
                                                                "Income tax instalment withheld (5% + council cents)"),
                                                  "amount": retenue},
                                                 {"label": text("TVA et CAC retenues à la source",
                                                                "VAT and council cents withheld at source"),
                                                  "amount": inv["taxes"]},
                                                 {"label": text("Net viré sur le compte", "Net transferred"), "amount": net}]})
            book.entry(day, refs["ars"], line("521", "debit", net), line("4492", "debit", retenue),
                       line("4458", "debit", inv["taxes"]), line("411", "credit", inv["ttc"]),
                       line("471", "debit", inv["taxes"]), line("4432", "credit", inv["taxes"]))
            special["public"][month] = {**inv, "retenue": retenue, "net": net, "ref": refs["ars"]}
        if unpaid["supplier"]:
            book.entry(d(month, end), refs["bank"], line("401", "debit", unpaid["supplier"]),
                       line("521", "credit", unpaid["supplier"]))
            rows.append((text("Virement à Frigo Pièces Mvog-Mbi", "Transfer to the parts supplier"), unpaid["supplier"]))
        # Approvisionnements chez le grossiste, payés à la fin du mois suivant.
        lines_, ht = [], 0
        for name_fr, name_en, _acc, qty, _used, base, rise in FAMILIES:
            unit = buy_price(base, rise, month)
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
        purchase_day = workday(month, 6)
        refs["purchase"] = book.piece(month, "facture_achat", purchase_day, f"Facture de Frigo Pièces Mvog-Mbi, {mfr}",
                                      f"Parts supplier's invoice, {men}",
                                      {"issuer": SUPPLIER, "customer": OWN, "number": f"FPM-2026-{300 + month:04d}",
                                       "einvoice": f"DGI-SFE-2026-{9100 + month:06d}", "lines": lines_, "totals": totals})
        book.entry(purchase_day, refs["purchase"], line("6041", "debit", ht), line("4452", "debit", taxes["taxes"]),
                   line("4492", "debit", precompte), line("401", "credit", due))
        unpaid["supplier"] = int(due)
        # Factures du mois : entreprises privées et contrat public (moins de 5 millions HT, art. 21 (2)).
        jobs = PRIVATE_JOBS[month - 1]
        refs["private"], unpaid["private"] = sale_invoice(
            book, month, PRIVATE[month % 2], f"ETF-2026-{2 * month - 1:04d}", f"DGI-SFE-2026-{9200 + month:06d}",
            [{"label": text("Dépannages et remises en service (climatiseurs, chambres froides)",
                            "Repairs and restarts (air conditioners, cold rooms)"),
              "qty": jobs, "unit_price": JOB, "amount": jobs * JOB}], jobs * JOB, workday(month, 24), False)
        units = PUBLIC_UNITS[month - 1]
        number = f"ETF-2026-{2 * month:04d}"
        refs["public"], unpaid["public"] = sale_invoice(
            book, month, PUBLIC[month % 2], number, f"DGI-SFE-2026-{9300 + month:06d}",
            [{"label": text("Entretien mensuel des climatiseurs (contrat public)", "Monthly air-conditioner servicing "
                            "(public contract)"), "qty": units, "unit_price": UNIT, "amount": units * UNIT}],
            units * UNIT, workday(month, 26), True)
        unpaid["public"]["number"] = number
        assert unpaid["public"]["ht"] < 5000000  # retenue de 5,5 % : commande publique de moins de 5 millions HT
        # Dépannages à domicile payés par Orange Money : facture et encaissement le même jour.
        home = HOME_JOBS[month - 1]
        home_ht = home * HOME
        home_tax = tva(home_ht)
        om_ttc = int(home_tax["ttc"])
        refs["orange"] = book.piece(month, "releve_momo", d(month, end), f"Relevé Orange Money de {mfr}",
                                    f"Orange Money statement, {men}",
                                    {"lines": [{"label": text("Dépannages à domicile", "Home repairs"), "qty": home,
                                                "unit_price": HOME, "amount": home_ht}],
                                     "totals": [{"label": text("Encaissements HT", "Receipts excl. tax"), "role": "ht",
                                                 "amount": home_ht},
                                                {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                                 "amount": int(home_tax["taxes"])},
                                                {"label": text("Encaissements TTC", "Receipts incl. tax"), "role": "ttc",
                                                 "amount": om_ttc},
                                                {"label": text("Frais de l'opérateur", "Operator fees"), "amount": OM_FEE},
                                                {"label": text("Transfert vers la banque", "Transfer to the bank"),
                                                 "amount": om_ttc - OM_FEE}]})
        book.entry(d(month, end), refs["orange"], line("5522", "debit", om_ttc), line("706", "credit", home_ht),
                   line("471", "credit", home_tax["taxes"]), line("471", "debit", home_tax["taxes"]),
                   line("4432", "credit", home_tax["taxes"]), line("631", "debit", OM_FEE),
                   line("5522", "credit", OM_FEE), line("585", "debit", om_ttc - OM_FEE),
                   line("5522", "credit", om_ttc - OM_FEE))
        refs["payroll"] = book.piece(month, "bulletin_paie", d(month, end), f"Bulletin de paie de l'aide-technicien, {mfr}",
                                     f"Assistant technician's payslip, {men}",
                                     {"lines": [{"label": r["name"], "amount": int(r["gross"])} for r in staff],
                                      "totals": [{"label": text("Salaire brut", "Gross pay"), "role": "ht",
                                                  "amount": int(pay["gross"])},
                                                 {"label": text("IRPP et CAC", "PIT and council cents"), "amount": int(pay["irpp"])},
                                                 {"label": text("RAV", "Audiovisual fee"), "amount": int(pay["rav"])},
                                                 {"label": text("TDL", "Local development tax"), "amount": int(pay["tdl"])},
                                                 {"label": text("CFC salariale", "Employee housing levy"), "amount": int(pay["cfc"])},
                                                 {"label": text("CNPS salariale (pension 4,2 %)", "Employee CNPS (pension 4.2%)"),
                                                  "amount": int(pay["cnps"])},
                                                 {"label": text("Net à payer", "Net pay"), "amount": int(pay["net"])},
                                                 {"label": text("CFC patronale", "Employer housing levy"), "amount": int(pay["cfc_pat"])},
                                                 {"label": text("CNPS patronale (pension 4,2 %)", "Employer CNPS (pension 4.2%)"),
                                                  "amount": int(pay["cnps_pat"])}]})
        book.entry(d(month, end), refs["payroll"], line("6611", "debit", pay["gross"]),
                   line("6413", "debit", pay["cfc_pat"]), line("6641", "debit", pay["cnps_pat"]),
                   line("4472", "credit", salary_taxes), line("431", "credit", pay["cnps"] + pay["cnps_pat"]),
                   line("422", "credit", pay["net"]))
        book.entry(d(month, end), refs["bank"], line("422", "debit", pay["net"]), line("521", "credit", pay["net"]))
        rows.append((text("Salaire net viré", "Net pay transferred"), int(pay["net"])))
        if month > 1:
            refs["settlement"] = settle(book, month - 1, d(month, 15), month)
        transfer = om_ttc - OM_FEE
        book.entry(d(month, end), refs["bank"], line("521", "debit", transfer), line("585", "credit", transfer),
                   line("1042", "debit", WITHDRAWAL), line("521", "credit", WITHDRAWAL),
                   line("631", "debit", BANK_FEE), line("521", "credit", BANK_FEE))
        rows += [(text("Transfert reçu d'Orange Money", "Transfer received from Orange Money"), transfer),
                 (text("Virement personnel de l'exploitant (prélèvement)", "Owner's personal transfer (drawings)"),
                  WITHDRAWAL), (text("Frais de tenue de compte", "Account fees"), BANK_FEE)]
        piece_of(book, refs["bank"])["payload"] = {"totals": [{"label": label, "amount": amount} for label, amount in rows]}
        special["months"][month] = refs
    year_end(book, special, lots)
    special["staff"] = staff
    return book, special


def settle(book, month, date, settled_in):
    """Déclaration du 15 pour `month` et son règlement : TVA sur les services encaissés (4432) moins la TVA déductible,
    TVA retenue à la source comprise (4458, art. 143 et 149 (2)) ; acompte d'IRPP net des précomptes et retenues
    imputés (4492) ; retenues sur salaires et sur loyer, CNPS."""
    credit_in = book.__dict__.setdefault("credit", 0)
    decl = ledger.monthly_declaration(book.entries, YEAR, month, minimum_rate=P["is.taux_minimum_perception"],
                                      cac_rate=P["cac.taux"], credit_reporte=credit_in)
    book.credit = decl["credit_tva"]
    in_month = [l for e in book.entries if e["date"].startswith(f"{YEAR}-{month:02d}") for l in e["lines"]]
    deductible = {}
    for l in in_month:
        if l["account"].startswith("445") and l["side"] == "debit":
            deductible[l["account"]] = deductible.get(l["account"], 0) + l["amount"]
    withheld = {acc: sum(l["amount"] for l in in_month if l["account"] == acc and l["side"] == "credit")
                for acc in ("4472", "4478", "431")}
    imputed = min(decl["precompte_impute"], decl["acompte_is"])
    year, mm = (YEAR, settled_in) if settled_in <= 12 else (YEAR + 1, settled_in - 12)
    ref = book.piece(mm, "declaration", date, f"Déclaration du 15 : période de {MONTHS_FR[month - 1]} {YEAR}",
                     f"15th return: {MONTHS_EN[month - 1]} {YEAR}",
                     {"fields": [{"label": text("Chiffre d'affaires HT facturé", "Turnover invoiced excl. tax"),
                                  "value": fcfa(decl["chiffre_affaires"])},
                                 {"label": text("TVA exigible (services encaissés)", "VAT due (services collected)"),
                                  "value": fcfa(decl["tva_collectee"])},
                                 {"label": text("TVA déductible, retenue à la source comprise",
                                                "Recoverable VAT, withheld VAT included"),
                                  "value": fcfa(decl["tva_deductible"])},
                                 {"label": text("Crédit de TVA reporté", "VAT credit brought forward"), "value": fcfa(credit_in)},
                                 {"label": text("Crédit de TVA à reporter", "VAT credit carried forward"),
                                  "value": fcfa(decl["credit_tva"])}],
                      "totals": [{"label": text("TVA due", "VAT due"), "amount": decl["tva_due"]},
                                 {"label": text("Acompte d'IRPP (2 % + CAC)", "Income tax instalment (2% + council cents)"),
                                  "amount": decl["acompte_is"]},
                                 {"label": text("Précomptes et retenues imputés", "Withholdings credited"),
                                  "amount": int(imputed)},
                                 {"label": text("Retenues et cotisations reversées", "Withholdings and contributions paid over"),
                                  "amount": sum(withheld.values())}]}, year=year)
    lines = [line("4432", "debit", decl["tva_collectee"])] if decl["tva_collectee"] else []
    lines += [line(acc, "credit", amount) for acc, amount in sorted(deductible.items()) if amount]
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


def year_end(book, special, lots):
    used = {f[0]: 12 * f[4] for f in FAMILIES}
    fields, sheet_lines = [], []
    for name_fr, name_en, *_ in FAMILIES:
        bought = sum(q for q, _ in lots[name_fr])
        fields.append({"label": text(f"{name_fr.capitalize()} : achetés, utilisés, en stock",
                                     f"{name_en.capitalize()}: bought, used, in stock"),
                       "value": f"{bought} / {used[name_fr]} / {bought - used[name_fr]}"})
        sheet_lines += [{"label": text(f"{name_fr.capitalize()}, lot {i}", f"{name_en.capitalize()}, lot {i}"), "qty": q,
                         "unit_price": u, "amount": q * u} for i, (q, u) in enumerate(lots[name_fr], start=1)]
    sheet = book.piece(12, "fiche_stock", d(12, 31), "Fiches de stock CMUP du fluide et des pièces",
                       "WAC stock cards for refrigerant and parts", {"fields": fields, "lines": sheet_lines})
    stock = {}
    for name_fr, _en, account, *_ in FAMILIES:
        family = [(D(q), D(u)) for q, u in lots[name_fr]]
        stock[name_fr] = (family, used[name_fr], calculs.sortie_cmup(family, D(used[name_fr])), account)
    book.entry(d(12, 31), sheet, *[line(v[3], "debit", v[2]["valeur_stock"]) for v in stock.values()],
               line("6033", "credit", sum(v[2]["valeur_stock"] for v in stock.values())))
    years = int(100 / P["amortissement.taux_max_auto_leger_ville"])
    dotation = int(calculs.amortissement_lineaire(D(VAN), years, 1)[0]["dotation"])
    schedule = book.piece(12, "fiche_stock", d(12, 31), "Plan d'amortissement de la camionnette, 2026",
                          "2026 depreciation schedule of the van",
                          {"fields": [{"label": text("Durée", "Useful life"),
                                       "value": text(f"{years} ans (25 %, taux fiscal maximal du matériel automobile léger)",
                                                     f"{years} years (25%, maximum tax rate for light vehicles)")}],
                           "lines": [{"label": text("Camionnette apportée le 2 janvier", "Van contributed on 2 January"),
                                      "amount": dotation}],
                           "totals": [{"label": text("Dotation de l'exercice", "Charge for the year"), "role": "ht",
                                       "amount": dotation}]})
    book.entry(d(12, 31), schedule, line("6813", "debit", dotation), line("2845", "credit", dotation))
    special.update(sheet=sheet, stock=stock, schedule=schedule, dotation=dotation, years=years)
    special["months"][12]["settlement_next"] = settle(book, 12, d(1, 15, YEAR + 1), 13)
    entries_2026 = [e for e in book.entries if e["date"] < f"{YEAR + 1}"]
    accounting = ledger.accounting_result(entries_2026)
    turnover = sum(l["amount"] for e in entries_2026 for l in e["lines"] if l["account"].startswith("70")
                   and l["side"] == "credit")
    tax_result = ledger.tax_result(accounting)
    rate = P["is.taux"]  # IRPP sur les BIC : taux de l'art. 17 (art. 69 (2)) ; le taux réduit de l'art. 17 bis vise l'IS
    prepaid = sum(l["amount"] for e in book.entries for l in e["lines"] if l["account"] == "441" and l["side"] == "debit")
    remaining = ledger.account_balance(book.entries, "4492", datetime.date(YEAR + 1, 12, 31))
    tax = ledger.corporate_tax(tax_result, turnover, prepaid + remaining, rate, P["is.taux_minimum_perception"],
                               P["cac.taux"])
    assert tax["du"] > remaining
    liquidation = book.piece(3, "declaration", d(3, 9, YEAR + 1), "Déclaration des résultats 2026 : liquidation de l'IRPP",
                             "2026 income return: income tax",
                             {"fields": [{"label": text("Bénéfice imposable (BIC)", "Taxable business profit"),
                                          "value": fcfa(tax_result)},
                                         {"label": text("Taux", "Rate"), "value": f"{int(rate)} %"}],
                              "totals": [{"label": text("IRPP calculé (CAC compris)", "Income tax computed"),
                                          "amount": tax["is_total"]},
                                         {"label": text("Minimum de perception (2 % du CA, CAC compris)", "Minimum tax"),
                                          "amount": tax["minimum_total"]},
                                         {"label": text("IRPP dû", "Income tax due"), "amount": tax["du"]},
                                         {"label": text("Acomptes versés", "Instalments paid"), "amount": prepaid},
                                         {"label": text("Retenues et précomptes non encore imputés",
                                                        "Withholdings not yet credited"), "amount": int(remaining)},
                                         {"label": text("Solde à payer", "Balance due"), "amount": tax["solde"]}]},
                             year=YEAR + 1)
    book.pieces[-1]["dsf"] = "liquidation_is"
    book.entry(d(12, 31), liquidation, line("1043", "debit", tax["du"]),
               *([line("4492", "credit", remaining)] if remaining else []), line("441", "credit", tax["du"] - remaining))
    closing_stock = sum(v[2]["valeur_stock"] for v in stock.values())
    end = datetime.date(YEAR, 12, 31)
    receivables = ledger.account_balance(entries_2026, "411", end)
    vat_pending = -ledger.account_balance(entries_2026, "471", end)
    withdrawals = 12 * WITHDRAWAL
    for table, fr, en, rows in (
        ("passage", "Déclaration 2026 : tableau de passage", "2026 return: reconciliation",
         [("Résultat comptable", "Accounting profit", accounting), ("Réintégrations", "Add-backs", 0),
          ("Bénéfice imposable", "Taxable profit", tax_result)]),
        ("compte_resultat", "Déclaration 2026 : compte de résultat", "2026 return: income statement",
         [("Chiffre d'affaires (services vendus)", "Turnover (services sold)", turnover),
          ("Résultat net de l'exercice", "Net profit for the year", accounting)]),
        ("bilan", "Déclaration 2026 : bilan (extrait)", "2026 return: balance sheet (extract)",
         [("Capital personnel", "Personal capital", VAN + CASH_IN),
          ("Compte de l'exploitant : prélèvements et IRPP", "Owner's account: drawings and income tax",
           withdrawals + tax["du"]),
          ("Résultat net de l'exercice", "Net profit for the year", accounting),
          ("Camionnette, valeur nette", "Van, net book value", VAN - dotation),
          ("Stocks de fluide et de pièces", "Refrigerant and parts inventory", closing_stock),
          ("Créances clients", "Trade receivables", receivables),
          ("TVA en attente d'encaissement (471)", "VAT awaiting collection (471)", vat_pending)]),
    ):
        book.piece(3, "declaration", d(3, 9, YEAR + 1), fr, en,
                   {"totals": [{"label": text(a, b), "amount": int(v)} for a, b, v in rows]}, year=YEAR + 1)
        book.pieces[-1]["dsf"] = table
    special.update(accounting=accounting, turnover=turnover, tax_result=tax_result, tax=tax, rate=rate, prepaid=prepaid,
                   remaining=int(remaining), liquidation=liquidation, net=accounting, closing_stock=closing_stock,
                   receivables=receivables, vat_pending=vat_pending, withdrawals=withdrawals)


# ---------------------------------------------------------------------------------------------------------- questions

def month_questions(book, special, month):
    module, refs = MODULE_OF_MONTH[month], special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    asks = [
        ("purchase", f"Passez l'écriture de la facture du grossiste de {mfr} (précompte compris).",
         f"Record the parts supplier's {men} invoice (withholding included).",
         "Matières consommables 6041, TVA 4452, précompte de 2 % en 4492 (CGI art. 21 (3)), fournisseur 401.",
         "Consumables 6041, VAT 4452, 2% withholding 4492, supplier 401."),
        ("private", f"Passez l'écriture de la facture de dépannages de {mfr}.", f"Record the {men} repair invoice.",
         "Client 411 au TTC, services vendus 706, TVA en attente 471 : la TVA des services n'est exigible qu'à "
         "l'encaissement (CGI art. 134 (1) b).",
         "Customer 411, services sold 706, VAT pending 471: VAT on services is due on collection."),
        ("public", f"Passez l'écriture de la facture du contrat public de {mfr}.",
         f"Record the {men} public contract invoice.",
         "Même schéma : 411, 706 et 471 ; les retenues ne se passent qu'au paiement.",
         "Same pattern: 411, 706 and 471; withholdings are booked only on payment."),
        ("ars", f"Passez l'écriture du paiement public et de l'ARS de {mfr}.",
         f"Record the {men} public payment and withholding certificate.",
         "Banque 521 pour le net, acompte retenu de 5,5 % en 4492 (art. 21 (2)), TVA retenue en 4458 (art. 149 (2)), "
         "client 411 soldé ; la TVA devient exigible : 471 au débit, 4432 au crédit.",
         "Bank 521 net, 5.5% instalment 4492, withheld VAT 4458, customer 411 cleared; VAT becomes due: 471 to 4432."),
        ("orange", f"Passez l'écriture du relevé Orange Money de {mfr}.", f"Record the {men} Orange Money statement.",
         "5522 au TTC, 706 et 471 ; encaissement immédiat : 471 soldé dans 4432 ; frais 631, transfert par 585.",
         "5522, 706 and 471; immediate collection: 471 cleared to 4432; fees 631, transfer through 585."),
        ("payroll", f"Passez l'écriture du bulletin de paie de {mfr}.", f"Record the {men} payslip.",
         "Salaire 6611, CFC patronale 6413, CNPS patronale 6641 ; retenues 4472 et 431, net 422.",
         "Gross 6611, employer levies 6413 and 6641; withholdings 4472 and 431, net 422."),
        ("bank", f"Passez les écritures du relevé bancaire de {mfr}.", f"Record the {men} bank statement entries.",
         "Client privé 411 et TVA exigible (471 vers 4432), fournisseur 401, salaire 422, transfert 585, "
         "prélèvement de l'exploitant 1042, frais 631.",
         "Private customer 411 and VAT due (471 to 4432), supplier 401, pay 422, transfer 585, drawings 1042, fees 631."),
        ("rent", f"Passez l'écriture de la quittance de loyer de {mfr}.", f"Record the {men} rent receipt.",
         "Loyer brut 6222, précompte de 10 % en 4478 (CGI art. 87), net payé par la banque.",
         "Gross rent 6222, 10% withholding 4478, net paid by bank."),
        ("settlement", f"Passez l'écriture du règlement de la déclaration du 15 {mfr}.",
         f"Record the payment of the {men} 15th return.",
         "TVA exigible 4432 moins TVA déductible et retenue (445) ; acompte d'IRPP en 441, précomptes et retenues imputés "
         "(4492) ; retenues et CNPS reversées.",
         "VAT due less recoverable and withheld VAT; instalment 441 net of withholdings; withholdings and CNPS paid over."),
    ]
    for key, fr, en, why_fr, why_en in asks:
        if key in refs:
            book.journal(module, "exam", refs[key], fr, en, why_fr, why_en)
    _ref, decl, _credit = book.declarations[month]
    period = f"{YEAR}-{month:02d}"
    for field, fr, en in (("tva_due" if decl["tva_due"] else "credit_tva", "TVA due (ou crédit à reporter)",
                           "VAT due (or credit carried forward)"),
                          ("acompte_is_net", "Acompte d'IRPP net des précomptes et retenues imputés",
                           "Income tax instalment net of withholdings"),
                          ("retenues_salaires", "Retenues à la source du mois (salaire et loyer)",
                           "Withholdings of the month (pay and rent)")):
        book.numeric(module, "exam", decl[field], f"Déclaration du 15 pour {mfr} {YEAR} : {fr} ?",
                     f"15th return for {men} {YEAR}: {en}?",
                     "Calcul sur les écritures du mois : TVA devenue exigible à l'encaissement (4432) moins TVA "
                     "déductible, TVA retenue à la source comprise, et crédit reporté ; acompte de 2 % du CA facturé "
                     "majoré de 10 % de CAC, moins les précomptes et retenues (CGI art. 21) ; retenues portées en 447.",
                     "Computed from the month's entries (CGI art. 21, 134, 149).",
                     declaration={"period": period, "field": field})
    end = datetime.date(YEAR, month, last(month))
    book.numeric(module, "exam", ledger.account_balance(book.entries, "521", end),
                 f"Solde comptable du compte 521 au {last(month)} {mfr} {YEAR} ?",
                 f"Book balance of account 521 at {men} {last(month)}, {YEAR}?",
                 "Débits moins crédits de 521 jusqu'à cette date : le solde à rapprocher du relevé.",
                 "Debits less credits of 521 up to that date.", piece=refs["bank"],
                 rapprochement={"account": "521", "date": end.isoformat()})
    if month in special["public"]:
        paid = special["public"][month]
        book.numeric(module, "exam", paid["retenue"], f"Acompte d'IRPP retenu par le payeur public en {mfr} ?",
                     f"Income tax instalment withheld by the public payer in {men}?",
                     "5 % du HT de la facture, majorés de 10 % de CAC : 5,5 % (CGI art. 21 (2)).",
                     "5% of the invoice before tax plus 10% council cents: 5.5%.", piece=paid["ref"],
                     calcul={"fonction": "retenue_source", "args": [paid["ht"], 5, 10], "resultat": ["retenue"]})
    private = piece_of(book, refs["private"])
    book.numeric(module, "exam", private["payload"]["totals"][0]["amount"],
                 f"Chiffre d'affaires HT des dépannages aux entreprises de {mfr} ?",
                 f"{men} business repair revenue excluding tax?", "Nombre d'interventions × prix, hors TVA (706).",
                 "Number of jobs × price, excluding VAT.", piece=refs["private"])


PROCEDURE_QUESTIONS = [
    ("Que délivre le CFCE à M. Tchinda ?", "What does the CFCE give Mr Tchinda?",
     "Registre de commerce, carte de contribuable et attestation de création", "Trade register, taxpayer card, "
     "creation certificate", "Des statuts notariés", "Notarised articles"),
    ("Pourquoi Ets Tchinda Froid relève-t-il du CIME et du réel ?", "Why is Ets Tchinda Froid at the MTO, actual regime?",
     "Son CA visé dépasse 50 millions", "Its target turnover exceeds 50 million", "Parce qu'il emploie un salarié",
     "Because it has an employee"),
    ("Dans quel délai l'aide-technicien doit-il être immatriculé à la CNPS ?", "Within how long must the assistant be "
     "registered?", "8 jours après l'embauche", "8 days after hiring", "À la fin de l'année", "At year end"),
    ("Pourquoi ouvrir un compte bancaire professionnel ?", "Why open a business bank account?",
     "Pour séparer l'argent de l'atelier de celui du ménage", "To separate business and household money",
     "Parce que la loi interdit les espèces", "Because the law bans cash"),
    ("Quelle pièce Orange demande-t-il en plus des documents légaux ?", "Which extra document does Orange require?",
     "Le RIB", "Bank details (RIB)", "Un bilan certifié", "A certified balance sheet"),
]


def build_questions(book, special):
    for ref, (fr, en, right_fr, right_en, wrong_fr, wrong_en) in zip(special["procedures"], PROCEDURE_QUESTIONS):
        book.choice(1, "quiz", ref, fr, en, [(right_fr, right_en, True), (wrong_fr, wrong_en, False)],
                    "Voir la démarche et sa source officielle.", "See the procedure and its official source.")
    book.choice(1, "quiz", special["apports"], "Un établissement individuel a-t-il un capital social (compte 101) ?",
                "Does a sole proprietorship have share capital (account 101)?",
                [("Non : le capital personnel de l'exploitant (103)", "No: the owner's personal capital (103)", True),
                 ("Oui, comme une SARL", "Yes, like an LLC", False)],
                "Pas d'associés, pas de parts : l'apport de l'exploitant va en 103.", "No partners, no shares: 103.")
    book.choice(1, "quiz", special["tools"], "L'outillage de 450 000 HT s'inscrit à l'actif et s'amortit.",
                "The 450,000 tools are capitalised and depreciated.", [("Vrai", "True", False), ("Faux", "False", True)],
                "Faux : sous le seuil de 500 000 HT, le petit outillage est une charge (6056, CGI art. 7).",
                "False: below the 500,000 threshold small tools are an expense (6056).", qtype="truefalse")
    for ref, fr, en, why_fr, why_en in (
        (special["apports"], "Passez l'écriture des apports de l'exploitant.", "Record the owner's contributions.",
         "Camionnette 2451 et banque 521 au débit, capital personnel 103 au crédit.",
         "Van 2451 and bank 521 debit, personal capital 103 credit."),
        (special["tools"], "Passez l'écriture de la facture d'outillage.", "Record the tools invoice.",
         "Petit outillage 6056 (sous le seuil de 500 000 HT, CGI art. 7), TVA 4454, payé par la banque.",
         "Small tools 6056 (below the 500,000 threshold), VAT 4454, paid by bank."),
    ):
        book.journal(1, "exam", ref, fr, en, why_fr, why_en)
    for month in range(1, 13):
        month_questions(book, special, month)
    june = special["public"][6]
    book.numeric(3, "quiz", int(calculs.retenue_source(D(june["ht"]), D(10), P["cac.taux"])["retenue"]),
                 "Contraste : si Ets Tchinda Froid ne figurait pas au fichier des contribuables actifs, quelle retenue le "
                 "payeur public aurait-il opérée sur la facture réglée en juin ?",
                 "Contrast: had Ets Tchinda Froid not been on the active taxpayer file, what would the public payer have "
                 "withheld on the invoice paid in June?",
                 "10 % du HT majorés de 10 % de CAC, soit 11 % (CGI art. 21 (2)) : le double. Rester à jour de ses "
                 "déclarations garde le taux de 5,5 %.",
                 "10% plus council cents, 11%: double. Keeping returns up to date keeps the 5.5% rate.",
                 piece=june["ref"], calcul={"fonction": "retenue_source", "args": [june["ht"], 10, 10],
                                            "resultat": ["retenue"]})
    for module, piece, fr, en, ok, why in (
        (2, special["months"][2]["ars"], "La TVA retenue par le payeur public est perdue pour Ets Tchinda Froid.",
         "The VAT withheld by the public payer is lost to Ets Tchinda Froid.", False,
         "Faux : sur présentation de l'ARS, elle se déduit de la TVA due (CGI art. 143 et 149 (2))."),
        (2, special["months"][3]["private"], "La TVA d'une facture de dépannage est due dès la facture.",
         "The VAT on a repair invoice is due on invoicing.", False,
         "Faux : pour les services, elle est exigible à l'encaissement (CGI art. 134 (1) b) ; d'ici là, 471."),
        (3, special["months"][5]["bank"], "Le virement personnel de M. Tchinda est une charge de l'atelier.",
         "Mr Tchinda's personal transfer is a business expense.", False,
         "Faux : c'est un prélèvement de l'exploitant (1042), jamais une charge ni un salaire."),
        (4, special["months"][8]["ars"], "La retenue de 5,5 % est imputée sur l'acompte mensuel d'IRPP.",
         "The 5.5% withholding is credited against the monthly instalment.", True,
         "Vrai : elle est une avance sur l'impôt de l'exploitant ; l'excédent s'impute sur le solde de l'année."),
        (5, special["months"][11]["public"], "Le contrat public de 2 100 000 HT subirait la retenue même au-delà de "
         "5 millions HT.", "The public contract would bear the withholding even above 5 million.", False,
         "Faux : la retenue de l'art. 21 (2) vise la commande publique de moins de 5 millions HT."),
    ):
        book.choice(module, "quiz", piece, fr, en, [("Vrai", "True", ok), ("Faux", "False", not ok)], why, why,
                    qtype="truefalse")
    for module, piece, fr, en, choices, why in (
        (4, special["months"][7]["orange"], "Un client paie un dépannage par Orange Money : quand la TVA devient-elle "
         "exigible ?", "A customer pays a repair by Orange Money: when is the VAT due?",
         [("Le jour du paiement", "On the day of payment", True), ("À la fin de l'année", "At year end", False),
          ("Jamais : Orange Money la paie", "Never: Orange Money pays it", False)],
         "Encaissement immédiat : 471 est soldé le jour même dans 4432."),
        (5, special["months"][10]["bank"], "Où passe le virement personnel de l'exploitant ?",
         "Where does the owner's personal transfer go?",
         [("1042, compte de l'exploitant", "1042, owner's account", True), ("6611, salaires", "6611, wages", False),
          ("6618, autres rémunérations", "6618, other pay", False)],
         "L'exploitant n'est pas salarié de lui-même : il prélève sur son compte (1042)."),
    ):
        book.choice(module, "quiz", piece, fr, en, choices, why, why)
    inventory_questions(book, special)
    bridge_questions(book, special)
    for module in book.questions:
        split_usage(book.questions[module])


def inventory_questions(book, special):
    sheet = special["sheet"]
    for name, (family, used, result, _account) in special["stock"].items():
        args = [[[int(q), int(u)] for q, u in family], int(used)]
        for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré", "weighted average unit cost"),
                            ("valeur_sortie", "coût des consommations au CMUP", "cost of items used at WAC"),
                            ("valeur_stock", "valeur du stock final au CMUP", "closing stock at WAC")):
            book.numeric(6, "exam", result[key], f"{name.capitalize()} : {fr} ?", f"{name}: {en}?",
                         "CMUP de l'exercice, arrondi au franc ; calculateur stock.", "Period WAC, rounded.",
                         piece=sheet, calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
        peps = calculs.sortie_peps(family, D(used))
        book.numeric(6, "exam", peps["valeur_sortie"], f"{name.capitalize()} : coût des consommations en PEPS (contraste) ?",
                     f"{name}: cost of items used under FIFO?", "Les lots les plus anciens sortent d'abord.",
                     "Oldest lots go first.", piece=sheet,
                     calcul={"fonction": "sortie_peps", "args": args, "resultat": ["valeur_sortie"]})
    book.journal(6, "exam", sheet, "Passez l'écriture du stock final de fluide et de pièces.",
                 "Record the closing stock of refrigerant and parts.",
                 "Stocks 3311 et 3312 au débit, variation des stocks d'autres approvisionnements 6033 au crédit.",
                 "Stock accounts 3311 and 3312 debited, 6033 credited.")
    book.journal(6, "exam", special["schedule"], "Passez l'écriture de la dotation de la camionnette.",
                 "Record the van's depreciation.", "Dotation 6813, amortissements du matériel de transport 2845.",
                 "Charge 6813, depreciation of transport equipment 2845.")
    van_years = special["years"]
    book.numeric(6, "exam", special["dotation"], f"Dotation 2026 de la camionnette (6 000 000, {van_years} ans, depuis janvier) ?",
                 f"2026 depreciation of the van (6,000,000, {van_years} years, from January)?",
                 "Linéaire sur douze mois au taux de 25 %, le taux fiscal maximal du matériel automobile léger (CGI art. 7).",
                 "Straight-line over twelve months at 25%, the maximum tax rate for light vehicles.",
                 piece=special["schedule"],
                 calcul={"fonction": "amortissement_lineaire", "args": [VAN, van_years, 1], "resultat": [0, "dotation"]})
    book.numeric(6, "exam", special["closing_stock"], "Montant de la variation des stocks (6033) au 31 décembre ?",
                 "Change in inventories (6033) at 31 December?", "Premier exercice : égale au stock final.",
                 "First year: equals the closing stock.", piece=sheet)
    book.numeric(6, "exam", VAN - special["dotation"], "Valeur nette comptable de la camionnette au 31 décembre ?",
                 "Net book value of the van at 31 December?", "Valeur d'apport moins amortissements.",
                 "Contribution value less depreciation.", piece=special["schedule"])
    book.numeric(6, "exam", special["vat_pending"], "TVA en attente au compte 471 au 31 décembre ?",
                 "VAT pending in account 471 at 31 December?",
                 "La TVA des deux factures de décembre, non encore encaissées : elle sera exigible en janvier 2027.",
                 "VAT on the two December invoices not yet collected: it falls due in January 2027.",
                 piece=special["months"][12]["public"])
    bought = sum(q * u for lots in special["stock"].values() for q, u in lots[0])
    book.numeric(6, "exam", bought, "Achats de fluide et de pièces de l'exercice (6041) ?",
                 "Refrigerant and parts purchased in the year (6041)?", "Somme des lots de la fiche de stock.",
                 "Sum of the stock card lots.", piece=sheet)
    book.numeric(6, "exam", bought - special["closing_stock"], "Coût des fluides et pièces consommés en 2026 ?",
                 "Cost of refrigerant and parts used in 2026?", "Achats (6041) moins variation des stocks (6033).",
                 "Purchases less the change in inventories.", piece=sheet)
    book.choice(6, "exam", special["schedule"], "Depuis quand la camionnette s'amortit-elle ?",
                "From when is the van depreciated?",
                [("Janvier : elle sert à l'atelier dès l'apport", "January: in use from the contribution", True),
                 ("Juillet : demi-année par convention", "July: half-year by convention", False)],
                "Prorata temporis à partir de la mise en service, le 2 janvier.", "Pro rata from first use, 2 January.")
    book.numeric(6, "exam", special["receivables"], "Créances clients (411) au 31 décembre ?",
                 "Trade receivables (411) at 31 December?", "Les deux factures de décembre, TTC.",
                 "The two December invoices, including tax.", piece=special["months"][12]["private"])
    for fr, en, choices, why in (
        ("Compte du stock final des pièces détachées ?", "Account for the closing stock of spare parts?",
         [("3312, sous-compte de 331 matières consommables", "3312, under 331 consumables", True),
          ("3111 marchandises", "3111 goods", False)],
         "Les pièces ne sont pas revendues en l'état : ce sont des matières consommées par les interventions."),
        ("Taux fiscal maximal d'amortissement de la camionnette ?", "Maximum tax depreciation rate for the van?",
         [("25 %", "25%", True), ("10 %", "10%", False)], "CGI art. 7 : 25 % pour le matériel automobile léger."),
        ("La TVA des factures de décembre non encaissées figure-t-elle dans la déclaration du 15 janvier ?",
         "Is the VAT on unpaid December invoices in the 15 January return?",
         [("Non : elle attend l'encaissement en 471", "No: it waits for collection in 471", True),
          ("Oui, dès la facture", "Yes, from invoicing", False)], "CGI art. 134 (1) b."),
    ):
        book.choice(6, "exam", special["schedule"], fr, en, choices, why, why)
    book.choice(6, "quiz", sheet, "En période de hausse des prix, le PEPS donne un coût des consommations plus faible "
                "que le CMUP.", "When prices rise, FIFO gives a lower cost of items used than WAC.",
                [("Vrai", "True", True), ("Faux", "False", False)], "Vrai : les lots anciens, moins chers, sortent "
                "d'abord.", "True: older, cheaper lots go first.", qtype="truefalse")


def bridge_questions(book, special):
    tax, liq = special["tax"], special["liquidation"]
    book.numeric(7, "exam", tax["du"], "IRPP dû pour 2026 (le plus élevé de l'impôt calculé et du minimum) ?",
                 "2026 income tax due?",
                 "Bénéfice imposable × 30 % (taux de l'art. 17, art. 69 (2)), CAC compris (art. 71), comparé à 2 % du CA.",
                 "Taxable profit × 30% plus council cents, compared with 2% of turnover.", piece=liq,
                 calcul={"fonction": "impot_societes", "args": [special["tax_result"], special["turnover"],
                                                                int(special["rate"]), 2, 10], "resultat": ["du"]})
    for value, fr, en, why, ref in (
        (special["accounting"], "Résultat comptable 2026 ?", "2026 accounting profit?",
         "Produits moins charges des classes 6 et 7 ; ni prélèvements ni IRPP ne sont des charges.", liq),
        (special["tax_result"], "Bénéfice imposable 2026 ?", "2026 taxable profit?",
         "Aucune réintégration : prélèvements et IRPP n'ont jamais été passés en charges.", liq),
        (tax["minimum_total"], "Minimum de perception 2026, CAC compris ?", "2026 minimum tax?",
         "2 % du CA arrondi au millier inférieur, majoré de 10 % (art. 69 (2) et 71).", liq),
        (special["prepaid"], "Acomptes d'IRPP comptabilisés au titre de 2026 (441) ?", "2026 instalments (441)?",
         "Somme des acomptes des douze déclarations, précomptes imputés compris.", liq),
        (special["remaining"], "Précomptes et retenues non encore imputés au 31 décembre (4492) ?",
         "Withholdings not yet credited at 31 December (4492)?",
         "Les retenues de 5,5 % ont souvent dépassé l'acompte du mois : l'excédent s'impute sur le solde.", liq),
        (tax["solde"], "Solde d'IRPP à payer avec la déclaration des résultats ?", "Income tax balance due?",
         "IRPP dû moins acomptes et retenues.", liq),
        (special["turnover"], "Chiffre d'affaires HT 2026 ?", "2026 turnover?", "Compte 706, toutes factures.", liq),
        (special["withdrawals"], "Prélèvements de l'exploitant en 2026 (1042) ?", "Owner's drawings in 2026 (1042)?",
         "Douze virements personnels de 300 000.", liq),
        (special["net"], "Résultat net de l'exercice inscrit au bilan ?", "Net profit in the balance sheet?",
         "Pour un exploitant individuel, l'IRPP n'est pas une charge : le résultat net égale le résultat comptable.", liq),
        (tax["is_total"], "IRPP calculé au taux de 30 %, CAC compris ?", "Income tax computed at 30%, council cents "
         "included?", "Bénéfice arrondi au millier inférieur × 30 %, puis 10 % de CAC (art. 69 (2) et 71).", liq),
        (special["withdrawals"] + tax["du"], "Débit total du compte de l'exploitant (104) pour 2026 ?",
         "Total debit of the owner's account (104) for 2026?", "Prélèvements (1042) et IRPP de l'exploitant (1043).",
         liq),
        (sum(p["retenue"] for p in special["public"].values()), "Acomptes de 5,5 % retenus par les payeurs publics en "
         "2026 ?", "5.5% instalments withheld by public payers in 2026?", "Somme des onze ARS de l'année.", liq),
        (sum(p["taxes"] for p in special["public"].values()), "TVA retenue à la source par les payeurs publics en 2026 "
         "(4458) ?", "VAT withheld by public payers in 2026 (4458)?",
         "Somme des onze ARS ; chaque montant a été déduit de la TVA due du mois (art. 143 et 149 (2)).", liq),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=ref)
    for ref, fr, en, why_fr, why_en in (
        (liq, "Passez l'écriture de l'IRPP de l'exploitant.", "Record the owner's income tax.",
         "Compte de l'exploitant 1043 au débit (impôt personnel, pas une charge) ; retenues non imputées 4492 et État "
         "441 au crédit.", "Owner's account 1043 debit; withholdings 4492 and State 441 credit."),
        (special["months"][12]["settlement_next"], "Passez l'écriture du règlement de la déclaration du 15 janvier 2027.",
         "Record the payment of the 15 January 2027 return.",
         "Période de décembre : même schéma que les autres mois.", "December period: same pattern."),
    ):
        book.journal(7, "exam", ref, fr, en, why_fr, why_en)
    for fr, en, qtype, choices, why in (
        ("Date limite de la déclaration des résultats 2026 d'Ets Tchinda Froid ?", "Filing deadline for 2026?", "single",
         [("15 mars 2027", "15 March 2027", True), ("15 avril 2027", "15 April 2027", False)],
         "CGI art. 74 : 15 mars pour l'exploitant individuel au réel, même rattaché au CIME ; le 15 avril de l'art. 18 "
         "vise l'IS des sociétés."),
        ("Taux de l'IRPP sur les bénéfices industriels et commerciaux ?", "Income tax rate on business profits?", "single",
         [("30 %, taux de l'art. 17", "30%, art. 17 rate", True), ("Le barème des salaires", "The salary scale", False),
          ("25 %, taux réduit de l'art. 17 bis", "25%, art. 17 bis reduced rate", False)], "CGI art. 69 (2)."),
        ("L'IRPP de l'exploitant est une charge de l'exercice (891).", "The owner's income tax is an expense (891).",
         "truefalse", [("Vrai", "True", False), ("Faux", "False", True)],
         "Faux : c'est un impôt personnel, porté au compte de l'exploitant (1043)."),
        ("Les prélèvements de l'exploitant se réintègrent au bénéfice imposable.", "Drawings are added back.",
         "truefalse", [("Vrai", "True", False), ("Faux", "False", True)],
         "Faux : ils n'ont jamais été déduits, puisqu'ils ne sont pas des charges."),
        ("L'IRPP calculé dépasse ici le minimum de perception.", "Here the computed tax exceeds the minimum.",
         "truefalse", [("Vrai", "True", special["tax"]["is_total"] > special["tax"]["minimum_total"]),
                       ("Faux", "False", special["tax"]["is_total"] <= special["tax"]["minimum_total"])],
         "Comparer l'impôt calculé et 2 % du CA, CAC compris."),
        ("Un excédent de retenues subies est perdu en fin d'année.", "Excess withholdings are lost at year end.",
         "truefalse", [("Vrai", "True", False), ("Faux", "False", True)],
         "Faux : il s'impute sur l'impôt de l'année (art. 21 (2))."),
    ):
        book.choice(7, "quiz", liq, fr, en, choices, why, why, qtype=qtype)


MODULES = [
    ("Création et janvier", "Set-up and January", "Immatriculer l'établissement, apporter ses biens, tenir le premier mois.",
     "Register the business, contribute assets, keep the first month."),
    ("Premier trimestre (février et mars)", "First quarter (February and March)",
     "Encaisser, constater la TVA, subir les retenues publiques.", "Collect, recognise VAT, bear public withholdings."),
    ("Deuxième trimestre", "Second quarter", "Comparer 5,5 % et 11 %.", "Compare 5.5% and 11%."),
    ("Troisième trimestre", "Third quarter", "Suivre la hausse des prix des pièces.", "Follow rising parts prices."),
    ("Quatrième trimestre", "Fourth quarter", "Préparer la clôture.", "Prepare the year end."),
    ("Inventaire", "Year-end inventory", "Valoriser les stocks, amortir la camionnette, isoler la TVA en attente.",
     "Value stock, depreciate the van, isolate pending VAT."),
    ("Passerelle et déclaration des résultats", "Tax bridge and income return",
     "Liquider l'IRPP de l'exploitant avant le 15 mars.", "Compute the owner's income tax before 15 March."),
]


def sections(book, special):
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    kinds = {p["ref"]: p["kind"] for p in book.pieces}
    out = {m: [] for m in range(1, 8)}
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file", narrative_d.company_file("fr"),
                   narrative_d.company_file("en")))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   "Chaque démarche précise l'organisme, les documents et ce que l'on obtient [[cgi:art. L 1]].\n\n"
                   f"{proc}\n", f"Each procedure gives the body, documents and outcome [[cgi:art. L 1]].\n\n{proc}\n"))
    special["why"] = {}
    for month in range(1, 13):
        module = MODULE_OF_MONTH[month]
        opening = [ref for ref in by_month[month] if kinds[ref] == "balance"]
        scenes = narrative_d.month_scenes(book, special, month)
        told = {s["ref"] for s in scenes}
        others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
        special["why"].update({s["ref"]: s["why"] for s in scenes})
        out[module].append((f"{len(out[module]) + 1:02d}-{ascii_name(month)}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}",
                            narrative_d.month_section(month, scenes, opening, others, "fr"),
                            narrative_d.month_section(month, scenes, opening, others, "en")))
    told, why = narrative_d.year_end_sections(book, special)
    special["why"].update(why)
    out[6].append(("01-inventaire", "Inventaire au 31 décembre", "Year-end inventory", told["inventory"]["fr"],
                   told["inventory"]["en"]))
    out[7].append(("01-passerelle", "Passerelle fiscale", "Tax bridge", told["bridge"]["fr"], told["bridge"]["en"]))
    out[7].append(("02-declaration", "Déclaration des résultats 2026", "2026 income return", told["dsf"]["fr"],
                   told["dsf"]["en"]))
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
        folder = f"d/m{number}"
        entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": text(comp_fr, comp_en), "sections": entries})
    write(OUT / "d" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "d" / "ledger.json", book.entries)
    partie = {
        "slug": "d", "title": text("Parcours D : prestataire en froid et climatisation (Ets Tchinda Froid)",
                                   "Track D: refrigeration and air-conditioning contractor (Ets Tchinda Froid)"),
        "description": text("Établissement individuel au réel à Yaoundé, rattaché au CIME : TVA à l'encaissement, "
                            "retenues des clients publics, IRPP de l'exploitant.",
                            "Sole proprietorship under the actual regime in Yaoundé: VAT on collection, public "
                            "withholdings, owner's income tax."),
        "forme": "individuelle", "centre_impots": "cime", "chiffre_affaires_vise": 65000000,
        "tva_encaissement": True, "compte_tva_attente": "471",
        "sous_comptes": {"5522": text("Orange Money", "Orange Money"),
                         "4458": text("TVA retenue à la source par les clients publics",
                                      "VAT withheld at source by public customers"),
                         "3311": text("Fluides frigorigènes", "Refrigerants"),
                         "3312": text("Pièces détachées", "Spare parts")},
        "pieces": "d/pieces.json", "ledger": "d/ledger.json", "exam": {"questions_per_module": 4}, "modules": modules}
    write_manifest({}, partie)
    low = min(ledger.account_balance(book.entries, "521", datetime.date.fromisoformat(e["date"])) for e in book.entries)
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, "
          f"résultat {special['accounting']}, IRPP {special['tax']}, banque au plus bas {low}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
