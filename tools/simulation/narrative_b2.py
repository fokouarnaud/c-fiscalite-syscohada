"""Récit du parcours B2, Ets Essomba Boissons puis Essomba Boissons SARL (S34, S38 à S41) : même canevas en cinq temps.

Un dépôt de boissons à Douala-Bépanda, à l'IGS et au SMT toute l'année 2026, qui reste sous le seuil de 50 millions ;
en septembre, le contrat d'un hôtel pour 2027 décide Paul Essomba à déclarer la cessation de l'Ets au 31 décembre et
à apporter son fonds à une SARL au réel au 1er janvier 2027. Tous les montants sont lus sur les pièces.
"""
import datetime

from tools.simulation.narrative_b3 import MONTHS_EN, MONTHS_FR, assemble, fcfa, qty, scene, total, typeset_fr

COMPANY_FR = (
    "## Ets Essomba Boissons\n\nDépôt de boissons à Douala-Bépanda, établissement individuel de M. Paul Essomba, "
    "immatriculé le 2 janvier 2026. Chiffre d'affaires prévisionnel de 46 millions, sous le seuil de 50 millions du "
    "négoce : régime de l'impôt général synthétique [[cgi:art. 93 quater]] [[cgi:art. C 39]], suivi par le centre de "
    "fiscalité locale de Douala V. Au-delà de 10 millions de chiffre d'affaires, le dépôt tient le système minimal de "
    "trésorerie et dépose une DSF du SMT [[cgi:art. C 44]] [[source:ohada-audcif]].\n\n"
    "Ce parcours a une particularité : le dépôt grandit. Tout dépassement de 50 millions en cours d'année entraînerait "
    "un reclassement d'office au réel [[cgi:art. C 39]] ; Paul reste donc sous le seuil en 2026, puis, quand un hôtel "
    "lui commande ses boissons pour 2027, il transforme son affaire en **Essomba Boissons SARL**, au réel, au "
    "1er janvier 2027.\n\n"
    "### Comptes utilisés\n\n"
    "En 2026 (Ets, SMT) : [[syscohada:103]] [[syscohada:104]] (1042 prélèvements) [[syscohada:521]] "
    "[[syscohada:5711]] [[syscohada:552]] (sous-compte 5522 Orange Money) [[syscohada:585]] [[syscohada:6011]] "
    "[[syscohada:6222]] [[syscohada:612]] [[syscohada:631]] [[syscohada:7011]]\n\n"
    "Au 1er janvier 2027 (SARL, réel) : [[syscohada:1013]] [[syscohada:311]] [[syscohada:2458]] [[syscohada:521]] "
    "[[syscohada:4621]] [[syscohada:4454]] [[syscohada:6324]] [[syscohada:6468]]\n\n"
    "### Taux et tarifs de l'exercice\n\n"
    "- précompte sur achats subi à l'IGS [[param:precompte.taux_igs]] [[cgi:art. 21]], qui reste dans le coût ;\n"
    "- IGS de la classe 10 (de 30 à moins de 50 millions) [[param:igs.classe10_montant]], moitié pour un adhérent "
    "d'un Centre de Gestion Agréé [[cgi:art. C 40]] ;\n"
    "- SMT et DSF dès [[param:igs.seuil_comptabilite]] de chiffre d'affaires [[cgi:art. C 44]] ;\n"
    "- SARL : part sociale d'au moins [[param:sarl.part_minimum]], notaire facultatif jusqu'à "
    "[[param:sarl.seuil_notaire_facultatif]] de capital [[source:loi-2016-014]] ; CIME dès "
    "[[param:dgi.seuil_cime]] de chiffre d'affaires [[source:dgi-cime]].\n\n"
    "### Les personnages\n\n| Personnage | Rôle |\n|---|---|\n"
    "| Paul Essomba | Exploitant : achats, banque, déclarations ; associé unique et gérant de la SARL en 2027 |\n"
    "| Brigitte Essomba | Son épouse, tient la caisse et le brouillard le soir |\n"
    "| Les pousseurs du marché de Bépanda | Livrent les casiers aux clients, payés à la course |\n"
    "| M. Kotto | Propriétaire du local |\n"
    "| M. Fouda | Commercial des Brasseries de la Sanaga, déjà rencontré dans les parcours B3 et B1 |\n"
    "| Mme Eyango | Économe de l'hôtel qui signe le contrat de 2027 |\n"
    "| Maître Ngo Bassa | Notaire qui rédige les statuts |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n\n"
    "### Les outils et les routines\n\n"
    "Au SMT, Paul tient un cahier des recettes et des dépenses : chaque ligne porte la date, la pièce, le montant et le "
    "moyen de paiement [[source:ohada-audcif]]. Brigitte note chaque vente du jour au brouillard de caisse ; la fiche "
    "de stock suit chaque casier. Les pièces vont dans trois classeurs : Recettes, Dépenses, Banque et Mobile Money ; la "
    "carte de contribuable et le bail au dossier permanent. En décembre, un quatrième classeur s'ouvre : « SARL ».\n\n"
    "- *Chaque soir* : arrêté de caisse, brouillard et fiche de stock à jour.\n"
    "- *Le 15 et en fin de mois* : versement des espèces à la banque, la caisse ne gardant que 20 000 de fonds.\n"
    "- *Chaque mois* : rapprochement du cahier avec le relevé bancaire et le relevé Orange Money ; suivi du chiffre "
    "d'affaires cumulé face au seuil de 50 millions.\n"
    "- *Chaque année* : inventaire des casiers ; déclaration de revenus au 15 mars [[cgi:art. 74]] ; à la cessation, "
    "déclaration de clôture dans les trois mois [[cgi:art. 95]] ; tout se conserve dix ans.\n")
