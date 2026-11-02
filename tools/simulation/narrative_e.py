"""Récit du parcours E, Froid Équipe Services SARL (S34) : SARL à l'IGS tenant le système minimal de trésorerie.

Même canevas que B3 (tools/simulation/narrative_b3.py), mais la règle s'exprime en recettes et en dépenses : le SMT
suit l'argent encaissé et décaissé (AUDCIF art. 13 et 21), la TVA payée aux fournisseurs entre dans le coût, le
précompte de 5 % est subi, le fonctionnaire associé est payé en honoraires et rembourse son avance. Tous les montants
sont lus sur les pièces générées.
"""
import datetime

from tools.simulation.narrative_b3 import MONTHS_EN, MONTHS_FR, assemble, fcfa, scene, total, typeset_fr

CAST_FR = (
    "### Les personnages\n\n"
    "| Personnage | Rôle |\n|---|---|\n"
    "| Hervé Ndjock | Gérant, associé à 20 % : interventions, achats, caisse |\n"
    "| M. Etoga | Fonctionnaire, associé à 80 %, professeur de froid dans un lycée technique public ; il forme les "
    "clients comme vacataire |\n"
    "| Clim Distribution Wouri SARL | Fournisseur de climatiseurs, au réel |\n"
    "| Pharmacie du Littoral, Hôtel Akwa Palace, École Les Palmiers | Clients des contrats d'entretien |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n")
CAST_EN = (
    "### The people\n\n"
    "| Person | Role |\n|---|---|\n"
    "| Hervé Ndjock | Manager, 20% partner: jobs, purchases, cash |\n"
    "| Mr Etoga | Civil servant, 80% partner, refrigeration teacher at a state technical school; trains customers as a "
    "part-timer |\n"
    "| Clim Distribution Wouri SARL | Air-conditioner supplier, actual regime |\n"
    "| Pharmacie du Littoral, Hôtel Akwa Palace, École Les Palmiers | Maintenance-contract customers |\n\n"
    "All are fictitious, like the companies and the amounts.\n")
ROUTINES_FR = (
    "### Les outils et les routines\n\n"
    "**Les outils.** Au système minimal de trésorerie, Hervé tient un cahier des recettes et des dépenses, sur papier "
    "ou sur tableur : chaque ligne porte la date, la pièce, le montant et le moyen de paiement (caisse, banque, Orange "
    "Money) [[source:ohada-audcif]]. Les pièces vont dans trois classeurs : Recettes, Dépenses, Banque et Mobile Money ; "
    "statuts, avance de M. Etoga et carte de contribuable au dossier permanent.\n\n"
    "**Les routines.**\n\n"
    "- *Chaque soir* : Hervé compte la caisse et inscrit les recettes et les dépenses du jour.\n"
    "- *Chaque mois* : il rapproche le cahier du relevé bancaire et du relevé Orange Money, verse les espèces à la "
    "banque.\n"
    "- *Chaque année* : inventaire des climatiseurs en stock, déclaration et paiement de l'IGS avant le 15 avril "
    "[[cgi:art. C 41]], DSF du SMT avant le 15 mai [[cgi:art. C 44]] ; les pièces se conservent dix ans.\n")
ROUTINES_EN = (
    "### Tools and routines\n\n"
    "**Tools.** Under the cash-basis system Hervé keeps a receipts and payments book, on paper or a spreadsheet: each "
    "line shows the date, document, amount and means of payment (cash, bank, Orange Money) [[source:ohada-audcif]]. "
    "Documents go into three binders: Receipts, Payments, Bank and Mobile Money; articles, Mr Etoga's advance and the "
    "taxpayer card go to the permanent file.\n\n"
    "**Routines.** Every evening: count the cash and enter the day's receipts and payments. Every month: reconcile the "
    "book with the bank and Orange Money statements, deposit the cash. Every year: count the units in stock and file "
    "the yearly IGS return and payment by 15 April [[cgi:art. C 41]], the cash-basis tax return by 15 May "
    "[[cgi:art. C 44]]; documents are kept ten years.\n")
STORE = {
    "in": ("Classeur Recettes ; une ligne au cahier des recettes et des dépenses.",
           "Receipts binder; one line in the receipts and payments book."),
    "out": ("Classeur Dépenses ; une ligne au cahier des recettes et des dépenses.",
            "Payments binder; one line in the receipts and payments book."),
    "bank": ("Classeur Banque et Mobile Money, avec le pointage du cahier.", "Bank and Mobile Money binder, with the "
             "book ticked."),
    "permanent": ("Dossier permanent ; une ligne au cahier.", "Permanent file; one line in the book."),
}


