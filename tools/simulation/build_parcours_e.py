"""Génère le parcours E de la simulation (Froid Équipe Services SARL, exercice 2026) dans content/simulation/e/.

Usage, depuis la racine du projet : .venv/Scripts/python -m tools.simulation.build_parcours_e

SARL à l'IGS (CGI art. 93 quater, C 39, C 40) tenant le SMT de l'AUDCIF (art. 13) : prestations de climatisation et
froid et vente de matériel ; gérant 20 %, fonctionnaire 80 % ; capital minimal de 100 000 FCFA (loi n° 2016/014) et
démarrage financé en compte courant d'associé (4621) ; le fonctionnaire est vacataire, payé en honoraires (S29 à S31).
Pas de TVA collectée ni déductible : la TVA payée aux fournisseurs entre dans le coût des achats. Questions numériques
ou à choix, sans écriture `journal` (S14). Les contrôles bloquants de courses/tests/content_rules.py vérifient la sortie.
"""
import calendar
import datetime
from decimal import Decimal as D

from referentiel import calculs
from tools.simulation import ledger, narrative_e
from tools.simulation.build_parcours_a import (
    LABELS, MONTHS_EN, MONTHS_FR, OUT, P, YEAR, Book, d, line, piece_list, split_usage, text, tva, workday, write,
    write_manifest,
)

SELLER = {"name": "Froid Équipe Services SARL", "niu": "M012600009134D", "rccm": "RC/DLA/2026/B/0233",
          "regime": "IGS", "centre": "Centre de fiscalité locale de Douala III", "address": "Logbaba, Douala"}
SUPPLIER = {"name": "Clim Distribution Wouri SARL", "niu": "M011800006620P", "rccm": "RC/DLA/2018/B/0377",
            "regime": "réel", "centre": "CIME Douala", "address": "Bonabéri, Douala"}
CLIENTS = [("Pharmacie du Littoral SARL", "M011600002281F"), ("Hôtel Akwa Palace (fictif)", "M010900001150Q"),
           ("École privée Les Palmiers", "M011200004473C")]
OWN = {"name": SELLER["name"], "niu": SELLER["niu"]}
MODULE_OF_MONTH = {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 5, 11: 5, 12: 5}
SERVICES = (450000, 380000)  # deux interventions facturées par mois, encaissées par virement et par Orange Money
CASH_SALES = 750000          # ventes de matériel au comptant
PURCHASE_HT = 520000         # matériel acheté chaque mois au fournisseur au réel
VACATION = 60000             # vacations mensuelles du fonctionnaire (honoraires, S30)
ADVANCE, CAPITAL, TOOLS_HT = 1400000, 100000, 400000
REPAY_FROM, REPAY = 7, 100000  # remboursement du compte courant à partir de juillet


def last(month):
    return calendar.monthrange(YEAR, month)[1]


