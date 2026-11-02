"""Récit du parcours D, Ets Tchinda Froid (S34, S36, S37) : même canevas en cinq temps que B3 et C.

Un technicien frigoriste installé à son compte à Yaoundé-Biyem-Assi : dépannages pour des entreprises, contrat
d'entretien avec des clients publics, dépannages à domicile payés par Orange Money. TVA exigible à l'encaissement,
retenues des payeurs publics attestées par une ARS, prélèvements de l'exploitant, IRPP sur les BIC. Tous les montants
sont lus sur les pièces générées.
"""
import datetime

from tools.simulation.narrative_b3 import MONTHS_EN, MONTHS_FR, assemble, fcfa, qty, scene, total, typeset_fr

COMPANY_FR = (
    "## Ets Tchinda Froid\n\nAtelier de froid et de climatisation à Yaoundé-Biyem-Assi, établissement individuel de "
    "Jean-Claude Tchinda, technicien frigoriste, immatriculé le 2 janvier 2026, au régime du réel et rattaché au CIME de "
    "Yaoundé (chiffre d'affaires visé : environ 65 millions) [[source:dgi-cime]]. Pas d'associés ni de parts : "
    "M. Tchinda apporte ses biens et répond des dettes de l'atelier sur son patrimoine.\n\n"
    "### Plan de comptes de l'entreprise\n\n"
    "[[syscohada:103]] [[syscohada:104]] (1042 prélèvements, 1043 impôts personnels) [[syscohada:2451]] "
    "[[syscohada:521]] [[syscohada:552]] (sous-compte 5522 Orange Money) [[syscohada:6041]] [[syscohada:331]] "
    "(3311 fluides, 3312 pièces) [[syscohada:706]] [[syscohada:471]] [[syscohada:4432]] [[syscohada:445]] "
    "(4458 TVA retenue à la source) [[syscohada:4492]] [[syscohada:441]] [[syscohada:4472]] [[syscohada:4478]]\n\n"
    "### Taux de l'exercice 2026\n\n"
    "- TVA [[param:tva.taux_principal]] et CAC [[param:cac.taux]] de la TVA [[cgi:art. 142]], exigible à "
    "l'encaissement pour les services [[cgi:art. 134]] ;\n"
    "- retenue sur la commande publique [[param:retenue.commande_publique]] du HT, majorée des CAC [[cgi:art. 21]] ; "
    "TVA retenue à la source par les payeurs publics [[cgi:art. 149]] ;\n"
    "- précompte sur achats [[param:precompte.taux_reel]] [[cgi:art. 21]] ; précompte sur loyer "
    "[[param:precompte.taux_loyer]] [[cgi:art. 87]] ;\n"
    "- IRPP sur les BIC au taux de l'IS [[param:is.taux]], au moins [[param:is.taux_minimum_perception]] du chiffre "
    "d'affaires [[cgi:art. 69]], majoré des CAC [[cgi:art. 71]] ; déclaration des résultats au 15 mars [[cgi:art. 74]] ;\n"
    "- amortissement du matériel automobile léger au plus [[param:amortissement.taux_max_auto_leger_ville]] "
    "[[cgi:art. 7]].\n\n"
    "### Les personnages\n\n| Personnage | Rôle |\n|---|---|\n"
    "| Jean-Claude Tchinda | Exploitant, technicien frigoriste : interventions, factures, banque, déclarations |\n"
    "| Brice Nkou | Aide-technicien salarié |\n"
    "| Mme Onana | Propriétaire de l'atelier |\n"
    "| M. Abena | Comptable de l'hôpital de district, client public |\n"
    "| Mme Mvondo | Vendeuse de Frigo Pièces Mvog-Mbi |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n\n"
    "### Les outils et les routines\n\n"
    "Jean-Claude tient sa comptabilité dans un logiciel comptable qui respecte l'AUDCIF [[source:ohada-audcif]] : "
    "journaux achats (AC), ventes (VT), banque (BQ), Orange Money (OM), opérations diverses (OD). Chaque intervention "
    "a son bon signé par le client ; les factures, les ARS des payeurs publics, les relevés et les déclarations vont "
    "dans les classeurs Achats, Ventes, Banque et Mobile Money, Paie et Déclarations fiscales. Son argent personnel "
    "reste sur son compte personnel : ce qu'il prend à l'atelier est un prélèvement, écrit comme tel.\n\n"
    "- *Chaque soir* : bons d'intervention du jour, pièces consommées notées sur la fiche de stock.\n"
    "- *Chaque semaine* : saisie et classement des pièces, relance des factures impayées.\n"
    "- *Chaque mois* : factures du 24 et du 26, rapprochements, balance, déclaration du 15 [[cgi:art. 21]].\n"
    "- *Chaque année* : inventaire, déclaration des résultats au 15 mars ; tout se conserve dix ans.\n")
