"""Récit du parcours A, Ngono Mode SARL (S34) : même canevas en cinq temps que B3 (tools/simulation/narrative_b3.py).

Une boutique de vêtements à Douala-Akwa, au réel : achats chez un grossiste, ventes au comptant, par Orange Money et
MTN MoMo, paie de trois salariés, voiture de livraison, provision pour litige, passerelle en six éléments. Tous les
montants sont lus sur les pièces générées.
"""
import datetime

from tools.simulation.narrative_b3 import (
    MONTHS_EN, MONTHS_FR, THIN, assemble, fcfa, qty, scene, total, typeset_fr,
)

CAST_FR = (
    "### Les personnages\n\n"
    "| Personnage | Rôle |\n|---|---|\n"
    "| Clarisse Ngono | Associée majoritaire, créatrice de la boutique |\n"
    "| Alain Ekwalla | Gérant salarié : achats, banque, déclarations |\n"
    "| Brenda et Sandrine | Vendeuses : caisse, Mobile Money, rangement des rayons |\n"
    "| M. Din | Commercial de Sawa Textiles SARL, le grossiste |\n"
    "| M. Tchoua | Propriétaire du local de la boutique |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n")
CAST_EN = (
    "### The people\n\n"
    "| Person | Role |\n|---|---|\n"
    "| Clarisse Ngono | Majority partner, founder of the shop |\n"
    "| Alain Ekwalla | Salaried manager: purchasing, bank, tax returns |\n"
    "| Brenda and Sandrine | Sales assistants: till, Mobile Money, shelves |\n"
    "| Mr Din | Sales rep of Sawa Textiles SARL, the wholesaler |\n"
    "| Mr Tchoua | Owner of the shop premises |\n\n"
    "All are fictitious, like the companies and the amounts.\n")

ROUTINES_FR = (
    "### Les outils et les routines de la boutique\n\n"
    "**Les outils.** Alain tient la comptabilité dans un logiciel comptable (Sage 100 Comptabilité, Odoo ou tout autre "
    "logiciel qui respecte l'AUDCIF) ; le logiciel valide chaque écriture et clôture les périodes "
    "[[source:ohada-audcif]].\n\n"
    "| Support | Ce qu'il contient | Qui le tient |\n|---|---|---|\n"
    "| Dossier permanent | Statuts, attestation de dépôt du capital, bail, RCCM, carte de contribuable | Alain |\n"
    "| Classeurs Achats, Ventes, Banque et Mobile Money, Caisse, Paie, Immobilisations, Déclarations fiscales | Les "
    "pièces de l'exercice, dans l'ordre, annotées du code du journal et du numéro d'écriture | Alain |\n"
    "| Brouillard de caisse | Les ventes en espèces du jour, signées le soir | Brenda et Sandrine |\n"
    "| Fiches de stock | Chemises, pantalons et robes entrés et sortis | Brenda |\n\n"
    "Journaux du logiciel : achats (AC), ventes (VT), banque (BQ), caisse (CA), MTN MoMo (MM), Orange Money (OM), "
    "opérations diverses (OD).\n\n"
    "**Les routines.**\n\n"
    "- *Chaque soir* : arrêté de caisse signé, relevé des paiements Mobile Money du jour.\n"
    "- *Chaque semaine* : saisie et classement des pièces de la semaine.\n"
    "- *Chaque mois* : rapprochements de la banque et des deux comptes Mobile Money, balance, déclaration du 15 "
    "[[cgi:art. 21]].\n"
    "- *Chaque trimestre* : clôture des périodes dans le logiciel.\n"
    "- *Chaque année* : inventaire des trois familles, livre d'inventaire, DSF ; tout se conserve dix ans.\n")
ROUTINES_EN = (
    "### The shop's tools and routines\n\n"
    "**Tools.** Alain keeps the books in accounting software (Sage 100 Comptabilité, Odoo or any AUDCIF-compliant "
    "software); it validates each entry and closes periods [[source:ohada-audcif]].\n\n"
    "| Support | Contents | Kept by |\n|---|---|---|\n"
    "| Permanent file | Articles, capital certificate, lease, trade register, taxpayer card | Alain |\n"
    "| Purchases, Sales, Bank and Mobile Money, Cash, Payroll, Fixed-asset, Tax returns binders | The year's "
    "documents, in order, marked with journal code and entry number | Alain |\n"
    "| Cash book | The day's cash sales, signed every evening | Brenda and Sandrine |\n"
    "| Stock cards | Shirts, trousers and dresses in and out | Brenda |\n\n"
    "Software journals: purchases (AC), sales (VT), bank (BQ), cash (CA), MTN MoMo (MM), Orange Money (OM), "
    "miscellaneous (OD).\n\n"
    "**Routines.** Every evening: till count and the day's Mobile Money payments. Every week: record and file the "
    "documents. Every month: bank and Mobile Money reconciliations, trial balance, 15th return. Every quarter: close "
    "the periods. Every year: count the three families, inventory book, tax return; everything is kept ten years.\n")