def build():
    book, special = Book("E"), {"months": {}}
    procedures = [
        ("Création de la SARL au CFCE de Douala", "Creating the LLC at the Douala business centre",
         text("Centre de formalités de création d'entreprises (CFCE) de Douala", "Douala business formalities centre"),
         text("Créer une SARL au capital minimal de 100 000 FCFA (20 parts de 5 000), notaire facultatif",
              "Create an LLC with the 100,000 FCFA minimum capital, notary optional"),
         [text("5 + N exemplaires des statuts sous seing privé, authentifiés par le CFCE", "5 + N copies of the articles"),
          text("Déclarations de régularité et de conformité", "Declarations of regularity and conformity"),
          text("Casiers judiciaires ou déclarations sur l'honneur, CNI des associés et du gérant",
               "Criminal records or sworn statements, IDs"),
          text("Plan de localisation, boîte postale, contact téléphonique", "Location map, PO box, phone"),
          text("Frais de création et d'annonce légale (à vérifier au CFCE)", "Creation and legal notice fees (check)")],
         text("Registre de commerce, carte de contribuable (NIU), attestation de création",
              "Trade register, taxpayer card, creation certificate"),
         "[[source:loi-2016-014]] [[source:minfi-cfce]]"),
        ("Rattachement fiscal à l'IGS", "IGS tax attachment",
         text("Centre de fiscalité locale du lieu d'activité", "Local tax office"),
         text("Suivi à l'impôt général synthétique : chiffre d'affaires visé sous 50 millions",
              "Follow-up under the IGS: target turnover below 50 million"),
         [text("Carte de contribuable délivrée au CFCE", "Taxpayer card from the CFCE"),
          text("Statuts et registre de commerce", "Articles and trade register")],
         text("Suivi au régime de l'IGS et déclaration annuelle avant le 15 mars", "IGS follow-up, yearly return by 15 March"),
         "[[cgi:art. 93 quater]] [[cgi:art. C 41]]"),
        ("Ouverture du compte bancaire", "Opening the bank account",
         text("Banque commerciale (Banque X, fictive)", "Commercial bank (Bank X, fictitious)"),
         text("Ouvrir le compte de la SARL", "Open the company account"),
         [text("Demande d'ouverture, registre de commerce, carte de contribuable", "Request, trade register, taxpayer card"),
          text("Statuts, pièces d'identité du gérant", "Articles, manager's ID")],
         text("Relevé d'identité bancaire (RIB)", "Bank details (RIB)"), "[[source:sg-cm-compte-entreprise]]"),
        ("Compte marchand Orange Money", "Orange Money merchant account",
         text("Orange Cameroun, partenaires Orange Money", "Orange Cameroon, Orange Money partners"),
         text("Encaisser les interventions par Orange Money", "Collect payments through Orange Money"),
         [text("Registre de commerce, carte de contribuable, patente, statuts", "Trade register, taxpayer card, licence"),
          text("CNI du gérant, RIB", "Manager's ID, bank details")],
         text("Code marchand Orange Money", "Orange Money merchant code"), "[[source:orange-om-partenaire]]"),
    ]
    special["procedures"] = [book.piece(1, "demarche", d(1, 2), f"Démarche : {fr}", f"Procedure: {en}",
                                        {"organisme": body, "objet": purpose, "documents_a_fournir": docs,
                                         "document_obtenu": got, "source": source})
                             for fr, en, body, purpose, docs, got, source in procedures]
    special["capital"] = book.piece(1, "releve_bancaire", d(1, 3), "Attestation de dépôt du capital (Banque X)",
                                    "Capital deposit certificate (Bank X)",
                                    {"fields": [{"label": text("Parts", "Shares"),
                                                 "value": text("16 parts au fonctionnaire, 4 au gérant",
                                                               "16 shares to the civil servant, 4 to the manager")}],
                                     "totals": [{"label": text("Capital libéré", "Paid-up capital"), "amount": CAPITAL}]})
    book.entry(d(1, 3), special["capital"], line("521", "debit", CAPITAL), line("1013", "credit", CAPITAL))
    special["advance"] = book.piece(1, "releve_bancaire", workday(1, 4), "Avis de crédit : avance en compte courant d'associé",
                                    "Credit notice: partner's current-account advance",
                                    {"fields": [{"label": text("Associé", "Partner"),
                                                 "value": text("Fonctionnaire associé à 80 %", "Civil servant, 80% partner")}],
                                     "totals": [{"label": text("Avance reçue", "Advance received"), "amount": ADVANCE}]})
    book.entry(workday(1, 4), special["advance"], line("521", "debit", ADVANCE), line("4621", "credit", ADVANCE))
    tools = tva(TOOLS_HT)
    special["tools"] = book.piece(1, "facture_achat", d(1, 6), "Facture d'outillage de climatisation",
                                  "Air-conditioning tools invoice",
                                  {"issuer": SUPPLIER, "customer": OWN, "number": "CDW-2026-0012",
                                   "einvoice": "DGI-SFE-2026-002012",
                                   "lines": [{"label": text("Pompe à vide, manifold, détecteur de fuites",
                                                            "Vacuum pump, manifold, leak detector"),
                                              "qty": 1, "unit_price": TOOLS_HT, "amount": TOOLS_HT}],
                                   "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht", "amount": TOOLS_HT},
                                              {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                               "amount": int(tools["taxes"])},
                                              {"label": text("Net à payer", "Amount due"), "role": "ttc",
                                               "amount": int(tools["ttc"])}]})
    book.entry(d(1, 6), special["tools"], line("6056", "debit", tools["ttc"]), line("521", "credit", tools["ttc"]))
    special["tools_ttc"] = int(tools["ttc"])

    lots, cash_previous = [], 0
    for month in range(1, 13):
        end, refs = last(month), {}
        mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
        # Achat de matériel au fournisseur au réel : TVA non déductible à l'IGS, précompte de 5 % (CGI art. 21 (3)).
        unit = 130000 + 1000 * (month - 1)
        qty = PURCHASE_HT // 130000
        ht = qty * unit
        taxes = tva(ht)
        withheld = calculs.franc(D(ht) * P["precompte.taux_igs"] / 100)
        lots.append((qty, unit))
        refs["purchase"] = book.piece(month, "facture_achat", workday(month, 5), f"Facture de matériel de {mfr}",
                                      f"{men} equipment invoice",
                                      {"issuer": SUPPLIER, "customer": OWN, "number": f"CDW-2026-{100 + month:04d}",
                                       "einvoice": f"DGI-SFE-2026-{2100 + month:06d}",
                                       "lines": [{"label": text("Climatiseurs split 1,5 CV", "1.5 HP split air conditioners"),
                                                  "qty": qty, "unit_price": unit, "amount": ht}],
                                       "totals": [{"label": text("Total HT", "Total excl. tax"), "role": "ht", "amount": ht},
                                                  {"label": text("TVA et CAC", "VAT and council cents"), "role": "tax",
                                                   "amount": int(taxes["taxes"])},
                                                  {"label": text("Précompte sur achats 5 %", "5% purchase withholding"),
                                                   "role": "tax", "amount": int(withheld)},
                                                  {"label": text("Net à payer", "Amount due"), "role": "ttc",
                                                   "amount": int(taxes["ttc"] + withheld)}]})
        book.entry(workday(month, 5), refs["purchase"], line("6011", "debit", taxes["ttc"]), line("4492", "debit", withheld),
                   line("521", "credit", taxes["ttc"] + withheld))
        # Deux interventions facturées, sans TVA (IGS) ; encaissées par virement et par Orange Money.
        for i, (amount, account) in enumerate(zip(SERVICES, ("521", "5522"))):
            client, niu = CLIENTS[(month + i) % 3]
            ref = book.piece(month, "facture_vente", workday(month, 10 + 8 * i), f"Facture d'intervention n° {month}-{i + 1}",
                             f"Service invoice no. {month}-{i + 1}",
                             {"issuer": SELLER, "customer": {"name": client, "niu": niu},
                              "number": f"FES-2026-{month:02d}{i + 1}", "einvoice": f"DGI-SFE-2026-{3000 + 10 * month + i:06d}",
                              "fields": [{"label": text("Régime", "Regime"),
                                          "value": text("IGS : facture sans TVA", "IGS: invoice without VAT")}],
                              "lines": [{"label": text("Entretien et dépannage de climatisation", "AC maintenance"),
                                         "amount": amount}],
                              "totals": [{"label": text("Total", "Total"), "role": "ht", "amount": amount},
                                         {"label": text("Net à payer", "Amount due"), "role": "ttc", "amount": amount}]})
            book.entry(workday(month, 10 + 8 * i), ref, line(account, "debit", amount), line("7061", "credit", amount))
            refs[f"service{i}"] = ref
        refs["cash"] = book.piece(month, "recu_caisse", d(month, end), f"Ventes de matériel au comptant de {mfr}",
                                  f"{men} cash equipment sales",
                                  {"totals": [{"label": text("Ventes encaissées", "Sales collected"), "amount": CASH_SALES}]})
        book.entry(d(month, end), refs["cash"], line("5711", "debit", CASH_SALES), line("7011", "credit", CASH_SALES))
        refs["vacation"] = book.piece(month, "recu_caisse", workday(month, 25), f"Note d'honoraires du vacataire, {mfr}",
                                      f"Part-time instructor's fee note, {men}",
                                      {"fields": [{"label": text("Intervenant", "Provider"),
                                                   "value": text("Fonctionnaire associé, vacataire (formation des clients)",
                                                                 "Civil servant partner, part-time trainer")}],
                                       "totals": [{"label": text("Honoraires payés en espèces", "Fees paid in cash"),
                                                   "amount": VACATION}]})
        book.entry(workday(month, 25), refs["vacation"], line("632", "debit", VACATION), line("5711", "credit", VACATION))
        # Relevé Orange Money : transfert de la recette vers la banque (585, S19) et frais de l'opérateur (631).
        transfer = SERVICES[1] - 3000
        refs["momo"] = book.piece(month, "releve_momo", d(month, end), f"Relevé Orange Money de {mfr}",
                                  f"{men} Orange Money statement",
                                  {"totals": [{"label": text("Encaissement reçu", "Payment received"), "amount": SERVICES[1]},
                                              {"label": text("Transfert vers la banque", "Transfer to the bank"),
                                               "amount": transfer},
                                              {"label": text("Frais de retrait", "Withdrawal fees"), "amount": 3000}]})
        book.entry(d(month, end), refs["momo"], line("585", "debit", transfer), line("631", "debit", 3000),
                   line("5522", "credit", SERVICES[1]))
        # Relevé bancaire : transfert reçu, versement des espèces du mois précédent, frais, remboursements.
        deposit = cash_previous
        lines = [line("521", "debit", transfer + deposit), line("585", "credit", transfer)]
        if deposit:
            lines += [line("5711", "credit", deposit)]
        lines += [line("631", "debit", 2500), line("521", "credit", 2500)]
        totals = [{"label": text("Transfert Orange Money et versement d'espèces", "Orange Money transfer and cash deposit"),
                   "amount": transfer + deposit},
                  {"label": text("Frais de tenue de compte", "Account fees"), "amount": 2500}]
        if month >= REPAY_FROM:
            lines += [line("4621", "debit", REPAY), line("521", "credit", REPAY)]
            totals.append({"label": text("Remboursement du compte courant d'associé", "Partner account repayment"),
                           "amount": REPAY})
        refs["bank"] = book.piece(month, "releve_bancaire", d(month, end), f"Relevé bancaire de {mfr} (Banque X)",
                                  f"{men} bank statement (Bank X)", {"totals": totals})
        book.entry(d(month, end), refs["bank"], *lines)
        cash_previous = CASH_SALES - VACATION
        special["months"][month] = refs
    special["lots"] = lots
    year_end(book, special)
    return book, special