COMPANY_EN = (
    "## Ets Essomba Boissons\n\nDrinks depot in Douala-Bépanda, the sole proprietorship of Mr Paul Essomba, registered on "
    "2 January 2026. Forecast turnover of 46 million, below the 50 million trading threshold: synthetic general tax "
    "(IGS) [[cgi:art. 93 quater]] [[cgi:art. C 39]], Douala V local tax office. Above 10 million of turnover the depot "
    "keeps the cash-basis system and files a cash-basis return [[cgi:art. C 44]] [[source:ohada-audcif]].\n\n"
    "This track has a twist: the depot grows. Crossing 50 million during the year would mean a forced move to the "
    "actual regime [[cgi:art. C 39]]; Paul stays below the threshold in 2026, then, when a hotel orders its drinks for "
    "2027, turns his business into **Essomba Boissons SARL**, under the actual regime, on 1 January 2027.\n\n"
    "### Accounts\n\nIn 2026: [[syscohada:103]] [[syscohada:104]] [[syscohada:521]] [[syscohada:5711]] [[syscohada:552]] "
    "[[syscohada:6011]] [[syscohada:6222]] [[syscohada:612]] [[syscohada:7011]]\n\n"
    "On 1 January 2027: [[syscohada:1013]] [[syscohada:311]] [[syscohada:2458]] [[syscohada:4621]] [[syscohada:6324]] "
    "[[syscohada:6468]]\n\n"
    "### Rates\n\n- purchase withholding suffered under the IGS [[param:precompte.taux_igs]] [[cgi:art. 21]];\n"
    "- class 10 IGS [[param:igs.classe10_montant]], halved for a management-centre member [[cgi:art. C 40]];\n"
    "- LLC: share of at least [[param:sarl.part_minimum]], notary optional up to "
    "[[param:sarl.seuil_notaire_facultatif]] [[source:loi-2016-014]].\n\n"
    "### The people\n\n| Person | Role |\n|---|---|\n| Paul Essomba | Owner; sole partner and manager of the LLC |\n"
    "| Brigitte Essomba | His wife, keeps the till in the evening |\n| The push-cart men | Deliver crates, paid by the "
    "trip |\n| Mr Kotto | Landlord |\n| Mr Fouda | Sanaga breweries sales rep, met in tracks B3 and B1 |\n"
    "| Mrs Eyango | Hotel bursar who signs the 2027 contract |\n| Maître Ngo Bassa | Notary |\n\nAll are fictitious.\n\n"
    "### Tools and routines\n\nPaul keeps a receipts and payments book [[source:ohada-audcif]], a daily cash book and a "
    "stock card. Every evening: till count. On the 15th and at month end: cash deposit. Every month: reconciliations "
    "and a check of cumulative turnover against the 50 million threshold. Every year: crate count; income return by "
    "15 March; at cessation, a closing return within three months [[cgi:art. 95]]; documents are kept ten years.\n")

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
    "sarl": ("Classeur « SARL » : il passera à la SARL avec ses pièces fondatrices.", "\"LLC\" binder: it goes to the "
             "LLC with its founding documents."),
}
SMT_COURSE = ("compta", 1, "Le cadre comptable OHADA", "The OHADA accounting framework")
IGS_COURSE = ("fisca", 1, "Le système fiscal et les régimes d'imposition", "The tax system and regimes")
ASSETS_COURSE = ("compta", 3, "Actif et passif", "Assets and liabilities")


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
            cap["date"], special["capital"], ("les économies de Paul", "Paul's savings"),
            (f"Paul verse {fcfa(total(cap, 'Économies'))} d'économies sur le compte du dépôt : de quoi payer les "
             "premières livraisons de la brasserie et garder une réserve.",
             f"Paul pays {fcfa(total(cap, 'Économies'), 'en')} of savings into the depot account: enough for the "
             "brewery's first deliveries and a reserve."),
            ("Capital personnel [[syscohada:103]], banque [[syscohada:521]].", "Personal capital 103, bank 521."),
            ("Pourquoi pas un capital social ? Le dépôt n'est pas une société : Paul exploite en son nom et répond de "
             "ses dettes sur tous ses biens. La SARL de 2027 changera cela.", "Why no share capital? The depot is not a "
             "company: Paul trades in his own name. The 2027 LLC will change that."),
            ("La trésorerie de départ est en banque ; aucune recette.", "Starting cash is in the bank; no receipt."),
            [ASSETS_COURSE], STORE["permanent"]))
    for i, label in ((0, ("la première livraison", "the first delivery")), (1, ("la seconde livraison", "the second delivery"))):
        buy = piece[m[f"purchase{i}"]]
        line_ = buy["payload"]["lines"][0]
        rise = month == 7 and i == 0
        out.append(scene(
            buy["date"], m[f"purchase{i}"], label,
            (f"Le camion de la brasserie livre {qty(line_['qty'])} casiers de 65 cl à {fcfa(line_['unit_price'])} HT. "
             f"Paul paie par virement {fcfa(total(buy, 'Net'))}, TVA et précompte compris."
             + (" M. Fouda annonce le nouveau tarif du second semestre." if rise else ""),
             f"The brewery truck delivers {qty(line_['qty'], 'en')} crates of 65 cl at {fcfa(line_['unit_price'], 'en')} "
             f"before tax. Paul pays {fcfa(total(buy, 'Net'), 'en')} by transfer, VAT and withholding included."
             + (" Mr Fouda announces the second-half price." if rise else "")),
            ("Achats [[syscohada:6011]] au coût complet ; précompte de 5 % pour un client à l'IGS [[cgi:art. 21]] "
             "[[param:precompte.taux_igs]] ; TVA non déductible [[cgi:art. C 38]].",
             "Purchases 6011 at full cost; 5% withholding for an IGS customer; VAT not recoverable."),
            (("Pourquoi tout dans le coût ? À l'IGS, Paul ne collecte pas de TVA, donc n'en déduit pas ; et le CGI ne "
              "prévoit l'imputation du précompte que sur l'IS ou l'IRPP, que l'IGS remplace." if first and i == 0 else
              "Rappel : TVA et précompte restent dans le coût ; seul le prix de vente fait la marge."),
             ("Why all in the cost? Under the IGS Paul charges no VAT, so recovers none; and the CGI credits the "
              "withholding only against income taxes, which the IGS replaces." if first and i == 0 else
              "Reminder: VAT and withholding stay in the cost.")),
            (f"Dépense de {fcfa(total(buy, 'Net'))} au cahier ; la fiche de stock gagne {qty(line_['qty'])} casiers.",
             f"A {fcfa(total(buy, 'Net'), 'en')} payment; the stock card gains {qty(line_['qty'], 'en')} crates."),
            [("compta", 6, "Les achats", "Purchases"), IGS_COURSE], STORE["purchase"]))
    if month == 11:
        dep, tri = piece[m["deposit_sarl"]], piece[m["tricycle"]]
        out.append(scene(
            dep["date"], m["deposit_sarl"], ("le numéraire de la SARL", "the LLC's cash"),
            (f"Paul vire {fcfa(total(dep, 'Apport'))} du compte du dépôt vers un compte bloqué ouvert au nom "
             "d'Essomba Boissons SARL, en formation. La banque lui remet le certificat du dépositaire.",
             f"Paul transfers {fcfa(total(dep, 'Apport'), 'en')} from the depot account to a blocked account in the "
             "name of Essomba Boissons SARL, being formed. The bank hands him the depositary's certificate."),
            ("Fonds déposés dès la souscription, bloqués jusqu'à l'immatriculation [[source:ohada-auscgie]] ; côté "
             "dépôt, un prélèvement [[syscohada:104]] (1042).", "Funds deposited on subscription, blocked until "
             "registration; for the depot, drawings 1042."),
            ("Pourquoi un prélèvement et pas une dépense ? L'argent du dépôt est celui de Paul : il le reprend pour "
             "l'apporter, en son nom, à la société. La SARL est une autre personne, qui ne naît qu'à l'immatriculation.",
             "Why drawings and not a payment? The depot's money is Paul's: he takes it back to contribute it, in his "
             "own name, to the company, a separate person born at registration."),
            ("La banque du dépôt baisse ; le capital de la SARL est en route.", "The depot's bank falls; the LLC's "
             "capital is on its way."),
            [ASSETS_COURSE, ("compta", 15, "Les opérations de financement", "Financing operations")], STORE["sarl"]))
        out.append(scene(
            tri["date"], m["tricycle"], ("le tricycle", "the tricycle"),
            (f"Pour livrer l'hôtel en 2027, Paul achète un tricycle à benne chez Moto Plus : {fcfa(total(tri, 'Net'))} "
             "TVA comprise, à son nom, payé depuis le compte du dépôt.",
             f"To deliver the hotel in 2027 Paul buys a box tricycle at Moto Plus: {fcfa(total(tri, 'Net'), 'en')} "
             "VAT included, in his own name, paid from the depot account."),
            ("Achat personnel : prélèvement [[syscohada:104]] (1042) ; il entrera dans la SARL comme apport en nature "
             "[[syscohada:2458]].", "Personal purchase: drawings 1042; it will enter the LLC as a contribution in kind "
             "(2458)."),
            ("Pourquoi ne pas l'acheter au nom du dépôt ? Au SMT, le dépôt ne suit pas ses immobilisations, et il cesse "
             "dans un mois ; acheté par Paul puis apporté, le tricycle entre dans la SARL à une valeur fixée aux statuts. "
             "La TVA payée ne se récupère pas : ni Paul ni le dépôt à l'IGS n'y ont droit.",
             "Why not buy it in the depot's name? The cash-basis depot does not track fixed assets and ceases in a "
             "month; bought by Paul then contributed, the tricycle enters the LLC at a value set in the articles. "
             "The VAT paid is not recoverable."),
            ("La banque du dépôt baisse encore ; Paul détient un bien qu'il apportera.", "The depot's bank falls again; "
             "Paul holds an asset he will contribute."),
            [("compta", 13, "Les immobilisations", "Fixed assets")], STORE["sarl"]))
    if month == 12:
        sta, nota = piece[m["statuts"]], piece[m["notary"]]
        out.append(scene(
            sta["date"], m["statuts"], ("les statuts", "the articles"),
            ("Chez Maître Ngo Bassa, Paul signe les statuts d'Essomba Boissons SARL : il apporte le stock de casiers qu'il "
             f"aura au 31 décembre, au coût moyen de l'année, son tricycle et le numéraire déjà déposé. Capital : "
             f"{fcfa(total(sta, 'Capital'))}.",
             "At Maître Ngo Bassa's office, Paul signs the articles of Essomba Boissons SARL: he contributes the crates "
             "he will hold on 31 December, at the year's average cost, his tricycle and the cash already deposited. "
             f"Capital: {fcfa(total(sta, 'Capital'), 'en')}."),
            ("Évaluation de chaque apport en nature ; commissaire aux apports au-delà de 5 millions "
             "[[source:ohada-auscgie]] ; acte notarié au-delà d'un million de capital [[source:loi-2016-014]] ; au "
             "1er janvier 2027, capital [[syscohada:1013]] face au stock [[syscohada:311]], au tricycle "
             "[[syscohada:2458]] et à la banque [[syscohada:521]].",
             "Each contribution in kind is valued; an auditor is needed above 5 million; a notarised deed above one "
             "million of capital; on 1 January 2027, capital 1013 against stock 311, tricycle 2458 and bank 521."),
            ("Pourquoi une SARL unipersonnelle plutôt qu'une société à plusieurs ? Paul reste seul maître de son "
             "affaire, mais son patrimoine personnel est désormais séparé : il ne risque plus que ses apports.",
             "Why a single-member LLC? Paul stays sole master of his business, but his personal assets are now "
             "ring-fenced: he risks only his contributions."),
            ("Aucune écriture au dépôt : l'apport prend effet le 1er janvier ; la SARL ouvrira son bilan ce jour-là.",
             "No entry for the depot: the contribution takes effect on 1 January, when the LLC opens its balance sheet."),
            [ASSETS_COURSE, ("compta", 25, "Clôture, réouverture et affectation du résultat",
                             "Closing, reopening and appropriation")], STORE["sarl"]))
        out.append(scene(
            nota["date"], m["notary"], ("la facture du notaire", "the notary's invoice"),
            (f"Le notaire facture ses honoraires et les droits d'enregistrement qu'il reverse au Trésor : "
             f"{fcfa(total(nota, 'Net'))}, que Paul avance depuis le compte du dépôt.",
             f"The notary bills fees and the registration duty he pays over to the Treasury: "
             f"{fcfa(total(nota, 'Net'), 'en')}, advanced by Paul from the depot account."),
            ("Droits dégressifs de 2 % du capital [[cgi:art. 346]] [[cgi:art. 544]] ; pour le dépôt, un prélèvement ; "
             "au 1er janvier, la SARL reprend la facture : honoraires [[syscohada:6324]], droits [[syscohada:6468]], "
             "TVA récupérable [[syscohada:4454]], dette envers Paul [[syscohada:4621]].",
             "2% degressive duty on the capital; for the depot, drawings; on 1 January the LLC takes over the invoice: "
             "fees 6324, duty 6468, recoverable VAT 4454, debt to Paul 4621."),
            ("Pourquoi en charges et non en frais d'établissement ? Le SYSCOHADA révisé a supprimé l'immobilisation des "
             "frais de constitution : ils sont des charges de la SARL, par nature.",
             "Why expenses and not set-up costs? Revised SYSCOHADA no longer capitalises formation costs: they are the "
             "LLC's expenses, by nature."),
            ("La SARL commence 2027 avec une dette envers son associé et de la TVA à récupérer.", "The LLC starts 2027 "
             "owing its partner and with VAT to recover."),
            [("fisca", 5, "Enregistrement et timbre", "Registration and stamp duty"),
             ("compta", 4, "Charges et produits", "Expenses and income")], STORE["sarl"]))
    cash, orange, rent = piece[m["cash"]], piece[m["orange"]], piece[m["rent"]]
    out.append(scene(
        rent["date"], m["rent"], ("le loyer", "the rent"),
        (f"Paul remet à M. Kotto {fcfa(total(rent, 'Loyer'))} en espèces, sur la recette de la quinzaine.",
         f"Paul hands Mr Kotto {fcfa(total(rent, 'Loyer'), 'en')} in cash, out of the fortnight's takings."),
        ("Loyer [[syscohada:6222]] payé brut [[cgi:art. 87]].", "Rent 6222 paid gross."),
        ("Pourquoi pas de précompte de 10 % ? La retenue sur loyer vise les locataires au réel ; un locataire à l'IGS "
         "paie le loyer brut." if first else "Rappel : loyer brut, sans retenue, à l'IGS.",
         "Why no 10% withholding? It applies to tenants under the actual regime; an IGS tenant pays gross."
         if first else "Reminder: gross rent under the IGS."),
        ("Une dépense au cahier, payée en espèces.", "A cash payment in the book."),
        [("compta", 10, "Autres charges et autres produits", "Other expenses and income")], STORE["rent"]))
    out.append(scene(
        cash["date"], m["cash"], ("les ventes au comptant", "cash sales"),
        (f"Au comptoir, Paul et Brigitte ont vendu {qty(cash['payload']['lines'][0]['qty'])} casiers au comptant, "
         f"casier plein contre casier vide : {fcfa(total(cash, 'Recettes'))}.",
         f"At the counter Paul and Brigitte sold {qty(cash['payload']['lines'][0]['qty'], 'en')} crates for cash, full "
         f"against empty: {fcfa(total(cash, 'Recettes'), 'en')}."),
        ("Recettes [[syscohada:7011]] en caisse [[syscohada:5711]], sans TVA [[cgi:art. C 38]].",
         "Receipts 7011 in the till 5711, no VAT."),
        ("Pourquoi suivre le cumul chaque mois ? Au-delà de 50 millions dans l'année, le dépôt serait reclassé d'office "
         "au réel [[cgi:art. C 39]] : Paul garde un œil sur le seuil." if month in (1, 6, 9, 12) else
         "Le brouillard du soir fonde le cahier.",
         "Why track the running total? Above 50 million in the year, the depot would be moved to the actual regime."
         if month in (1, 6, 9, 12) else "The evening cash book backs the book."),
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
        (f"Les pousseurs du marché ont livré les clients : {qty(trip['payload']['lines'][0]['qty'])} courses à "
         "1 500 F.", f"The push-cart men delivered customers: {qty(trip['payload']['lines'][0]['qty'], 'en')} trips at "
         "1,500 F."),
        ("Transports sur ventes [[syscohada:612]], payés en espèces.", "Transport on sales 612, paid in cash."),
        ("Pourquoi 612 et pas un salaire ? Les pousseurs ne sont pas employés : ils sont payés à la course, comme un "
         "transporteur." if first else "Rappel : payés à la course.",
         "Why 612 and not wages? They are not employees: paid by the trip." if first else "Reminder: paid by the trip."),
        ("Une dépense de transport au cahier.", "A transport payment in the book."),
        [("compta", 10, "Autres charges et autres produits", "Other expenses and income")], STORE["transport"]))
    last_month = month == 12
    out.append(scene(
        dep["date"], m["deposits"], ("les versements à la banque", "the bank deposits"),
        (f"Le 15 et le dernier jour, Paul porte la recette à la banque : {fcfa(total(dep, 'Versement du 15'))} puis "
         f"{fcfa(total(dep, 'Versement de fin'))}. "
         + ("Le 31 décembre, la caisse est vidée : le dépôt cesse." if last_month else
            "La caisse garde 20 000 pour rendre la monnaie."),
         f"On the 15th and the last day Paul banks the takings: {fcfa(total(dep, 'Versement du 15'), 'en')} then "
         f"{fcfa(total(dep, 'Versement de fin'), 'en')}. "
         + ("On 31 December the till is emptied: the depot ceases." if last_month else "The till keeps 20,000 of float.")),
        ("[[syscohada:585]] au débit, [[syscohada:5711]] au crédit.", "585 debit, 5711 credit."),
        ("Pourquoi ne pas tout garder en caisse ? Un dépôt manipule beaucoup d'espèces : les verser limite le risque "
         "et laisse une trace à la banque." if first else
         ("Pourquoi vider la caisse ? L'Ets cesse ; la SARL aura sa propre caisse." if last_month else
          "Rappel : la caisse ne garde que son fonds."),
         "Why not keep it all in the till? Banking limits risk and leaves a trace." if first else
         ("Why empty the till? The business ceases; the LLC will have its own." if last_month else
          "Reminder: the till keeps only its float.")),
        ("La caisse est à zéro." if last_month else "La caisse revient à son fonds de 20 000.",
         "The till is at zero." if last_month else "The till is back to its 20,000 float."),
        [("compta", 12, "Les règlements", "Settlements")], STORE["deposits"]))
    end = datetime.date.fromisoformat(piece[m["bank"]]["date"])
    out.append(scene(
        piece[m["bank"]]["date"], m["bank"], ("le relevé bancaire", "the bank statement"),
        ("Le relevé reprend les versements, le transfert d'Orange Money, les virements à la brasserie et le virement de "
         "120 000 que Paul fait sur son compte personnel pour son ménage."
         + (" Le 31, Paul vire le solde sur son compte personnel et ferme le compte du dépôt." if last_month else ""),
         "The statement shows deposits, the Orange Money transfer, the brewery transfers and the 120,000 Paul moves to "
         "his personal account." + (" On the 31st Paul moves the balance to his personal account and closes the depot "
                                    "account." if last_month else "")),
        ("Virements internes [[syscohada:585]], prélèvement [[syscohada:104]] (1042), frais [[syscohada:631]].",
         "585, drawings 1042, fees 631."),
        ("Pourquoi le virement personnel n'est-il pas une dépense ? Paul se paie sur ce que le dépôt gagne ; ce qu'il "
         "prend est un prélèvement, qui réduit ses capitaux, pas le résultat." if first else
         ("Pourquoi solder le compte ? Le dépôt cesse au 31 décembre ; Paul garde ce solde pour payer l'IGS de 2026 "
          "avec la déclaration de clôture." if last_month else "Un écart s'explique avant de s'écrire."),
         "Why is the personal transfer not a payment of the business? It is drawings: it reduces equity, not profit."
         if first else ("Why settle the account? The depot ceases on 31 December; Paul keeps the balance to pay the "
                        "2026 IGS with the closing return." if last_month else "A gap is explained before it is booked.")),
        (f"Solde du 521 au {end.day} {mfr} : {fcfa(ledger.account_balance(book.entries, '521', end))}.",
         f"521 balance at {men} {end.day}: {fcfa(ledger.account_balance(book.entries, '521', end), 'en')}."),
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE["bank"]))
    return out


