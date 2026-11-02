"""Récit du parcours B1, Ets Bilounga Boissons (S34, S38 à S40) : même canevas en cinq temps que les autres parcours.

Un petit dépôt de boissons à Yaoundé-Ekounou, à l'IGS, qui tient le système minimal de trésorerie : achats à la
brasserie, ventes au casier en espèces et par Orange Money, loyer payé brut, versements à la banque, prélèvements de
l'exploitante ; en 2027, déclaration de l'art. 74, IGS et DSF du SMT. Tous les montants sont lus sur les pièces.
"""
import datetime

from tools.simulation.narrative_b3 import MONTHS_EN, MONTHS_FR, assemble, fcfa, qty, scene, total, typeset_fr

COMPANY_FR = (
    "## Ets Bilounga Boissons\n\nDépôt de boissons à Yaoundé-Ekounou, établissement individuel de Mme Thérèse Bilounga, "
    "immatriculé le 2 janvier 2026. Chiffre d'affaires prévisionnel de 28 millions, sous le seuil de 50 millions du "
    "négoce : régime de l'impôt général synthétique [[cgi:art. 93 quater]] [[cgi:art. C 39]], suivi par le centre de "
    "fiscalité locale. Au-delà de 10 millions de chiffre d'affaires, le dépôt tient le système minimal de trésorerie et "
    "dépose une DSF du SMT [[cgi:art. C 44]] [[source:ohada-audcif]].\n\n"
    "### Comptes utilisés\n\n"
    "[[syscohada:103]] [[syscohada:104]] (1042 prélèvements) [[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] "
    "(sous-compte 5522 Orange Money) [[syscohada:585]] [[syscohada:6011]] [[syscohada:6222]] [[syscohada:612]] "
    "[[syscohada:631]] [[syscohada:7011]]\n\n"
    "### Taux et tarifs de l'exercice\n\n"
    "- précompte sur achats subi à l'IGS [[param:precompte.taux_igs]] [[cgi:art. 21]], qui reste dans le coût ;\n"
    "- IGS de la classe 9 (de 20 à moins de 30 millions) [[param:igs.classe9_montant]], moitié pour un adhérent d'un "
    "Centre de Gestion Agréé [[cgi:art. C 40]] ;\n"
    "- SMT et DSF dès [[param:igs.seuil_comptabilite]] de chiffre d'affaires [[cgi:art. C 44]].\n\n"
    "### Les personnages\n\n| Personnage | Rôle |\n|---|---|\n"
    "| Thérèse Bilounga | Exploitante : achats, caisse, banque, déclarations |\n"
    "| Junior | Son neveu, aide bénévole le soir et le samedi |\n"
    "| Les pousseurs du carrefour | Livrent les casiers aux clients, payés à la course |\n"
    "| M. Owona | Propriétaire du local |\n"
    "| M. Fouda | Commercial des Brasseries de la Sanaga, déjà rencontré dans le parcours B3 |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n\n"
    "### Les outils et les routines\n\n"
    "Au SMT, Thérèse tient un cahier des recettes et des dépenses, sur papier ou tableur : chaque ligne porte la date, "
    "la pièce, le montant et le moyen de paiement (caisse, banque, Orange Money) [[source:ohada-audcif]]. Le brouillard "
    "de caisse note chaque vente du jour ; la fiche de stock, chaque casier entré ou sorti. Les pièces vont dans trois "
    "classeurs : Recettes, Dépenses, Banque et Mobile Money ; la carte de contribuable et le bail au dossier permanent.\n\n"
    "- *Chaque soir* : arrêté de caisse, brouillard et fiche de stock à jour.\n"
    "- *Le 15 et en fin de mois* : versement des espèces à la banque, la caisse ne gardant que 20 000 de fonds.\n"
    "- *Chaque mois* : rapprochement du cahier avec le relevé bancaire et le relevé Orange Money.\n"
    "- *Chaque année* : inventaire des casiers ; déclaration de revenus au 15 mars [[cgi:art. 74]], IGS au 15 avril "
    "[[cgi:art. C 41]], DSF du SMT au 15 mai ; tout se conserve dix ans.\n")