def year_end(book, special):
    lots = [(D(q), D(u)) for q, u in special["lots"]]
    bought = sum(q for q, _ in special["lots"])
    unsold = 6
    sold = bought - unsold
    result = calculs.sortie_cmup(lots, D(sold))
    special["stock"] = (book.piece(12, "fiche_stock", d(12, 31), "Fiche de stock des climatiseurs (inventaire physique)",
                                   "Air conditioner stock card (physical count)",
                                   {"fields": [{"label": text("Achetés / en stock au 31/12", "Bought / in stock at 31/12"),
                                                "value": f"{bought} / {unsold}"}],
                                    "lines": [{"label": text(f"Lot {i}", f"Lot {i}"), "qty": q, "unit_price": u,
                                               "amount": q * u} for i, (q, u) in enumerate(special["lots"], start=1)]}),
                        lots, sold, result)
    entries = book.entries
    turnover = sum(l["amount"] for e in entries for l in e["lines"] if l["account"].startswith("70") and l["side"] == "credit")
    classes = [(D(P[f"igs.classe{i}_plafond"]), D(P[f"igs.classe{i}_montant"])) for i in range(1, 11)]
    igs = calculs.igs_annuel(D(turnover), classes)
    special.update(turnover=turnover, igs=int(igs), igs_cga=int(calculs.igs_annuel(D(turnover), classes, True)),
                   classes=[[int(c), int(m)] for c, m in classes],
                   precompte=sum(l["amount"] for e in entries for l in e["lines"]
                                 if l["account"] == "4492" and l["side"] == "debit"),
                   current_account=-ledger.account_balance(entries, "4621", datetime.date(YEAR, 12, 31)),
                   cash_result=sum(l["amount"] for e in entries for l in e["lines"] if l["account"][0] == "7")
                   - sum(l["amount"] for e in entries for l in e["lines"] if l["account"][0] == "6"))
    special["igs_return"] = book.piece(3, "declaration", d(3, 15, YEAR + 1), "Déclaration annuelle de l'IGS 2026",
                                       "2026 yearly IGS return",
                                       {"fields": [{"label": text("Chiffre d'affaires HT 2026", "2026 turnover"),
                                                    "value": f"{turnover:,}".replace(",", " ")}],
                                        "totals": [{"label": text("IGS annuel (CGI art. C 40)", "Yearly IGS"),
                                                    "amount": int(igs)}]}, year=YEAR + 1)