HOOKS = {1: ("Janvier 2026 : Paul Essomba ouvre son dépôt à Bépanda.", "January 2026: Paul Essomba opens his depot in "
             "Bépanda."),
         7: ("Juillet 2026 : la brasserie relève son prix ; Paul garde le sien.", "July 2026: the brewery raises its "
             "price; Paul keeps his."),
         9: ("Septembre 2026 : l'hôtel de Mme Eyango veut ses boissons pour 2027 ; Paul déclare la cessation de l'Ets.",
             "September 2026: Mrs Eyango's hotel wants its drinks for 2027; Paul gives notice of cessation."),
         11: ("Novembre 2026 : le capital de la SARL se prépare.", "November 2026: the LLC's capital is prepared."),
         12: ("Décembre 2026 : derniers casiers de l'Ets, statuts de la SARL.", "December 2026: the depot's last crates, "
              "the LLC's articles.")}


def month_section(month, scenes, opening, others, lang):
    default = (f"{MONTHS_FR[month - 1].capitalize()} 2026 : achats, ventes au casier et versements.",
               f"{MONTHS_EN[month - 1]} 2026: purchases, crate sales and deposits.")
    hook = HOOKS.get(month, default)[0 if lang == "fr" else 1]
    intro = (f"{hook} Lisez chaque scène, puis répondez aux questions du quiz [[cgi:art. C 38]].\n" if lang == "fr" else
             f"{hook} Read each scene, then answer the quiz [[cgi:art. C 38]].\n")
    nxt = ("la clôture de l'Ets et le bilan d'ouverture de la SARL" if month == 12 else f"les achats de {MONTHS_FR[month]}",
           "closing the business and the LLC's opening balance sheet" if month == 12 else f"{MONTHS_EN[month]}'s purchases")
    summary = (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- Recettes et dépenses portées au cahier, pièces classées, banque "
               f"et Orange Money rapprochées.\n- Aucune déclaration mensuelle : à l'IGS, tout se déclare une fois l'an.\n\n"
               f"Prochaine étape : {nxt[0]}.\n" if lang == "fr" else
               f"### {MONTHS_EN[month - 1]} in brief\n\n- Receipts and payments booked, documents filed, bank and Orange "
               f"Money reconciled.\n- No monthly return: under the IGS everything is filed once a year.\n\nNext: {nxt[1]}.\n")
    return assemble(intro, scenes, opening, others, summary, lang)