def month_scenes(book, special, month):
    piece = {p["ref"]: p for p in book.pieces}
    m = special["months"][month]
    first = month == 1
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    out = []
    if first:
        cap, adv, tools = piece[special["capital"]], piece[special["advance"]], piece[special["tools"]]
        out.append(scene(
            cap["date"], special["capital"], ("le capital minimal", "the minimum capital"),
            (f"Hervé et M. Etoga déposent {fcfa(total(cap, 'Capital'))} : 20 parts de 5 000 FCFA, 16 pour M. Etoga, 4 "
             "pour Hervé. Sous un million de capital, le notaire est facultatif [[source:loi-2016-014]].",
             f"Hervé and Mr Etoga deposit {fcfa(total(cap, 'Capital'), 'en')}: 20 shares of 5,000 FCFA, 16 for Mr Etoga, "
             "4 for Hervé. Below one million of capital, a notary is optional."),
            ("Au SMT, c'est une recette de trésorerie qui n'est pas un produit : un apport.",
             "Under the cash basis it is a cash receipt that is not revenue: a contribution."),
            ("Le capital ne se compte pas dans le chiffre d'affaires de l'IGS : seules les ventes et les prestations "
             "comptent.", "Capital is not part of the IGS turnover: only sales and services count."),
            ("La banque reçoit les premiers fonds.", "The bank receives the first funds."),
            [("compta", 3, "Actif et passif", "Assets and liabilities")], STORE["permanent"]))
        out.append(scene(
            adv["date"], special["advance"], ("l'avance de M. Etoga", "Mr Etoga's advance"),
            (f"Cent mille francs ne suffisent pas pour démarrer. M. Etoga avance {fcfa(total(adv, 'Avance'))} à la SARL, "
             "remboursables à partir de juillet.",
             f"A hundred thousand francs is not enough to start. Mr Etoga lends the company {fcfa(total(adv, 'Avance'), 'en')}, "
             "repayable from July."),
            ("Compte courant d'associé [[syscohada:4621]] : une dette de la SARL envers M. Etoga.",
             "Partner current account 4621: a debt of the company to Mr Etoga."),
            ("Pourquoi une avance et pas plus de capital ? Le capital reste bloqué dans la société ; l'avance se "
             "rembourse quand la trésorerie le permet.",
             "Why an advance rather than more capital? Capital stays locked in the company; an advance is repaid when "
             "cash allows."),
            ("Au cahier : une recette, qui n'est ni une vente ni un produit.", "In the book: a receipt that is neither a "
             "sale nor revenue."),
            [("compta", 15, "Les opérations de financement", "Financing")], STORE["permanent"]))
        out.append(scene(
            tools["date"], special["tools"], ("l'outillage", "the tools"),
            ("Hervé achète une pompe à vide, un manifold et un détecteur de fuites chez Clim Distribution Wouri, payés "
             "par virement.", "Hervé buys a vacuum pump, a manifold and a leak detector from Clim Distribution Wouri, paid "
             "by transfer."),
            ("Petit outillage en charge [[syscohada:6056]], sous le seuil de 500 000 HT [[cgi:art. 7]] ; à l'IGS, la "
             "TVA facturée entre dans le coût.", "Small tools as an expense 6056, under the 500,000 threshold; under the "
             "IGS, VAT charged is part of the cost."),
            ("Un contribuable à l'IGS ne collecte pas de TVA, donc il n'en déduit pas : la dépense est le prix TTC.",
             "An IGS taxpayer does not charge VAT, so it does not recover any: the payment is the price incl. tax."),
            (f"Dépense de {fcfa(total(tools, 'Net'))} au cahier.", f"A {fcfa(total(tools, 'Net'), 'en')} payment in the book."),
            [("fisca", 1, "Le système fiscal et les régimes d'imposition", "The tax system and regimes")], STORE["out"]))
    purchase = piece[m["purchase"]]
    out.append(scene(
        purchase["date"], m["purchase"], ("les climatiseurs du mois", "the month's air conditioners"),
        (f"Hervé achète les climatiseurs split à revendre. Le fournisseur, au réel, facture la TVA et retient un "
         f"précompte de {fcfa(total(purchase, 'Précompte'))} parce que la SARL est à l'IGS.",
         f"Hervé buys split air conditioners for resale. The supplier, under the actual regime, charges VAT and a "
         f"{fcfa(total(purchase, 'Précompte'), 'en')} withholding because the company is under the IGS."),
        ("Précompte de 5 % pour un client à l'IGS [[cgi:art. 21]] [[param:precompte.taux_igs]] ; TVA non déductible.",
         "5% withholding for an IGS customer; VAT not recoverable."),
        (("Pourquoi 5 % et pas 2 % ? Le taux de 2 % vise les acheteurs au réel ; un contribuable à l'IGS subit 5 %. "
          "Et pourquoi le compter dans le coût ? Le CGI ne prévoit son imputation que sur l'IS ou l'IRPP ; l'IGS, "
          "impôt synthétique, n'en offre pas : la SARL le supporte, comme la TVA." if first else
          "Rappel : 5 % parce que la SARL est à l'IGS ; précompte et TVA restent dans le coût."),
         ("Why 5% and not 2%? The 2% rate is for actual-regime buyers; an IGS taxpayer suffers 5%. Why count it in the "
          "cost? The CGI credits it only against corporate or personal income tax; the IGS offers no credit, so the "
          "company bears it, like VAT." if first else "Reminder: 5% because the company is under the IGS; withholding "
          "and VAT stay in the cost.")),
        (f"Dépense de {fcfa(total(purchase, 'Net'))} au cahier.", f"A {fcfa(total(purchase, 'Net'), 'en')} payment."),
        [("fisca", 1, "Le système fiscal et les régimes d'imposition", "The tax system and regimes")], STORE["out"]))
    for key, how_fr, how_en in (("service0", "par virement", "by transfer"), ("service1", "par Orange Money",
                                                                               "by Orange Money")):
        inv = piece[m[key]]
        client = inv["payload"]["customer"]["name"]
        out.append(scene(
            inv["date"], m[key], (f"une intervention chez {client}", f"a job at {client}"),
            (f"Hervé entretient les climatiseurs de {client} ; la facture, sans TVA, est réglée {how_fr}.",
             f"Hervé services {client}'s air conditioners; the invoice, without VAT, is paid {how_en}."),
            ("Prestation [[syscohada:7061]] ; facture sans TVA à l'IGS [[cgi:art. C 38]].",
             "Service 7061; invoice without VAT under the IGS."),
            ("Pourquoi pas de TVA ? L'IGS est libératoire de la patente et de la TVA : la SARL paie à la place un "
             "montant annuel fixé selon sa classe de chiffre d'affaires [[cgi:art. C 40]]." if first else
             "Rappel : pas de TVA à l'IGS.",
             "Why no VAT? The IGS discharges the business licence and VAT: the company pays instead a yearly amount set "
             "by its turnover class." if first else "Reminder: no VAT under the IGS."),
            (f"Recette de {fcfa(total(inv, 'Net'))}, qui compte dans le chiffre d'affaires de l'IGS.",
             f"A {fcfa(total(inv, 'Net'), 'en')} receipt, part of the IGS turnover."),
            [("fisca", 1, "Le système fiscal et les régimes d'imposition", "The tax system and regimes")], STORE["in"]))
    fee = piece[m["vacation"]]
    out.append(scene(
        fee["date"], m["vacation"], ("la formation des clients", "training the customers"),
        ("Le samedi, M. Etoga forme le personnel des clients à l'usage des climatiseurs. Fonctionnaire, il ne peut pas "
         "être salarié : il remet une note d'honoraires, payée en espèces.",
         "On Saturdays Mr Etoga trains customers' staff to use the units. As a civil servant he cannot be an employee: "
         "he issues a fee note, paid in cash."),
        ("Honoraires [[syscohada:632]], et non salaires.", "Fees 632, not wages."),
        ("Un contrat de travail est en principe interdit au fonctionnaire ; l'honoraire rémunère une prestation "
         "ponctuelle, sans bulletin de paie ni CNPS.",
         "An employment contract is in principle barred for a civil servant; a fee pays for a one-off service, with no "
         "payslip and no CNPS."),
        (f"Dépense de {fcfa(total(fee, 'Honoraires'))} au cahier.", f"A {fcfa(total(fee, 'Honoraires'), 'en')} payment."),
        [("compta", 10, "Autres charges et autres produits", "Other expenses and income")], STORE["out"]))
    cash, momo, bank = piece[m["cash"]], piece[m["momo"]], piece[m["bank"]]
    out.append(scene(
        cash["date"], m["cash"], ("les ventes au comptant", "cash sales"),
        (f"Des particuliers achètent des climatiseurs au comptant : {fcfa(total(cash, 'Ventes'))} dans le mois.",
         f"Private customers buy units for cash: {fcfa(total(cash, 'Ventes'), 'en')} in the month."),
        ("Ventes de marchandises [[syscohada:7011]], en caisse [[syscohada:5711]].", "Goods sold 7011, in cash 5711."),
        ("Au SMT, la recette se note le jour où l'argent entre, pas le jour de la commande.",
         "Under the cash basis the receipt is entered the day the money comes in, not the day of the order."),
        ("Les espèces seront versées à la banque le mois suivant.", "The cash is deposited at the bank the next month."),
        [("compta", 7, "Les ventes", "Sales")], STORE["in"]))
    out.append(scene(
        momo["date"], m["momo"], ("le relevé Orange Money", "the Orange Money statement"),
        (f"Le relevé Orange Money montre l'encaissement du client et le transfert vers la banque, moins "
         f"{fcfa(total(momo, 'Frais'))} de frais.",
         f"The Orange Money statement shows the customer's payment and the transfer to the bank, less "
         f"{fcfa(total(momo, 'Frais'), 'en')} of fees."),
        ("Sous-compte [[syscohada:552]] (5522), transfert par [[syscohada:585]], frais [[syscohada:631]].",
         "Sub-account 552 (5522), transfer through 585, fees 631."),
        ("Un transfert entre Orange Money et la banque n'est ni une recette ni une dépense : l'argent change seulement "
         "de poche.", "A transfer between Orange Money and the bank is neither a receipt nor a payment: money only "
         "changes pockets."),
        ("Seuls les frais sont une dépense au cahier.", "Only the fees are a payment in the book."),
        [("compta", 12, "Les règlements", "Settlements")], STORE["bank"]))
    repay = total(bank, "Remboursement", 0)
    out.append(scene(
        bank["date"], m["bank"], ("le relevé bancaire", "the bank statement"),
        ("Le relevé reprend le transfert Orange Money, le versement des espèces et les frais"
         + (", ainsi que le remboursement mensuel à M. Etoga" if repay else "") + ". Hervé le pointe ligne à ligne.",
         "The statement shows the Orange Money transfer, the cash deposit and the fees"
         + (", plus the monthly repayment to Mr Etoga" if repay else "") + ". Hervé ticks it line by line."),
        ("Banque [[syscohada:521]]" + (" ; remboursement du compte courant [[syscohada:4621]]" if repay else "") + ".",
         "Bank 521" + (", repayment of the current account 4621" if repay else "") + "."),
        (("Rembourser M. Etoga n'est pas une dépense de l'activité : c'est le retour d'une dette." if repay else
          "Le pointage fait apparaître tout oubli du cahier."),
         ("Repaying Mr Etoga is not a business expense: it returns a debt." if repay else
          "Ticking reveals anything missing from the book.")),
        ("La trésorerie du mois est arrêtée.", "The month's cash position is closed."),
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE["bank"]))
    return out