COMPANY_EN = (
    "## Ets Tchinda Froid\n\nRefrigeration and air-conditioning workshop in Yaoundé-Biyem-Assi, the sole proprietorship "
    "of Jean-Claude Tchinda, refrigeration technician, registered on 2 January 2026, actual regime, attached to the "
    "Yaoundé medium-sized taxpayer office [[source:dgi-cime]]. No partners, no shares: Mr Tchinda contributes his "
    "assets and answers for the workshop's debts with his own estate.\n\n"
    "### Chart of accounts\n\n[[syscohada:103]] [[syscohada:104]] [[syscohada:2451]] [[syscohada:521]] "
    "[[syscohada:552]] [[syscohada:6041]] [[syscohada:331]] [[syscohada:706]] [[syscohada:471]] [[syscohada:4432]] "
    "[[syscohada:445]] [[syscohada:4492]] [[syscohada:441]]\n\n"
    "### 2026 rates\n\n- VAT [[param:tva.taux_principal]], council cents [[param:cac.taux]] [[cgi:art. 142]], due on "
    "collection for services [[cgi:art. 134]];\n"
    "- public procurement withholding [[param:retenue.commande_publique]] plus council cents [[cgi:art. 21]]; VAT "
    "withheld by public payers [[cgi:art. 149]];\n"
    "- purchase withholding [[param:precompte.taux_reel]]; rent withholding [[param:precompte.taux_loyer]] "
    "[[cgi:art. 87]];\n"
    "- income tax on business profits at [[param:is.taux]], at least [[param:is.taux_minimum_perception]] of turnover "
    "[[cgi:art. 69]], plus council cents; income return by 15 March [[cgi:art. 74]].\n\n"
    "### The people\n\n| Person | Role |\n|---|---|\n"
    "| Jean-Claude Tchinda | Owner, refrigeration technician |\n| Brice Nkou | Salaried assistant technician |\n"
    "| Mrs Onana | Workshop landlord |\n| Mr Abena | District hospital accountant, public customer |\n"
    "| Mrs Mvondo | Sales assistant at Frigo Pièces Mvog-Mbi |\n\nAll are fictitious.\n\n"
    "### Tools and routines\n\nJean-Claude keeps the books in accounting software [[source:ohada-audcif]]; documents "
    "are filed by binder and kept ten years. Every evening: job sheets and stock card. Every week: filing and chasing "
    "unpaid invoices. Every month: invoices, reconciliations, trial balance, 15th return. Every year: count and income "
    "return by 15 March.\n")

STORE = {
    "rent": ("Quittance au classeur Banque ; bail au dossier permanent. Journal BQ.",
             "Receipt in the Bank binder; lease in the permanent file. Journal BQ."),
    "purchase": ("Facture au classeur Achats, avec le bon de livraison. Journal AC.",
                 "Invoice in the Purchases binder with the delivery note. Journal AC."),
    "sale": ("Double de la facture au classeur Ventes, avec les bons d'intervention signés. Journal VT.",
             "Invoice copy in the Sales binder with the signed job sheets. Journal VT."),
    "ars": ("Avis de paiement et ARS au classeur Déclarations fiscales : l'ARS justifie la déduction. Journal BQ.",
            "Payment notice and certificate in the Tax returns binder: the certificate supports the deduction. "
            "Journal BQ."),
    "orange": ("Relevé imprimé au classeur Banque et Mobile Money. Journal OM.",
               "Printed statement in the Bank and Mobile Money binder. Journal OM."),
    "payroll": ("Bulletin signé au classeur Paie. Journal OD.", "Signed payslip in the Payroll binder. Journal OD."),
    "settlement": ("Déclaration et accusé de réception au classeur Déclarations fiscales. Journal BQ.",
                   "Return and acknowledgement in the Tax returns binder. Journal BQ."),
    "bank": ("Relevé et état de rapprochement au classeur Banque. Journal BQ.",
             "Statement and reconciliation in the Bank binder. Journal BQ."),
    "permanent": ("Dossier permanent, avec le rapport de l'expert pour la camionnette. Journal OD.",
                  "Permanent file, with the assessor's report on the van. Journal OD."),
    "tools": ("Facture au classeur Achats. Journal AC.", "Invoice in the Purchases binder. Journal AC."),
}
TVA_COURSE = ("fisca", 4, "La TVA et les droits d'accises", "VAT and excise duties")


