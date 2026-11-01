"""Récit du parcours B3 (S34, docs/form3-conception.md, section 5) : une scène par pièce, en cinq temps.

Chaque scène dit ce qui se passe, la règle et sa source, pourquoi ce choix plutôt qu'un autre, ce que ça change, puis
renvoie au module du cours. Tous les montants sont lus sur les pièces générées : le récit ne contredit jamais le livre.
Janvier (pilote), puis, à la demande de l'utilisateur du 2026-11-01, février à décembre, inventaire, passerelle et DSF.
"""
import datetime
import re

# Typographie française : espace fine insécable avant ; : ? ! pour qu'aucun signe ne commence une ligne.
FRENCH_SPACE = re.compile(r" ([;:?!])")


def typeset_fr(text):
    return FRENCH_SPACE.sub(" \\1", text)

DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FIGURE = "/static/content/simulation/b3/{name}.{lang}.svg"
# Renvois au cours (numérotation continue de la plateforme, US-22) : (formation, numéro, titre FR, titre EN).
COURSE = {
    "compta": ("Comptabilité", "Accounting"),
    "fisca": ("Fiscalité", "Taxation"),
}

CAST_FR = (
    "### Les personnages\n\n"
    "| Personnage | Rôle |\n|---|---|\n"
    "| Rose Ateba | Associée majoritaire, ancienne revendeuse de boissons au marché Mvog-Mbi |\n"
    "| Serge Mballa | Gérant salarié : achats, banque, déclarations |\n"
    "| Didier | Magasinier : réception, vides, comptage |\n"
    "| Paul | Chauffeur-livreur, recruté dès janvier ; il prend le volant du camion en février |\n"
    "| Mme Ngah | Propriétaire du Snack-Bar Le Rond-Point, cliente à crédit |\n"
    "| M. Fouda | Commercial des Brasseries de la Sanaga |\n\n"
    "Tous sont fictifs, comme les entreprises et les montants.\n")
CAST_EN = (
    "### The people\n\n"
    "| Person | Role |\n|---|---|\n"
    "| Rose Ateba | Majority partner, former drinks seller at Mvog-Mbi market |\n"
    "| Serge Mballa | Salaried manager: purchasing, bank, tax returns |\n"
    "| Didier | Storekeeper: receiving, empties, counting |\n"
    "| Paul | Delivery driver, hired in January; he takes the wheel of the truck in February |\n"
    "| Mrs Ngah | Owner of the Le Rond-Point snack bar, a credit customer |\n"
    "| Mr Fouda | Sales rep of the Sanaga breweries |\n\n"
    "All are fictitious, like the companies and the amounts.\n")


MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
             "novembre", "décembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
NBSP, THIN = " ", " "  # le montant et son unité, et les milliers, ne se séparent jamais en fin de ligne


def fcfa(value, lang="fr"):
    text = f"{int(value):,}"
    return text.replace(",", THIN) + f"{NBSP}FCFA" if lang == "fr" else text + f"{NBSP}FCFA"


def qty(value, lang="fr"):
    text = f"{int(value):,}"
    return text.replace(",", THIN) if lang == "fr" else text


def total(piece, prefix, default=None):
    """Montant d'une ligne de totaux dont le libellé FR commence par `prefix`."""
    return next((t["amount"] for t in piece["payload"]["totals"] if t["label"]["fr"].startswith(prefix)), default)


def day_title(date, title_fr, title_en):
    day = datetime.date.fromisoformat(date)
    year = f" {day.year}" if day.year != 2026 else ""  # l'exercice est 2026 ; l'année n'apparaît qu'au-delà
    return (f"{DAYS_FR[day.weekday()].capitalize()} {day.day} {MONTHS_FR[day.month - 1]}{year} : {title_fr}",
            f"{DAYS_EN[day.weekday()]} {day.day} {MONTHS_EN[day.month - 1]}{year}: {title_en}")


def revoir(refs):
    fr = " ; ".join(f"{COURSE[c][0]} M{n} « {t_fr} »" for c, n, t_fr, _t_en in refs)
    en = "; ".join(f"{COURSE[c][1]} M{n} “{t_en}”" for c, n, _t_fr, t_en in refs)
    return fr, en


def scene(date, ref, titles, story, rule, why, effect, refs, store, figure=None):
    """Une scène : {date, ref, fr, en} en Markdown ; la pièce apparaît dans la scène, au moment où elle naît. Le
    « pourquoi » est un encadré (blockquote) ; « Où ça se range » dit le classeur, le registre et le journal du
    logiciel où la pièce aboutit (AUDCIF art. 17 et 19)."""
    title_fr, title_en = day_title(date, *titles)
    see_fr, see_en = revoir(refs)
    image = {lang: f"\n\n![{figure[1 if lang == 'fr' else 2]}]({FIGURE.format(name=figure[0], lang=lang)})" if figure else ""
             for lang in ("fr", "en")}
    return {
        "date": date, "ref": ref,
        "fr": (f"### {title_fr}\n\n{story[0]}\n\n[[piece:{ref}]]{image['fr']}\n\n**La règle.** {rule[0]}\n\n"
               f"> **Pourquoi ce choix et pas un autre.** {why[0]}\n\n**Ce que ça change.** {effect[0]}\n\n"
               f"**Où ça se range.** {store[0]}\n\n**Revoir :** {see_fr}.\n"),
        "en": (f"### {title_en}\n\n{story[1]}\n\n[[piece:{ref}]]{image['en']}\n\n**The rule.** {rule[1]}\n\n"
               f"> **Why this choice and not another.** {why[1]}\n\n**What it changes.** {effect[1]}\n\n"
               f"**Where it is filed.** {store[1]}\n\n**See again:** {see_en}.\n"),
        "why": why,
    }


ROUTINES_FR = (
    "### Les outils et les routines du dépôt\n\n"
    "**Les outils.** Serge tient la comptabilité dans un logiciel comptable (Sage 100 Comptabilité, Odoo ou tout "
    "autre logiciel qui respecte l'AUDCIF) ; un journal tenu sur registre papier serait aussi régulier. Le logiciel "
    "doit valider chaque écriture et clôturer les périodes, sans retour possible [[source:ohada-audcif]].\n\n"
    "| Support | Ce qu'il contient | Qui le tient |\n|---|---|---|\n"
    "| Dossier permanent | Statuts, déclaration notariée, attestation de dépôt du capital, bail, RCCM, carte de "
    "contribuable | Serge |\n"
    "| Classeurs Achats, Ventes, Banque et Mobile Money, Caisse, Paie, Immobilisations | Les pièces de l'exercice, "
    "dans l'ordre chronologique, chacune annotée du code du journal et du numéro d'écriture | Serge |\n"
    "| Brouillard de caisse (cahier) | Les entrées et sorties d'espèces du jour, signées le soir | Didier |\n"
    "| Fiche de stock | Les casiers pleins entrés et sortis, par format | Didier |\n"
    "| Cahier des vides | Les casiers consignés à chaque client et ceux qu'il a rendus | Didier |\n\n"
    "Journaux du logiciel : achats (AC), ventes (VT), banque (BQ), caisse (CA), Orange Money (OM), opérations "
    "diverses (OD).\n\n"
    "**Les routines.**\n\n"
    "- *Chaque soir* : Didier arrête la caisse, compte les vides et met à jour la fiche de stock ; Serge et lui "
    "signent le brouillard.\n"
    "- *Chaque semaine* : la recette part à la banque ; Serge saisit les pièces de la semaine et les classe.\n"
    "- *Chaque mois* : rapprochement de la banque et d'Orange Money, balance, centralisation des journaux, "
    "déclaration du 15 [[cgi:art. 21]].\n"
    "- *Chaque trimestre* : clôture des périodes dans le logiciel.\n"
    "- *Chaque année* : inventaire physique, livre d'inventaire, états financiers et DSF ; les livres et les pièces "
    "se conservent dix ans.\n")
ROUTINES_EN = (
    "### The depot's tools and routines\n\n"
    "**Tools.** Serge keeps the books in accounting software (Sage 100 Comptabilité, Odoo or any software that "
    "complies with the AUDCIF); a paper journal would be lawful too. The software must validate each entry and close "
    "periods irreversibly [[source:ohada-audcif]].\n\n"
    "| Support | Contents | Kept by |\n|---|---|---|\n"
    "| Permanent file | Articles, notarised declaration, capital certificate, lease, trade register, taxpayer card | "
    "Serge |\n"
    "| Purchases, Sales, Bank and Mobile Money, Cash, Payroll, Fixed-asset binders | The year's documents, in date "
    "order, each marked with its journal code and entry number | Serge |\n"
    "| Cash book (notebook) | The day's cash in and out, signed every evening | Didier |\n"
    "| Stock card | Full crates in and out, by format | Didier |\n"
    "| Empties book | Crates on deposit with each customer and those returned | Didier |\n\n"
    "Software journals: purchases (AC), sales (VT), bank (BQ), cash (CA), Orange Money (OM), miscellaneous (OD).\n\n"
    "**Routines.**\n\n"
    "- *Every evening*: Didier closes the till, counts the empties and updates the stock card; he and Serge sign "
    "the cash book.\n"
    "- *Every week*: takings go to the bank; Serge records and files the week's documents.\n"
    "- *Every month*: bank and Orange Money reconciliations, trial balance, journal centralisation, 15th return.\n"
    "- *Every quarter*: periods are closed in the software.\n"
    "- *Every year*: physical count, inventory book, financial statements and tax return; books and documents are "
    "kept for ten years.\n")