STORE = {
    "capital": ("Au dossier permanent. Écriture au journal de banque (BQ).", "Permanent file. Bank journal (BQ)."),
    "notary": ("Au dossier permanent, comme preuve des frais de création. Journal de banque (BQ).",
               "Permanent file, as proof of set-up costs. Bank journal (BQ)."),
    "rent": ("Quittance au classeur Banque et Mobile Money ; bail au dossier permanent. Journal de banque (BQ).",
             "Receipt in the Bank and Mobile Money binder; lease in the permanent file. Bank journal (BQ)."),
    "purchase": ("Facture au classeur Achats, avec le bon de réception signé par Brenda. Journal des achats (AC).",
                 "Invoice in the Purchases binder, with the delivery note signed by Brenda. Purchases journal (AC)."),
    "settlement": ("Déclaration et accusé de réception au classeur Déclarations fiscales. Journal de banque (BQ).",
                   "Return and acknowledgement in the Tax returns binder. Bank journal (BQ)."),
    "cash_out": ("Bordereau tamponné au classeur Caisse. Journal de caisse (CA).",
                 "Stamped slip in the Cash binder. Cash journal (CA)."),
    "cash": ("Brouillards quotidiens et récapitulatif au classeur Caisse. Journal de caisse (CA).",
             "Daily cash book pages and summary in the Cash binder. Cash journal (CA)."),
    "orange": ("Relevé imprimé au classeur Banque et Mobile Money. Journal Orange Money (OM).",
               "Printed statement in the Bank and Mobile Money binder. Orange Money journal (OM)."),
    "mtn": ("Relevé imprimé au classeur Banque et Mobile Money. Journal MTN MoMo (MM).",
            "Printed statement in the Bank and Mobile Money binder. MTN MoMo journal (MM)."),
    "payroll": ("Bulletins signés au classeur Paie. Journal des opérations diverses (OD).",
                "Signed payslips in the Payroll binder. Miscellaneous journal (OD)."),
    "bank": ("Relevé et état de rapprochement signé au classeur Banque et Mobile Money. Journal de banque (BQ).",
             "Statement and signed reconciliation in the Bank and Mobile Money binder. Bank journal (BQ)."),
    "event": ("Pièce au classeur concerné, avec une note pour la passerelle fiscale.",
              "Document in its binder, with a note for the tax bridge."),
}