def balances(book):
    for month in range(2, 13):
        date = d(month, 1)
        book.piece(month, "balance", date, f"Balance au {last(month - 1)} {MONTHS_FR[month - 2]} {YEAR}",
                   f"Trial balance at {MONTHS_EN[month - 2]} {last(month - 1)}, {YEAR}",
                   ledger.balance_piece(book.entries, before=datetime.date.fromisoformat(date), labels=LABELS))


def monthly_questions(book, special, month):
    module, refs = MODULE_OF_MONTH[month], special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    purchase = next(p for p in book.pieces if p["ref"] == refs["purchase"])
    totals = {t["label"]["fr"]: t["amount"] for t in purchase["payload"]["totals"]}
    asks = [
        (refs["purchase"], totals["Précompte sur achats 5 %"], f"Précompte de 5 % subi sur l'achat de {mfr} ?",
         f"5% withholding suffered on the {men} purchase?", "Contribuable à l'IGS : 5 % du HT (CGI art. 21 (3))."),
        (refs["purchase"], totals["Net à payer"], f"Dépense de trésorerie de l'achat de {mfr} ?",
         f"Cash outflow for the {men} purchase?",
         "À l'IGS, la TVA payée n'est pas déductible : elle s'ajoute au coût, avec le précompte."),
        (refs["service0"], SERVICES[0], f"Recette de la première intervention de {mfr} ?", f"Receipt of {men}'s first job?",
         "Facture sans TVA : un contribuable à l'IGS ne la facture pas."),
        (refs["service1"], SERVICES[1], f"Recette encaissée par Orange Money en {mfr} ?",
         f"Receipt collected by Orange Money in {men}?", "Encaissement porté au sous-compte 5522 (S19)."),
        (refs["cash"], CASH_SALES, f"Ventes de matériel au comptant de {mfr} ?", f"{men} cash equipment sales?",
         "Recette de caisse 5711, ventes de marchandises 7011."),
        (refs["vacation"], VACATION, f"Honoraires du vacataire en {mfr} ?", f"Part-time trainer's fees in {men}?",
         "Honoraires 632 : le fonctionnaire n'est pas salarié de la SARL (S30)."),
    ]
    for piece, value, fr, en, why in asks:
        book.numeric(module, "exam", value, fr, en, why, why, piece=piece)
    receipts = SERVICES[0] + SERVICES[1] + CASH_SALES
    book.numeric(module, "exam", receipts, f"Total des recettes de {mfr} (SMT) ?", f"Total {men} receipts (cash basis)?",
                 "Le SMT enregistre les recettes encaissées : deux interventions et les ventes au comptant.",
                 "Cash-basis receipts: two jobs and cash sales.", piece=refs["cash"])
    balance = ledger.account_balance(book.entries, "521", datetime.date(YEAR, month, last(month)))
    book.numeric(module, "exam", balance, f"Solde de trésorerie en banque au {last(month)} {mfr} ?",
                 f"Bank balance at {men} {last(month)}?", "Recettes moins dépenses passées par la banque à cette date.",
                 "Bank receipts less payments at that date.", piece=refs["bank"],
                 rapprochement={"account": "521", "date": d(month, last(month))})
    if month > 1:
        balance_ref = next(p["ref"] for p in book.pieces if p["kind"] == "balance" and p["date"] == d(month, 1))
        previous = datetime.date(YEAR, month - 1, last(month - 1))
        book.numeric(module, "exam", ledger.account_balance(book.entries, "5711", previous),
                     f"Caisse au début de {mfr}, d'après la balance ?", f"Cash in hand at the start of {men}?",
                     "Solde débiteur du compte 5711 dans la balance officielle.", "Debit balance of account 5711.",
                     piece=balance_ref, rapprochement={"account": "5711", "date": previous.isoformat()})
    book.numeric(module, "exam", 3000, f"Frais Orange Money de {mfr} ?", f"{men} Orange Money fees?",
                 "Frais de l'opérateur en services bancaires (631).", "Operator fees in account 631.", piece=refs["momo"])
    if month >= REPAY_FROM:
        book.numeric(module, "exam", REPAY, f"Remboursement du compte courant d'associé en {mfr} ?",
                     f"Partner current-account repayment in {men}?",
                     "La SARL rembourse l'avance du fonctionnaire (4621) ; ce n'est pas une charge.",
                     "Repaying the partner's advance is not an expense.", piece=refs["bank"])