# « Où ça se range » de chaque scène de janvier, dans l'ordre des scènes (AUDCIF art. 17 et 19 : pièces datées,
# classées et annotées de leur référence d'enregistrement ; journaux auxiliaires centralisés chaque mois).
STORE = [
    ("Au dossier permanent, avec les statuts et la déclaration notariée : il se garde toute la vie de la société. "
     "Écriture au journal de banque (BQ).",
     "In the permanent file, with the articles and the notarised declaration, kept for the company's whole life. "
     "Entry in the bank journal (BQ)."),
    ("Quittance au classeur Banque et Mobile Money, avec l'ordre de virement ; le bail original va au dossier "
     "permanent. Écriture au journal de banque (BQ) ; Serge note la retenue pour la déclaration du 15.",
     "Receipt in the Bank and Mobile Money binder with the transfer order; the original lease goes to the permanent "
     "file. Entry in the bank journal (BQ); Serge notes the withholding for the 15th return."),
    ("Facture au dossier permanent, car elle prouve les frais de création. Écriture au journal des achats (AC).",
     "Invoice in the permanent file, as proof of the set-up costs. Entry in the purchases journal (AC)."),
    ("Facture au classeur Achats, agrafée aux bons de livraison signés par Didier ; les mêmes bons alimentent "
     "chaque soir la fiche de stock. Écriture au journal des achats (AC), le jour de réception de la facture.",
     "Invoice in the Purchases binder, stapled to the delivery notes signed by Didier; the same notes feed the stock "
     "card every evening. Entry in the purchases journal (AC) on the day the invoice arrives."),
    ("Facture au classeur Immobilisations, copie au dossier permanent ; les casiers entrent au tableau des "
     "immobilisations du logiciel. Écriture au journal des achats (AC).",
     "Invoice in the Fixed-asset binder, copy in the permanent file; the crates join the software's asset register. "
     "Entry in the purchases journal (AC)."),
    ("Double de la facture au classeur Ventes, dans l'ordre des numéros, sans trou ; Didier inscrit les casiers "
     "consignés au cahier des vides, à la ligne de Mme Ngah. Écriture au journal des ventes (VT).",
     "Copy of the invoice in the Sales binder, in number order with no gaps; Didier enters the deposited crates in "
     "the empties book under Mrs Ngah. Entry in the sales journal (VT)."),
    ("Chaque soir, Didier compte les espèces et les inscrit au brouillard de caisse, qu'il signe avec Serge ; le "
     "récapitulatif du mois va au classeur Caisse. Écriture au journal de caisse (CA).",
     "Every evening Didier counts the cash and enters it in the cash book, signed with Serge; the monthly summary "
     "goes to the Cash binder. Entry in the cash journal (CA)."),
    ("Relevé téléchargé depuis l'espace marchand, imprimé et classé au classeur Banque et Mobile Money. Écriture au "
     "journal Orange Money (OM).",
     "Statement downloaded from the merchant area, printed and filed in the Bank and Mobile Money binder. Entry in "
     "the Orange Money journal (OM)."),
    ("Bulletins signés au classeur Paie, un double remis à chaque salarié. Écriture au journal des opérations "
     "diverses (OD).",
     "Signed payslips in the Payroll binder, a copy handed to each employee. Entry in the miscellaneous journal "
     "(OD)."),
    ("Bordereaux tamponnés par la banque, agrafés au brouillard de caisse dans le classeur Caisse. Écriture au "
     "journal de caisse (CA).",
     "Slips stamped by the bank, stapled to the cash book in the Cash binder. Entry in the cash journal (CA)."),
    ("Relevé au classeur Banque et Mobile Money, avec l'état de rapprochement signé par Serge. Écritures au journal de "
     "banque (BQ), puis rapprochement dans le logiciel avant de clôturer le mois.",
     "Statement in the Bank and Mobile Money binder, with the reconciliation signed by Serge. Entries in the bank "
     "journal (BQ), then reconciliation in the software before closing the month."),
]