def month_section(book, special, month, opening, others, lang):
    scenes = month_scenes(book, special, month)
    hook = ("Janvier 2026 : la SARL démarre avec cent mille francs de capital et l'avance d'un associé."
            if month == 1 else f"{MONTHS_FR[month - 1].capitalize()} 2026 : contrats d'entretien et ventes au comptant.",
            "January 2026: the company starts with a hundred thousand francs of capital and a partner's advance."
            if month == 1 else f"{MONTHS_EN[month - 1]} 2026: maintenance contracts and cash sales.")
    if month == 7:
        hook = ("Juillet 2026 : la SARL commence à rembourser M. Etoga.", "July 2026: the company starts repaying Mr Etoga.")
    intro = (f"{hook[0]} Au système minimal de trésorerie, on suit l'argent qui entre et qui sort "
             "[[cgi:art. 93 quater]].\n" if lang == "fr" else
             f"{hook[1]} Under the cash-basis system we follow the money in and out [[cgi:art. 93 quater]].\n")
    summary = (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- Recettes et dépenses inscrites au cahier, relevés pointés.\n\n"
               "Rappel : pas de déclaration de TVA à l'IGS ; l'impôt se règle avec la déclaration annuelle.\n"
               if lang == "fr" else
               f"### {MONTHS_EN[month - 1]} in brief\n\n- Receipts and payments entered, statements ticked.\n\n"
               "Reminder: no VAT return under the IGS; the tax is settled with the yearly return.\n")
    return assemble(intro, scenes, opening, others, summary, lang)