COMPANY_EN = (
    "## Ets Bilounga Boissons\n\nDrinks depot in Yaoundé-Ekounou, the sole proprietorship of Mrs Thérèse Bilounga, "
    "registered on 2 January 2026. Forecast turnover of 28 million, below the 50 million trading threshold: synthetic "
    "general tax (IGS) [[cgi:art. 93 quater]] [[cgi:art. C 39]], local tax office. Above 10 million of turnover the depot "
    "keeps the cash-basis system and files a cash-basis return [[cgi:art. C 44]] [[source:ohada-audcif]].\n\n"
    "### Accounts\n\n[[syscohada:103]] [[syscohada:104]] [[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] "
    "[[syscohada:6011]] [[syscohada:6222]] [[syscohada:612]] [[syscohada:7011]]\n\n"
    "### Rates\n\n- purchase withholding suffered under the IGS [[param:precompte.taux_igs]] [[cgi:art. 21]];\n"
    "- class 9 IGS [[param:igs.classe9_montant]], halved for a management-centre member [[cgi:art. C 40]].\n\n"
    "### The people\n\n| Person | Role |\n|---|---|\n| Thérèse Bilounga | Owner |\n"
    "| Junior | Her nephew, unpaid help in the evenings |\n| The push-cart men | Deliver crates, paid by the trip |\n"
    "| Mr Owona | Landlord |\n| Mr Fouda | Sanaga breweries sales rep, met in track B3 |\n\nAll are fictitious.\n\n"
    "### Tools and routines\n\nThérèse keeps a receipts and payments book [[source:ohada-audcif]], a daily cash book "
    "and a stock card. Every evening: till count. On the 15th and at month end: cash deposit. Every month: "
    "reconciliations. Every year: crate count; income return by 15 March, IGS by 15 April, cash-basis return by 15 May; "
    "documents are kept ten years.\n")