def january(book, special):
    """Les scènes de janvier 2026, dans l'ordre du calendrier (pilote S34)."""
    piece = {p["ref"]: p for p in book.pieces}
    m = special["months"][1]
    capital = total(piece[special["capital"]], "Capital")
    rent = piece[m["rent"]]
    notary = piece[special["notary"]]
    purchase = piece[m["purchase"]]
    crates = piece[special["crates"]]
    sale = piece[m["sale"]]
    cash = piece[m["cash"]]
    orange = piece[m["orange"]]
    payroll = piece[m["payroll"]]
    deposit = piece[m["cash_out"]]
    bank = piece[m["bank"]]
    delivered = sum(line["qty"] for line in purchase["payload"]["lines"])
    to_ngah = sum(line["qty"] for line in sale["payload"]["lines"])
    return [
        scene(special_date(piece, special["capital"]), special["capital"],
              ("le capital à la banque", "the capital goes to the bank"),
              (f"Rose Ateba et son associé versent {fcfa(capital)} à la Banque X, sur un compte ouvert au nom de la "
               "société en formation. Le notaire constate ce dépôt dans une déclaration de souscription et de versement, "
               "et les fonds restent bloqués jusqu'à l'immatriculation au registre du commerce [[source:ohada-auscgie]].",
               f"Rose Ateba and her partner pay {fcfa(capital, 'en')} to Bank X, into an account in the name of the "
               "company being formed. The notary records the deposit in a declaration of subscription and payment, and "
               "the funds stay blocked until the company is entered in the trade register."),
              ("Le capital souscrit, appelé et versé va au crédit de [[syscohada:1013]] ; la banque [[syscohada:521]] est "
               "débitée.", "Subscribed, called and paid-up capital is credited to 1013; the bank 521 is debited."),
              ("Un débutant y voit une « recette » : ce n'est pas un produit, l'entreprise n'a rien vendu. Ce n'est pas "
               "non plus une dette envers Rose ([[syscohada:4621]]) : le capital reste dans la société et se rémunère "
               "par les dividendes, pas par un remboursement.",
               "A beginner sees “income”: it is not revenue, nothing was sold. Nor is it a debt to Rose (4621): capital "
               "stays in the company and is rewarded by dividends, not repaid."),
              (f"La banque passe à {fcfa(capital)}, disponibles dès l'immatriculation ; le résultat ne bouge pas.",
               f"The bank shows {fcfa(capital, 'en')}, available once the company is registered; profit does not change."),
              [("compta", 3, "Actif et passif", "Assets and liabilities")], STORE[0]),
        scene(rent["date"], m["rent"], ("le loyer de l'entrepôt", "the warehouse rent"),
              (f"Le dépôt s'installe dans un entrepôt loué à Mvog-Ada. Serge paie le loyer de {fcfa(RENT_OF(rent))}, "
               f"mais ne verse à Mme Owona que {fcfa(total(rent, 'Net'))} : il garde le reste pour les impôts.",
               f"The depot moves into a rented warehouse in Mvog-Ada. Serge pays the {fcfa(RENT_OF(rent), 'en')} rent "
               f"but hands Mrs Owona only {fcfa(total(rent, 'Net'), 'en')}: he keeps the rest for the tax office."),
              ("Le locataire au réel retient un précompte sur loyer [[cgi:art. 87]] et le reverse le 15 du mois suivant : "
               "loyer brut en [[syscohada:6222]], retenue en [[syscohada:4478]].",
               "A tenant under the actual regime withholds tax on rent (art. 87) and pays it over by the 15th: gross "
               "rent in 6222, withholding in 4478."),
              ("Passer seulement le net en charge serait faux : la charge est le loyer brut, et la retenue est une dette "
               "envers l'État, pas une économie.",
               "Booking only the net is wrong: the expense is the gross rent, and the withholding is a debt to the "
               "State, not a saving."),
              (f"{fcfa(total(rent, 'Précompte'))} entrent dans la déclaration du 15 février.",
               f"{fcfa(total(rent, 'Précompte'), 'en')} go into the 15 February return."),
              [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")], STORE[1]),
        scene(notary["date"], special["notary"], ("les statuts chez le notaire", "the articles at the notary's"),
              ("Avec dix millions de capital, la SARL dépasse le seuil d'un million : ses statuts passent chez le notaire "
               "[[source:loi-2016-014]]. La société est immatriculée, les fonds sont débloqués : Serge règle la facture de "
               "Maître Abena, honoraires, TVA et droits d'enregistrement avancés par le notaire.",
               "With ten million of capital the LLC is above the one-million threshold, so a notary drafts its "
               "articles. The company is now registered and the funds released: Serge pays Maître Abena's invoice for "
               "fees, VAT and the registration duties he advanced."),
              ("Honoraires en [[syscohada:6324]], droits d'enregistrement en [[syscohada:646]], TVA récupérable sur "
               "services en [[syscohada:4454]].",
               "Fees in 6324, registration duties in 646, recoverable VAT on services in 4454."),
              ("Le réflexe hérité est de les immobiliser en « frais d'établissement ». Le SYSCOHADA révisé a supprimé ce "
               "poste : ce sont des charges de l'exercice, par nature.",
               "The old reflex is to capitalise them as formation expenses. Revised SYSCOHADA removed that line: they are "
               "expenses of the year, by nature."),
              ("Le premier exercice commence par une charge ; la TVA des honoraires viendra en déduction le 15 février.",
               "The first year starts with an expense; the VAT on fees is deducted on 15 February."),
              [("compta", 1, "Le cadre comptable OHADA", "The OHADA accounting framework")], STORE[2]),
        scene(purchase["date"], m["purchase"], ("la facture du stock de départ", "the opening-stock invoice"),
              (f"Depuis le 2, les camions de la brasserie font plusieurs tournées par jour pour remplir l'entrepôt : "
               f"{qty(delivered)} casiers pleins en tout. Didier compte chaque chargement et signe les bons de livraison ; "
               "M. Fouda les récapitule le 5 sur une seule facture. Bouteilles et casiers restent la propriété de la "
               "brasserie, qui les facture en consigne.",
               f"Since the 2nd, the brewery's trucks have made several runs a day to fill the warehouse: "
               f"{qty(delivered, 'en')} full crates in all. Didier counts each load and signs the delivery notes; Mr "
               "Fouda sums them up on one invoice on the 5th. Bottles and crates still belong to the brewery, which "
               "charges a deposit on them."),
              ("Achats de marchandises en [[syscohada:6011]], accises comprises [[cgi:art. 142]] ; TVA en "
               "[[syscohada:4452]] ; précompte en [[syscohada:4492]] [[cgi:art. 21]] ; consigne en [[syscohada:4094]] "
               "[[guide:1re partie, ch. 2]].",
               "Purchases in 6011, excise included; VAT in 4452; withholding in 4492; deposit in 4094."),
              ("Trois pièges. Les accises n'ont pas de compte à elles chez le dépôt : la brasserie paie le droit de 25 % "
               "et le droit spécifique additionnel (75 par bouteille de 65 cl), et les comprend dans son prix ; la "
               "facture ne montre que le second, pour information. "
               "La consigne n'est pas un achat : c'est une créance que la brasserie rendra au retour des vides. Le "
               "précompte n'est pas une charge : c'est une avance sur l'impôt, qui s'impute sur l'acompte d'IS.",
               "Three traps. Excise has no account of its own at the depot: the brewer pays the 25% duty and the "
               "additional specific duty (75 per 65 cl bottle) and includes both in its price; the invoice shows only "
               "the latter, for information. The deposit is "
               "not a purchase: it is a receivable refunded when the empties go back. The withholding is not an "
               "expense: it is an advance on tax, credited against the CIT instalment."),
              (f"La dette envers la brasserie atteint {fcfa(total(purchase, 'Net'))}, payable à la fin du mois suivant ; "
               f"{fcfa(total(purchase, 'Consigne'))} de consignes attendent le retour des vides.",
               f"The debt to the brewery is {fcfa(total(purchase, 'Net'), 'en')}, payable at the end of next month; "
               f"{fcfa(total(purchase, 'Consigne'), 'en')} of deposits wait for the empties."),
              [("compta", 6, "Les achats", "Purchases"), ("fisca", 4, "La TVA et les droits d'accises", "VAT and excise duties")], STORE[3],
              figure=("circuit-casiers", "Le circuit des casiers et des consignes", "The crate and deposit circuit")),
        scene(crates["date"], special["crates"], ("les casiers marqués Ateba", "crates marked Ateba"),
              (f"Pour ne pas dépendre des seuls casiers de la brasserie, Rose fait fabriquer {CRATES_OF(crates)} casiers "
               "vides marqués au nom du dépôt. Ils tourneront pendant des années entre l'entrepôt et les bars.",
               f"So as not to depend on the brewery's crates alone, Rose orders {CRATES_OF(crates)} empty crates marked "
               "with the depot's name. They will circulate for years between the warehouse and the bars."),
              ("Un emballage récupérable, identifiable et durable est une immobilisation : [[syscohada:243]], TVA sur "
               "immobilisations en [[syscohada:4451]], amortissement à l'inventaire.",
               "Returnable, identifiable, durable packaging is a fixed asset: 243, VAT on fixed assets 4451, "
               "depreciated at year end."),
              ("Pas [[syscohada:6082]] : ces casiers ne sont pas consommés dans l'année. Pas [[syscohada:2493]] non "
               "plus, malgré son libellé : c'est la ligne des immobilisations en cours, pas celle des casiers en service.",
               "Not 6082: these crates are not used up within the year. Not 2493 either, despite its label: that line is "
               "for assets in progress, not crates in service."),
              ("L'actif s'enrichit d'un million ; la charge viendra par l'amortissement, sur cinq ans.",
               "Assets grow by one million; the expense comes through depreciation over five years."),
              [("compta", 13, "Les immobilisations", "Fixed assets")], STORE[4]),
        scene(sale["date"], m["sale"], ("la commande du Rond-Point", "the Rond-Point order"),
              (f"Mme Ngah prépare la soirée de fin de mois de son snack-bar et commande {qty(to_ngah)} casiers, payables le 10 "
               "du mois suivant. Elle ne rapporte pas encore de vides : le dépôt lui facture une consigne par casier.",
               f"Mrs Ngah gets her snack bar ready for the month-end evening and orders {qty(to_ngah, "en")} crates, payable on the "
               "10th of next month. She has no empties yet, so the depot charges her a deposit per crate."),
              ("Vente en [[syscohada:7011]], TVA facturée en [[syscohada:4431]], client [[syscohada:411]] ; la consigne "
               "va en [[syscohada:4194]], hors de la base de la TVA pour un emballage identifiable [[cgi:art. 139]].",
               "Sale in 7011, VAT charged 4431, customer 411; the deposit goes to 4194, outside the VAT base for "
               "identifiable packaging (art. 139)."),
              ("La consigne n'est pas une vente : le dépôt devra la rendre quand les vides reviendront. La mettre en "
               "7011 gonflerait le chiffre d'affaires, l'acompte d'IS et la TVA.",
               "The deposit is not a sale: the depot must refund it when the empties come back. Booking it in 7011 would "
               "inflate turnover, the CIT instalment and VAT."),
              (f"Mme Ngah doit {fcfa(total(sale, 'Net'))}, dont {fcfa(total(sale, 'Consigne'))} de consigne.",
               f"Mrs Ngah owes {fcfa(total(sale, 'Net'), 'en')}, of which {fcfa(total(sale, 'Consigne'), 'en')} is deposit."),
              [("compta", 7, "Les ventes", "Sales")], STORE[5]),
        scene(cash["date"], m["cash"], ("la caisse du comptoir", "the counter till"),
              ("Tout le mois, les petits bars du quartier sont venus au comptoir, ont posé leurs vides et sont repartis "
               "avec des pleins, payés en espèces. Didier arrête la caisse le soir du 31.",
               "All month, local bars came to the counter, dropped their empties and left with full crates, paid in "
               "cash. Didier closes the till on the evening of the 31st."),
              ("Caisse [[syscohada:5711]] au TTC, ventes [[syscohada:7011]] au HT, TVA [[syscohada:4431]] [[cgi:art. 142]].",
               "Cash 5711 incl. tax, sales 7011 excl. tax, VAT 4431."),
              ("Pas de consigne ici : l'échange vide contre plein est immédiat, rien n'est dû de part et d'autre.",
               "No deposit here: empties are swapped for full crates on the spot, nothing is owed either way."),
              (f"{fcfa(total(cash, 'Ventes TTC'))} sont en caisse ; la TVA collectée s'ajoute à la déclaration du 15.",
               f"{fcfa(total(cash, 'Ventes TTC'), 'en')} are in the till; the VAT collected adds to the 15th return."),
              [("compta", 7, "Les ventes", "Sales")], STORE[6]),
        scene(orange["date"], m["orange"], ("le relevé Orange Money", "the Orange Money statement"),
              ("D'autres bars paient par Orange Money depuis leur téléphone. En fin de mois, l'opérateur envoie son "
               "relevé : encaissements, frais prélevés, puis le transfert du solde vers la banque.",
               "Other bars pay by Orange Money from their phones. At month end the operator sends its statement: "
               "receipts, fees deducted, then the balance transferred to the bank."),
              ("Sous-compte [[syscohada:552]] (5522 Orange Money), frais en [[syscohada:631]], transfert par "
               "[[syscohada:585]].", "Sub-account 552 (5522 Orange Money), fees in 631, transfer through 585."),
              ("Les frais ne réduisent pas la vente : c'est un service, comme les frais bancaires. Et le transfert ne "
               "passe jamais directement de 5522 à 521 : il transite par 585 jusqu'à ce que la banque le reçoive.",
               "Fees do not reduce the sale: they are a service, like bank charges. The transfer never goes straight "
               "from 5522 to 521: it waits in 585 until the bank receives it."),
              (f"{fcfa(total(orange, 'Transfert'))} partent vers la banque.",
               f"{fcfa(total(orange, 'Transfert'), 'en')} leave for the bank."),
              [("compta", 12, "Les règlements", "Settlements")], STORE[7]),
        scene(payroll["date"], m["payroll"], ("la première paie", "the first payroll"),
              ("Serge prépare la paie de Didier, de Paul, recruté avant l'arrivée du camion, et la sienne. Le bulletin donne les "
               "cotisations CNPS ; Serge calcule l'IRPP, les centimes communaux, la RAV, la TDL et le crédit foncier.",
               "Serge prepares pay for Didier, for Paul (hired ahead of the truck) and for himself. The payslip gives the "
               "CNPS contributions; Serge computes income tax, council cents, the audiovisual fee, local tax and the "
               "housing levy."),
              ("Salaires bruts en [[syscohada:6611]], charges patronales en [[syscohada:6413]] et [[syscohada:6641]] ; "
               "retenues fiscales en [[syscohada:4472]], CNPS en [[syscohada:431]], nets en [[syscohada:422]] "
               "[[cgi:art. 29]].",
               "Gross pay 6611, employer levies 6413 and 6641; tax withheld 4472, CNPS 431, net pay 422."),
              ("Les retenues ne sont pas des charges de l'entreprise : elles appartiennent aux salariés, que le dépôt "
               "verse pour eux à l'État et à la CNPS. La charge, c'est le brut et les cotisations patronales.",
               "Withholdings are not the company's expenses: they belong to the employees and the depot pays them over "
               "to the State and the CNPS. The expense is gross pay plus employer contributions."),
              (f"{fcfa(total(payroll, 'Nets'))} sont virés aux salariés ; les retenues entrent dans la déclaration du 15.",
               f"{fcfa(total(payroll, 'Nets'), 'en')} are paid to staff; withholdings go into the 15th return."),
              [("compta", 11, "La paie", "Payroll"), ("fisca", 3, "L'impôt sur le revenu des personnes physiques",
                                                    "Personal income tax")], STORE[8]),
        scene(deposit["date"], m["cash_out"], ("la recette part à la banque", "the takings go to the bank"),
              ("Garder des millions en espèces dans un entrepôt est risqué : chaque semaine, Didier porte la recette à la "
               "banque et rapporte un bordereau tamponné par le guichetier. Le 31, Serge réunit les bordereaux du mois "
               "et les récapitule.",
               "Keeping millions in cash in a warehouse is risky: every week Didier takes the takings to the bank and "
               "brings back a slip stamped by the cashier. On the 31st Serge gathers the month's slips and sums them up."),
              ("Virement interne : [[syscohada:585]] au débit, caisse [[syscohada:5711]] au crédit ; la banque débitera "
               "521 et soldera 585 à réception.",
               "Internal transfer: 585 debit, cash 5711 credit; the bank debits 521 and clears 585 on receipt."),
              ("Débiter directement 521 depuis la caisse marche une fois, puis tout se complique : la pièce de caisse et "
               "le relevé bancaire passeraient chacun leur écriture, et le versement serait compté deux fois. 585 "
               "garantit une seule écriture par pièce.",
               "Debiting 521 straight from the till works once, then breaks: the cash slip and the bank statement would "
               "each record the deposit, counting it twice. 585 keeps one entry per document."),
              (f"{fcfa(total(deposit, 'Espèces'))} quittent la caisse, qui revient à zéro.",
               f"{fcfa(total(deposit, 'Espèces'), 'en')} leave the till, which returns to zero."),
              [("compta", 12, "Les règlements", "Settlements")], STORE[9],
              figure=("trois-caisses", "Les trois caisses du dépôt et le virement interne",
                      "The depot's three tills and the internal transfer")),
        scene(bank["date"], m["bank"], ("le relevé de la banque", "the bank statement"),
              ("Le relevé de janvier arrive : salaires virés, versements reçus, frais de tenue de compte. Serge le "
               "pointe ligne par ligne contre le compte 521.",
               "January's statement arrives: salaries paid, deposits received, account fees. Serge ticks it line by "
               "line against account 521."),
              ("Chaque ligne du relevé solde la contrepartie qui l'attendait : [[syscohada:422]] pour les salaires, "
               "[[syscohada:585]] pour les virements internes ; les frais vont en [[syscohada:631]].",
               "Each statement line clears the account waiting for it: 422 for salaries, 585 for internal transfers; "
               "fees go to 631."),
              ("Un écart entre le relevé et le 521 ne se « corrige » pas en forçant le compte : il s'explique "
               "(opération pas encore passée d'un côté), puis on passe l'écriture qui manque.",
               "A gap between the statement and 521 is not “fixed” by forcing the account: it is explained (an item "
               "not yet recorded on one side), then the missing entry is booked."),
              ("Le solde du 521 au 31 janvier est celui que l'apprenant calcule dans le quiz du mois.",
               "The 521 balance at 31 January is the one learners compute in the month's quiz."),
              [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")], STORE[10]),
    ]


def special_date(piece, ref):
    return piece[ref]["date"]


def RENT_OF(piece):  # noqa: N802 (lecture d'une pièce, pas une constante)
    return total(piece, "Loyer brut")


def CRATES_OF(piece):  # noqa: N802
    return sum(line["qty"] for line in piece["payload"]["lines"])


SUMMARY_FR = (
    "### Bilan de janvier\n\n"
    "- Un apport n'est pas un produit : le capital va en 1013.\n"
    "- Une consigne n'est ni un achat ni une vente : créance en 4094 chez la brasserie, dette en 4194 envers le client.\n"
    "- Les accises sont dans le prix d'achat ; le précompte est une avance sur l'impôt.\n"
    "- Les retenues (loyer, salaires) sont des dettes envers l'État, pas des charges.\n"
    "- Tout ce qui circule entre la caisse, Orange Money et la banque transite par 585.\n\n"
    "Prochaine étape : la déclaration du 15 février, qui reprend la TVA, l'acompte d'IS et les retenues de janvier "
    "[[cgi:art. 21]].\n")
SUMMARY_EN = (
    "### January in brief\n\n"
    "- A contribution is not revenue: capital goes to 1013.\n"
    "- A deposit is neither a purchase nor a sale: receivable 4094 with the brewery, debt 4194 to the customer.\n"
    "- Excise is in the purchase price; the withholding is an advance on tax.\n"
    "- Withholdings (rent, pay) are debts to the State, not expenses.\n"
    "- Everything moving between the till, Orange Money and the bank goes through 585.\n\n"
    "Next: the 15 February return, covering January's VAT, CIT instalment and withholdings [[cgi:art. 21]].\n")


# ------------------------------------------------------------------------------------------- février à décembre

# Accroche de chaque mois : ce qui change dans la vie du dépôt (les volumes restent ceux du livre officiel).
HOOKS = {
    2: ("Février 2026 : le camion arrive, la banque prête, et la première déclaration du 15 tombe.",
        "February 2026: the truck arrives, the bank lends, and the first 15th return falls due."),
    3: ("Mars 2026 : premier remboursement de l'emprunt ; la routine s'installe.",
        "March 2026: first loan repayment; the routine settles in."),
    4: ("Avril 2026 : un mois sans surprise, l'occasion de vérifier que chaque pièce trouve sa place.",
        "April 2026: a quiet month, a chance to check every document finds its place."),
    5: ("Mai 2026 : le camion est arrêté à un contrôle routier.", "May 2026: the truck is stopped at a roadside check."),
    6: ("Juin 2026 : la brasserie refuse de reprendre des casiers abîmés au prix plein.",
        "June 2026: the brewery will not take back damaged crates at full price."),
    7: ("Juillet 2026 : la brasserie augmente son prix ; le dépôt garde le sien.",
        "July 2026: the brewery raises its price; the depot keeps its own."),
    8: ("Août 2026 : une dépense payée sans facture.", "August 2026: an expense paid without an invoice."),
    9: ("Septembre 2026 : à son tour, le dépôt retient une partie de la consigne du snack-bar.",
        "September 2026: this time the depot keeps part of the snack bar's deposit."),
    10: ("Octobre 2026 : Rose veut aider une association du quartier.",
         "October 2026: Rose wants to help a neighbourhood association."),
    11: ("Novembre 2026 : dernier mois avant l'inventaire ; tout doit être à jour.",
         "November 2026: last month before the count; everything must be up to date."),
    12: ("Décembre 2026 : la fin de l'année prépare l'inventaire du 31 et la DSF.",
         "December 2026: the end of the year prepares the 31 December count and the tax return."),
}

STORE_OF = {"rent": STORE[1], "purchase": STORE[3], "sale": STORE[5], "cash": STORE[6], "orange": STORE[7],
            "payroll": STORE[8], "cash_out": STORE[9], "bank": STORE[10]}
STORE_OF.update({
    "settlement": ("Déclaration, accusé de réception et avis de paiement au classeur Déclarations fiscales. Écriture "
                   "au journal de banque (BQ).",
                   "Return, acknowledgement and payment notice in the Tax returns binder. Entry in the bank journal "
                   "(BQ)."),
    "loan": ("Contrat de prêt et tableau d'amortissement au dossier permanent ; avis de crédit au classeur Banque. "
             "Écriture au journal de banque (BQ).",
             "Loan agreement and repayment schedule in the permanent file; credit notice in the Bank binder. Entry in "
             "the bank journal (BQ)."),
    "truck": ("Facture et carte grise au classeur Immobilisations, copie au dossier permanent ; le camion entre au "
              "tableau des immobilisations. Écriture au journal des achats (AC).",
              "Invoice and registration papers in the Fixed-asset binder, copy in the permanent file; the truck joins "
              "the asset register. Entry in the purchases journal (AC)."),
    "fine": ("Quittance au classeur Banque, avec une note qui la signale pour la passerelle fiscale. Écriture au "
             "journal de banque (BQ).",
             "Receipt in the Bank binder, with a note flagging it for the tax bridge. Entry in the bank journal (BQ)."),
    "no_receipt": ("Bon de caisse interne au classeur Caisse, signé par Serge, avec une note pour la passerelle. "
                   "Écriture au journal de caisse (CA).",
                   "Internal voucher in the Cash binder, signed by Serge, with a note for the tax bridge. Entry in the "
                   "cash journal (CA)."),
    "donation": ("Reçu de l'association au classeur Banque, avec une note pour la passerelle. Écriture au journal de "
                 "banque (BQ).",
                 "The association's receipt in the Bank binder, with a note for the tax bridge. Entry in the bank "
                 "journal (BQ)."),
})


def _lines_qty(piece):
    return {("65" if "65" in line["label"]["fr"] else "33"): line["qty"] for line in piece["payload"]["lines"]}


def later_month(book, special, month):
    """Scènes d'un mois de février à décembre : opérations récurrentes en version courte, événements du mois en
    version complète ; tous les montants sont lus sur les pièces du mois."""
    from tools.simulation import ledger

    piece = {p["ref"]: p for p in book.pieces}
    m = special["months"][month]
    mfr, men = MONTHS_FR[month - 1], MONTHS_EN[month - 1]
    pfr, pen = MONTHS_FR[month - 2], MONTHS_EN[month - 2]
    end = datetime.date.fromisoformat(piece[m["bank"]]["date"])
    out = []
    rent, purchase, sale = piece[m["rent"]], piece[m["purchase"]], piece[m["sale"]]
    bought, ordered = _lines_qty(purchase), _lines_qty(sale)
    deconsign = total(purchase, "Déconsigne", 0)
    mali = total(purchase, "Retenue", 0)
    boni = total(sale, "Retenue", 0)
    deposits_with_brewery = ledger.account_balance(book.entries, "4094", end)

    out.append(scene(
        rent["date"], m["rent"], ("le loyer", "the rent"),
        (f"Comme chaque mois, Serge vire le loyer de l'entrepôt à Mme Owona, moins la retenue de "
         f"{fcfa(total(rent, 'Précompte'))}.",
         f"As every month, Serge pays Mrs Owona the warehouse rent, less the {fcfa(total(rent, 'Précompte'), 'en')} "
         "withholding."),
        ("Loyer brut en [[syscohada:6222]], retenue en [[syscohada:4478]] [[cgi:art. 87]].",
         "Gross rent 6222, withholding 4478."),
        ("Rappel de janvier : la charge est le loyer brut ; la retenue appartient à l'État.",
         "Reminder from January: the expense is the gross rent; the withholding belongs to the State."),
        (f"La retenue entre dans la déclaration du 15 {MONTHS_FR[month % 12] if month < 12 else 'janvier 2027'}.",
         f"The withholding goes into the 15th {MONTHS_EN[month % 12] if month < 12 else 'January 2027'} return."),
        [("fisca", 3, "L'impôt sur le revenu des personnes physiques", "Personal income tax")], STORE_OF["rent"]))

    story_fr = (f"M. Fouda envoie la facture de {mfr} : {qty(bought['65'])} casiers de 65 cl et {qty(bought['33'])} "
                f"de 33 cl, livrés en plusieurs tournées. Sur la même facture, la brasserie déconsigne les vides que "
                f"Didier lui a rendus, pour {fcfa(deconsign)}.")
    story_en = (f"Mr Fouda sends the {men} invoice: {qty(bought['65'], 'en')} crates of 65 cl and "
                f"{qty(bought['33'], 'en')} of 33 cl, delivered in several runs. On the same invoice the brewery refunds "
                f"the deposit on the empties Didier returned, {fcfa(deconsign, 'en')}.")
    why = ("La déconsigne n'est ni un produit ni une réduction d'achat : elle solde la créance de [[syscohada:4094]], "
           "créée quand les casiers sont arrivés pleins.",
           "The refund is neither income nor a purchase discount: it clears the 4094 receivable created when the "
           "crates arrived full.")
    if month == 7:
        story_fr += (f" Depuis le 1er juillet, la brasserie a relevé ses prix de 60{NBSP}FCFA HT par casier ; "
                     "le dépôt garde les siens.")
        story_en += " Since 1 July the brewery has raised its prices by 60 FCFA a crate before tax; the depot keeps its own."
        why = (why[0] + " La hausse change le coût moyen du stock : c'est ce que montrera la fiche CMUP de décembre.",
               why[1] + " The rise changes the average stock cost, as December's WAC card will show.")
    if mali:
        story_fr += (f" Mais vingt casiers rendus sont fendus : la brasserie ne les reprend qu'à 3{THIN}000 au lieu de "
                     f"3{THIN}600 et retient {fcfa(mali)}.")
        story_en += (f" But twenty returned crates are cracked: the brewery takes them back at 3,000 instead of 3,600 "
                     f"and keeps {fcfa(mali, 'en')}.")
        why = ("La retenue n'est pas une baisse de la consigne à rendre : le dépôt a perdu une partie de sa créance, "
               "c'est un mali en [[syscohada:6224]], assimilé à une location d'emballage [[guide:1re partie, ch. 2]].",
               "The amount kept is not a smaller deposit: the depot has lost part of its receivable, a loss in 6224, "
               "treated like a packaging rental.")
    out.append(scene(
        purchase["date"], m["purchase"], ("la facture de la brasserie", "the brewery invoice"),
        (story_fr, story_en),
        ("Achats [[syscohada:6011]], TVA [[syscohada:4452]], précompte [[syscohada:4492]] [[cgi:art. 21]] ; consigne "
         "des pleins au débit de [[syscohada:4094]], déconsigne des vides au crédit.",
         "Purchases 6011, VAT 4452, withholding 4492; deposit on full crates debited to 4094, refund on empties "
         "credited."),
        why,
        (f"Le dépôt doit {fcfa(total(purchase, 'Net'))} à la brasserie ; au {end.day} {mfr}, "
         f"{fcfa(deposits_with_brewery)} de consignes restent à récupérer.",
         f"The depot owes the brewery {fcfa(total(purchase, 'Net'), 'en')}; at {men} {end.day}, "
         f"{fcfa(deposits_with_brewery, 'en')} of deposits are still to be recovered."),
        [("compta", 6, "Les achats", "Purchases")], STORE_OF["purchase"]))

    settlement = m.get("settlement")
    if settlement:
        decl = piece[settlement]
        paid = (total(decl, "TVA due") + total(decl, "Acompte") - total(decl, "Précompte imputé")
                + total(decl, "Retenues"))
        credit = next(f["value"] for f in decl["payload"]["fields"] if f["label"]["fr"].startswith("Crédit de TVA à"))
        first = month == 2
        out.append(scene(
            decl["date"], settlement, ("la déclaration du 15", "the 15th return"),
            ((f"{'Première échéance : ' if first else ''}Serge télédéclare les impôts de {pfr} et les paie le même jour : "
              f"TVA, acompte d'IS et retenues, pour {fcfa(paid)} au total.",
              f"{'First deadline: ' if first else ''}Serge files {pen}'s taxes online and pays them the same day: VAT, "
              f"CIT instalment and withholdings, {fcfa(paid, 'en')} in all.")),
            ("TVA facturée moins TVA déductible ; acompte d'IS de 2 % du chiffre d'affaires, majoré des centimes "
             "additionnels, moins le précompte subi ; retenues sur loyer et salaires reversées [[cgi:art. 21]] "
             "[[cgi:art. 143]].",
             "VAT charged less VAT recoverable; CIT instalment of 2% of turnover plus council cents, less the "
             "withholding suffered; rent and payroll withholdings paid over."),
            (("Le précompte payé à la brasserie n'est pas perdu : il s'impute sur l'acompte. Et un crédit de TVA ne se "
              "rembourse pas tout seul : il se reporte sur le mois suivant." if first else
              "Rien de nouveau dans la méthode : c'est la régularité qui compte, une déclaration en retard coûte des "
              "pénalités."),
             ("The withholding paid to the brewery is not lost: it is credited against the instalment. A VAT credit is "
              "not refunded by itself: it is carried forward." if first else
              "Nothing new in the method: regularity matters, a late return costs penalties.")),
            (f"La banque baisse de {fcfa(paid)} ; crédit de TVA reporté : {credit} FCFA.",
             f"The bank drops by {fcfa(paid, 'en')}; VAT credit carried forward: {credit} FCFA."),
            [("compta", 5, "La TVA : mécanisme et déclaration", "VAT: mechanism and return"),
             ("fisca", 7, "Obligations déclaratives et contrôle", "Filing obligations and audit")],
            STORE_OF["settlement"]))

    sale_fr = (f"Mme Ngah commande {qty(ordered['65'])} casiers de 65 cl et {qty(ordered['33'])} de 33 cl pour son "
               f"snack-bar ; elle rend les vides du mois dernier, que le dépôt déconsigne sur la facture.")
    sale_en = (f"Mrs Ngah orders {qty(ordered['65'], 'en')} crates of 65 cl and {qty(ordered['33'], 'en')} of 33 cl for "
               "her snack bar; she returns last month's empties, refunded on the invoice.")
    sale_why = ("La déconsigne rembourse une dette : elle se passe au débit de [[syscohada:4194]], jamais en réduction "
                "du chiffre d'affaires.",
                "The refund settles a debt: it is debited to 4194, never deducted from turnover.")
    if boni:
        sale_fr += (f" Trente casiers rendus sont abîmés : le dépôt ne les reprend qu'à 3{THIN}000 et garde "
                    f"{fcfa(boni)}.")
        sale_en += f" Thirty returned crates are damaged: the depot takes them back at 3,000 and keeps {fcfa(boni, 'en')}."
        sale_why = ("Ce que le dépôt garde n'est pas une vente de bière : c'est un boni sur reprise d'emballages, en "
                    "[[syscohada:7074]] [[guide:1re partie, ch. 2]]. En juin, le dépôt subissait le mali ; ici, il est "
                    "du côté qui reprend.",
                    "What the depot keeps is not a beer sale: it is a gain on returned packaging, in 7074. In June the "
                    "depot suffered the loss; here it is the one taking the crates back.")
    out.append(scene(
        sale["date"], m["sale"], ("la commande du Rond-Point", "the Rond-Point order"), (sale_fr, sale_en),
        ("Ventes [[syscohada:7011]], TVA [[syscohada:4431]], client [[syscohada:411]] ; consigne en "
         "[[syscohada:4194]], hors base de TVA [[cgi:art. 139]].",
         "Sales 7011, VAT 4431, customer 411; deposit in 4194, outside the VAT base."),
        sale_why,
        (f"Mme Ngah doit {fcfa(total(sale, 'Net'))}, payables le 10 du mois suivant.",
         f"Mrs Ngah owes {fcfa(total(sale, 'Net'), 'en')}, payable on the 10th of next month."),
        [("compta", 7, "Les ventes", "Sales")], STORE_OF["sale"]))

    out += _month_events(book, special, month, piece)

    cash, orange, payroll, deposit = piece[m["cash"]], piece[m["orange"]], piece[m["payroll"]], piece[m["cash_out"]]
    out.append(scene(
        cash["date"], m["cash"], ("la caisse du mois", "the month's till"),
        (f"Après un mois d'arrêtés de caisse quotidiens, Didier totalise le brouillard de {mfr}, "
         f"{fcfa(total(cash, 'Ventes TTC'))} encaissés au comptoir.",
         f"After a month of daily till counts, Didier totals the {men} cash book, "
         f"{fcfa(total(cash, 'Ventes TTC'), 'en')} taken at the counter."),
        ("Caisse [[syscohada:5711]] au TTC, ventes [[syscohada:7011]], TVA [[syscohada:4431]].",
         "Cash 5711 incl. tax, sales 7011, VAT 4431."),
        ("Une seule écriture récapitulative pour le mois est régulière, à condition que le brouillard quotidien la "
         "justifie [[source:ohada-audcif]].",
         "One monthly summary entry is lawful, provided the daily cash book supports it."),
        ("La TVA collectée du mois augmente d'autant.", "The month's VAT collected rises accordingly."),
        [("compta", 7, "Les ventes", "Sales")], STORE_OF["cash"]))
    out.append(scene(
        orange["date"], m["orange"], ("le relevé Orange Money", "the Orange Money statement"),
        (f"Le relevé de {mfr} arrive : encaissements des bars, frais de l'opérateur, transfert vers la banque.",
         f"The {men} statement arrives: bar payments, operator fees, transfer to the bank."),
        ("[[syscohada:552]] (5522), frais [[syscohada:631]], transfert par [[syscohada:585]].",
         "552 (5522), fees 631, transfer through 585."),
        ("Les frais restent des services bancaires (631), jamais une réduction de la vente.",
         "Fees stay bank services (631), never a sales discount."),
        (f"{fcfa(total(orange, 'Transfert'))} partent vers la banque.",
         f"{fcfa(total(orange, 'Transfert'), 'en')} leave for the bank."),
        [("compta", 12, "Les règlements", "Settlements")], STORE_OF["orange"]))
    out.append(scene(
        payroll["date"], m["payroll"], ("la paie", "payroll"),
        (f"Serge édite les trois bulletins de {mfr} et vire les salaires nets.",
         f"Serge prints the three {men} payslips and transfers the net pay."),
        ("Brut [[syscohada:6611]], charges patronales [[syscohada:6413]] et [[syscohada:6641]] ; retenues "
         "[[syscohada:4472]] et [[syscohada:431]], nets [[syscohada:422]] [[cgi:art. 29]].",
         "Gross 6611, employer levies 6413 and 6641; withholdings 4472 and 431, net 422."),
        ("Rappel : les retenues sont des dettes envers l'État et la CNPS, pas des charges.",
         "Reminder: withholdings are debts to the State and the CNPS, not expenses."),
        (f"{fcfa(total(payroll, 'Nets'))} versés aux salariés.", f"{fcfa(total(payroll, 'Nets'), 'en')} paid to staff."),
        [("compta", 11, "La paie", "Payroll")], STORE_OF["payroll"]))
    out.append(scene(
        deposit["date"], m["cash_out"], ("les versements de la semaine", "the weekly deposits"),
        (f"Serge réunit les bordereaux de versement de {mfr} : {fcfa(total(deposit, 'Espèces'))} portés à la banque.",
         f"Serge gathers the {men} deposit slips: {fcfa(total(deposit, 'Espèces'), 'en')} taken to the bank."),
        ("[[syscohada:585]] au débit, [[syscohada:5711]] au crédit.", "585 debit, 5711 credit."),
        ("585 garantit une seule écriture par pièce : la caisse sort l'argent, la banque le reçoit.",
         "585 keeps one entry per document: the till pays out, the bank receives."),
        ("La caisse revient à zéro en fin de mois.", "The till is back to zero at month end."),
        [("compta", 12, "Les règlements", "Settlements")], STORE_OF["cash_out"]))
    bank_rows = [t["label"]["fr"] for t in piece[m["bank"]]["payload"]["totals"]]
    loan_line = any(r.startswith("Échéance") for r in bank_rows)
    out.append(scene(
        piece[m["bank"]]["date"], m["bank"], ("le relevé et le rapprochement", "the statement and reconciliation"),
        ("Le relevé de la Banque X arrive : règlement de la brasserie, virement de Mme Ngah, salaires, versements"
         + (", échéance de l'emprunt" if loan_line else "") + ". Serge pointe chaque ligne contre le 521.",
         "Bank X's statement arrives: brewery payment, Mrs Ngah's transfer, salaries, deposits"
         + (", loan instalment" if loan_line else "") + ". Serge ticks each line against 521."),
        ("Brasserie [[syscohada:401]], client [[syscohada:411]], salaires [[syscohada:422]], virements internes "
         "[[syscohada:585]]" + (", emprunt [[syscohada:162]] et intérêts [[syscohada:6712]]" if loan_line else "")
         + ", frais [[syscohada:631]].",
         "Brewery 401, customer 411, salaries 422, internal transfers 585"
         + (", loan 162 and interest 6712" if loan_line else "") + ", fees 631."),
        (("L'échéance se coupe en deux : le capital remboursé diminue la dette (162), seuls les intérêts sont une "
          "charge (6712)." if loan_line else
          "Le rapprochement explique les écarts ; il ne force jamais le compte."),
         ("The instalment splits in two: principal reduces the debt (162), only interest is an expense (6712)."
          if loan_line else "Reconciliation explains gaps; it never forces the account.")),
        (f"Solde comptable du 521 au {end.day} {mfr} : {fcfa(ledger.account_balance(book.entries, '521', end))}.",
         f"Book balance of 521 at {men} {end.day}: {fcfa(ledger.account_balance(book.entries, '521', end), 'en')}."),
        [("compta", 15, "Les opérations de financement", "Financing")] if loan_line else
        [("compta", 29, "Organisation et contrôles comptables", "Organisation and accounting controls")],
        STORE_OF["bank"]))
    return out


def _month_events(book, special, month, piece):
    """Pièces propres au mois : emprunt et camion (février), amende (mai), dépense sans pièce (août), don (octobre)."""
    out = []
    if month == 2:
        loan, truck = piece[special["loan"]], piece[special["truck"]]
        out.append(scene(
            loan["date"], special["loan"], ("la banque prête pour le camion", "the bank lends for the truck"),
            (f"Livrer les bars à pied ne suffit plus. La Banque X accepte de prêter {fcfa(total(loan, 'Montant'))} "
             "sur trois ans pour acheter un camion ; les fonds arrivent sur le compte.",
             f"Delivering on foot is no longer enough. Bank X agrees to lend {fcfa(total(loan, 'Montant'), 'en')} over "
             "three years to buy a truck; the funds reach the account."),
            ("Banque [[syscohada:521]] au débit, emprunt [[syscohada:162]] au crédit.",
             "Bank 521 debit, borrowings 162 credit."),
            ("L'argent prêté n'est pas un produit : il faudra le rendre. Les intérêts, eux, seront des charges, mois "
             "après mois.", "Borrowed money is not income: it must be repaid. Interest will be an expense, month by "
             "month."),
            ("La trésorerie grossit, la dette aussi ; le résultat ne change pas.",
             "Cash grows, so does debt; profit does not change."),
            [("compta", 15, "Les opérations de financement", "Financing")], STORE_OF["loan"]))
        out.append(scene(
            truck["date"], special["truck"], ("le camion", "the truck"),
            ("Paul prend le volant du camion de 10 tonnes acheté au Centre Poids Lourds du Mfoundi ; la facture est "
             "réglée le 6 par virement.",
             "Paul takes the wheel of the 10-tonne truck bought from the Mfoundi heavy-vehicle dealer; the invoice is "
             "paid by transfer on the 6th."),
            ("Matériel automobile [[syscohada:2451]], TVA sur immobilisations [[syscohada:4451]], fournisseur "
             "d'immobilisations [[syscohada:4812]].",
             "Vehicles 2451, VAT on fixed assets 4451, fixed-asset supplier 4812."),
            ("Le camion servira des années : ce n'est pas une charge du mois. Et son vendeur n'est pas un fournisseur de "
             "marchandises : la dette va en 4812, pas en 401.",
             "The truck will serve for years: it is not this month's expense. Its seller is not a goods supplier: "
             "the debt goes to 4812, not 401."),
            ("La TVA du camion, déductible, crée un crédit de TVA à la déclaration du 15 mars ; l'amortissement "
             "commencera dès février.",
             "The truck's VAT, recoverable, creates a VAT credit on the 15 March return; depreciation starts in "
             "February."),
            [("compta", 13, "Les immobilisations", "Fixed assets")], STORE_OF["truck"]))
    if month == 5:
        fine = piece[special["fine"]]
        out.append(scene(
            fine["date"], special["fine"], ("l'amende", "the fine"),
            ("À un contrôle routier, le camion est trouvé en surcharge à l'essieu. Serge paie l'amende par virement.",
             "At a roadside check the truck is found overloaded on the axle. Serge pays the fine by transfer."),
            ("Amendes [[syscohada:6478]] ; elles ne sont pas déductibles du résultat fiscal [[cgi:art. 7]].",
             "Fines 6478; they are not deductible for tax."),
            ("C'est bien une charge en comptabilité, mais l'État ne laisse pas réduire l'impôt par une sanction : "
             "elle sera réintégrée à la passerelle.",
             "It is an accounting expense, but the State does not let a penalty reduce tax: it will be added back in "
             "the tax bridge."),
            (f"Le résultat comptable baisse de {fcfa(total(fine, 'Amende'))} ; le résultat fiscal, non.",
             f"Accounting profit drops by {fcfa(total(fine, 'Amende'), 'en')}; taxable profit does not."),
            [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")], STORE_OF["fine"]))
    if month == 8:
        voucher = piece[special["no_receipt"]]
        out.append(scene(
            voucher["date"], special["no_receipt"], ("une dépense sans facture", "an expense without an invoice"),
            ("Une crevaison sur la route de Mbalmayo : un réparateur de bord de route remet le camion en état, payé en "
             "espèces, sans facture. Serge rédige un bon de caisse interne.",
             "A flat tyre on the Mbalmayo road: a roadside mechanic fixes the truck, paid in cash, with no invoice. "
             "Serge writes an internal voucher."),
            ("Charges diverses [[syscohada:6588]], caisse [[syscohada:5711]] ; une charge sans pièce justificative "
             "n'est pas déductible [[cgi:art. 7]].",
             "Sundry expenses 6588, cash 5711; an expense without a supporting document is not deductible."),
            ("La dépense est réelle, elle s'enregistre ; mais un bon interne ne prouve rien face à l'administration : "
             "elle sera réintégrée. La bonne pratique est d'exiger un reçu, même manuscrit.",
             "The expense is real and is recorded; but an internal voucher proves nothing to the tax office: it will "
             "be added back. Good practice is to ask for a receipt, even handwritten."),
            (f"{fcfa(total(voucher, 'Dépense'))} sortent de la caisse.", f"{fcfa(total(voucher, 'Dépense'), 'en')} leave the till."),
            [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")], STORE_OF["no_receipt"]))
    if month == 10:
        gift = piece[special["donation"]]
        out.append(scene(
            gift["date"], special["donation"], ("le don à l'association", "the donation"),
            ("Une association du quartier qui équipe l'école publique de Mvog-Ada demande un soutien. Rose accepte ; "
             "l'association remet un reçu.",
             "A neighbourhood association equipping the Mvog-Ada state school asks for support. Rose agrees; the "
             "association issues a receipt."),
            ("Dons [[syscohada:6582]] ; déductibles dans la limite de 0,5 % du chiffre d'affaires "
             "[[param:dons.plafond_interet_general]] [[cgi:art. 7]].",
             "Donations 6582; deductible up to 0.5% of turnover."),
            ("Un don n'est pas interdit fiscalement, il est plafonné : seule la part au-delà de la limite sera "
             "réintégrée en fin d'année.",
             "A donation is not barred for tax, it is capped: only the part above the limit is added back at year end."),
            (f"{fcfa(total(gift, 'Don'))} quittent la banque.", f"{fcfa(total(gift, 'Don'), 'en')} leave the bank."),
            [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")], STORE_OF["donation"]))
    return out


def month_summary(month, lang):
    """Bilan du mois : la notion nouvelle, la routine de fin de mois et l'échéance qui suit."""
    new = {
        2: ("Un emprunt est une dette (162), un camion une immobilisation (2451) ; la première déclaration du 15 impute "
            "le précompte et reporte le crédit de TVA.",
            "A loan is a debt (162), a truck a fixed asset (2451); the first 15th return credits the withholding and "
            "carries the VAT credit forward."),
        3: ("Chaque échéance se coupe en capital (162) et intérêts (6712).",
            "Each instalment splits into principal (162) and interest (6712)."),
        5: ("Une amende est une charge comptable mais pas fiscale : à réintégrer.",
            "A fine is an accounting expense but not a tax one: add it back."),
        6: ("Un casier repris à moindre prix est un mali (6224) pour celui qui le rend.",
            "A crate taken back for less is a loss (6224) for the one returning it."),
        7: ("Une hausse du prix d'achat se lira dans le coût moyen du stock.",
            "A purchase price rise will show in the average stock cost."),
        8: ("Une dépense sans pièce s'enregistre mais ne se déduit pas.",
            "An expense without a document is recorded but not deducted."),
        9: ("Le boni (7074) est le miroir du mali : le dépôt est cette fois celui qui reprend.",
            "The gain (7074) mirrors the loss: this time the depot is the one taking back."),
        10: ("Un don se déduit dans la limite de 0,5 % du chiffre d'affaires.",
             "A donation is deductible up to 0.5% of turnover."),
    }.get(month, ("Les opérations courantes suivent les règles de janvier ; ce qui compte, c'est la régularité.",
                  "Routine operations follow January's rules; regularity is what counts."))
    nxt = (("Prochaine étape : l'inventaire du 31 décembre et la déclaration du 15 janvier 2027.",
            "Next: the 31 December count and the 15 January 2027 return.") if month == 12 else
           (f"Prochaine étape : la déclaration du 15 {MONTHS_FR[month]} [[cgi:art. 21]].",
            f"Next: the 15 {MONTHS_EN[month]} return."))
    if lang == "fr":
        return (f"### Bilan de {MONTHS_FR[month - 1]}\n\n- {new[0]}\n- Fin de mois : relevés rapprochés, balance éditée, "
                f"journaux centralisés, pièces classées.\n\n{nxt[0]}\n")
    return (f"### {MONTHS_EN[month - 1]} in brief\n\n- {new[1]}\n- Month end: statements reconciled, trial balance "
            f"printed, journals centralised, documents filed.\n\n{nxt[1]}\n")


def month_section(scenes, other_refs, lang, month=1, opening=()):
    """Section mensuelle narrée : accroche, balance d'ouverture, scènes dans l'ordre du calendrier, pièces sans
    scène, bilan."""
    if month == 1:
        intro = ("Janvier 2026 : le dépôt ouvre. Lisez chaque scène, regardez la pièce qu'elle produit, puis passez "
                 "l'écriture dans le quiz [[cgi:art. 142]].\n" if lang == "fr" else
                 "January 2026: the depot opens. Read each scene, look at the document it produces, then record the "
                 "entry in the quiz [[cgi:art. 142]].\n")
        summary = SUMMARY_FR if lang == "fr" else SUMMARY_EN
    else:
        hook = HOOKS[month][0 if lang == "fr" else 1]
        intro = (f"{hook} Le mois s'ouvre sur la balance arrêtée la veille, tirée du livre officiel "
                 "[[syscohada:521]].\n" if lang == "fr" else
                 f"{hook} The month opens with the trial balance closed the day before, taken from the official "
                 "ledger [[syscohada:521]].\n")
        summary = month_summary(month, lang)
    return assemble(intro, scenes, opening, other_refs, summary, lang)


def assemble(intro, scenes, opening, other_refs, summary, lang):
    """Section narrée de tout parcours : accroche, pièces d'ouverture (balance), scènes dans l'ordre du calendrier,
    pièces sans scène, bilan ; typographie française appliquée au texte FR."""
    head = "".join(f"\n[[piece:{ref}]]\n" for ref in opening)
    rest = "".join(f"\n[[piece:{ref}]]\n" for ref in other_refs)
    body = "\n".join(s[lang] for s in sorted(scenes, key=lambda s: s["date"]))
    text = f"{intro}{head}\n{body}{rest}\n{summary}"
    return typeset_fr(text) if lang == "fr" else text


# ---------------------------------------------------------------------------------- inventaire, passerelle, DSF

def year_end_sections(book, special):
    """Récit des modules Inventaire (M6) et Passerelle + DSF (M7) : {clé: {fr, en}} en Markdown."""
    piece = {p["ref"]: p for p in book.pieces}
    sheet, schedule, liq = special["sheet"], special["schedule"], special["liquidation"]
    counted = {f: int(sum(q for q, _ in lots) - sold) for f, (lots, sold, _r) in special["stock"].items()}
    truck, crates = special["truck_dotation"], special["crates_dotation"]
    add, tax = special["add_backs"], special["tax"]
    count = scene(
        piece[sheet]["date"], sheet, ("le comptage du 31 décembre", "the 31 December count"),
        (f"Le 31 au soir, l'entrepôt est fermé aux clients. Didier et Serge comptent chaque casier plein, rangée par "
         f"rangée : {qty(counted['65'])} casiers de 65 cl et {qty(counted['33'])} de 33 cl. Le compte physique concorde "
         "avec la fiche de stock tenue chaque soir.",
         f"On the evening of the 31st the warehouse closes to customers. Didier and Serge count every full crate, row "
         f"by row: {qty(counted['65'], 'en')} crates of 65 cl and {qty(counted['33'], 'en')} of 33 cl. The physical "
         "count matches the stock card kept every evening."),
        ("Inventaire intermittent : les achats sont passés en [[syscohada:6011]] toute l'année ; au 31 décembre, le "
         "stock final valorisé au coût moyen pondéré entre en [[syscohada:3111]] et [[syscohada:3112]], par "
         "[[syscohada:6031]] [[source:ohada-audcif]].",
         "Periodic inventory: purchases go to 6011 all year; on 31 December closing stock at weighted average cost "
         "goes into 3111 and 3112, through 6031."),
        ("Pourquoi le CMUP et pas le PEPS ? Les deux méthodes sont admises, mais il faut en choisir une et la garder. "
         "Avec la hausse de juillet, le PEPS donnerait un stock final plus élevé, donc un résultat plus élevé : "
         "l'exercice de contraste le mesure.",
         "Why WAC rather than FIFO? Both are allowed, but one must be chosen and kept. With July's price rise FIFO "
         "would give a higher closing stock, hence a higher profit: the contrast exercise measures it."),
        (f"Le stock final de {fcfa(special['closing_stock'])} réduit le coût des ventes de l'exercice.",
         f"Closing stock of {fcfa(special['closing_stock'], 'en')} reduces the year's cost of sales."),
        [("compta", 20, "Les stocks à l'inventaire", "Inventories at year end")],
        ("Feuilles de comptage signées et fiche CMUP au classeur Inventaire ; le résumé de l'inventaire est transcrit "
         "au livre d'inventaire. Écriture au journal des opérations diverses (OD).",
         "Signed count sheets and WAC card in the Inventory binder; the inventory summary goes into the inventory "
         "book. Entry in the miscellaneous journal (OD)."))
    depreciation = scene(
        piece[schedule]["date"], schedule, ("les amortissements", "depreciation"),
        (f"Serge ouvre le tableau des immobilisations : le camion, en service depuis février, et les casiers achetés en "
         f"janvier. Il calcule {fcfa(truck)} pour le camion (11 mois) et {fcfa(crates)} pour les casiers.",
         f"Serge opens the asset register: the truck, in use since February, and the crates bought in January. He "
         f"computes {fcfa(truck, 'en')} for the truck (11 months) and {fcfa(crates, 'en')} for the crates."),
        ("Dotations [[syscohada:6813]] ; amortissements [[syscohada:2845]] et [[syscohada:2843]], linéaires sur cinq "
         "ans au prorata temporis.",
         "Charges 6813; accumulated depreciation 2845 and 2843, straight-line over five years, pro rata."),
        ("Pourquoi cinq ans ? C'est la durée d'usage retenue par l'entreprise. Le fisc fixe des taux maximaux "
         "(33,33 % pour un camion) [[cgi:art. 7]] : le taux comptable de 20 % reste en dessous, rien à réintégrer.",
         "Why five years? It is the useful life the company chose. Tax law sets maximum rates (33.33% for a truck): "
         "the 20% book rate stays below, nothing to add back."),
        (f"{fcfa(truck + crates)} de charges, sans sortie d'argent.",
         f"{fcfa(truck + crates, 'en')} of expenses, with no cash going out."),
        [("compta", 18, "Les amortissements", "Depreciation")],
        ("Tableau des immobilisations édité et classé au classeur Immobilisations. Écriture au journal des opérations "
         "diverses (OD).",
         "Asset register printed and filed in the Fixed-asset binder. Entry in the miscellaneous journal (OD)."))
    inventory = {}
    for lang in ("fr", "en"):
        lead = ("Le 31 décembre, l'exercice s'arrête : on compte, on évalue, on amortit [[syscohada:6031]].\n\n"
                if lang == "fr" else "On 31 December the year stops: count, value, depreciate [[syscohada:6031]].\n\n")
        inventory[lang] = lead + count[lang] + "\n[[calc:stock]]\n\n" + depreciation[lang] + "\n[[calc:amortissement]]\n"
    rows_fr = (f"| Amende de circulation (mai) | {fcfa(add['amendes'])} |\n"
               f"| Réparation payée sans facture (août) | {fcfa(add['charge_sans_piece'])} |\n"
               f"| Part du don au-delà de 0,5 % du chiffre d'affaires (octobre) | {fcfa(add['dons_excedentaires'])} |\n")
    rows_en = (f"| Traffic fine (May) | {fcfa(add['amendes'], 'en')} |\n"
               f"| Repair paid without an invoice (August) | {fcfa(add['charge_sans_piece'], 'en')} |\n"
               f"| Donation above 0.5% of turnover (October) | {fcfa(add['dons_excedentaires'], 'en')} |\n")
    pieces = "\n\n".join(f"[[piece:{special[k]}]]" for k in ("fine", "no_receipt", "donation"))
    bridge = {
        "fr": ("### Janvier 2027 : la passerelle fiscale\n\n"
               "Serge reprend les notes laissées dans les classeurs : trois dépenses de 2026 ont été enregistrées en "
               "charges, mais le fisc ne les admet pas [[cgi:art. 7]].\n\n"
               "| Réintégration | Montant |\n|---|---|\n" + rows_fr +
               f"\n**Résultat comptable avant impôt** : {fcfa(special['accounting'])}. **Résultat fiscal** : "
               f"{fcfa(special['tax_result'])}.\n\n"
               "> **Pourquoi réintégrer et pas corriger la comptabilité ?** Les trois dépenses sont réelles : la "
               "comptabilité les garde. Seul le calcul de l'impôt les écarte, dans le tableau de passage.\n\n"
               f"{pieces}\n\n**Revoir :** Fiscalité M2 « L'impôt sur les sociétés ».\n"),
        "en": ("### January 2027: the tax bridge\n\n"
               "Serge goes back over the notes left in the binders: three 2026 expenses were booked, but tax law does "
               "not allow them [[cgi:art. 7]].\n\n"
               "| Add-back | Amount |\n|---|---|\n" + rows_en +
               f"\n**Accounting profit before tax**: {fcfa(special['accounting'], 'en')}. **Taxable profit**: "
               f"{fcfa(special['tax_result'], 'en')}.\n\n"
               "> **Why add back rather than change the books?** The three expenses are real: the books keep them. "
               "Only the tax computation sets them aside, in the reconciliation table.\n\n"
               f"{pieces}\n\n**See again:** Taxation M2 “Corporate income tax”.\n"),
    }
    liquidation = scene(
        piece[liq]["date"], liq, ("l'impôt de l'année", "the year's tax"),
        (f"Avec un résultat fiscal de {fcfa(special['tax_result'])}, l'IS au taux de 25 % ne serait que de "
         f"{fcfa(tax['is_total'])}, centimes compris. Mais le dépôt a vendu pour {fcfa(special['turnover'])} : le "
         f"minimum de perception, {fcfa(tax['minimum_total'])}, l'emporte. Les acomptes versés chaque 15 du mois le "
         "couvrent déjà.",
         f"With a taxable profit of {fcfa(special['tax_result'], 'en')}, CIT at 25% would be only "
         f"{fcfa(tax['is_total'], 'en')}, council cents included. But the depot sold "
         f"{fcfa(special['turnover'], 'en')}: the minimum tax, {fcfa(tax['minimum_total'], 'en')}, prevails. The "
         "instalments paid every 15th already cover it."),
        ("L'IS dû est le plus élevé de l'IS calculé et du minimum de perception [[cgi:art. 17 bis]] [[cgi:art. 21]] "
         "[[cgi:art. 23]] ; impôt [[syscohada:891]] contre État [[syscohada:441]].",
         "CIT due is the higher of computed CIT and the minimum tax; tax 891 against State 441."),
        ("Pourquoi un dépôt de boissons paie-t-il le minimum ? Sa marge est mince : quelques centaines de francs par "
         "casier. Le minimum se calcule sur le chiffre d'affaires, pas sur le bénéfice : c'est la réalité de la "
         "distribution.",
         "Why does a beverage depot pay the minimum? Its margin is thin, a few hundred francs a crate. The minimum is "
         "computed on turnover, not on profit: that is the reality of distribution."),
        ((f"Bénéfice net : {fcfa(special['net'])}." if special["net"] >= 0 else
          f"Perte nette : {fcfa(-special['net'])}. Le dépôt a gagné de l'argent avant impôt, mais le minimum de "
          "perception, calculé sur le chiffre d'affaires, dépasse ce bénéfice."),
         (f"Net profit: {fcfa(special['net'], 'en')}." if special["net"] >= 0 else
          f"Net loss: {fcfa(-special['net'], 'en')}. The depot made money before tax, but the minimum tax, computed "
          "on turnover, exceeds that profit.")),
        [("fisca", 2, "L'impôt sur les sociétés", "Corporate income tax")],
        ("Liquidation de l'IS jointe à la DSF, au classeur Déclarations fiscales. Écriture au journal des opérations "
         "diverses (OD), datée du 31 décembre 2026.",
         "CIT computation attached to the return, in the Tax returns binder. Entry in the miscellaneous journal (OD), "
         "dated 31 December 2026."))
    for lang in ("fr", "en"):
        bridge[lang] += "\n" + liquidation[lang]
    dsf_refs = "\n\n".join(f"[[piece:{p['ref']}]]" for p in book.pieces if p.get("dsf") and p["ref"] != liq)
    dsf = {
        "fr": ("### Avant le 15 avril 2027 : la DSF\n\n"
               "Serge reporte le bilan, le compte de résultat et le tableau de passage dans la DSF et la dépose en "
               "ligne au CIME de Yaoundé, avant l'échéance du 15 avril [[cgi:art. 18]]. Les états financiers sont "
               "arrêtés dans les quatre mois de la clôture [[source:ohada-audcif]].\n\n"
               f"{dsf_refs}\n\n"
               "**Où ça se range.** DSF et accusé de réception au classeur Déclarations fiscales ; bilan, compte de "
               "résultat et tableau des flux transcrits au livre d'inventaire ; tout se conserve dix ans.\n"),
        "en": ("### Before 15 April 2027: the tax return\n\n"
               "Serge carries the balance sheet, income statement and reconciliation into the return and files it "
               "online with the Yaoundé medium-sized taxpayer office before the 15 April deadline [[cgi:art. 18]].\n\n"
               f"{dsf_refs}\n\n"
               "**Where it is filed.** Return and acknowledgement in the Tax returns binder; financial statements "
               "copied into the inventory book; everything is kept for ten years.\n"),
    }
    result = {}
    for key, value in (("inventory", inventory), ("bridge", bridge), ("dsf", dsf)):
        result[key] = {"fr": typeset_fr(value["fr"]), "en": value["en"]}
    return result
