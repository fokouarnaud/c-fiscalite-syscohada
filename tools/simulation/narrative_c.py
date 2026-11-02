"""Récit du parcours C, Tech Clim Bonamoussadi SARL (S34, S35) : même canevas en cinq temps que B3.

Vente d'appareils et pose de climatiseurs à Douala ; un fonctionnaire associé à 80 %, jamais gérant ni salarié, payé en
honoraires quand il forme les techniciens ; provision pour garantie ; dividendes et IRCM en 2027. Tous les montants
sont lus sur les pièces générées.
"""
from tools.simulation.narrative_b3 import MONTHS_EN, MONTHS_FR, assemble, fcfa, qty, scene, total, typeset_fr

COMPANY_FR = (
    "## Tech Clim Bonamoussadi SARL\n\nBoutique d'appareils et atelier de pose de climatiseurs à Douala-Bonamoussadi, "
    "SARL au capital de 2 000 000 FCFA créée le 2 janvier 2026, au régime du réel, rattachée au CIME de Douala "
    "[[source:dgi-cime]]. Un fonctionnaire détient 80 % des parts ; la gérance est confiée à un tiers salarié "
    "[[source:ohada-auscgie]].\n\n### Plan de comptes de l'entreprise\n\n"
    "[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] (sous-compte 5522 Orange Money) [[syscohada:6011]] "
    "[[syscohada:7011]] [[syscohada:706]] [[syscohada:632]] [[syscohada:2412]] [[syscohada:192]] [[syscohada:465]] "
    "[[syscohada:111]] [[syscohada:4452]] [[syscohada:4431]] [[syscohada:4492]] [[syscohada:4478]]\n\n"
    "### Taux de l'exercice 2026\n\n"
    "- TVA [[param:tva.taux_principal]] et CAC [[param:cac.taux]] de la TVA [[cgi:art. 142]] ;\n"
    "- précompte sur achats [[param:precompte.taux_reel]] [[cgi:art. 21]] ;\n"
    "- IS au taux réduit [[param:is.taux_reduit]] [[cgi:art. 17 bis]], acompte [[param:is.taux_minimum_perception]] ;\n"
    "- précompte sur loyer [[param:precompte.taux_loyer]] [[cgi:art. 87]] ;\n"
    "- retenue sur honoraires [[param:retenue.honoraires]] [[cgi:art. 92 bis]], si le payeur est sur la liste ;\n"
    "- IRCM [[param:ircm.taux]] [[cgi:art. 70]].\n\n"
    "### Les personnages\n\n| Personnage | Rôle |\n|---|---|\n"
    "| M. Kamga | Ingénieur fonctionnaire, associé à 80 % ; forme les techniciens quelques samedis |\n"
    "| Mme Eyenga | Associée à 20 % |\n"
    "| Patrice Mouelle | Gérant salarié, non associé : achats, banque, déclarations |\n"
    "| Joël et Rodrigue | Techniciens poseurs |\n"
    "| Linda | Vendeuse : comptoir, Orange Money |\n"
    "| M. Essomba | Commercial d'Électro Import Wouri |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n\n"
    "### Les outils et les routines\n\n"
    "Patrice tient la comptabilité dans un logiciel comptable (Sage 100 Comptabilité, Odoo ou tout autre logiciel qui "
    "respecte l'AUDCIF) [[source:ohada-audcif]] : journaux achats (AC), ventes (VT), banque (BQ), caisse (CA), Orange "
    "Money (OM), opérations diverses (OD). Les pièces vont dans les classeurs Achats, Ventes, Banque et Mobile Money, "
    "Caisse, Paie, Immobilisations et Déclarations fiscales ; statuts, procès-verbaux d'assemblée et bail au dossier "
    "permanent. Linda tient le brouillard de caisse et les fiches de stock ; les techniciens remplissent un bon "
    "d'intervention par pose, signé du client.\n\n"
    "- *Chaque soir* : arrêté de caisse, bons d'intervention du jour.\n"
    "- *Chaque semaine* : versement des espèces, saisie et classement des pièces.\n"
    "- *Chaque mois* : rapprochements, balance, déclaration du 15 [[cgi:art. 21]].\n"
    "- *Chaque année* : inventaire, DSF, assemblée dans les six mois ; tout se conserve dix ans.\n")