STORE = {
    "purchase": ("Facture au classeur Dépenses, avec le bon de livraison signé ; une ligne au cahier.",
                 "Invoice in the Payments binder with the signed delivery note; a line in the book."),
    "cash": ("Brouillard au classeur Recettes ; total reporté au cahier.", "Cash book in the Receipts binder."),
    "orange": ("Relevé imprimé au classeur Banque et Mobile Money.", "Printed statement in the Bank and Mobile Money binder."),
    "rent": ("Quittance au classeur Dépenses ; bail au dossier permanent.", "Receipt in the Payments binder."),
    "transport": ("Bons des pousseurs au classeur Dépenses.", "Push-cart slips in the Payments binder."),
    "deposits": ("Bordereaux tamponnés au classeur Banque et Mobile Money.", "Stamped slips in the Bank binder."),
    "bank": ("Relevé et rapprochement au classeur Banque et Mobile Money.", "Statement and reconciliation in the Bank "
             "binder."),
    "permanent": ("Dossier permanent.", "Permanent file."),
}
SMT_COURSE = ("compta", 1, "Le cadre comptable OHADA", "The OHADA accounting framework")
IGS_COURSE = ("fisca", 1, "Le système fiscal et les régimes d'imposition", "The tax system and regimes")


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
        cap = piece[special["capital"]]
        out.append(scene(
            cap["date"], special["capital"], ("les économies de Thérèse", "Thérèse's savings"),
            (f"Thérèse verse {fcfa(total(cap, 'Économies'))} d'économies sur le compte du dépôt : de quoi payer les deux "
             "premières livraisons de la brasserie.",
             f"Thérèse pays {fcfa(total(cap, 'Économies'), 'en')} of savings into the depot account: enough for the "
             "brewery's first two deliveries."),
            ("Capital personnel [[syscohada:103]], banque [[syscohada:521]].", "Personal capital 103, bank 521."),
            ("Pourquoi pas un capital social ? Le dépôt n'est pas une société : Thérèse exploite en son nom et répond "
             "de ses dettes sur ses biens.", "Why no share capital? The depot is not a company: Thérèse trades in her "
             "own name."),
            ("La trésorerie de départ est en banque ; aucune recette.", "Starting cash is in the bank; no receipt."),
            [("compta", 3, "Actif et passif", "Assets and liabilities")], STORE["permanent"]))
    for i, label in ((0, ("la première livraison", "the first delivery")), (1, ("la seconde livraison", "the second delivery"))):
        buy = piece[m[f"purchase{i}"]]
        line_ = buy["payload"]["lines"][0]
        rise = month == 7 and i == 0
        out.append(scene(
            buy["date"], m[f"purchase{i}"], label,
            (f"M. Fouda fait livrer {qty(line_['qty'])} casiers de 65 cl à {fcfa(line_['unit_price'])} HT. Thérèse paie "
             f"par virement {fcfa(total(buy, 'Net'))}, TVA et précompte compris."
             + (" La brasserie applique son nouveau tarif du second semestre." if rise else ""),
             f"Mr Fouda delivers {qty(line_['qty'], 'en')} crates of 65 cl at {fcfa(line_['unit_price'], 'en')} before "
             f"tax. Thérèse pays {fcfa(total(buy, 'Net'), 'en')} by transfer, VAT and withholding included."
             + (" The brewery applies its second-half price." if rise else "")),
            ("Achats [[syscohada:6011]] au coût complet ; précompte de 5 % pour un client à l'IGS [[cgi:art. 21]] "
             "[[param:precompte.taux_igs]] ; TVA non déductible [[cgi:art. C 38]].",
             "Purchases 6011 at full cost; 5% withholding for an IGS customer; VAT not recoverable."),
            (("Pourquoi tout dans le coût ? À l'IGS, Thérèse ne collecte pas de TVA, donc n'en déduit pas ; et le CGI "
              "ne prévoit l'imputation du précompte que sur l'IS ou l'IRPP, que l'IGS remplace. Ce qu'elle paie à la "
              "brasserie est son vrai prix de revient." if first and i == 0 else
              "Rappel : TVA et précompte restent dans le coût ; seul le prix de vente fait la marge."),
             ("Why all in the cost? Under the IGS Thérèse charges no VAT, so recovers none; and the CGI credits the "
              "withholding only against income taxes, which the IGS replaces." if first and i == 0 else
              "Reminder: VAT and withholding stay in the cost.")),
            (f"Dépense de {fcfa(total(buy, 'Net'))} au cahier ; la fiche de stock gagne {qty(line_['qty'])} casiers.",
             f"A {fcfa(total(buy, 'Net'), 'en')} payment; the stock card gains {qty(line_['qty'], 'en')} crates."),
            [("compta", 6, "Les achats", "Purchases"), IGS_COURSE], STORE["purchase"]))
    cash, orange, rent = piece[m["cash"]], piece[m["orange"]], piece[m["rent"]]
    out.append(scene(
        rent["date"], m["rent"], ("le loyer", "the rent"),
        (f"Thérèse remet à M. Owona {fcfa(total(rent, 'Loyer'))} en espèces, sur la recette de la quinzaine.",
         f"Thérèse hands Mr Owona {fcfa(total(rent, 'Loyer'), 'en')} in cash, out of the fortnight's takings."),
        ("Loyer [[syscohada:6222]] payé brut [[cgi:art. 87]].", "Rent 6222 paid gross."),
        ("Pourquoi pas de précompte de 10 % ? La retenue sur loyer vise les locataires au réel ; un locataire à l'IGS "
         "paie le loyer brut." if first else "Rappel : loyer brut, sans retenue, à l'IGS.",
         "Why no 10% withholding? It applies to tenants under the actual regime; an IGS tenant pays gross."
         if first else "Reminder: gross rent under the IGS."),
        ("Une dépense au cahier, payée en espèces.", "A cash payment in the book."),
        [("compta", 10, "Autres charges et autres produits", "Other expenses and income")], STORE["rent"]))
    out.append(scene(
        cash["date"], m["cash"], ("les ventes au comptant", "cash sales"),
        (f"Au comptoir, Thérèse et Junior ont vendu {qty(cash['payload']['lines'][0]['qty'])} casiers au comptant, "
         f"casier plein contre casier vide : {fcfa(total(cash, 'Recettes'))}.",
         f"At the counter Thérèse and Junior sold {qty(cash['payload']['lines'][0]['qty'], 'en')} crates for cash, full "
         f"against empty: {fcfa(total(cash, 'Recettes'), 'en')}."),
        ("Recettes [[syscohada:7011]] en caisse [[syscohada:5711]], sans TVA [[cgi:art. C 38]].",
         "Receipts 7011 in the till 5711, no VAT."),
        ("Pourquoi aucune consigne ? Le client rapporte un casier vide pour en prendre un plein : rien à rembourser, "
         "rien à inscrire en dette." if first else "Le brouillard du soir fonde le cahier.",
         "Why no deposit? The customer returns an empty crate for a full one: nothing to refund." if first else
         "The evening cash book backs the book."),
        ("La recette grossit ; la caisse aussi, jusqu'au versement.", "Receipts grow, and the till, until the deposit."),
        [("compta", 7, "Les ventes", "Sales"), SMT_COURSE], STORE["cash"]))
    out.append(scene(
        orange["date"], m["orange"], ("les paiements par Orange Money", "Orange Money payments"),
        (f"Un client sur trois paie par téléphone : {fcfa(total(orange, 'Encaissements'))} ce mois ; l'opérateur prend "
         "ses frais, le solde part vers la banque.",
         f"One customer in three pays by phone: {fcfa(total(orange, 'Encaissements'), 'en')} this month; the operator "
         "takes its fees and the balance goes to the bank."),
        ("[[syscohada:552]] (5522), frais [[syscohada:631]], transfert par [[syscohada:585]].", "552, fees 631, 585."),
        ("Pourquoi 585 ? Le transfert sort d'Orange Money et entre à la banque : le compte de virements internes évite "
         "de compter deux fois la même somme.", "Why 585? It avoids counting the same money twice."),
        ("La recette Orange Money rejoint la banque.", "Orange Money receipts reach the bank."),
        [("compta", 12, "Les règlements", "Settlements")], STORE["orange"]))
    trip, dep = piece[m["transport"]], piece[m["deposits"]]
    out.append(scene(
        trip["date"], m["transport"], ("les pousse-pousse", "the push-carts"),
        (f"Les pousseurs du carrefour ont livré les clients : {qty(trip['payload']['lines'][0]['qty'])} courses à "
         "1 500 F.", f"The push-cart men delivered customers: {qty(trip['payload']['lines'][0]['qty'], 'en')} trips at "
         "1,500 F."),
        ("Transports sur ventes [[syscohada:612]], payés en espèces.", "Transport on sales 612, paid in cash."),
        ("Pourquoi 612 et pas un salaire ? Les pousseurs ne sont pas employés : ils sont payés à la course, comme un "
         "transporteur." if first else "Rappel : payés à la course.",
         "Why 612 and not wages? They are not employees: paid by the trip." if first else "Reminder: paid by the trip."),
        ("Une dépense de transport au cahier.", "A transport payment in the book."),
        [("compta", 10, "Autres charges et autres produits", "Other expenses and income")], STORE["transport"]))
    out.append(scene(
        dep["date"], m["deposits"], ("les versements à la banque", "the bank deposits"),
        (f"Le 15 et le dernier jour, Thérèse porte la recette à la banque : {fcfa(total(dep, 'Versement du 15'))} puis "
         f"{fcfa(total(dep, 'Versement de fin'))}. La caisse garde 20 000 pour rendre la monnaie.",
         f"On the 15th and the last day Thérèse banks the takings: {fcfa(total(dep, 'Versement du 15'), 'en')} then "
         f"{fcfa(total(dep, 'Versement de fin'), 'en')}. The till keeps 20,000 of float."),
        ("[[syscohada:585]] au débit, [[syscohada:5711]] au crédit.", "585 debit, 5711 credit."),
        ("Pourquoi ne pas tout garder en caisse ? Un dépôt manipule beaucoup d'espèces : les verser limite le risque "
         "et laisse une trace à la banque." if first else "Rappel : la caisse ne garde que son fonds.",
         "Why not keep it all in the till? Banking limits risk and leaves a trace." if first else
         "Reminder: the till keeps only its float."),
        ("La caisse revient à son fonds de 20 000.", "The till is back to its 20,000 float."),
        [("compta", 12, "Les règlements", "Settlements")], STORE["deposits"]))
    end = datetime.date.fromisoformat(piece[m["bank"]]["date"])
    out.append(scene(
        piece[m["bank"]]["date"], m["bank"], ("le relevé bancaire", "the bank statement"),
        ("Le relevé reprend les versements, le transfert d'Orange Money, les virements à la brasserie et le virement de "
         "100 000 que Thérèse fait sur son compte personnel pour son ménage.",
         "The statement shows deposits, the Orange Money transfer, the brewery transfers and the 100,000 Thérèse moves "
         "to her personal account."),
        ("Virements internes [[syscohada:585]], prélèvement [[syscohada:104]] (1042), frais [[syscohada:631]].",
         "585, drawings 1042, fees 631."),
        ("Pourquoi le virement personnel n'est-il pas une dépense ? Thérèse se paie sur ce que le dépôt gagne ; ce "
         "qu'elle prend est un prélèvement, qui réduit ses capitaux, pas le résultat." if first else
         "Un écart s'explique avant de s'écrire.",
         "Why is the personal transfer not a payment of the business? It is drawings: it reduces equity, not profit."
         if first else "A gap is explained before it is booked."),
        (f"Solde du 521 au {end.day} {mfr} : {fcfa(ledger.account_balance(book.entries, '521', end))}.",
         f"521 balance at {men} {end.day}: {fcfa(ledger.account_balance(book.entries, '521', end), 'en')}."),
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE["bank"]))
    return out