def cessation_section(special):
    ref = special["cessation"]
    fr = ("Fin septembre, Mme Eyango, économe d'un hôtel de Bonapriso, propose à Paul de livrer toutes ses boissons à "
          "partir de janvier 2027. Avec ce contrat, le dépôt ferait environ 75 millions de chiffre d'affaires : bien "
          "au-delà du seuil de 50 millions de l'IGS [[cgi:art. 93 quater]].\n\n"
          "Garder l'Ets, ce serait franchir le seuil en cours d'année 2027 et subir un reclassement d'office au réel "
          "[[cgi:art. C 39]]. Paul choisit une date nette : l'Ets cesse au 31 décembre 2026, et son fonds est apporté à "
          "une SARL qui démarre au réel le 1er janvier 2027. Pour une entreprise nouvelle, c'est le chiffre d'affaires "
          "prévisionnel qui fixe le régime.\n\n"
          "Toute cessation se déclare au moins trois mois avant sa date [[cgi:art. 95]] : pour le 31 décembre, au plus "
          "tard le 30 septembre. Paul la dépose le 25.\n\n"
          f"[[piece:{ref}]]\n\n"
          "> **Pourquoi ce choix et pas un autre.** Attendre janvier pour décider aurait été trop tard : la déclaration "
          "doit précéder la cessation de trois mois. Et la déclaration ouvre un contrôle de la situation fiscale de l'Ets "
          "[[cgi:art. 95 bis]] : mieux vaut un cahier du SMT bien tenu.\n\n"
          "**Ce que ça change.** Le dernier trimestre prépare la SARL ; l'Ets continue de vendre jusqu'au 31 décembre.\n")
    en = ("At the end of September, Mrs Eyango, bursar of a Bonapriso hotel, offers Paul to supply all its drinks from "
          "January 2027. With this contract the depot would turn over about 75 million: well above the 50 million IGS "
          "threshold [[cgi:art. 93 quater]].\n\nKeeping the sole proprietorship would mean crossing the threshold during "
          "2027 and a forced move to the actual regime [[cgi:art. C 39]]. Paul picks a clean date: the business ceases "
          "on 31 December 2026 and is contributed to an LLC trading under the actual regime from 1 January 2027.\n\n"
          "Any cessation is notified at least three months ahead [[cgi:art. 95]]: by 30 September for 31 December. "
          f"Paul files on the 25th.\n\n[[piece:{ref}]]\n\n"
          "> **Why this choice and not another.** Waiting until January would be too late. The notice also opens a review "
          "of the business's tax position [[cgi:art. 95 bis]].\n\n**What it changes.** The last quarter prepares the "
          "LLC; the depot keeps selling until 31 December.\n")
    return {"fr": typeset_fr(fr), "en": en}