def build_questions(book, special):
    for ref, (fr, en, right, wrong) in zip(special["procedures"], [
        ("Capital minimum d'une SARL au Cameroun ?", "Minimum capital of a Cameroonian LLC?",
         ("100 000 FCFA (loi n° 2016/014)", "100,000 FCFA"), ("1 000 000 FCFA", "1,000,000 FCFA")),
        ("Pourquoi la SARL relève-t-elle de l'IGS ?", "Why is the LLC under the IGS?",
         ("Chiffre d'affaires visé sous 50 millions", "Target turnover below 50 million"),
         ("Parce que c'est une SARL", "Because it is an LLC")),
        ("Que remet la banque à l'ouverture du compte ?", "What does the bank give?",
         ("Un RIB", "Bank details (RIB)"), ("Une patente", "A licence")),
        ("Quelle pièce Orange exige-t-il en plus des documents légaux ?", "Which extra document does Orange require?",
         ("Le RIB", "Bank details (RIB)"), ("Un bilan certifié", "A certified balance sheet")),
    ]):
        book.choice(1, "quiz", ref, fr, en, [(right[0], right[1], True), (wrong[0], wrong[1], False)],
                    "Voir la démarche et sa source officielle.", "See the procedure and its official source.")
    for piece, value, fr, en, why in (
        (special["capital"], CAPITAL, "Capital libéré de la SARL ?", "Paid-up capital?",
         "Capital minimal de 100 000 FCFA : 20 parts de 5 000 (loi n° 2016/014 art. 2)."),
        (special["capital"], 80000, "Apport du fonctionnaire au capital (80 %) ?", "Civil servant's share (80%)?",
         "16 parts de 5 000 FCFA."),
        (special["capital"], 20000, "Apport du gérant au capital (20 %) ?", "Manager's share (20%)?", "4 parts de 5 000 FCFA."),
        (special["advance"], ADVANCE, "Avance du fonctionnaire en compte courant d'associé ?", "Partner's advance?",
         "Compte 4621 : dette de la SARL envers l'associé, remboursable (S31)."),
        (special["tools"], special["tools_ttc"], "Coût de l'outillage, TVA comprise ?", "Tools cost, VAT included?",
         "Petit outillage (6056) sous le seuil de 500 000 HT (CGI art. 7) ; TVA non déductible à l'IGS."),
        (special["tools"], special["tools_ttc"] - TOOLS_HT, "TVA et CAC payées sur l'outillage, non récupérables ?",
         "Non-recoverable VAT on the tools?", "À l'IGS, la TVA facturée par le fournisseur au réel s'ajoute au coût."),
        (special["advance"], CAPITAL + ADVANCE, "Fonds apportés au démarrage (capital et avance) ?",
         "Start-up funds (capital and advance)?", "100 000 de capital et 1 400 000 d'avance : environ 1 500 000 (S31)."),
    ):
        book.numeric(1, "exam", value, fr, en, why, why, piece=piece)
    for month in range(1, 13):
        monthly_questions(book, special, month)
    stock_ref, lots, sold, result = special["stock"]
    args = [[[int(q), int(u)] for q, u in lots], int(sold)]
    for key, fr, en in (("cout_unitaire", "coût moyen unitaire pondéré d'un climatiseur", "weighted average unit cost"),
                        ("valeur_sortie", "coût des climatiseurs vendus au CMUP", "cost of units sold at WAC")):
        book.numeric(6, "exam", result[key], f"Inventaire : {fr} ?", f"Inventory: {en}?",
                     "CMUP de l'année, arrondi au franc.", "Period WAC, rounded.", piece=stock_ref,
                     calcul={"fonction": "sortie_cmup", "args": args, "resultat": [key]})
    peps = calculs.sortie_peps(lots, D(sold))
    book.numeric(6, "exam", peps["valeur_sortie"], "Inventaire : coût des ventes en PEPS (contraste) ?",
                 "Inventory: cost of units sold under FIFO?", "Les plus anciens lots sortent d'abord.",
                 "Oldest lots go first.", piece=stock_ref, calcul={"fonction": "sortie_peps", "args": args,
                                                                    "resultat": ["valeur_sortie"]})
    year = [
        (special["turnover"], "Chiffre d'affaires HT 2026 (prestations et ventes) ?", "2026 turnover?",
         "Prestations 7061 et ventes de marchandises 7011."),
        (special["precompte"], "Total des précomptes de 5 % subis en 2026 ?", "Total 2026 withholdings?",
         "Somme des précomptes portés en 4492."),
        (special["current_account"], "Solde du compte courant d'associé au 31 décembre ?", "Partner account balance?",
         "Avance de 1 400 000 moins six remboursements de 100 000."),
        (special["cash_result"], "Excédent des recettes sur les dépenses de 2026 (classes 7 et 6) ?",
         "2026 surplus of receipts over expenses?", "Produits moins charges enregistrés en trésorerie."),
        (sum(q for q, _ in special["lots"]) - sold, "Climatiseurs en stock au 31 décembre ?", "Units in stock?",
         "Inventaire physique."),
    ]
    def total(prefix, side="debit"):
        return sum(l["amount"] for e in book.entries for l in e["lines"] if l["account"].startswith(prefix)
                   and l["side"] == side)

    year += [
        (total("6011"), "Achats de matériel de l'année, TVA comprise ?", "Year's equipment purchases?",
         "Douze factures du fournisseur, TVA non récupérable comprise."),
        (total("7061", "credit"), "Recettes des interventions de l'année ?", "Year's service receipts?",
         "Compte 7061."),
        (total("7011", "credit"), "Ventes de matériel au comptant de l'année ?", "Year's cash sales?", "Compte 7011."),
        (total("631"), "Frais bancaires et Orange Money de l'année ?", "Year's bank and Orange Money fees?",
         "Compte 631."),
    ]
    for value, fr, en, why in year:
        book.numeric(6, "exam", value, fr, en, why, why, piece=stock_ref)
    for fr, en, choices, why in (
        ("Le SMT est-il ouvert à cette SARL ?", "Is the cash-basis system open to this LLC?",
         [("Oui : CA sous 30 millions (services) et sous 60 millions (négoce)", "Yes", True), ("Non", "No", False)],
         "AUDCIF art. 13."),
        ("Une SARL à l'IGS facture-t-elle la TVA ?", "Does an IGS LLC charge VAT?",
         [("Non", "No", True), ("Oui, à 19,25 %", "Yes, at 19.25%", False)], "Le régime de l'IGS est synthétique."),
        ("Le remboursement du compte courant est une charge.", "Repaying the partner account is an expense.",
         [("Vrai", "True", False), ("Faux", "False", True)], "Faux : c'est le remboursement d'une dette (4621)."),
        ("Les honoraires du vacataire sont des salaires soumis à la CNPS.", "The trainer's fees are CNPS-liable wages.",
         [("Vrai", "True", False), ("Faux", "False", True)], "Faux : honoraires (632), pas de contrat de travail (S30)."),
        ("La TVA payée aux fournisseurs est récupérable à l'IGS.", "VAT paid to suppliers is recoverable under IGS.",
         [("Vrai", "True", False), ("Faux", "False", True)], "Faux : elle entre dans le coût (CGI art. 143)."),
        ("Le PEPS donne un coût des ventes plus faible quand les prix montent.",
         "FIFO gives a lower cost of sales when prices rise.",
         [("Vrai", "True", True), ("Faux", "False", False)], "Vrai : les lots anciens, moins chers, sortent d'abord."),
        ("Les ventes au comptant sont-elles des recettes du SMT ?", "Are cash sales cash-basis receipts?",
         [("Oui", "Yes", True), ("Non", "No", False)], "Le SMT suit les recettes et les dépenses encaissées."),
        ("L'inventaire physique compte-t-il les climatiseurs en stock ?", "Does the count include units in stock?",
         [("Oui", "Yes", True), ("Non", "No", False)], "Oui : six climatiseurs au 31 décembre."),
    ):
        qtype = "truefalse" if choices[0][0] in ("Vrai", "Faux") else "single"
        book.choice(6, "quiz", stock_ref, fr, en, choices, why, why, qtype=qtype)
    igs_ref = special["igs_return"]
    book.numeric(7, "exam", special["igs"], "IGS annuel 2026 de la SARL ?", "2026 yearly IGS?",
                 "Tarif de la classe du chiffre d'affaires (CGI art. C 40 (1)).", "Tariff of the turnover class.",
                 piece=igs_ref, calcul={"fonction": "igs_annuel", "args": [special["turnover"], special["classes"]],
                                        "resultat": []})
    book.numeric(7, "exam", special["igs_cga"], "IGS 2026 si la SARL adhère à un Centre de Gestion Agréé ?",
                 "2026 IGS with a registered management centre?", "Tarif réduit de moitié (CGI art. C 40 (2)).",
                 "Halved tariff.", piece=igs_ref,
                 calcul={"fonction": "igs_annuel", "args": [special["turnover"], special["classes"], True], "resultat": []})
    for value, fr, en, why in (
        (special["turnover"], "Chiffre d'affaires déclaré pour l'IGS 2026 ?", "Turnover declared for the 2026 IGS?",
         "Total des recettes HT de l'année."),
        (special["igs"] - special["igs_cga"], "Économie d'IGS procurée par un Centre de Gestion Agréé ?",
         "IGS saving with a management centre?", "Moitié du tarif (CGI art. C 40 (2))."),
        (special["precompte"], "Précomptes de 5 % subis sur l'année ?", "Withholdings suffered over the year?",
         "Somme des précomptes sur achats."),
        (special["current_account"], "Dette restante envers le fonctionnaire au 31 décembre ?", "Remaining debt?",
         "Solde du compte courant d'associé."),
        (special["cash_result"], "Excédent de trésorerie de l'exercice ?", "Year's cash surplus?",
         "Recettes moins dépenses."),
        (CAPITAL, "Capital social de la SARL ?", "Share capital?", "Loi n° 2016/014 art. 2."),
        (80000, "Part du capital détenue par le fonctionnaire, en FCFA ?", "Civil servant's capital, in FCFA?",
         "80 % de 100 000."),
        (12 * VACATION, "Honoraires versés au vacataire sur l'année ?", "Fees paid to the trainer over the year?",
         "Douze notes d'honoraires."),
        ((13 - REPAY_FROM) * REPAY, "Remboursements du compte courant sur l'année ?",
         "Partner account repayments over the year?", "Six remboursements, de juillet à décembre."),
        (special["igs"], "Montant à payer avec la déclaration annuelle de l'IGS ?", "Amount due with the IGS return?",
         "Tarif annuel de la classe (CGI art. C 40)."),
        (special["tools_ttc"], "Coût de l'outillage acheté en janvier ?", "Tools bought in January?",
         "Petit outillage, TVA comprise."),
        (12 * SERVICES[0], "Recettes annuelles des premières interventions du mois ?", "Yearly receipts of first jobs?",
         "Douze factures."),
    ):
        book.numeric(7, "exam", value, fr, en, why, why, piece=igs_ref)
    for fr, en, choices, why in (
        ("Date limite de la déclaration annuelle de l'IGS 2026 ?", "Deadline of the 2026 IGS return?",
         [("15 mars 2027", "15 March 2027", True), ("15 avril 2027", "15 April 2027", False)], "CGI art. C 41."),
        ("La SARL dépose-t-elle une DSF normale ?", "Does the LLC file a standard return?",
         [("Non : déclaration annuelle de l'IGS", "No: yearly IGS return", True), ("Oui", "Yes", False)],
         "À l'IGS et au SMT, pas de DSF normale (S14)."),
        ("Quel article fixe le tarif de l'IGS ?", "Which article sets the IGS tariff?",
         [("CGI art. C 40", "CGI art. C 40", True), ("CGI art. 17", "CGI art. 17", False)], "Article C 40 (1)."),
        ("Le tarif de l'IGS dépend-il du bénéfice ?", "Does the IGS depend on profit?",
         [("Non, de la classe de chiffre d'affaires", "No, on the turnover class", True), ("Oui", "Yes", False)],
         "Tarif forfaitaire par classe."),
        ("À 50 millions de CA, la SARL reste-t-elle à l'IGS ?", "At 50 million, does it stay under IGS?",
         [("Non : régime du réel", "No: actual regime", True), ("Oui", "Yes", False)], "CGI art. C 39 et 93 quater."),
        ("Le gérant détient quelle part du capital ?", "What share does the manager hold?",
         [("20 %", "20%", True), ("80 %", "80%", False)], "Profil du parcours E (S29)."),
        ("Le fonctionnaire peut-il être salarié de la SARL ?", "May the civil servant be an employee?",
         [("Non : il intervient comme vacataire", "No: as a part-time trainer", True), ("Oui", "Yes", False)], "S30."),
        ("Le recours au notaire est-il obligatoire pour cette SARL ?", "Is a notary required?",
         [("Non : capital inférieur à 1 000 000", "No: capital below 1,000,000", True), ("Oui", "Yes", False)],
         "Loi n° 2016/014 art. 4."),
    ):
        book.choice(7, "quiz", igs_ref, fr, en, choices, why, why)
    for module in book.questions:
        split_usage(book.questions[module])