HOOKS = {1: ("Janvier 2026 : Thérèse Bilounga ouvre son dépôt à Ekounou.", "January 2026: Thérèse Bilounga opens her "
             "depot in Ekounou."),
         7: ("Juillet 2026 : la brasserie relève son prix ; Thérèse garde le sien.", "July 2026: the brewery raises its "
             "price; Thérèse keeps hers."),
         12: ("Décembre 2026 : les fêtes font tourner les casiers.", "December 2026: the festive season moves crates.")}


def month_section(month, scenes, opening, others, lang):
    default = (f"{MONTHS_FR[month - 1].capitalize()} 2026 : achats, ventes au casier et versements.",
               f"{MONTHS_EN[month - 1]} 2026: purchases, crate sales and deposits.")
    hook = HOOKS.get(month, default)[0 if lang == "fr" else 1]
    intro = (f"{hook} Lisez chaque scène, puis répondez aux questions du quiz [[cgi:art. C 38]].\n" if lang == "fr" else
             f"{hook} Read each scene, then answer the quiz [[cgi:art. C 38]].\n")
    nxt = ("l'inventaire du 31 décembre" if month == 12 else f"les achats de {MONTHS_FR[month]}",
           "the 31 December count" if month == 12 else f"{MONTHS_EN[month]}'s purchases")
    summary = (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- Recettes et dépenses portées au cahier, pièces classées, banque "
               f"et Orange Money rapprochées.\n- Aucune déclaration mensuelle : à l'IGS, tout se déclare une fois l'an.\n\n"
               f"Prochaine étape : {nxt[0]}.\n" if lang == "fr" else
               f"### {MONTHS_EN[month - 1]} in brief\n\n- Receipts and payments booked, documents filed, bank and Orange "
               f"Money reconciled.\n- No monthly return: under the IGS everything is filed once a year.\n\nNext: {nxt[1]}.\n")
    return assemble(intro, scenes, opening, others, summary, lang)