def sarl_procedures_section(special):
    refs = "\n\n".join(f"[[piece:{ref}]]" for ref in special["sarl_procedures"])
    fr = ("Quatre démarches font naître Essomba Boissons SARL, de novembre à la fin décembre : dépôt des fonds en compte "
          "bloqué [[source:ohada-auscgie]], statuts notariés et enregistrés [[source:loi-2016-014]] [[cgi:art. 544]], "
          "immatriculation au CFCE [[source:minfi-cfce]], rattachement au CIME [[source:dgi-cime]]. Chacune précise "
          f"l'organisme, les documents à fournir et ce que l'on obtient.\n\n{refs}\n")
    en = ("Four procedures bring Essomba Boissons SARL to life, from November to late December: blocked deposit of the "
          "funds [[source:ohada-auscgie]], notarised and registered articles [[source:loi-2016-014]] [[cgi:art. 544]], "
          "registration at the CFCE [[source:minfi-cfce]], attachment to the CIME [[source:dgi-cime]].\n\n"
          f"{refs}\n")
    return {"fr": typeset_fr(fr), "en": en}


def _opening_table(book, lang):
    """Bilan d'ouverture de la SARL, lu sur les écritures du 1er janvier 2027 qui portent les apports (statuts)."""
    statuts = next(p["ref"] for p in book.pieces if p["kind"] == "statuts")
    lines = [l for e in book.entries if e["date"] == "2027-01-01" and e["piece"] == statuts for l in e["lines"]]
    labels = {"311": ("Stock de marchandises", "Goods in stock"), "2458": ("Tricycle de livraison", "Delivery tricycle"),
              "521": ("Banque", "Bank"), "1013": ("Capital social", "Share capital")}
    i = 0 if lang == "fr" else 1
    actif = [(l["account"], labels[l["account"]][i], l["amount"]) for l in lines if l["side"] == "debit"]
    passif = [(l["account"], labels[l["account"]][i], l["amount"]) for l in lines if l["side"] == "credit"]
    head = ("| Actif | Montant | Passif | Montant |\n|---|---:|---|---:|\n" if lang == "fr" else
            "| Assets | Amount | Equity and liabilities | Amount |\n|---|---:|---|---:|\n")
    rows = []
    for k in range(max(len(actif), len(passif))):
        a = actif[k] if k < len(actif) else None
        p = passif[k] if k < len(passif) else None
        rows.append(f"| {f'{a[1]} ({a[0]})' if a else ''} | {fcfa(a[2], lang) if a else ''} | "
                    f"{f'{p[1]} ({p[0]})' if p else ''} | {fcfa(p[2], lang) if p else ''} |")
    total_ = sum(a[2] for a in actif)
    assert total_ == sum(p[2] for p in passif), "bilan d'ouverture déséquilibré"
    rows.append(f"| **Total** | **{fcfa(total_, lang)}** | **Total** | **{fcfa(total_, lang)}** |")
    return head + "\n".join(rows) + "\n"