def month_scenes(book, special, month):
    """Scènes d'un mois du parcours A ; janvier est raconté en détail, les autres mois en version courte."""
    from tools.simulation import ledger

    piece = {p["ref"]: p for p in book.pieces}
    m = special["months"][month]
    first = month == 1
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    end = datetime.date.fromisoformat(piece[m["bank"]]["date"])
    out = []
    if first:
        cap, notary = piece[special["capital"]], piece[special["notary"]]
        out.append(scene(
            cap["date"], special["capital"], ("le capital à la banque", "the capital goes to the bank"),
            (f"Clarisse Ngono et son associé versent {fcfa(total(cap, 'Capital'))} à la Banque X, sur un compte au nom "
             "de la société en formation ; les fonds restent bloqués jusqu'à l'immatriculation [[source:ohada-auscgie]].",
             f"Clarisse Ngono and her partner pay {fcfa(total(cap, 'Capital'), 'en')} to Bank X, into an account in the "
             "name of the company being formed; the funds stay blocked until registration."),
            ("Capital [[syscohada:1013]] au crédit, banque [[syscohada:521]] au débit.", "Capital 1013 credit, bank 521 debit."),
            ("Un apport n'est pas une vente : aucun produit. Ce n'est pas non plus un prêt de Clarisse (4621) : le "
             "capital reste dans la société.",
             "A contribution is not a sale, so no revenue. Nor is it a loan from Clarisse (4621): capital stays in the "
             "company."),
            ("La banque est approvisionnée ; le résultat ne bouge pas.", "The bank is funded; profit does not move."),
            [("compta", 3, "Actif et passif", "Assets and liabilities")], STORE["capital"]))
        out.append(scene(
            notary["date"], special["notary"], ("la facture du notaire", "the notary's invoice"),
            ("Maître Ekambi a rédigé les statuts. Sa facture distingue ses honoraires, soumis à la TVA, et les droits "
             "d'enregistrement qu'il a avancés, qui n'en portent pas.",
             "Maître Ekambi drafted the articles. The invoice separates the fees, subject to VAT, from the registration "
             "duties he advanced, which carry none."),
            ("Honoraires [[syscohada:6324]], droits [[syscohada:646]], TVA sur services [[syscohada:4454]].",
             "Fees 6324, duties 646, VAT on services 4454."),
            ("Le SYSCOHADA révisé ne connaît plus les frais d'établissement à l'actif : ce sont des charges de "
             "l'exercice.", "Revised SYSCOHADA no longer capitalises formation expenses: they are expenses of the year."),
            ("Le premier mois s'ouvre sur une charge ; la TVA des honoraires viendra en déduction le 15 février.",
             "The first month opens with an expense; the VAT on fees is deducted on 15 February."),
            [("compta", 1, "Le cadre comptable OHADA", "The OHADA accounting framework")], STORE["notary"]))
    rent, purchase = piece[m["rent"]], piece[m["purchase"]]
    out.append(scene(
        rent["date"], m["rent"], ("le loyer de la boutique", "the shop rent"),
        ((f"Alain règle à M. Tchoua le loyer du local d'Akwa, moins la retenue de {fcfa(total(rent, 'Précompte'))}."
          + (" Le locataire au réel retient l'impôt du bailleur et le reverse lui-même." if first else ""),
          f"Alain pays Mr Tchoua the Akwa shop rent, less the {fcfa(total(rent, 'Précompte'), 'en')} withholding."
          + (" A tenant under the actual regime withholds the landlord's tax and pays it over." if first else ""))),
        ("Loyer brut [[syscohada:6222]], retenue [[syscohada:4478]] [[cgi:art. 87]].", "Gross rent 6222, withholding 4478."),
        ("La charge est le loyer brut ; la retenue est une dette envers l'État.",
         "The expense is the gross rent; the withholding is a debt to the State."),
        ("La retenue rejoint la déclaration du 15 suivant.", "The withholding joins the next 15th return."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")], STORE["rent"]))
    lines = {line["label"]["fr"].lower(): line["qty"] for line in purchase["payload"]["lines"]}
    out.append(scene(
        purchase["date"], m["purchase"], ("le réassort chez le grossiste", "restocking at the wholesaler"),
        (f"M. Din livre {qty(lines.get('chemises', 0))} chemises, {qty(lines.get('pantalons', 0))} pantalons et "
         f"{qty(lines.get('robes', 0))} robes ; Brenda compte les cartons et signe le bon de réception. Sawa Textiles "
         "est payée par virement le 12.",
         f"Mr Din delivers {qty(lines.get('chemises', 0), 'en')} shirts, {qty(lines.get('pantalons', 0), 'en')} trousers "
         f"and {qty(lines.get('robes', 0), 'en')} dresses; Brenda counts the boxes and signs the delivery note. Sawa "
         "Textiles is paid by transfer on the 12th."),
        ("Achats [[syscohada:6011]], TVA [[syscohada:4452]], précompte de 2 % [[syscohada:4492]] [[cgi:art. 21]], "
         "fournisseur [[syscohada:401]].", "Purchases 6011, VAT 4452, 2% withholding 4492, supplier 401."),
        (("Le précompte s'ajoute à la facture mais n'est pas un coût : c'est une avance sur l'impôt, imputée sur "
          "l'acompte d'IS. Les vêtements ne vont pas en stock (31) au fil de l'année : en inventaire intermittent, on "
          "ne touche aux comptes de stock qu'au 31 décembre." if first else
          "Rappel : le précompte est une avance sur l'impôt ; le stock ne se compte qu'au 31 décembre."),
         ("The withholding is added to the invoice but is not a cost: it is an advance on tax, credited against the CIT "
          "instalment. Clothes do not go to stock (31) during the year: under periodic inventory, stock accounts move "
          "only on 31 December." if first else
          "Reminder: the withholding is an advance on tax; stock is counted only on 31 December.")),
        (f"Sawa Textiles reçoit {fcfa(total(purchase, 'Net'))}.", f"Sawa Textiles receives {fcfa(total(purchase, 'Net'), 'en')}."),
        [("compta", 6, "Les achats", "Purchases")], STORE["purchase"]))
    if m.get("settlement"):
        decl = piece[m["settlement"]]
        paid = total(decl, "TVA due") + total(decl, "Acompte") - total(decl, "Précompte imputé") + total(decl, "Retenues")
        out.append(scene(
            decl["date"], m["settlement"], ("la déclaration du 15", "the 15th return"),
            (f"Alain télédéclare la TVA, l'acompte d'IS et les retenues de {MONTHS_FR[month - 2]}, et paie "
             f"{fcfa(paid)}.",
             f"Alain files {MONTHS_EN[month - 2]}'s VAT, CIT instalment and withholdings online, and pays "
             f"{fcfa(paid, 'en')}."),
            ("TVA facturée moins TVA déductible ; acompte de 2 % du chiffre d'affaires majoré des centimes, moins le "
             "précompte subi ; retenues reversées [[cgi:art. 21]] [[cgi:art. 143]].",
             "VAT charged less VAT recoverable; 2% instalment plus council cents, less withholding suffered; "
             "withholdings paid over."),
            ("Le précompte payé à Sawa Textiles vient en déduction de l'acompte : il n'est pas perdu.",
             "The withholding paid to Sawa Textiles reduces the instalment: it is not lost."),
            (f"La banque baisse de {fcfa(paid)}.", f"The bank drops by {fcfa(paid, 'en')}."),
            [("compta", 5, "La TVA : mécanisme et déclaration", "VAT: mechanism and return"),
             ("fisca", 7, "Obligations déclaratives et contrôle", "Filing obligations and audit")], STORE["settlement"]))
    if m.get("cash_out"):
        slip = piece[m["cash_out"]]
        out.append(scene(
            slip["date"], m["cash_out"], ("la recette part à la banque", "the takings go to the bank"),
            (f"Chaque semaine, Brenda porte la recette en espèces à la banque ; le dernier jour du mois, Alain réunit les "
             f"bordereaux tamponnés : {fcfa(total(slip, 'Espèces'))} versés.",
             f"Every week Brenda takes the cash takings to the bank; on the last day of the month Alain gathers the "
             f"stamped slips: {fcfa(total(slip, 'Espèces'), 'en')} deposited."),
            ("[[syscohada:585]] au débit, caisse [[syscohada:5711]] au crédit ; la banque solde 585 à réception.",
             "585 debit, till 5711 credit; the bank clears 585 on receipt."),
            ("Le virement interne transite par 585 pour qu'une seule pièce porte chaque écriture.",
             "The internal transfer goes through 585 so that one document carries each entry."),
            ("La caisse se vide, la banque se remplit ; le résultat ne bouge pas.",
             "The till empties, the bank fills; profit does not move."),
            [("compta", 12, "Les règlements", "Settlements")], STORE["cash_out"]))
    out += _events(book, special, month, piece)
    cash = piece[m["cash"]]
    out.append(scene(
        cash["date"], m["cash"], ("les ventes au comptoir", "counter sales"),
        (f"Les clientes d'Akwa paient en espèces : {fcfa(total(cash, 'Ventes TTC'))} sur le mois, arrêtés chaque soir "
         "au brouillard de caisse.",
         f"Akwa customers pay cash: {fcfa(total(cash, 'Ventes TTC'), 'en')} over the month, counted every evening in the "
         "cash book."),
        ("Caisse [[syscohada:5711]] au TTC, ventes [[syscohada:7011]], TVA [[syscohada:4431]] [[cgi:art. 142]].",
         "Cash 5711 incl. tax, sales 7011, VAT 4431."),
        ("La TVA encaissée n'appartient pas à la boutique : elle sera reversée le 15.",
         "VAT collected does not belong to the shop: it is paid over on the 15th."),
        ("Le chiffre d'affaires du mois augmente, et avec lui l'acompte d'IS.", "Turnover rises, and with it the CIT instalment."),
        [("compta", 7, "Les ventes", "Sales")], STORE["cash"]))
    for key, operator, account in (("orange", "Orange Money", "5522"), ("mtn", "MTN MoMo", "5521")):
        st = piece[m[key]]
        out.append(scene(
            st["date"], m[key], (f"le relevé {operator}", f"the {operator} statement"),
            (f"Le relevé {operator} du mois : {fcfa(total(st, 'Encaissements TTC'))} payés par téléphone, moins "
             f"{fcfa(total(st, 'Frais'))} de frais de l'opérateur.",
             f"The month's {operator} statement: {fcfa(total(st, 'Encaissements TTC'), 'en')} paid by phone, less "
             f"{fcfa(total(st, 'Frais'), 'en')} of operator fees."),
            (f"Sous-compte [[syscohada:552]] ({account} {operator}), ventes [[syscohada:7011]], TVA [[syscohada:4431]], "
             "frais [[syscohada:631]].", f"Sub-account 552 ({account}), sales 7011, VAT 4431, fees 631."),
            ("Un sous-compte par opérateur : chacun se rapproche de son propre relevé. Les frais sont un service, pas "
             "une remise accordée aux clientes.",
             "One sub-account per operator: each is reconciled with its own statement. Fees are a service, not a "
             "discount to customers."),
            ("Le solde est viré vers la banque en fin de mois, par 585.", "The balance moves to the bank at month end, via 585."),
            [("compta", 12, "Les règlements", "Settlements")], STORE[key]))
    payroll = piece[m["payroll"]]
    out.append(scene(
        payroll["date"], m["payroll"], ("la paie", "payroll"),
        (f"Alain établit les bulletins du gérant et des deux vendeuses et vire {fcfa(total(payroll, 'Nets'))} de nets.",
         f"Alain prepares the payslips for the manager and the two assistants and transfers "
         f"{fcfa(total(payroll, 'Nets'), 'en')} of net pay."),
        ("Brut [[syscohada:6611]], charges patronales [[syscohada:6413]] et [[syscohada:6641]], retenues "
         "[[syscohada:4472]] et [[syscohada:431]], nets [[syscohada:422]] [[cgi:art. 29]].",
         "Gross 6611, employer levies 6413 and 6641, withholdings 4472 and 431, net 422."),
        ("Les retenues sont des dettes envers l'État et la CNPS, pas des charges : la charge est le brut et les "
         "cotisations patronales.", "Withholdings are debts to the State and the CNPS, not expenses."),
        ("Les retenues rejoignent la déclaration du 15.", "Withholdings join the 15th return."),
        [("compta", 11, "La paie", "Payroll")], STORE["payroll"]))
    out.append(scene(
        piece[m["bank"]]["date"], m["bank"], ("le relevé et le rapprochement", "the statement and reconciliation"),
        ("Le relevé de la Banque X reprend le règlement de Sawa Textiles, les salaires, les virements internes et les "
         "frais" + (", ainsi qu'une échéance de la voiture payée à Auto Wouri" if month in (5, 6, 7) else "")
         + ". Alain le pointe contre le 521.",
         "Bank X's statement shows the Sawa Textiles payment, salaries, internal transfers and fees"
         + (", plus a car instalment paid to Auto Wouri" if month in (5, 6, 7) else "") + ". Alain ticks it against 521."),
        ("Fournisseur [[syscohada:401]], salaires [[syscohada:422]], virements [[syscohada:585]], frais "
         "[[syscohada:631]]" + (", dette sur la voiture [[syscohada:4812]]" if month in (5, 6, 7) else "") + ".",
         "Supplier 401, salaries 422, transfers 585, fees 631" + (", car debt 4812" if month in (5, 6, 7) else "") + "."),
        ("Un écart s'explique avant de s'écrire ; on ne force jamais le compte.", "A gap is explained before it is booked."),
        (f"Solde du 521 au {end.day} {mfr} : {fcfa(ledger.account_balance(book.entries, '521', end))}.",
         f"521 balance at {men} {end.day}: {fcfa(ledger.account_balance(book.entries, '521', end), 'en')}."),
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE["bank"]))
    return out


def _events(book, special, month, piece):
    out = []
    if month == 3:
        p = piece[special["provision"]]
        out.append(scene(
            p["date"], special["provision"], ("une mise en demeure", "a formal notice"),
            (f"Le propriétaire de l'immeuble voisin réclame {fcfa(total(p, 'Montant'))} pour un mur abîmé pendant "
             "l'aménagement de la boutique. Clarisse conteste, mais le risque de payer est réel.",
             f"The owner of the next building claims {fcfa(total(p, 'Montant'), 'en')} for a wall damaged while the shop "
             "was being fitted out. Clarisse disputes it, but the risk of paying is real."),
            ("Provision pour litige : dotation [[syscohada:6911]], provision [[syscohada:191]].",
             "Litigation provision: charge 6911, provision 191."),
            ("Rien n'est encore payé, mais la prudence impose de constater le risque dès qu'il est probable. Le fisc, lui, "
             "ne l'admet pas ici : la dotation sera réintégrée.",
             "Nothing is paid yet, but prudence requires booking the risk once it is probable. Tax law does not accept "
             "it here: the charge will be added back."),
            ("Le résultat comptable baisse ; le résultat fiscal, non.", "Accounting profit drops; taxable profit does not."),
            [("compta", 22, "Les provisions pour risques et charges", "Provisions for risks and charges")], STORE["event"]))
    if month == 4:
        p = piece[special["vehicle"]]
        out.append(scene(
            p["date"], special["vehicle"], ("la voiture de livraison", "the delivery car"),
            ("Pour livrer les commandes des clientes de Bonapriso et de Bonanjo, Clarisse achète une voiture légère à Auto "
             "Wouri, payable en trois échéances de mai à juillet.",
             "To deliver orders to customers in Bonapriso and Bonanjo, Clarisse buys a light car from Auto Wouri, payable "
             "in three instalments from May to July."),
            ("Matériel automobile [[syscohada:2451]], TVA sur immobilisations [[syscohada:4451]], fournisseur "
             "d'immobilisations [[syscohada:4812]].", "Vehicles 2451, VAT on fixed assets 4451, fixed-asset supplier 4812."),
            ("La voiture sert plusieurs années : immobilisation, pas charge. Amortie comptablement sur trois ans, elle "
             "dépasse le taux fiscal maximal de 25 % [[cgi:art. 7]] : l'excédent sera réintégré.",
             "The car serves several years: a fixed asset, not an expense. Depreciated over three years in the books, it "
             "exceeds the 25% maximum tax rate: the excess is added back."),
            ("La TVA de la voiture crée un crédit de TVA à la déclaration de mai.", "The car's VAT creates a VAT credit on "
             "the May return."),
            [("compta", 13, "Les immobilisations", "Fixed assets")], STORE["event"]))
    if month == 7:
        p = piece[special["penalty"]]
        out.append(scene(
            p["date"], special["penalty"], ("une pénalité de retard", "a late-filing penalty"),
            ("La déclaration du 15 juin est partie avec quelques jours de retard, le temps de retrouver une facture. La "
             "recette des impôts applique une pénalité.",
             "The 15 June return went in a few days late while an invoice was found. The tax office applies a penalty."),
            ("Pénalités [[syscohada:6471]] ; non déductibles [[cgi:art. 7]].", "Penalties 6471; not deductible."),
            ("Une sanction est une charge comptable, jamais une charge fiscale : elle sera réintégrée.",
             "A penalty is an accounting expense, never a tax one: it is added back."),
            (f"{fcfa(total(p, 'Pénalité'))} payés ; la leçon : classer les pièces chaque semaine.",
             f"{fcfa(total(p, 'Pénalité'), 'en')} paid; the lesson: file documents every week."),
            [("fisca", 8, "Sanctions et contentieux", "Penalties and disputes")], STORE["event"]))
    if month == 9:
        p = piece[special["no_receipt"]]
        out.append(scene(
            p["date"], special["no_receipt"], ("une dépense sans facture", "an expense without an invoice"),
            ("Un tailleur du marché retouche des robes pour une cliente pressée ; il est payé en espèces et ne délivre "
             "aucun reçu. Alain rédige un bon de caisse interne.",
             "A market tailor alters dresses for a customer in a hurry; he is paid cash and gives no receipt. Alain "
             "writes an internal voucher."),
            ("Charges diverses [[syscohada:6588]] ; sans pièce justificative, non déductible [[cgi:art. 7]].",
             "Sundry expenses 6588; without a supporting document, not deductible."),
            ("La dépense est réelle et s'enregistre, mais seul un justificatif externe la rend déductible.",
             "The expense is real and is booked, but only an external document makes it deductible."),
            (f"{fcfa(total(p, 'Dépense'))} sortent de la caisse.", f"{fcfa(total(p, 'Dépense'), 'en')} leave the till."),
            [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")], STORE["event"]))
    if month == 10:
        p = piece[special["donation"]]
        out.append(scene(
            p["date"], special["donation"], ("le don", "the donation"),
            ("Clarisse soutient une association d'Akwa qui forme des jeunes couturières ; l'association remet un reçu.",
             "Clarisse supports an Akwa association training young seamstresses; it issues a receipt."),
            ("Dons [[syscohada:6582]], déductibles dans la limite de 0,5 % du chiffre d'affaires "
             "[[param:dons.plafond_interet_general]] [[cgi:art. 7]].", "Donations 6582, deductible up to 0.5% of turnover."),
            ("Le don n'est pas interdit fiscalement, il est plafonné : seule la part au-delà sera réintégrée.",
             "A donation is not barred for tax, only capped: the excess is added back."),
            (f"{fcfa(total(p, 'Don'))} quittent la banque.", f"{fcfa(total(p, 'Don'), 'en')} leave the bank."),
            [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")], STORE["event"]))
    if month == 11:
        p = piece[special["reversal"]]
        out.append(scene(
            p["date"], special["reversal"], ("le litige se règle", "the dispute is settled"),
            ("Un accord est signé avec le voisin : il renonce à sa réclamation. Le risque a disparu.",
             "An agreement is signed with the neighbour: he drops his claim. The risk is gone."),
            ("Reprise de provision : [[syscohada:191]] au débit, [[syscohada:7911]] au crédit.",
             "Provision reversal: 191 debit, 7911 credit."),
            ("La provision a été réintégrée quand elle a été dotée : sa reprise, déjà taxée, se déduit du résultat "
             "fiscal, sinon elle serait imposée deux fois.",
             "The provision was added back when it was booked: its reversal, already taxed, is deducted, otherwise it "
             "would be taxed twice."),
            ("Le résultat comptable remonte ; le résultat fiscal, non.", "Accounting profit rises; taxable profit does not."),
            [("compta", 22, "Les provisions pour risques et charges", "Provisions for risks and charges")], STORE["event"]))
    return out


HOOKS = {
    1: ("Janvier 2026 : Ngono Mode ouvre ses portes à Akwa.", "January 2026: Ngono Mode opens its doors in Akwa."),
    3: ("Mars 2026 : une lettre recommandée arrive à la boutique.", "March 2026: a registered letter reaches the shop."),
    4: ("Avril 2026 : la boutique s'équipe d'une voiture de livraison.", "April 2026: the shop gets a delivery car."),
    7: ("Juillet 2026 : un retard de déclaration coûte cher.", "July 2026: a late return costs money."),
    9: ("Septembre 2026 : une retouche payée sans reçu.", "September 2026: an alteration paid without a receipt."),
    10: ("Octobre 2026 : la boutique soutient une association.", "October 2026: the shop supports an association."),
    11: ("Novembre 2026 : le litige de mars se règle.", "November 2026: March's dispute is settled."),
}


def month_section(book, special, month, opening, others, lang):
    scenes = month_scenes(book, special, month)
    hook = HOOKS.get(month, (f"{MONTHS_FR[month - 1].capitalize()} 2026 : les ventes suivent leur rythme.",
                             f"{MONTHS_EN[month - 1]} 2026: sales keep their pace."))[0 if lang == "fr" else 1]
    intro = (f"{hook} Lisez chaque scène, regardez la pièce, puis passez l'écriture dans le quiz [[cgi:art. 142]].\n"
             if lang == "fr" else
             f"{hook} Read each scene, look at the document, then record the entry in the quiz [[cgi:art. 142]].\n")
    nxt = ("l'inventaire du 31 décembre" if month == 12 else f"la déclaration du 15 {MONTHS_FR[month]}",
           "the 31 December count" if month == 12 else f"the 15 {MONTHS_EN[month]} return")
    summary = (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- Pièces saisies, classées et rapprochées ; balance éditée.\n\n"
               f"Prochaine étape : {nxt[0]}.\n" if lang == "fr" else
               f"### {MONTHS_EN[month - 1]} in brief\n\n- Documents recorded, filed and reconciled; trial balance "
               f"printed.\n\nNext: {nxt[1]}.\n")
    return assemble(intro, scenes, opening, others, summary, lang), {s["ref"]: s["why"] for s in scenes}


def year_end_sections(book, special):
    """Inventaire, passerelle (six éléments, S21) et DSF du parcours A."""
    piece = {p["ref"]: p for p in book.pieces}
    add, ded, tax = special["add_backs"], special["deductions"], special["tax"]
    sheet = next(iter(special["stock"].values()))[0]
    value = sum(v[3]["valeur_stock"] for v in special["stock"].values())
    count = scene(
        piece[sheet]["date"], sheet, ("l'inventaire des trois familles", "counting the three families"),
        ("Le 31 au soir, Brenda et Sandrine comptent chemises, pantalons et robes, rayon par rayon ; Alain valorise "
         "chaque famille au coût moyen pondéré de l'année.",
         "On the evening of the 31st Brenda and Sandrine count shirts, trousers and dresses, shelf by shelf; Alain values "
         "each family at the year's weighted average cost."),
        ("Stock final en [[syscohada:3111]], [[syscohada:3112]] et [[syscohada:3121]], par [[syscohada:6031]].",
         "Closing stock in 3111, 3112 and 3121, through 6031."),
        ("Le CMUP lisse les hausses de prix du grossiste ; le PEPS, en contraste, valoriserait le stock aux derniers "
         "prix, plus élevés.", "WAC smooths the wholesaler's price rises; FIFO would value stock at the latest, higher "
         "prices."),
        (f"Le stock final de {fcfa(value)} réduit le coût des ventes.", f"Closing stock of {fcfa(value, 'en')} reduces "
         "cost of sales."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Feuilles de comptage et fiches CMUP au classeur Inventaire ; résumé au livre d'inventaire. Journal OD.",
         "Count sheets and WAC cards in the Inventory binder; summary in the inventory book. Journal OD."))
    dep = scene(
        piece[special["schedule"]]["date"], special["schedule"], ("l'amortissement de la voiture", "depreciating the car"),
        (f"La voiture roule depuis avril : neuf mois d'amortissement sur trois ans, soit {fcfa(special['dotation'])}.",
         f"The car has run since April: nine months over three years, {fcfa(special['dotation'], 'en')}."),
        ("Dotation [[syscohada:6813]], amortissements [[syscohada:2845]].", "Charge 6813, accumulated depreciation 2845."),
        ("Le taux comptable (33,33 %) dépasse le taux fiscal maximal d'une voiture légère en ville (25 %) "
         "[[cgi:art. 7]] : l'écart sera réintégré.",
         "The book rate (33.33%) exceeds the 25% maximum tax rate for a light car in town: the gap is added back."),
        (f"{fcfa(special['dotation'])} de charge, sans sortie d'argent.", f"{fcfa(special['dotation'], 'en')} of expense, "
         "no cash out."),
        [("compta", 18, "Les amortissements", "Depreciation")],
        ("Tableau des immobilisations au classeur Immobilisations. Journal OD.", "Asset register in the Fixed-asset "
         "binder. Journal OD."))
    inventory = {lang: ("Le 31 décembre, la boutique ferme plus tôt pour compter [[syscohada:6031]].\n\n" if lang == "fr"
                        else "On 31 December the shop closes early to count [[syscohada:6031]].\n\n")
                 + count[lang] + "\n[[calc:stock]]\n\n" + dep[lang] + "\n[[calc:amortissement]]\n" for lang in ("fr", "en")}
    rows = [("Pénalité de retard (juillet)", "Late-filing penalty (July)", add["amendes"]),
            ("Amortissement de la voiture au-delà de 25 %", "Car depreciation above 25%", add["amortissement_excedentaire"]),
            ("Don au-delà de 0,5 % du chiffre d'affaires", "Donation above 0.5% of turnover", add["dons_excedentaires"]),
            ("Retouche payée sans reçu (septembre)", "Alteration paid without a receipt (September)", add["charge_sans_piece"]),
            ("Provision pour litige (mars)", "Litigation provision (March)", add["provision"])]
    bridge = {}
    for lang in ("fr", "en"):
        fr = lang == "fr"
        table = ("| Réintégration | Montant |\n|---|---|\n" if fr else "| Add-back | Amount |\n|---|---|\n") + "".join(
            f"| {a if fr else b} | {fcfa(v, lang)} |\n" for a, b, v in rows)
        table += (f"| Déduction : reprise de la provision déjà taxée (novembre) | {fcfa(ded['reprise_provision_taxee'])} |\n"
                  if fr else f"| Deduction: reversal of the already-taxed provision (November) | "
                  f"{fcfa(ded['reprise_provision_taxee'], 'en')} |\n")
        bridge[lang] = (("### Janvier 2027 : la passerelle fiscale\n\nAlain reprend les notes laissées dans les "
                         "classeurs : cinq charges à réintégrer, une reprise à déduire [[cgi:art. 7]].\n\n" if fr else
                         "### January 2027: the tax bridge\n\nAlain goes back over his notes: five add-backs and one "
                         "deduction [[cgi:art. 7]].\n\n")
                        + table +
                        (f"\n**Résultat comptable** : {fcfa(special['accounting'])}. **Résultat fiscal** : "
                         f"{fcfa(special['tax_result'])}.\n" if fr else
                         f"\n**Accounting profit**: {fcfa(special['accounting'], 'en')}. **Taxable profit**: "
                         f"{fcfa(special['tax_result'], 'en')}.\n"))
    liq = scene(
        piece[special["liquidation"]]["date"], special["liquidation"], ("l'impôt de l'année", "the year's tax"),
        (f"Au taux réduit de 25 %, l'IS atteint {fcfa(tax['is_total'])}, centimes compris, au-dessus du minimum de "
         f"perception ({fcfa(tax['minimum_total'])}) : c'est l'IS qui est dû. Les acomptes versés viennent en déduction.",
         f"At the 25% reduced rate CIT reaches {fcfa(tax['is_total'], 'en')}, above the minimum tax "
         f"({fcfa(tax['minimum_total'], 'en')}): CIT is due. Instalments paid are deducted."),
        ("IS dû = le plus élevé de l'IS et du minimum [[cgi:art. 17 bis]] [[cgi:art. 21]] ; impôt [[syscohada:891]], "
         "État [[syscohada:441]].", "CIT due = higher of CIT and the minimum; tax 891, State 441."),
        ("Une boutique à forte marge paie l'IS sur son bénéfice ; le minimum ne joue que si le bénéfice est faible : "
         "comparez avec le dépôt de boissons du parcours B3.",
         "A high-margin shop pays CIT on its profit; the minimum only bites when profit is low: compare with the "
         "beverage depot of track B3."),
        (f"Solde à payer avec la DSF : {fcfa(tax['solde'])}.", f"Balance due with the return: {fcfa(tax['solde'], 'en')}."),
        [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")],
        ("Liquidation jointe à la DSF, au classeur Déclarations fiscales. Journal OD, au 31 décembre.",
         "Computation attached to the return, in the Tax returns binder. Journal OD, at 31 December."))
    for lang in ("fr", "en"):
        bridge[lang] += "\n" + liq[lang]
    dsf_refs = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces
                           if p.get("dsf") and p["ref"] != special["liquidation"])
    dsf = {"fr": ("### Avant le 15 avril 2027 : la DSF\n\nAlain dépose la DSF en ligne au CIME de Douala avant le "
                  f"15 avril [[cgi:art. 18]].\n\n{dsf_refs}\n\n**Où ça se range.** DSF et accusé de réception au "
                  "classeur Déclarations fiscales ; états financiers au livre d'inventaire ; conservation dix ans.\n"),
           "en": ("### Before 15 April 2027: the tax return\n\nAlain files the return online with the Douala "
                  f"medium-sized taxpayer office before 15 April [[cgi:art. 18]].\n\n{dsf_refs}\n\n**Where it is "
                  "filed.** Return and acknowledgement in the Tax returns binder; financial statements in the "
                  "inventory book; kept ten years.\n")}
    result = {}
    for key, value in (("inventory", inventory), ("bridge", bridge), ("dsf", dsf)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    return result, {s["ref"]: s["why"] for s in (count, dep, liq)}


def company_extra(lang):
    return typeset_fr(CAST_FR + "\n" + ROUTINES_FR) if lang == "fr" else CAST_EN + "\n" + ROUTINES_EN