def year_end_sections(book, special):
    piece = {p["ref"]: p for p in book.pieces}
    count = scene(
        piece[special["sheet"]]["date"], special["sheet"], ("l'inventaire des casiers", "the crate count"),
        ("Le 31 au soir, Thérèse et Junior comptent les casiers pleins : les 30 d'avance achetés en janvier sont "
         "toujours là, valorisés au coût moyen de l'année.",
         "On the evening of the 31st Thérèse and Junior count the full crates: the 30 bought ahead in January are still "
         "there, valued at the year's average cost."),
        ("Au SMT, pas d'écriture d'inventaire ; le stock final corrige le résultat de la DSF du SMT "
         "[[source:ohada-audcif]].", "Under the cash basis there is no inventory entry; closing stock adjusts the "
         "cash-basis return."),
        ("Pourquoi le CMUP sur les prix HT de la brasserie ? C'est la référence de la fiche de stock ; le PEPS, en "
         "contraste, garde les derniers casiers, achetés plus cher.", "Why WAC on brewery HT prices? It is the stock "
         "card reference; FIFO keeps the latest, dearer crates."),
        (f"Stock final : {fcfa(special['stock_value'])}.", f"Closing stock: {fcfa(special['stock_value'], 'en')}."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Fiche de stock signée au classeur Dépenses ; résumé au cahier.", "Signed stock card; summary in the book."))
    close = {lang: (("Le 31 décembre, l'année se ferme sur le comptage [[syscohada:5711]].\n\n" if lang == "fr" else
                     "On 31 December the year closes with the count [[syscohada:5711]].\n\n") + count[lang]
                    + "\n[[calc:stock]]\n") for lang in ("fr", "en")}
    art74, igs, smt = piece[special["art74"]], piece[special["igs_return"]], special["smt_return"]
    s1 = scene(
        art74["date"], special["art74"], ("la déclaration de revenus", "the income return"),
        (f"Avant le 15 mars, Thérèse dépose sa déclaration annuelle de revenus : {fcfa(special['turnover'])} de chiffre "
         "d'affaires, sous l'IGS.", f"Before 15 March Thérèse files her yearly income return: "
         f"{fcfa(special['turnover'], 'en')} of turnover, under the IGS."),
        ("Une personne physique à l'IGS reste tenue à la déclaration annuelle de l'art. 74 [[cgi:art. C 39]] "
         "[[cgi:art. 74]].", "An individual under the IGS still files the art. 74 yearly return."),
        ("Pourquoi déclarer si l'IGS libère de l'IRPP ? L'administration recoupe les revenus de chaque personne ; la "
         "déclaration n'ajoute pas d'impôt sur le dépôt.", "Why file if the IGS discharges income tax? The tax office "
         "cross-checks each person's income; no extra tax on the depot."),
        ("Aucun paiement à cette date.", "No payment at this date."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")],
        ("Accusé de réception au dossier permanent.", "Acknowledgement in the permanent file."))
    s2 = scene(
        igs["date"], special["igs_return"], ("l'IGS de l'année", "the year's IGS"),
        (f"Le chiffre d'affaires place le dépôt en classe 9 : {fcfa(special['igs'])} à payer avec la déclaration, avant "
         f"le 15 avril. Adhérente d'un Centre de Gestion Agréé, Thérèse n'aurait payé que {fcfa(special['igs_cga'])}.",
         f"Turnover places the depot in class 9: {fcfa(special['igs'], 'en')} due with the return by 15 April. As a "
         f"management-centre member she would have paid {fcfa(special['igs_cga'], 'en')}."),
        ("Tarif par classe [[cgi:art. C 40]] ; déclaration et paiement au 15 avril, ou par trimestre sur option "
         "[[cgi:art. C 41]].", "Tariff by class; return and payment by 15 April, or quarterly by option."),
        (f"Pourquoi l'IGS pèse-t-il si lourd ? Il ne dépend pas de la marge : sur un résultat de "
         f"{fcfa(special['smt_result'])}, un IGS de {fcfa(special['igs'])} en prend une grande part. Le Centre de Gestion "
         "Agréé, ou un meilleur prix de vente, change la donne.",
         f"Why is the IGS so heavy? It ignores the margin: on a {fcfa(special['smt_result'], 'en')} profit, a "
         f"{fcfa(special['igs'], 'en')} IGS takes a large share."),
        (f"La banque baisse de {fcfa(special['igs'])} en avril 2027.", f"The bank drops by {fcfa(special['igs'], 'en')}."),
        [("fisca", 6, "La fiscalité locale", "Local taxation"), IGS_COURSE],
        ("Déclaration et quittance au dossier permanent.", "Return and receipt in the permanent file."))
    refs = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces if p.get("dsf"))
    smt_fr = ("### Avant le 15 mai 2027 : la DSF du SMT\n\nAvec plus de 10 millions de chiffre d'affaires, Thérèse dépose "
              "la DSF du SMT au plus tard le 15 mai [[cgi:art. C 44]] : un bilan et un compte de résultat établis à "
              f"partir de la trésorerie, corrigés du stock final [[source:ohada-audcif]].\n\n{refs}\n\n**Où ça se range.** "
              "Dossier permanent, avec l'accusé de réception ; conservation dix ans.\n")
    smt_en = ("### Before 15 May 2027: the cash-basis return\n\nWith more than 10 million of turnover, Thérèse files the "
              "cash-basis return by 15 May [[cgi:art. C 44]]: a balance sheet and an income statement drawn from cash, "
              f"adjusted for closing stock.\n\n{refs}\n\n**Where it is filed.** Permanent file; kept ten years.\n")
    returns = {"fr": "Trois échéances en 2027, à ne pas confondre [[cgi:art. C 41]].\n\n" + s1["fr"] + "\n" + s2["fr"]
               + "\n" + smt_fr,
               "en": "Three deadlines in 2027 [[cgi:art. C 41]].\n\n" + s1["en"] + "\n" + s2["en"] + "\n" + smt_en}
    result = {}
    for key, value in (("close", close), ("returns", returns)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    assert smt in refs
    return result