MODULES = [
    ("Création et janvier", "Set-up and January"), ("Premier trimestre (février et mars)", "First quarter"),
    ("Deuxième trimestre", "Second quarter"), ("Troisième trimestre", "Third quarter"),
    ("Quatrième trimestre", "Fourth quarter"), ("Clôture et inventaire", "Year-end and inventory"),
    ("IGS annuel", "Yearly IGS"),
]
COMPETENCE = text("Tenir les recettes et les dépenses d'une SARL à l'IGS (SMT) sur pièces",
                  "Keep the cash-basis records of an IGS company from documents")


def sections(book, special):
    by_month = {m: [p["ref"] for p in book.pieces if p["date"].startswith(f"{YEAR}-{m:02d}") and p["kind"] != "demarche"]
                for m in range(1, 13)}
    out = {m: [] for m in range(1, 8)}
    company = ("## Froid Équipe Services SARL\n\nSARL de prestations de climatisation et froid et de vente de matériel à "
               "Douala-Logbaba, créée le 2 janvier {y} au capital minimal de 100 000 FCFA [[source:loi-2016-014]] : "
               "un gérant (20 %) et un fonctionnaire (80 %), qui finance le démarrage en compte courant d'associé "
               "[[syscohada:4621]] et intervient comme vacataire. Chiffre d'affaires visé sous 30 millions : régime de "
               "l'IGS [[cgi:art. 93 quater]] et système minimal de trésorerie [[source:ohada-audcif]].\n\n"
               "### Comptes utilisés\n\n[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] (sous-compte 5522 Orange "
               "Money) [[syscohada:7061]] [[syscohada:7011]] [[syscohada:6011]] [[syscohada:4492]] [[syscohada:632]]\n\n"
               "### Taux de l'exercice\n\n- précompte sur achats à l'IGS [[param:precompte.taux_igs]] [[cgi:art. 21]] ;\n"
               "- capital minimum d'une SARL [[param:sarl.capital_minimum]].\n").format(y=YEAR)
    company_en = ("## Froid Équipe Services SARL\n\nAir-conditioning services and equipment LLC in Douala, created on "
                  "2 January {y} with the minimum capital [[source:loi-2016-014]], under the IGS "
                  "[[cgi:art. 93 quater]] and the cash-basis system.\n\n### Accounts\n\n[[syscohada:521]] "
                  "[[syscohada:5711]] [[syscohada:4621]] [[syscohada:7061]]\n\n### Rates\n\n- IGS purchase withholding "
                  "[[param:precompte.taux_igs]] [[cgi:art. 21]];\n- minimum LLC capital [[param:sarl.capital_minimum]].\n"
                  ).format(y=YEAR)
    out[1].append(("01-dossier", "Dossier d'entreprise", "Company file",
                   company + "\n" + narrative_e.company_extra("fr"), company_en + "\n" + narrative_e.company_extra("en")))
    proc = piece_list(special["procedures"])
    out[1].append(("02-creation", "Démarches de création", "Set-up procedures",
                   f"Les démarches et leurs sources officielles [[cgi:art. C 41]].\n\n{proc}\n",
                   f"Procedures and their official sources [[cgi:art. C 41]].\n\n{proc}\n"))
    kinds = {p["ref"]: p["kind"] for p in book.pieces}
    for month in range(1, 13):
        # S34 : chaque mois est raconté scène par scène ; la balance d'ouverture suit l'accroche.
        module = MODULE_OF_MONTH[month]
        opening = [ref for ref in by_month[month] if kinds[ref] == "balance"]
        told = {s["ref"] for s in narrative_e.month_scenes(book, special, month)}
        others = [ref for ref in by_month[month] if ref not in told and ref not in opening]
        name = MONTHS_FR[month - 1].replace("é", "e").replace("û", "u")
        out[module].append((f"{len(out[module]) + 1:02d}-{name}", f"{MONTHS_FR[month - 1].capitalize()} {YEAR}",
                            f"{MONTHS_EN[month - 1]} {YEAR}",
                            narrative_e.month_section(book, special, month, opening, others, "fr"),
                            narrative_e.month_section(book, special, month, opening, others, "en")))
    told = narrative_e.year_end_sections(book, special)
    out[6].append(("01-cloture", "Clôture et inventaire", "Year-end and inventory", told["close"]["fr"],
                   told["close"]["en"]))
    out[7].append(("01-igs", "IGS annuel", "Yearly IGS", told["igs"]["fr"], told["igs"]["en"]))
    return out