COMPANY_EN = (
    "## Tech Clim Bonamoussadi SARL\n\nAppliance shop and air-conditioner installation workshop in Douala, LLC with "
    "2,000,000 FCFA capital created on 2 January 2026, actual regime, attached to the Douala medium-sized taxpayer office "
    "[[source:dgi-cime]]. A civil servant holds 80% of the shares; a salaried third party manages the company.\n\n"
    "### Chart of accounts\n\n[[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] [[syscohada:6011]] "
    "[[syscohada:7011]] [[syscohada:706]] [[syscohada:632]] [[syscohada:2412]] [[syscohada:192]] [[syscohada:465]]\n\n"
    "### 2026 rates\n\n- VAT [[param:tva.taux_principal]], council cents [[param:cac.taux]] [[cgi:art. 142]];\n"
    "- purchase withholding [[param:precompte.taux_reel]] [[cgi:art. 21]];\n- reduced CIT rate [[param:is.taux_reduit]];\n"
    "- withholding on fees [[param:retenue.honoraires]] [[cgi:art. 92 bis]], when the payer is on the list;\n"
    "- tax on dividends [[param:ircm.taux]] [[cgi:art. 70]].\n\n"
    "### The people\n\n| Person | Role |\n|---|---|\n"
    "| Mr Kamga | Civil-servant engineer, 80% partner; trains the technicians on some Saturdays |\n"
    "| Mrs Eyenga | 20% partner |\n| Patrice Mouelle | Salaried manager, not a partner |\n"
    "| Joël and Rodrigue | Installers |\n| Linda | Sales assistant |\n| Mr Essomba | Sales rep of Électro Import Wouri |\n\n"
    "All are fictitious.\n\n### Tools and routines\n\nPatrice keeps the books in accounting software "
    "[[source:ohada-audcif]]; documents are filed by binder and kept ten years. Every evening: till count and job "
    "sheets. Every week: cash deposits and filing. Every month: reconciliations, trial balance, 15th return. Every year: "
    "count, tax return, general meeting within six months.\n")

STORE = {
    "rent": ("Quittance au classeur Banque ; bail au dossier permanent. Journal BQ.",
             "Receipt in the Bank binder; lease in the permanent file. Journal BQ."),
    "purchase": ("Facture au classeur Achats, avec les bons de livraison signés par Linda. Journal AC.",
                 "Invoice in the Purchases binder with delivery notes signed by Linda. Journal AC."),
    "pose": ("Double de la facture au classeur Ventes, avec les bons d'intervention signés par le client. Journal VT.",
             "Invoice copy in the Sales binder with the job sheets signed by the customer. Journal VT."),
    "cash": ("Brouillards quotidiens et récapitulatif au classeur Caisse. Journal CA.",
             "Daily cash book pages and summary in the Cash binder. Journal CA."),
    "orange": ("Relevé imprimé au classeur Banque et Mobile Money. Journal OM.",
               "Printed statement in the Bank and Mobile Money binder. Journal OM."),
    "payroll": ("Bulletins signés au classeur Paie. Journal OD.", "Signed payslips in the Payroll binder. Journal OD."),
    "settlement": ("Déclaration et accusé de réception au classeur Déclarations fiscales. Journal BQ.",
                   "Return and acknowledgement in the Tax returns binder. Journal BQ."),
    "fees": ("Note d'honoraires au classeur Banque, avec la feuille de présence des techniciens. Journal BQ.",
             "Fee note in the Bank binder, with the technicians' attendance sheet. Journal BQ."),
    "cash_out": ("Bordereaux tamponnés au classeur Caisse. Journal CA.", "Stamped slips in the Cash binder. Journal CA."),
    "bank": ("Relevé et état de rapprochement au classeur Banque. Journal BQ.",
             "Statement and reconciliation in the Bank binder. Journal BQ."),
    "permanent": ("Dossier permanent. Journal BQ.", "Permanent file. Journal BQ."),
    "assets": ("Facture au classeur Immobilisations ; l'outillage entre au tableau des immobilisations. Journal AC.",
               "Invoice in the Fixed-asset binder; the tools join the asset register. Journal AC."),
}


def company_file(lang):
    return typeset_fr(COMPANY_FR) if lang == "fr" else COMPANY_EN