def company_file(lang):
    return typeset_fr(COMPANY_FR) if lang == "fr" else COMPANY_EN


def month_scenes(book, special, month):
    from tools.simulation import ledger

    piece = {p["ref"]: p for p in book.pieces}
    m = special["months"][month]
    first = month == 1
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    out = []
    if first:
        apports, tools = piece[special["apports"]], piece[special["tools"]]
        out.append(scene(
            apports["date"], special["apports"], ("les apports de l'exploitant", "the owner's contributions"),
            (f"Jean-Claude affecte à l'atelier la camionnette qu'il possédait, estimée à {fcfa(6000000)} par un expert, "
             f"et dépose {fcfa(3000000)} d'économies sur le compte professionnel.",
             f"Jean-Claude assigns to the workshop the van he owned, valued at {fcfa(6000000, 'en')} by an assessor, "
             f"and deposits {fcfa(3000000, 'en')} of savings in the business account."),
            ("Capital personnel [[syscohada:103]] ; camionnette [[syscohada:2451]], banque [[syscohada:521]].",
             "Personal capital 103; van 2451, bank 521."),
            ("Pourquoi 103 et pas 101 ? Il n'y a ni société ni associés : le capital social n'existe pas. Ce que "
             "l'exploitant apporte reste à lui, mais l'atelier le suit dans ses comptes.",
             "Why 103 and not 101? There is no company and no partners: share capital does not exist. What the owner "
             "contributes remains his, but the workshop tracks it in its books."),
            ("L'atelier démarre avec un véhicule et une trésorerie ; aucun produit.",
             "The workshop starts with a vehicle and cash; no revenue."),
            [("compta", 3, "Actif et passif", "Assets and liabilities")], STORE["permanent"]))
        out.append(scene(
            tools["date"], special["tools"], ("l'outillage", "the tools"),
            (f"Il achète un jeu de manomètres, une pompe à vide et un détecteur de fuites : {fcfa(total(tools, 'Total HT'))} "
             "HT, payés par virement.",
             f"He buys a gauge set, a vacuum pump and a leak detector: {fcfa(total(tools, 'Total HT'), 'en')} before "
             "tax, paid by transfer."),
            ("Petit matériel [[syscohada:6056]], TVA [[syscohada:4454]] [[cgi:art. 7]].", "Small tools 6056, VAT 4454."),
            ("Pourquoi une charge et pas une immobilisation ? Sous le seuil de 500 000 FCFA HT, le petit outillage se "
             "passe en charge [[param:petit_materiel.seuil]] ; Tech Clim, au-dessus du seuil, l'avait immobilisé.",
             "Why an expense and not a fixed asset? Below the 500,000 FCFA threshold, small tools are expensed; Tech "
             "Clim, above it, had capitalised them."),
            ("Une charge du premier mois et un crédit de TVA.", "A first-month expense and a VAT credit."),
            [("compta", 13, "Les immobilisations", "Fixed assets")], STORE["tools"]))
    rent, purchase = piece[m["rent"]], piece[m["purchase"]]
    out.append(scene(
        rent["date"], m["rent"], ("le loyer de l'atelier", "the workshop rent"),
        (f"Jean-Claude paie à Mme Onana le loyer de l'atelier, moins {fcfa(total(rent, 'Précompte'))} retenus pour le fisc.",
         f"Jean-Claude pays Mrs Onana the workshop rent, less {fcfa(total(rent, 'Précompte'), 'en')} withheld for tax."),
        ("Loyer brut [[syscohada:6222]], retenue [[syscohada:4478]] [[cgi:art. 87]].", "Gross rent 6222, withholding 4478."),
        ("Au réel, le locataire retient le précompte et le reverse : la charge reste le loyer brut.",
         "Under the actual regime the tenant withholds and pays over: the expense remains the gross rent."),
        ("La retenue rejoint la déclaration du 15.", "The withholding joins the 15th return."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")], STORE["rent"]))
    rise = month in (4, 7, 10)
    out.append(scene(
        purchase["date"], m["purchase"], ("le réassort de fluide et de pièces", "restocking refrigerant and parts"),
        ("Mme Mvondo livre les bouteilles de R410A et les kits de pièces du mois."
         + (" Ce trimestre, les prix montent." if rise else ""),
         "Mrs Mvondo delivers the month's R410A cylinders and parts kits." + (" Prices rise this quarter." if rise else "")),
        ("Matières consommables [[syscohada:6041]], TVA [[syscohada:4452]], précompte de 2 % [[syscohada:4492]] "
         "[[cgi:art. 21]].", "Consumables 6041, VAT 4452, 2% withholding 4492."),
        (("Pourquoi 6041 et pas 6011 ? Jean-Claude ne revend pas ces pièces en l'état : il les consomme dans ses "
          "interventions, qu'il facture comme des services." if first else
          "Rappel : 6041 toute l'année, stock compté au 31 décembre, précompte imputable sur l'acompte."),
         ("Why 6041 and not 6011? Jean-Claude does not resell these parts as such: he uses them in jobs he invoices as "
          "services." if first else "Reminder: 6041 all year, stock counted on 31 December, withholding credited.")),
        (f"Dette envers le grossiste : {fcfa(total(purchase, 'Net'))}, payable à la fin du mois suivant.",
         f"Debt to the supplier: {fcfa(total(purchase, 'Net'), 'en')}, payable at the end of next month."),
        [("compta", 6, "Les achats", "Purchases")], STORE["purchase"]))
    if m.get("settlement"):
        decl = piece[m["settlement"]]
        paid = total(decl, "TVA due") + total(decl, "Acompte") - total(decl, "Précomptes") + total(decl, "Retenues")
        out.append(scene(
            decl["date"], m["settlement"], ("la déclaration du 15", "the 15th return"),
            (f"Jean-Claude télédéclare la TVA, l'acompte d'IRPP et les retenues de {MONTHS_FR[month - 2]} et paie "
             f"{fcfa(paid)}.",
             f"Jean-Claude files {MONTHS_EN[month - 2]}'s VAT, instalment and withholdings and pays {fcfa(paid, 'en')}."),
            ("TVA devenue exigible à l'encaissement moins TVA déductible, retenue à la source comprise ; acompte de 2 % "
             "majoré des CAC moins les précomptes et retenues subis [[cgi:art. 21]] [[cgi:art. 134]].",
             "VAT due on collection less recoverable VAT, withheld VAT included; 2% instalment less withholdings."),
            ("Pourquoi la TVA des factures du mois n'y est-elle pas ? Seule compte la TVA des services encaissés ; "
             "celle des factures impayées attend en 471." if month == 2 else
             "Pourquoi l'acompte net est-il souvent nul ? Les retenues de 5,5 % des payeurs publics et le précompte "
             "dépassent l'acompte du mois ; l'excédent attend en 4492." if month in (3, 6, 9) else
             "La régularité évite les pénalités.",
             "Why is this month's invoicing absent? Only VAT on collected services counts; the rest waits in 471."
             if month == 2 else "Why is the net instalment often nil? Public withholdings exceed it; the excess waits."
             if month in (3, 6, 9) else "Regularity avoids penalties."),
            (f"La banque baisse de {fcfa(paid)}.", f"The bank drops by {fcfa(paid, 'en')}."),
            [("fisca", 7, "Obligations déclaratives et contrôle", "Filing obligations and audit")], STORE["settlement"]))
    if m.get("ars"):
        ars, paid = piece[m["ars"]], special["public"][month]
        out.append(scene(
            ars["date"], m["ars"], ("le paiement du client public", "the public customer's payment"),
            (f"Le Trésor règle la facture du mois dernier (client : {paid['client']}) : sur {fcfa(paid['ttc'])}, il retient "
             f"{fcfa(paid['retenue'])} d'acompte d'impôt et {fcfa(paid['taxes'])} de TVA, et vire {fcfa(paid['net'])}. "
             "M. Abena remet l'attestation de retenue à la source, générée par le système de la DGI.",
             f"The Treasury pays the invoice of {paid['client']}: out of {fcfa(paid['ttc'], 'en')} it withholds "
             f"{fcfa(paid['retenue'], 'en')} of tax instalment and {fcfa(paid['taxes'], 'en')} of VAT, and transfers "
             f"{fcfa(paid['net'], 'en')}. Mr Abena hands over the withholding certificate."),
            ("Retenue de 5 % du HT majorée des CAC [[cgi:art. 21]] en [[syscohada:4492]] ; TVA retenue à la source "
             "[[cgi:art. 149]], déductible sur présentation de l'ARS [[cgi:art. 143]] (4458) ; la TVA devient exigible : "
             "[[syscohada:471]] soldé dans [[syscohada:4432]].",
             "5% withholding plus council cents in 4492; VAT withheld at source, deductible with the certificate (4458); "
             "VAT becomes due: 471 cleared to 4432."),
            ("Pourquoi ne pas passer le net en chiffre d'affaires ? Le client a payé toute la facture : une part à "
             "Jean-Claude, une part au fisc pour son compte. Les deux retenues sont des avances sur ses propres impôts, "
             "pas des remises." + (" Sans ARS issue du système de la DGI, la TVA retenue ne se déduirait pas." if month == 2
                                   else ""),
             "Why not book the net as revenue? The customer paid the whole invoice: part to Jean-Claude, part to the "
             "tax office on his behalf. Both withholdings are advances on his own taxes, not discounts."),
            ("La créance publique est soldée ; deux avances fiscales attendent la déclaration du 15.",
             "The public receivable is cleared; two tax advances await the 15th return."),
            [TVA_COURSE, ("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")],
            STORE["ars"]))
    private, public = piece[m["private"]], piece[m["public"]]
    jobs, units = private["payload"]["lines"][0]["qty"], public["payload"]["lines"][0]["qty"]
    out.append(scene(
        private["date"], m["private"], ("les dépannages aux entreprises", "repairs for businesses"),
        (f"Jean-Claude et Brice ont fait {qty(jobs)} interventions chez {private['payload']['customer']['name']}. "
         "La facture part avec les bons signés, payable le 10 du mois suivant.",
         f"Jean-Claude and Brice made {qty(jobs, 'en')} call-outs at {private['payload']['customer']['name']}. The "
         "invoice goes with the signed job sheets, payable on the 10th of next month."),
        ("Services vendus [[syscohada:706]], client [[syscohada:411]] ; TVA en attente [[syscohada:471]], exigible à "
         "l'encaissement [[cgi:art. 134]].", "Services 706, customer 411; VAT pending 471, due on collection."),
        ("Pourquoi 471 et pas 4432 ? Pour une prestation de services, la TVA n'est due qu'à l'encaissement : tant "
         "que le client n'a pas payé, elle n'est pas encore une dette envers l'État, mais elle est déjà facturée."
         if first else "Rappel : 471 à la facture, 4432 au paiement.",
         "Why 471 and not 4432? For services VAT is due only on collection: until the customer pays, it is not yet a "
         "debt to the State, though it is already invoiced." if first else "Reminder: 471 on invoicing, 4432 on payment."),
        (f"Créance de {fcfa(total(private, 'Total HT') + total(private, 'TVA') + total(private, 'CAC'))} sur le client.",
         "A receivable on the customer."),
        [("compta", 7, "Les ventes", "Sales"), TVA_COURSE], STORE["sale"]))
    out.append(scene(
        public["date"], m["public"], ("le contrat d'entretien public", "the public maintenance contract"),
        (f"Ce mois, {qty(units)} climatiseurs entretenus pour {public['payload']['customer']['name']}. Le contrat reste "
         "sous 5 millions HT.",
         f"This month {qty(units, 'en')} units serviced for {public['payload']['customer']['name']}. The contract stays "
         "under 5 million before tax."),
        ("Même écriture que pour un client privé : [[syscohada:411]], [[syscohada:706]], [[syscohada:471]].",
         "Same entry as for a private customer: 411, 706, 471."),
        ("Pourquoi ne pas déduire tout de suite les retenues ? Elles naissent au paiement, quand le Trésor les "
         "opère ; à la facture, Jean-Claude réclame le TTC entier." if first else
         "Rappel : les retenues s'écrivent au paiement, avec l'ARS.",
         "Why not deduct withholdings now? They arise on payment, when the Treasury makes them; on invoicing Jean-Claude "
         "claims the full amount." if first else "Reminder: withholdings are booked on payment, with the certificate."),
        ("Une créance sur le payeur public, réglée le mois suivant.", "A receivable on the public payer, paid next month."),
        [("compta", 7, "Les ventes", "Sales")], STORE["sale"]))
    orange, payroll = piece[m["orange"]], piece[m["payroll"]]
    out.append(scene(
        orange["date"], m["orange"], ("les dépannages à domicile", "home repairs"),
        (f"Des particuliers ont payé {fcfa(total(orange, 'Encaissements TTC'))} par Orange Money ; l'opérateur prélève "
         "ses frais et le solde part vers la banque.",
         f"Households paid {fcfa(total(orange, 'Encaissements TTC'), 'en')} by Orange Money; the operator takes its fees "
         "and the balance goes to the bank."),
        ("[[syscohada:552]] (5522), [[syscohada:706]] ; facture et paiement le même jour : [[syscohada:471]] aussitôt "
         "soldé dans [[syscohada:4432]] ; frais [[syscohada:631]], transfert par [[syscohada:585]].",
         "552, 706; invoice and payment the same day: 471 cleared to 4432 at once; fees 631, transfer through 585."),
        ("Pourquoi passer par 471 si le paiement est immédiat ? Le logiciel applique une seule règle à toutes les "
         "prestations : la TVA attend en 471 et devient exigible au paiement, ici le jour même.",
         "Why go through 471 if payment is immediate? The software applies one rule to all services: VAT waits in 471 "
         "and falls due on payment, here the same day."),
        ("La TVA de ces dépannages est due dès ce mois.", "VAT on these repairs is due this month."),
        [("compta", 12, "Les règlements", "Settlements"), TVA_COURSE], STORE["orange"]))
    out.append(scene(
        payroll["date"], m["payroll"], ("la paie de Brice", "Brice's pay"),
        (f"Jean-Claude établit le bulletin de Brice et vire {fcfa(total(payroll, 'Net'))} de net.",
         f"Jean-Claude prepares Brice's payslip and transfers {fcfa(total(payroll, 'Net'), 'en')} net."),
        ("Brut [[syscohada:6611]], charges [[syscohada:6413]] et [[syscohada:6641]], retenues [[syscohada:4472]] et "
         "[[syscohada:431]], net [[syscohada:422]] [[cgi:art. 29]].", "Gross 6611, levies, withholdings, net 422."),
        ("Brice est salarié ; Jean-Claude, lui, n'a pas de bulletin : on ne s'emploie pas soi-même.",
         "Brice is an employee; Jean-Claude has no payslip: one does not employ oneself."),
        ("Les retenues rejoignent la déclaration du 15.", "Withholdings join the 15th return."),
        [("compta", 11, "La paie", "Payroll")], STORE["payroll"]))
    end = datetime.date.fromisoformat(piece[m["bank"]]["date"])
    out.append(scene(
        piece[m["bank"]]["date"], m["bank"], ("le relevé bancaire", "the bank statement"),
        ("Le relevé reprend le virement du client privé, le paiement du grossiste, le salaire, le transfert d'Orange "
         "Money et le virement de 300 000 FCFA que Jean-Claude fait sur son compte personnel pour son ménage.",
         "The statement shows the private customer's transfer, the supplier's payment, the wage, the Orange Money "
         "transfer and the 300,000 FCFA Jean-Claude moves to his personal account for his household."),
        ("Client [[syscohada:411]] et TVA exigible ([[syscohada:471]] vers [[syscohada:4432]]), fournisseur "
         "[[syscohada:401]], salaire [[syscohada:422]], virement [[syscohada:585]], prélèvement [[syscohada:104]] "
         "(1042), frais [[syscohada:631]].", "411 and VAT due, 401, 422, 585, drawings 1042, 631."),
        ("Pourquoi le virement personnel n'est-il pas un salaire ? L'exploitant se rémunère par le bénéfice ; ce qu'il "
         "prend en cours d'année est une avance sur ce bénéfice, au compte de l'exploitant, jamais une charge."
         if first else "Un écart s'explique avant de s'écrire.",
         "Why is the personal transfer not a wage? The owner is paid through profit; what he takes during the year is an "
         "advance on it, in the owner's account, never an expense." if first else "A gap is explained before it is booked."),
        (f"Solde du 521 au {end.day} {mfr} : {fcfa(ledger.account_balance(book.entries, '521', end))}.",
         f"521 balance at {men} {end.day}: {fcfa(ledger.account_balance(book.entries, '521', end), 'en')}."),
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE["bank"]))
    return out


HOOKS = {1: ("Janvier 2026 : Jean-Claude Tchinda s'installe à son compte à Biyem-Assi.",
             "January 2026: Jean-Claude Tchinda sets up on his own in Biyem-Assi."),
         2: ("Février 2026 : premier paiement du Trésor, avec ses retenues.",
             "February 2026: first Treasury payment, with its withholdings."),
         3: ("Mars 2026 : la saison sèche fait chauffer les climatiseurs et le carnet de commandes.",
             "March 2026: the dry season heats up the units and the order book."),
         6: ("Juin 2026 : et si l'atelier n'était pas au fichier des contribuables actifs ?",
             "June 2026: what if the workshop were not on the active taxpayer file?"),
         7: ("Juillet 2026 : le grossiste relève ses prix.", "July 2026: the supplier raises prices."),
         12: ("Décembre 2026 : les factures du mois ne seront payées qu'en janvier.",
              "December 2026: this month's invoices will only be paid in January.")}


def month_section(month, scenes, opening, others, lang):
    default = (f"{MONTHS_FR[month - 1].capitalize()} 2026 : interventions, encaissements et déclarations.",
               f"{MONTHS_EN[month - 1]} 2026: jobs, collections and returns.")
    hook = HOOKS.get(month, default)[0 if lang == "fr" else 1]
    intro = (f"{hook} Lisez chaque scène, puis passez l'écriture dans le quiz [[cgi:art. 134]].\n" if lang == "fr" else
             f"{hook} Read each scene, then record the entry in the quiz [[cgi:art. 134]].\n")
    nxt = ("l'inventaire du 31 décembre" if month == 12 else f"la déclaration du 15 {MONTHS_FR[month]}",
           "the 31 December count" if month == 12 else f"the 15 {MONTHS_EN[month]} return")
    summary = (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- Pièces saisies, classées et rapprochées.\n- TVA des factures "
               f"impayées en attente au compte 471.\n\nProchaine étape : {nxt[0]}.\n" if lang == "fr" else
               f"### {MONTHS_EN[month - 1]} in brief\n\n- Documents recorded, filed and reconciled.\n- VAT on unpaid "
               f"invoices pending in 471.\n\nNext: {nxt[1]}.\n")
    return assemble(intro, scenes, opening, others, summary, lang)


def year_end_sections(book, special):
    piece = {p["ref"]: p for p in book.pieces}
    tax = special["tax"]
    count = scene(
        piece[special["sheet"]]["date"], special["sheet"], ("l'inventaire", "the count"),
        ("Le 31, Jean-Claude et Brice comptent les bouteilles de fluide et les kits de pièces restés à l'atelier et les "
         "valorisent au coût moyen de l'année.",
         "On the 31st Jean-Claude and Brice count the refrigerant cylinders and parts kits left in the workshop and value "
         "them at the year's average cost."),
        ("Stock final en [[syscohada:331]] (3311 et 3312), par [[syscohada:6033]].", "Closing stock in 331, through 6033."),
        ("Pourquoi 6033 et pas 6031 ? Ce ne sont pas des marchandises revendues mais des approvisionnements "
         "consommés ; leur variation a son propre compte.",
         "Why 6033 and not 6031? These are not goods for resale but supplies used up; their change has its own account."),
        (f"Stock final : {fcfa(special['closing_stock'])}.", f"Closing stock: {fcfa(special['closing_stock'], 'en')}."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Feuilles de comptage au classeur Inventaire. Journal OD.", "Count sheets in the Inventory binder. Journal OD."))
    charges = scene(
        piece[special["schedule"]]["date"], special["schedule"], ("amortir la camionnette", "depreciating the van"),
        ("Jean-Claude amortit la camionnette sur quatre ans, depuis janvier.",
         "Jean-Claude depreciates the van over four years, from January."),
        ("Dotation [[syscohada:6813]], amortissements [[syscohada:2845]] ; au plus 25 % pour le matériel automobile "
         "léger [[cgi:art. 7]].", "Charge 6813, depreciation 2845; at most 25% for light vehicles."),
        ("Pourquoi amortir un bien apporté, qui n'a rien coûté à l'atelier ? Il s'use au service de l'atelier ; sa "
         "valeur d'apport est son coût d'entrée.",
         "Why depreciate a contributed asset that cost the workshop nothing? It wears out in the workshop's service; its "
         "contribution value is its cost."),
        (f"{fcfa(special['dotation'])} de charge.", f"{fcfa(special['dotation'], 'en')} of expense."),
        [("compta", 18, "Les amortissements", "Depreciation")],
        ("Tableau des immobilisations au classeur Immobilisations. Journal OD.", "Asset register. Journal OD."))
    inventory = {lang: (("Le 31 décembre, on compte, on amortit, et l'on regarde ce qui reste en 471 : "
                         f"{fcfa(special['vat_pending'])} de TVA sur les factures de décembre, exigible seulement à leur "
                         "paiement en janvier [[cgi:art. 134]].\n\n" if lang == "fr" else
                         "On 31 December: count, depreciate, and look at what remains in 471: VAT on the December "
                         "invoices, due only when they are paid in January [[cgi:art. 134]].\n\n")
                        + count[lang] + "\n[[calc:stock]]\n\n" + charges[lang] + "\n[[calc:amortissement]]\n")
                 for lang in ("fr", "en")}
    liq = scene(
        piece[special["liquidation"]]["date"], special["liquidation"], ("l'impôt de l'exploitant", "the owner's income tax"),
        (f"Bénéfice imposable : {fcfa(special['tax_result'])}. Au taux de 30 %, l'IRPP atteint {fcfa(tax['is_total'])}, "
         f"CAC compris ; le minimum (2 % du CA) serait de {fcfa(tax['minimum_total'])}. Acomptes et retenues déduits, "
         f"Jean-Claude paie {fcfa(tax['solde'])} avec sa déclaration.",
         f"Taxable profit: {fcfa(special['tax_result'], 'en')}. At 30%, income tax reaches {fcfa(tax['is_total'], 'en')}; "
         f"the minimum would be {fcfa(tax['minimum_total'], 'en')}. After instalments and withholdings Jean-Claude pays "
         f"{fcfa(tax['solde'], 'en')}."),
        ("IRPP sur les BIC au taux de l'art. 17, au moins 2 % du CA [[cgi:art. 69]], majoré des CAC [[cgi:art. 71]] ; "
         "[[syscohada:104]] (1043) contre [[syscohada:441]] et [[syscohada:4492]].",
         "Income tax at the art. 17 rate, at least 2% of turnover, plus council cents; 1043 against 441 and 4492."),
        ("Pourquoi au compte de l'exploitant et pas en 891 ? L'établissement n'est pas un contribuable distinct : "
         "l'impôt est celui de Jean-Claude sur son revenu, payé par l'atelier pour lui. Et pourquoi 30 % et pas le "
         "taux réduit de 25 % ? L'art. 17 bis vise l'IS des sociétés ; l'art. 69 renvoie au taux de l'art. 17.",
         "Why the owner's account and not 891? The business is not a separate taxpayer: the tax is Jean-Claude's, paid "
         "by the workshop for him. Why 30% and not 25%? Art. 17 bis concerns corporate tax; art. 69 refers to art. 17."),
        (f"Solde à payer : {fcfa(tax['solde'])}.", f"Balance due: {fcfa(tax['solde'], 'en')}."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")],
        ("Liquidation jointe à la déclaration des résultats, classeur Déclarations fiscales. Journal OD.",
         "Attached to the income return. Journal OD."))
    bridge = {lang: (("### Février 2027 : la passerelle\n\nJean-Claude relit les charges de 2026 : aucune n'est à "
                      "réintégrer. Ses prélèvements et son impôt n'ont jamais été des charges [[cgi:art. 7]].\n\n"
                      if lang == "fr" else
                      "### February 2027: the tax bridge\n\nJean-Claude reviews 2026's expenses: none is to be added "
                      "back; his drawings and tax were never expenses [[cgi:art. 7]].\n\n") + liq[lang])
              for lang in ("fr", "en")}
    refs = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces if p.get("dsf") and p["ref"] != special["liquidation"])
    dsf = {"fr": ("### Avant le 15 mars 2027 : la déclaration des résultats\n\nJean-Claude dépose en ligne la "
                  "déclaration annuelle des résultats de son exploitation et paie le solde de l'IRPP au plus tard le "
                  "15 mars [[cgi:art. 74]] [[cgi:art. 91]]. Une SARL du même CIME aurait eu jusqu'au 15 avril "
                  f"[[cgi:art. 18]].\n\n{refs}\n\n**Où ça se range.** Classeur Déclarations fiscales ; états "
                  "financiers au livre d'inventaire ; conservation dix ans.\n"),
           "en": ("### Before 15 March 2027: the income return\n\nJean-Claude files the annual return of his business "
                  "results online and pays the income tax balance by 15 March [[cgi:art. 74]]. A company of the same "
                  f"office would have had until 15 April [[cgi:art. 18]].\n\n{refs}\n\n**Where it is filed.** Tax "
                  "returns binder; kept ten years.\n")}
    result = {}
    for key, value in (("inventory", inventory), ("bridge", bridge), ("dsf", dsf)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    return result, {s["ref"]: s["why"] for s in (count, charges, liq)}