def main():
    book, special = build()
    balances(book)
    build_questions(book, special)
    module_sections = sections(book, special)
    modules = []
    for number, (title_fr, title_en) in enumerate(MODULES, start=1):
        folder = f"e/m{number}"
        entries = []
        for order, (file, s_fr, s_en, body_fr, body_en) in enumerate(module_sections[number], start=1):
            write(OUT / folder / f"{file}.fr.md", body_fr)
            write(OUT / folder / f"{file}.en.md", body_en)
            entries.append({"order": order, "file": file, "kind": "content", "title": text(s_fr, s_en)})
        write(OUT / folder / "questions.json", book.questions[number])
        modules.append({"order": number, "dir": folder, "title": text(title_fr, title_en), "duration_hours": 6,
                        "competence": COMPETENCE, "sections": entries})
    write(OUT / "e" / "pieces.json", sorted(book.pieces, key=lambda p: (p["date"], p["ref"])))
    write(OUT / "e" / "ledger.json", book.entries)
    partie = {
        "slug": "e", "title": text("Parcours E : climatisation et froid à l'IGS (Froid Équipe Services SARL)",
                                   "Track E: air conditioning under the IGS (Froid Équipe Services SARL)"),
        "description": text("SARL à l'IGS, au SMT : prestations de climatisation et froid et vente de matériel à Douala.",
                            "LLC under the IGS, cash basis: air-conditioning services and equipment in Douala."),
        "regime": "igs", "systeme_comptable": "smt", "centre_impots": "cfl", "chiffre_affaires_vise": 20000000,
        "sous_comptes": {"5522": text("Orange Money", "Orange Money")},
        "pieces": "e/pieces.json", "ledger": "e/ledger.json", "exam": {"questions_per_module": 4}, "modules": modules}
    write_manifest({}, partie)
    print(f"{len(book.pieces)} pièces, {len(book.entries)} écritures, "
          f"{sum(len(q) for q in book.questions.values())} questions ; CA {special['turnover']}, IGS {special['igs']}")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