def month_scenes(book, special, month):
    from tools.simulation import ledger
    import datetime

    piece = {p["ref"]: p for p in book.pieces}
    m = special["months"][month]
    first = month == 1
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    out = []
    if first:
        cap, notary, tools = piece[special["capital"]], piece[special["notary"]], piece[special["tools"]]
        out.append(scene(
            cap["date"], special["capital"], ("le capital", "the capital"),
            (f"M. Kamga et Mme Eyenga versent {fcfa(total(cap, 'Capital'))} sur un compte au nom de la société en "
             "formation, bloqué jusqu'à l'immatriculation [[source:ohada-auscgie]].",
             f"Mr Kamga and Mrs Eyenga pay {fcfa(total(cap, 'Capital'), 'en')} into an account in the name of the company "
             "being formed, blocked until registration."),
            ("Capital [[syscohada:1013]], banque [[syscohada:521]].", "Capital 1013, bank 521."),
            ("Être associé ne fait pas de M. Kamga un dirigeant : fonctionnaire, il détient des parts mais confie la "
             "gérance à Patrice, un tiers.",
             "Being a partner does not make Mr Kamga a manager: as a civil servant he holds shares but entrusts the "
             "management to Patrice, a third party."),
            ("La banque est approvisionnée ; aucun produit.", "The bank is funded; no revenue."),
            [("compta", 3, "Actif et passif", "Assets and liabilities")], STORE["permanent"]))
        out.append(scene(
            notary["date"], special["notary"], ("la facture du notaire", "the notary's invoice"),
            ("Avec deux millions de capital, les statuts passent chez Maître Moukoko [[source:loi-2016-014]]. La société "
             "immatriculée, Patrice règle sa facture.",
             "With two million of capital the articles go through Maître Moukoko. Once the company is registered, "
             "Patrice pays the invoice."),
            ("Honoraires [[syscohada:6324]], droits [[syscohada:646]], TVA [[syscohada:4454]].",
             "Fees 6324, duties 646, VAT 4454."),
            ("Pas de « frais d'établissement » à l'actif : le SYSCOHADA révisé en fait des charges.",
             "No capitalised formation expenses: revised SYSCOHADA expenses them."),
            ("Une charge dès le premier mois.", "An expense in the first month."),
            [("compta", 1, "Le cadre comptable OHADA", "The OHADA accounting framework")], STORE["permanent"]))
        out.append(scene(
            tools["date"], special["tools"], ("l'outillage de pose", "the installation tools"),
            (f"Pour poser des climatiseurs dans les règles, l'atelier achète une station de récupération de fluide, une "
             f"pompe à vide et des perceuses : {fcfa(total(tools, 'Total HT'))} HT.",
             f"To install units properly, the workshop buys a refrigerant recovery unit, a vacuum pump and drills: "
             f"{fcfa(total(tools, 'Total HT'), 'en')} before tax."),
            ("Outillage industriel [[syscohada:2412]], TVA sur immobilisations [[syscohada:4451]], fournisseur "
             "d'immobilisations [[syscohada:4812]], payé à 30 jours.",
             "Industrial tools 2412, VAT on fixed assets 4451, fixed-asset supplier 4812, paid at 30 days."),
            ("Au-delà de 500 000 FCFA HT, le petit outillage s'inscrit à l'actif [[cgi:art. 7]] : il sera amorti, pas "
             "passé en charge d'un coup.",
             "Above 500,000 FCFA before tax, tools go on the balance sheet: they are depreciated, not expensed at once."),
            ("L'actif s'enrichit ; la TVA crée un crédit à la déclaration de février.", "Assets grow; the VAT creates a "
             "credit on the February return."),
            [("compta", 13, "Les immobilisations", "Fixed assets")], STORE["assets"]))
    rent, purchase, pose = piece[m["rent"]], piece[m["purchase"]], piece[m["pose"]]
    lines = {l["label"]["fr"].lower(): l["qty"] for l in purchase["payload"]["lines"]}
    out.append(scene(
        rent["date"], m["rent"], ("le loyer", "the rent"),
        (f"Patrice règle à M. Ngando le loyer de la boutique, moins {fcfa(total(rent, 'Précompte'))} retenus pour le fisc.",
         f"Patrice pays Mr Ngando the shop rent, less {fcfa(total(rent, 'Précompte'), 'en')} withheld for tax."),
        ("Loyer brut [[syscohada:6222]], retenue [[syscohada:4478]] [[cgi:art. 87]].", "Gross rent 6222, withholding 4478."),
        ("La charge est le loyer brut ; la retenue est une dette envers l'État.", "The expense is gross rent; the "
         "withholding is a debt to the State."),
        ("La retenue rejoint la déclaration du 15.", "The withholding joins the 15th return."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")], STORE["rent"]))
    rise = month in (4, 7, 10)
    out.append(scene(
        purchase["date"], m["purchase"], ("le réassort chez l'importateur", "restocking at the importer"),
        (f"M. Essomba livre {qty(lines.get('téléviseurs', 0))} téléviseurs, {qty(lines.get('climatiseurs', 0))} "
         f"climatiseurs et {qty(lines.get('petit électroménager', 0))} petits appareils."
         + (" Ce trimestre, ses prix montent de 2 500 FCFA par appareil." if rise else ""),
         f"Mr Essomba delivers {qty(lines.get('téléviseurs', 0), 'en')} TV sets, {qty(lines.get('climatiseurs', 0), 'en')} "
         f"air conditioners and {qty(lines.get('petit électroménager', 0), 'en')} small appliances."
         + (" This quarter his prices rise by 2,500 FCFA per unit." if rise else "")),
        ("Achats [[syscohada:6011]], TVA [[syscohada:4452]], précompte de 2 % [[syscohada:4492]] [[cgi:art. 21]].",
         "Purchases 6011, VAT 4452, 2% withholding 4492."),
        (("Les appareils restent en achats (6011) toute l'année ; le stock ne se compte qu'au 31 décembre. Le précompte "
          "est une avance sur l'impôt, pas un coût." if first else
          "Rappel : précompte récupérable sur l'acompte, stock compté au 31 décembre."
          + (" La hausse se lira dans le coût moyen." if rise else "")),
         ("Appliances stay in purchases (6011) all year; stock is counted on 31 December. The withholding is an advance "
          "on tax, not a cost." if first else "Reminder: withholding credited, stock counted on 31 December.")),
        (f"Dette envers l'importateur : {fcfa(total(purchase, 'Net'))}, payable à la fin du mois suivant.",
         f"Debt to the importer: {fcfa(total(purchase, 'Net'), 'en')}, payable at the end of next month."),
        [("compta", 6, "Les achats", "Purchases")], STORE["purchase"]))
    if m.get("settlement"):
        decl = piece[m["settlement"]]
        paid = total(decl, "TVA due") + total(decl, "Acompte") - total(decl, "Précompte imputé") + total(decl, "Retenues")
        out.append(scene(
            decl["date"], m["settlement"], ("la déclaration du 15", "the 15th return"),
            (f"Patrice télédéclare la TVA, l'acompte d'IS et les retenues de {MONTHS_FR[month - 2]} et paie {fcfa(paid)}.",
             f"Patrice files {MONTHS_EN[month - 2]}'s VAT, instalment and withholdings and pays {fcfa(paid, 'en')}."),
            ("TVA collectée moins déductible, acompte de 2 % majoré des CAC moins le précompte, retenues reversées "
             "[[cgi:art. 21]].", "VAT, 2% instalment less withholding, withholdings paid over."),
            ("La TVA des poses (706) est due dès la facture : le régime de la TVA à l'encaissement ne vise pas cette "
             "SARL." if month == 2 else "La régularité évite les pénalités.",
             "VAT on installations is due on invoicing." if month == 2 else "Regularity avoids penalties."),
            (f"La banque baisse de {fcfa(paid)}.", f"The bank drops by {fcfa(paid, 'en')}."),
            [("fisca", 7, "Obligations déclaratives et contrôle", "Filing obligations and audit")], STORE["settlement"]))
    poses = pose["payload"]["lines"][0]["qty"]
    out.append(scene(
        pose["date"], m["pose"], ("les poses du mois", "the month's installations"),
        (f"Joël et Rodrigue ont posé {poses} climatiseurs chez {pose['payload']['customer']['name']}. Patrice facture la "
         "pose, payable le 10 du mois suivant.",
         f"Joël and Rodrigue installed {poses} units at {pose['payload']['customer']['name']}. Patrice invoices the "
         "installation, payable on the 10th of next month."),
        ("Services vendus [[syscohada:706]], TVA facturée [[syscohada:4431]], client [[syscohada:411]].",
         "Services sold 706, VAT charged 4431, customer 411."),
        ("Pourquoi 706 et pas 7011 ? L'appareil est une marchandise vendue ; la pose est un travail, une prestation de "
         "services. Séparer les deux montre ce que rapporte l'atelier." if first else
         "Rappel : la pose est une prestation (706), l'appareil une marchandise (7011).",
         "Why 706 and not 7011? The unit is goods sold; installing it is work, a service." if first else
         "Reminder: installation is a service (706), the unit is goods (7011)."),
        (f"Créance de {fcfa(total(pose, 'Net'))} sur le client.", f"A {fcfa(total(pose, 'Net'), 'en')} receivable."),
        [("compta", 7, "Les ventes", "Sales")], STORE["pose"]))
    if m.get("fees"):
        fee = piece[m["fees"]]
        out.append(scene(
            fee["date"], m["fees"], ("la formation des techniciens", "training the technicians"),
            ("Un samedi, M. Kamga forme Joël et Rodrigue aux nouveaux fluides frigorigènes. Il remet une note d'honoraires, "
             "payée par virement.",
             "On a Saturday Mr Kamga trains Joël and Rodrigue on the new refrigerants. He issues a fee note, paid by "
             "transfer."),
            ("Honoraires [[syscohada:632]] ; la retenue de 5 % ne s'applique que si le payeur figure sur la liste "
             "réglementaire [[cgi:art. 92 bis]].",
             "Fees 632; the 5% withholding applies only if the payer is on the regulatory list."),
            ("Pourquoi pas un salaire ? Un fonctionnaire ne peut en principe pas être salarié d'une entreprise privée. Et "
             "pourquoi pas de retenue ? La SARL n'est pas sur la liste de l'art. 92 bis : elle paie le montant entier.",
             "Why not wages? A civil servant cannot in principle be a private employee. Why no withholding? The company "
             "is not on the art. 92 bis list: it pays the full amount."),
            (f"{fcfa(total(fee, 'Honoraires'))} de charge.", f"{fcfa(total(fee, 'Honoraires'), 'en')} of expense."),
            [("compta", 10, "Autres charges et autres produits", "Other expenses and income")], STORE["fees"]))
    cash, orange, payroll, slip = piece[m["cash"]], piece[m["orange"]], piece[m["payroll"]], piece[m["cash_out"]]
    out.append(scene(
        cash["date"], m["cash"], ("le comptoir", "the counter"),
        (f"Linda a vendu au comptoir, en espèces, pour {fcfa(total(cash, 'Ventes TTC'))} TTC.",
         f"Linda sold {fcfa(total(cash, 'Ventes TTC'), 'en')} incl. tax at the counter, in cash."),
        ("Caisse [[syscohada:5711]], ventes [[syscohada:7011]], TVA [[syscohada:4431]] [[cgi:art. 142]].",
         "Cash 5711, sales 7011, VAT 4431."),
        ("La TVA encaissée n'appartient pas à la boutique.", "VAT collected does not belong to the shop."),
        ("Le chiffre d'affaires grossit.", "Turnover grows."), [("compta", 7, "Les ventes", "Sales")], STORE["cash"]))
    out.append(scene(
        orange["date"], m["orange"], ("le relevé Orange Money", "the Orange Money statement"),
        (f"Les clients payant par téléphone ont réglé {fcfa(total(orange, 'Encaissements TTC'))} ; l'opérateur prélève "
         "ses frais et le solde part vers la banque.",
         f"Customers paying by phone paid {fcfa(total(orange, 'Encaissements TTC'), 'en')}; the operator takes its fees "
         "and the balance goes to the bank."),
        ("[[syscohada:552]] (5522), frais [[syscohada:631]], transfert par [[syscohada:585]].", "552, fees 631, 585."),
        ("Les frais sont un service bancaire, pas une remise.", "Fees are a bank service, not a discount."),
        ("Le transfert rejoint la banque.", "The transfer reaches the bank."),
        [("compta", 12, "Les règlements", "Settlements")], STORE["orange"]))
    out.append(scene(
        payroll["date"], m["payroll"], ("la paie", "payroll"),
        (f"Patrice établit les quatre bulletins, le sien compris, et vire {fcfa(total(payroll, 'Nets'))} de nets.",
         f"Patrice prepares the four payslips, his own included, and transfers {fcfa(total(payroll, 'Nets'), 'en')}."),
        ("Brut [[syscohada:6611]], charges [[syscohada:6413]] et [[syscohada:6641]], retenues [[syscohada:4472]] et "
         "[[syscohada:431]], nets [[syscohada:422]] [[cgi:art. 29]].", "Gross 6611, levies, withholdings, net 422."),
        ("Le gérant non associé est salarié ; le fonctionnaire associé ne l'est pas.",
         "The non-partner manager is an employee; the civil-servant partner is not."),
        ("Les retenues rejoignent la déclaration du 15.", "Withholdings join the 15th return."),
        [("compta", 11, "La paie", "Payroll")], STORE["payroll"]))
    out.append(scene(
        slip["date"], m["cash_out"], ("les versements d'espèces", "the cash deposits"),
        (f"Chaque semaine, Linda porte la recette à la banque : {fcfa(total(slip, 'Espèces'))} sur le mois.",
         f"Every week Linda takes the takings to the bank: {fcfa(total(slip, 'Espèces'), 'en')} over the month."),
        ("[[syscohada:585]] au débit, [[syscohada:5711]] au crédit.", "585 debit, 5711 credit."),
        ("585 évite de compter deux fois le même versement.", "585 avoids counting the same deposit twice."),
        ("La caisse revient à zéro.", "The till is back to zero."),
        [("compta", 12, "Les règlements", "Settlements")], STORE["cash_out"]))
    end = datetime.date.fromisoformat(piece[m["bank"]]["date"])
    out.append(scene(
        piece[m["bank"]]["date"], m["bank"], ("le relevé bancaire", "the bank statement"),
        ("Le relevé reprend le paiement de l'importateur, le virement du client des poses, les salaires et les versements. "
         "Patrice le pointe contre le 521.",
         "The statement shows the importer's payment, the installation customer's transfer, salaries and deposits. "
         "Patrice ticks it against 521."),
        ("Fournisseur [[syscohada:401]], client [[syscohada:411]], salaires [[syscohada:422]], virements "
         "[[syscohada:585]], frais [[syscohada:631]].", "401, 411, 422, 585, 631."),
        ("Un écart s'explique avant de s'écrire.", "A gap is explained before it is booked."),
        (f"Solde du 521 au {end.day} {mfr} : {fcfa(ledger.account_balance(book.entries, '521', end))}.",
         f"521 balance at {men} {end.day}: {fcfa(ledger.account_balance(book.entries, '521', end), 'en')}."),
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE["bank"]))
    return out


HOOKS = {1: ("Janvier 2026 : la boutique ouvre à Bonamoussadi et l'atelier s'équipe.",
             "January 2026: the shop opens in Bonamoussadi and the workshop equips itself."),
         3: ("Mars 2026 : première formation des techniciens par M. Kamga.", "March 2026: Mr Kamga's first training day."),
         4: ("Avril 2026 : l'importateur relève ses prix.", "April 2026: the importer raises prices."),
         12: ("Décembre 2026 : des clients signalent des pannes sous garantie.",
              "December 2026: customers report failures under warranty.")}


def month_section(month, scenes, opening, others, lang):
    default = (f"{MONTHS_FR[month - 1].capitalize()} 2026 : ventes au comptoir, poses et déclarations.",
               f"{MONTHS_EN[month - 1]} 2026: counter sales, installations and returns.")
    hook = HOOKS.get(month, default)[0 if lang == "fr" else 1]
    intro = (f"{hook} Lisez chaque scène, puis passez l'écriture dans le quiz [[cgi:art. 142]].\n" if lang == "fr" else
             f"{hook} Read each scene, then record the entry in the quiz [[cgi:art. 142]].\n")
    nxt = ("l'inventaire du 31 décembre" if month == 12 else f"la déclaration du 15 {MONTHS_FR[month]}",
           "the 31 December count" if month == 12 else f"the 15 {MONTHS_EN[month]} return")
    summary = (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- Pièces saisies, classées et rapprochées.\n\nProchaine étape : "
               f"{nxt[0]}.\n" if lang == "fr" else
               f"### {MONTHS_EN[month - 1]} in brief\n\n- Documents recorded, filed and reconciled.\n\nNext: {nxt[1]}.\n")
    return assemble(intro, scenes, opening, others, summary, lang)


def year_end_sections(book, special):
    piece = {p["ref"]: p for p in book.pieces}
    tax = special["tax"]
    count = scene(
        piece[special["sheet"]]["date"], special["sheet"], ("l'inventaire", "the count"),
        ("Le 31, Linda et Patrice comptent téléviseurs, climatiseurs et petits appareils en réserve et les valorisent au "
         "coût moyen de l'année.", "On the 31st Linda and Patrice count the TV sets, units and small appliances in store "
         "and value them at the year's average cost."),
        ("Stock final en [[syscohada:3111]], [[syscohada:3112]] et [[syscohada:3121]], par [[syscohada:6031]].",
         "Closing stock in 3111, 3112, 3121, through 6031."),
        ("Le CMUP lisse les hausses trimestrielles de l'importateur ; le PEPS donnerait un stock plus élevé.",
         "WAC smooths the importer's quarterly rises; FIFO would give a higher stock."),
        (f"Stock final : {fcfa(special['closing_stock'])}.", f"Closing stock: {fcfa(special['closing_stock'], 'en')}."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Feuilles de comptage au classeur Inventaire, résumé au livre d'inventaire. Journal OD.",
         "Count sheets in the Inventory binder, summary in the inventory book. Journal OD."))
    charges = scene(
        piece[special["schedule"]]["date"], special["schedule"], ("amortir et provisionner", "depreciate and provide"),
        ("Patrice amortit l'outillage sur cinq ans. Neuf clients ont signalé en décembre une panne sur des climatiseurs "
         "posés depuis novembre, encore sous garantie : il chiffre les réparations à 50 000 FCFA chacune.",
         "Patrice depreciates the tools over five years. Nine customers reported in December a failure on units "
         "installed since November, still under warranty: he estimates each repair at 50,000 FCFA."),
        ("Dotation [[syscohada:6813]], amortissements [[syscohada:2841]] ; provision [[syscohada:6911]] contre "
         "[[syscohada:192]].", "Charge 6813, depreciation 2841; provision 6911 against 192."),
        ("Pourquoi cette provision est-elle déductible, alors que celle du litige de Ngono Mode ne l'était pas ? Ici, la "
         "charge est nettement précisée (neuf réparations chiffrées), probable (pannes déclarées) et comptabilisée : les "
         "trois conditions du CGI sont réunies [[cgi:art. 7]].",
         "Why is this provision deductible, unlike Ngono Mode's litigation provision? Here the charge is precise (nine "
         "costed repairs), probable (failures reported) and booked: the CGI's three conditions are met."),
        (f"{fcfa(special['dotation'] + 450000)} de charges de clôture.", f"{fcfa(special['dotation'] + 450000, 'en')} of "
         "year-end charges."),
        [("compta", 22, "Les provisions pour risques et charges", "Provisions for risks and charges")],
        ("Tableau des immobilisations et liste des pannes au classeur Immobilisations. Journal OD.",
         "Asset register and failure list in the Fixed-asset binder. Journal OD."))
    inventory = {lang: (("Le 31 décembre, on compte, on amortit, on provisionne [[syscohada:6031]].\n\n" if lang == "fr"
                         else "On 31 December: count, depreciate, provide [[syscohada:6031]].\n\n")
                        + count[lang] + "\n[[calc:stock]]\n\n" + charges[lang] + "\n[[calc:amortissement]]\n")
                 for lang in ("fr", "en")}
    liq = scene(
        piece[special["liquidation"]]["date"], special["liquidation"], ("l'impôt de l'année", "the year's tax"),
        (f"Résultat fiscal : {fcfa(special['tax_result'])}, sans réintégration. Au taux réduit de 25 %, l'IS atteint "
         f"{fcfa(tax['is_total'])}, CAC compris, au-dessus du minimum de perception ({fcfa(tax['minimum_total'])}).",
         f"Taxable profit: {fcfa(special['tax_result'], 'en')}, with no add-back. At 25%, CIT reaches "
         f"{fcfa(tax['is_total'], 'en')}, above the minimum tax ({fcfa(tax['minimum_total'], 'en')})."),
        ("IS dû = le plus élevé de l'IS et du minimum [[cgi:art. 17 bis]] [[cgi:art. 21]] ; [[syscohada:891]] contre "
         "[[syscohada:441]].", "CIT due = higher of CIT and the minimum; 891 against 441."),
        ("Pourquoi l'IS cette fois ? Une marge confortable sur les appareils et les poses : le bénéfice dépasse ce que "
         "représente le minimum, au contraire du dépôt de boissons.",
         "Why CIT this time? A comfortable margin on appliances and installations: profit exceeds what the minimum "
         "represents, unlike the beverage depot."),
        (f"Solde à payer avec la DSF : {fcfa(tax['solde'])}.", f"Balance due with the return: {fcfa(tax['solde'], 'en')}."),
        [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")],
        ("Liquidation jointe à la DSF, classeur Déclarations fiscales. Journal OD.", "Attached to the return. Journal OD."))
    bridge = {lang: (("### Janvier 2027 : la passerelle\n\nPatrice relit les charges de 2026 : aucune n'est à réintégrer, "
                      "la provision pour garantie remplissant les conditions de déduction [[cgi:art. 7]].\n\n"
                      if lang == "fr" else
                      "### January 2027: the tax bridge\n\nPatrice reviews 2026's expenses: none is to be added back "
                      "[[cgi:art. 7]].\n\n") + liq[lang]) for lang in ("fr", "en")}
    dsf_refs = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces if p.get("dsf") and p["ref"] != special["liquidation"])
    dsf = {"fr": ("### Avant le 15 avril 2027 : la DSF\n\nPatrice dépose la DSF en ligne au CIME de Douala "
                  f"[[cgi:art. 18]].\n\n{dsf_refs}\n\n**Où ça se range.** Classeur Déclarations fiscales ; états financiers "
                  "au livre d'inventaire ; conservation dix ans.\n"),
           "en": ("### Before 15 April 2027: the tax return\n\nPatrice files the return online with the Douala MTO "
                  f"[[cgi:art. 18]].\n\n{dsf_refs}\n\n**Where it is filed.** Tax returns binder; financial statements in "
                  "the inventory book; kept ten years.\n")}
    meeting, payout, paid = piece[special["meeting"]], piece[special["payout"]], piece[special["ircm_paid"]]
    s1 = scene(
        meeting["date"], special["meeting"], ("l'assemblée des associés", "the partners' meeting"),
        (f"M. Kamga et Mme Eyenga approuvent les comptes 2026. Sur le bénéfice de {fcfa(special['net'])}, ils dotent la "
         f"réserve légale de {fcfa(special['reserve'])}, distribuent {fcfa(total(meeting, 'Dividendes'))} et reportent le "
         "reste.",
         f"Mr Kamga and Mrs Eyenga approve the 2026 accounts. Out of the {fcfa(special['net'], 'en')} profit they fund the "
         f"legal reserve with {fcfa(special['reserve'], 'en')}, distribute {fcfa(total(meeting, 'Dividendes'), 'en')} and "
         "carry the rest forward."),
        ("Assemblée dans les six mois de la clôture ; un dixième au moins du bénéfice va à la réserve légale, jusqu'au "
         "cinquième du capital [[source:ohada-auscgie]] : [[syscohada:131]] contre [[syscohada:111]], "
         "[[syscohada:465]] et [[syscohada:121]].",
         "Meeting within six months of year end; at least one tenth of profit funds the legal reserve, up to one fifth "
         "of capital: 131 against 111, 465 and 121."),
        (f"Pourquoi seulement {fcfa(special['reserve'])} de réserve et pas le dixième du bénéfice ? La réserve s'arrête "
         "au cinquième du capital, soit 400 000 FCFA. Et les dividendes ne sont pas une charge : ils partagent un "
         "bénéfice déjà imposé.",
         f"Why only {fcfa(special['reserve'], 'en')}? The reserve stops at one fifth of capital, 400,000 FCFA. Dividends "
         "are not an expense: they share a profit already taxed."),
        (f"Une dette de {fcfa(total(meeting, 'Dividendes'))} envers les associés (465).", "A debt to the partners (465)."),
        [("compta", 25, "Clôture, réouverture et affectation du résultat", "Closing, reopening and appropriation")],
        ("Procès-verbal signé au dossier permanent. Journal OD.", "Signed minutes in the permanent file. Journal OD."))
    s2 = scene(
        payout["date"], special["payout"], ("le paiement des dividendes", "paying the dividends"),
        (f"Patrice vire les dividendes nets ({fcfa(total(payout, 'Dividendes nets'))}), après retenue de l'IRCM "
         f"({fcfa(special['ircm'])}). M. Kamga reçoit 80 % du net.",
         f"Patrice transfers the net dividends ({fcfa(total(payout, 'Dividendes nets'), 'en')}) after the "
         f"{fcfa(special['ircm'], 'en')} withholding. Mr Kamga receives 80% of the net."),
        ("IRCM de 15 % majoré des CAC, retenu à la mise à disposition [[cgi:art. 70]] : [[syscohada:465]] contre "
         "[[syscohada:4478]] et [[syscohada:521]].", "15% withholding plus council cents: 465 against 4478 and 521."),
        ("La SARL retient l'impôt de ses associés : c'est leur impôt, pas le sien. Elle le reverse, sans le payer de sa "
         "poche.", "The company withholds its partners' tax: it is their tax, not the company's."),
        (f"La banque baisse du net ; {fcfa(special['ircm'])} attendent d'être reversés.", "The bank drops by the net."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")],
        ("Avis de virement au classeur Banque. Journal BQ.", "Transfer notice in the Bank binder. Journal BQ."))
    s3 = scene(
        paid["date"], special["ircm_paid"], ("le reversement de l'IRCM", "paying over the withholding tax"),
        ("Avant le 15 du mois suivant, Patrice reverse l'IRCM retenu à la recette des impôts.",
         "Before the 15th of the next month, Patrice pays the withholding over to the tax office."),
        ("[[syscohada:4478]] soldé par [[syscohada:521]] [[cgi:art. 70]].", "4478 cleared by 521."),
        ("Garder l'IRCM retenu serait garder l'argent de l'État.", "Keeping the withholding would keep the State's money."),
        ("La dette fiscale est soldée.", "The tax debt is cleared."),
        [("fisca", 7, "Obligations déclaratives et contrôle", "Filing obligations and audit")],
        ("Quittance au classeur Déclarations fiscales. Journal BQ.", "Receipt in the Tax returns binder. Journal BQ."))
    dividends = {lang: ("Juin à août 2027 : l'assemblée, puis le paiement des dividendes [[cgi:art. 70]].\n\n" if lang == "fr"
                        else "June to August 2027: the meeting, then the dividends [[cgi:art. 70]].\n\n")
                 + "\n".join(s[lang] for s in (s1, s2, s3)) for lang in ("fr", "en")}
    result = {}
    for key, value in (("inventory", inventory), ("bridge", bridge), ("dsf", dsf), ("dividends", dividends)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    return result, {s["ref"]: s["why"] for s in (count, charges, liq, s1, s2, s3)}