def year_end_sections(book, special):
    piece = {p["ref"]: p for p in book.pieces}
    count = scene(
        piece[special["sheet"]]["date"], special["sheet"], ("l'inventaire des casiers", "the crate count"),
        ("Le 31 au soir, Paul et Brigitte comptent les casiers pleins : les 60 d'avance achetés en janvier sont "
         "toujours là, valorisés au coût moyen de l'année. Ce sont eux qui passent à la SARL.",
         "On the evening of the 31st Paul and Brigitte count the full crates: the 60 bought ahead in January are still "
         "there, valued at the year's average cost. They go to the LLC."),
        ("Au SMT, pas d'écriture d'inventaire ; le stock final corrige le résultat de la DSF du SMT "
         "[[source:ohada-audcif]] et fixe la valeur de l'apport.", "Under the cash basis there is no inventory entry; "
         "closing stock adjusts the cash-basis return and sets the contribution value."),
        ("Pourquoi le CMUP sur les prix HT de la brasserie ? C'est la référence de la fiche de stock, reprise aux "
         "statuts ; le PEPS, en contraste, garde les derniers casiers, achetés plus cher.", "Why WAC on brewery HT "
         "prices? It is the stock card reference used in the articles; FIFO keeps the latest, dearer crates."),
        (f"Stock final : {fcfa(special['stock_value'])}.", f"Closing stock: {fcfa(special['stock_value'], 'en')}."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Fiche de stock signée, copie au classeur « SARL ».", "Signed stock card, copy in the LLC binder."))
    statuts = special["months"][12]["statuts"]
    opening_fr = (
        "### Vendredi 1er janvier 2027 : le bilan d'ouverture de la SARL\n\n"
        "Le dépôt a cessé la veille ; Essomba Boissons SARL commence. Son premier état est le bilan d'ouverture, lu sur "
        f"les statuts [[piece:{statuts}]] : chaque apport devient un actif, leur somme est le capital "
        "[[syscohada:1013]].\n\n" + _opening_table(book, "fr") +
        "\nLe même jour, la SARL reprend la facture du notaire, avancée par Paul : honoraires [[syscohada:6324]] et "
        "droits [[syscohada:6468]] en charges, TVA récupérable [[syscohada:4454]], dette envers l'associé "
        "[[syscohada:4621]]. Ce sont ses premières opérations, après le bilan d'ouverture.\n\n"
        "> **Pourquoi ce choix et pas un autre.** Le bilan d'ouverture d'une société nouvelle ne contient que ses "
        "apports ; les frais de constitution sont déjà une charge de son premier exercice, jamais un actif.\n")
    opening_en = (
        "### Friday 1 January 2027: the LLC's opening balance sheet\n\nThe depot ceased the day before; Essomba Boissons "
        f"SARL begins. Its first statement is the opening balance sheet, read from the articles [[piece:{statuts}]]: each "
        "contribution becomes an asset, their sum is the capital [[syscohada:1013]].\n\n" + _opening_table(book, "en") +
        "\nThe same day the LLC takes over the notary's invoice advanced by Paul: fees [[syscohada:6324]] and duty "
        "[[syscohada:6468]] as expenses, recoverable VAT [[syscohada:4454]], debt to the partner [[syscohada:4621]].\n")
    smt_close_fr = ("Le 31 décembre, l'Ets ferme : caisse vidée, Orange Money transféré, compte bancaire soldé au profit "
                    "de Paul [[syscohada:5711]] [[syscohada:521]]. Le bilan du SMT ne garde que le stock, qui part à la "
                    "SARL le lendemain.\n\n")
    smt_close_en = ("On 31 December the business closes: till emptied, Orange Money transferred, bank account settled to "
                    "Paul [[syscohada:5711]] [[syscohada:521]]. The cash-basis balance sheet keeps only the stock, which "
                    "goes to the LLC the next day.\n\n")
    close = {"fr": smt_close_fr + count["fr"] + "\n[[calc:stock]]\n\n" + opening_fr,
             "en": smt_close_en + count["en"] + "\n[[calc:stock]]\n\n" + opening_en}
    art74, closing = piece[special["art74"]], piece[special["closing_return"]]
    s1 = scene(
        art74["date"], special["art74"], ("la déclaration de revenus", "the income return"),
        (f"Avant le 15 mars, Paul dépose sa déclaration annuelle de revenus : {fcfa(special['turnover'])} de chiffre "
         "d'affaires, sous l'IGS.", f"Before 15 March Paul files his yearly income return: "
         f"{fcfa(special['turnover'], 'en')} of turnover, under the IGS."),
        ("Une personne physique à l'IGS reste tenue à la déclaration annuelle de l'art. 74 [[cgi:art. C 39]] "
         "[[cgi:art. 74]].", "An individual under the IGS still files the art. 74 yearly return."),
        ("Pourquoi déclarer si l'IGS libère de l'IRPP ? L'administration recoupe les revenus de chaque personne ; la "
         "déclaration n'ajoute pas d'impôt sur le dépôt.", "Why file if the IGS discharges income tax? The tax office "
         "cross-checks each person's income."),
        ("Aucun paiement à cette date.", "No payment at this date."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")],
        ("Accusé de réception au dossier permanent.", "Acknowledgement in the permanent file."))
    s2 = scene(
        closing["date"], special["closing_return"], ("la déclaration de clôture", "the closing return"),
        (f"Trois mois après la cessation au plus tard, Paul dépose la déclaration de clôture de l'Ets : chiffre "
         f"d'affaires, stock apporté, cessionnaire. Il paie avec elle l'IGS de la classe 10, {fcfa(special['igs'])}, "
         "sur le solde gardé au 31 décembre.",
         f"Within three months of cessation Paul files the closing return: turnover, stock transferred, transferee. He "
         f"pays the class 10 IGS with it, {fcfa(special['igs'], 'en')}, out of the balance kept on 31 December."),
        ("Déclaration de clôture dans les trois mois [[cgi:art. 95]], accompagnée du paiement des droits "
         "[[cgi:art. 96]] ; tarif par classe [[cgi:art. C 40]].", "Closing return within three months, with payment; "
         "tariff by class."),
        (f"Pourquoi payer dès mars et non au 15 avril ? La cessation avance l'échéance : la clôture liquide tout ce que "
         f"l'Ets doit. Adhérent d'un Centre de Gestion Agréé, Paul n'aurait payé que {fcfa(special['igs_cga'])}.",
         f"Why pay in March, not by 15 April? Cessation brings the deadline forward. As a management-centre member he "
         f"would have paid {fcfa(special['igs_cga'], 'en')}."),
        ("L'Ets n'a plus d'obligation ; la SARL suit le réel au CIME.", "The business has no obligation left; the LLC "
         "follows the actual regime at the CIME."),
        [("fisca", 7, "Obligations déclaratives et contrôle", "Filing obligations and audits"), IGS_COURSE],
        ("Déclaration et quittance au dossier permanent de l'Ets, conservé dix ans.", "Return and receipt in the "
         "business's permanent file, kept ten years."))
    refs = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces if p.get("dsf"))
    smt_fr = ("### Avec la clôture : la DSF du SMT\n\nAvec plus de 10 millions de chiffre d'affaires, l'Ets dépose la "
              "DSF du SMT [[cgi:art. C 44]] : un bilan et un compte de résultat établis à partir de la trésorerie, "
              "corrigés du stock final [[source:ohada-audcif]]. Le 15 mai reste la limite ; Paul la joint à la "
              f"clôture.\n\n{refs}\n\n**Où ça se range.** Dossier permanent de l'Ets ; conservation dix ans.\n")
    smt_en = ("### With the closing return: the cash-basis return\n\nWith more than 10 million of turnover, the business "
              "files the cash-basis return [[cgi:art. C 44]]: a balance sheet and an income statement drawn from cash, "
              f"adjusted for closing stock. Paul files it with the closing return.\n\n{refs}\n\n**Where it is filed.** "
              "The business's permanent file; kept ten years.\n")
    next_fr = ("### Et la SARL ?\n\nDès février 2027, Essomba Boissons SARL dépose ses déclarations mensuelles au CIME "
               "de Douala : TVA collectée sur l'hôtel, TVA déductible (dont celle du notaire), acompte d'impôt, précompte "
               "de 2 % sur ses achats [[cgi:art. 21]]. C'est le parcours B3, au réel, qui en montre le détail.\n")
    next_en = ("### And the LLC?\n\nFrom February 2027, Essomba Boissons SARL files monthly returns at the Douala CIME: "
               "VAT on the hotel's purchases, deductible VAT (the notary's included), tax instalment, 2% withholding on "
               "its purchases [[cgi:art. 21]]. Track B3, under the actual regime, shows the detail.\n")
    returns = {"fr": "Deux échéances pour l'Ets en 2027, la seconde avancée par la cessation [[cgi:art. 95]].\n\n"
                     + s1["fr"] + "\n" + s2["fr"] + "\n" + smt_fr + "\n" + next_fr,
               "en": "Two deadlines for the business in 2027, the second brought forward by cessation [[cgi:art. 95]].\n\n"
                     + s1["en"] + "\n" + s2["en"] + "\n" + smt_en + "\n" + next_en}
    result = {}
    for key, value in (("close", close), ("returns", returns)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    return result