def year_end_sections(book, special):
    piece = {p["ref"]: p for p in book.pieces}
    stock_ref = special["stock"][0]
    igs_ref = special["igs_return"]
    count = scene(
        piece[stock_ref]["date"], stock_ref, ("l'inventaire des climatiseurs", "counting the units"),
        ("Le 31 décembre, Hervé compte les climatiseurs restés au magasin et les valorise au coût moyen de l'année.",
         "On 31 December Hervé counts the units left in the store and values them at the year's average cost."),
        ("Au SMT, le cahier suit l'argent ; le comptage du stock dit ce que l'argent dépensé est devenu "
         "[[source:ohada-audcif]].",
         "Under the cash basis the book follows money; counting the stock shows what the money spent has become."),
        ("Pourquoi compter ce qui n'a pas été vendu ? Le stock est de la trésorerie immobilisée : sans lui, l'excédent de "
         "l'année serait mal compris.", "Why count what was not sold? Stock is tied-up cash: without it the year's "
         "surplus would be misread."),
        ("Le CMUP sert de référence ; le PEPS est calculé en contraste.", "WAC is the reference; FIFO is computed as a "
         "contrast."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Fiche de stock signée au classeur Dépenses ; résumé au cahier.", "Signed stock card in the Payments binder; "
         "summary in the book."))
    igs = scene(
        piece[igs_ref]["date"], igs_ref, ("la déclaration annuelle de l'IGS", "the yearly IGS return"),
        (f"Hervé additionne les recettes de l'année : {fcfa(special['turnover'])}. Ce chiffre place la SARL dans une classe "
         f"du tarif de l'IGS : {fcfa(special['igs'])} à payer avec la déclaration, avant le 15 avril 2027.",
         f"Hervé adds up the year's receipts: {fcfa(special['turnover'], 'en')}. That turnover places the company in an "
         f"IGS class: {fcfa(special['igs'], 'en')} due with the return, by 15 April 2027."),
        ("Tarif par classe de chiffre d'affaires [[cgi:art. C 40]], déclaration annuelle [[cgi:art. C 41]].",
         "Tariff by turnover class [[cgi:art. C 40]], yearly return [[cgi:art. C 41]]."),
        ("Pourquoi un tarif et pas un impôt sur le bénéfice ? L'IGS est un impôt synthétique : un montant fixe selon la "
         "classe de chiffre d'affaires, réduit de moitié pour un adhérent d'un Centre de Gestion Agréé "
         f"({fcfa(special['igs_cga'])}) [[cgi:art. C 38]]. Le délai est le 15 avril depuis la LF 2026, paiement "
         "compris ; la SARL pourrait aussi payer par trimestre.",
         "Why a tariff and not a tax on profit? The IGS is a synthetic tax: a fixed amount by turnover class, halved for "
         f"a member of a registered management centre ({fcfa(special['igs_cga'], 'en')}). The deadline is 15 April "
         "since the 2026 Finance Act, payment included; quarterly payment is an option."),
        ("La SARL reste sous le seuil de 50 millions [[cgi:art. C 39]] : elle demeure à l'IGS.",
         "The company stays below the 50 million threshold: it remains under the IGS."),
        [("fisca", 1, "Le système fiscal et les régimes d'imposition", "The tax system and regimes")],
        ("Déclaration et quittance au dossier permanent ; une dernière ligne au cahier.", "Return and receipt in the "
         "permanent file; a last line in the book."))
    close = {lang: (("Le 31 décembre, l'année se ferme sur l'inventaire [[syscohada:5711]].\n\n" if lang == "fr" else
                     "On 31 December the year closes with the count [[syscohada:5711]].\n\n") + count[lang])
             for lang in ("fr", "en")}
    smt = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces if p.get("dsf"))
    smt_text = {
        "fr": ("\n### Avant le 15 mai 2027 : la DSF du SMT\n\nAvec plus de 10 millions de chiffre d'affaires, la SARL tient "
               "le SMT et dépose une DSF au plus tard le 15 mai [[cgi:art. C 44]] : un bilan et un compte de résultat "
               "établis à partir de la trésorerie, corrigés de la variation des stocks [[source:ohada-audcif]]. Ce n'est "
               f"pas la DSF du système normal.\n\n{smt}\n\n**Où ça se range.** Dossier permanent, avec l'accusé de "
               "réception ; conservation dix ans.\n"),
        "en": ("\n### Before 15 May 2027: the cash-basis tax return\n\nWith more than 10 million of turnover, the company "
               "keeps the cash-basis system and files a return by 15 May [[cgi:art. C 44]]: a balance sheet and an "
               "income statement drawn from cash, adjusted for the change in inventories. It is not the standard "
               f"return.\n\n{smt}\n\n**Where it is filed.** Permanent file, with the acknowledgement; kept ten years.\n")}
    yearly = {lang: igs[lang] + smt_text[lang] for lang in ("fr", "en")}
    result = {}
    for key, value in (("close", close), ("igs", yearly)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    return result


def company_extra(lang):
    return typeset_fr(CAST_FR + "\n" + ROUTINES_FR) if lang == "fr" else CAST_EN + "\n" + ROUTINES_EN
