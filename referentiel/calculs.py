"""Formules de référence des calculateurs (US-26, C12), en Decimal et au franc près.

Les taux sont toujours passés en argument, en pourcentage (17.5 pour 17,5 %) : ils viennent de FiscalParameter, jamais
d'une constante. static/acad/js/calculators.js doit donner les mêmes résultats (vecteurs de referentiel/tests).
"""
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENT = Decimal("100")


def franc(value):
    """Arrondi au franc le plus proche (demi-franc vers le haut)."""
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def millier_inferieur(value):
    """Arrondi au millier de francs inférieur (CGI art. 17 et 23)."""
    return (value / 1000).quantize(Decimal("1"), rounding=ROUND_DOWN) * 1000


def tva_depuis_ht(ht, taux_tva, taux_cac):
    """TVA au taux principal, centimes additionnels communaux sur la TVA (CGI art. 142) et prix TTC."""
    tva = franc(ht * taux_tva / CENT)
    cac = franc(tva * taux_cac / CENT)
    return {"ht": ht, "tva": tva, "cac": cac, "taxes": tva + cac, "ttc": ht + tva + cac}


def tva_depuis_ttc(ttc, taux_tva, taux_cac):
    """Prix HT retrouvé à partir du TTC ; les taxes sont la différence, pour que HT + taxes = TTC au franc près."""
    taux_global = taux_tva * (1 + taux_cac / CENT)
    ht = franc(ttc / (1 + taux_global / CENT))
    return {"ht": ht, "taxes": ttc - ht, "ttc": ttc}


def taux_is(chiffre_affaires, seuil, taux_normal, taux_reduit):
    """Taux réduit de l'IS jusqu'au seuil de chiffre d'affaires inclus (CGI art. 17 bis), taux normal au-delà."""
    return taux_reduit if chiffre_affaires <= seuil else taux_normal


def impot_societes(benefice, base_minimum, taux_is, taux_minimum, taux_cac):
    """IS sur le bénéfice (fraction inférieure à 1 000 F négligée), minimum de perception sur le chiffre d'affaires de
    référence arrondi au millier inférieur ; chacun majoré des CAC. L'impôt dû est le plus élevé des deux."""
    impot = franc(millier_inferieur(max(benefice, Decimal(0))) * taux_is / CENT)
    minimum = franc(millier_inferieur(base_minimum) * taux_minimum / CENT)
    is_total = impot + franc(impot * taux_cac / CENT)
    minimum_total = minimum + franc(minimum * taux_cac / CENT)
    return {"is": impot, "cac": is_total - impot, "is_total": is_total,
            "minimum": minimum, "minimum_total": minimum_total, "du": max(is_total, minimum_total)}


def amortissement_lineaire(valeur, annees, mois_debut=1):
    """Plan linéaire par exercice civil, prorata en mois à partir du mois de mise en service (1 = janvier)."""
    mensuel = valeur / (annees * 12)
    plan, cumul, restant = [], Decimal(0), annees * 12
    mois = 13 - mois_debut
    while restant > 0:
        mois = min(mois, restant)
        dotation = valeur - cumul if mois == restant else franc(mensuel * mois)
        cumul += dotation
        restant -= mois
        plan.append({"dotation": dotation, "cumul": cumul, "vnc": valeur - cumul})
        mois = 12
    return plan


def amortissement_degressif(valeur, annees, coefficient):
    """Taux linéaire × coefficient sur la valeur résiduelle ; passage au linéaire dès qu'il donne une dotation au
    moins égale, la dernière dotation soldant la valeur."""
    taux = coefficient / annees
    plan, vnc = [], valeur
    for rang in range(annees):
        restant = annees - rang
        dotation = vnc if restant == 1 else franc(max(vnc * taux, vnc / restant))
        vnc -= dotation
        plan.append({"dotation": dotation, "cumul": valeur - vnc, "vnc": vnc})
    return plan


def facture(brut, remise, rabais, ristourne, escompte, taux_tva):
    """Réductions commerciales en cascade, puis escompte, puis TVA sur le net financier."""
    net = brut
    for taux in (remise, rabais, ristourne):
        net = franc(net * (1 - taux / CENT))
    montant_escompte = franc(net * escompte / CENT)
    net_financier = net - montant_escompte
    tva = franc(net_financier * taux_tva / CENT)
    return {"brut": brut, "net_commercial": net, "escompte": montant_escompte, "net_financier": net_financier,
            "tva": tva, "ttc": net_financier + tva}


def _verifier_quantite(lots, quantite):
    if quantite > sum(q for q, _ in lots):
        raise ValueError("Sortie supérieure au stock disponible.")


def sortie_cmup(lots, quantite):
    """Sortie valorisée au coût moyen unitaire pondéré des lots [(quantité, coût unitaire)]."""
    _verifier_quantite(lots, quantite)
    total_quantite = sum(q for q, _ in lots)
    cout = franc(sum(q * c for q, c in lots) / total_quantite)
    return {"cout_unitaire": cout, "valeur_sortie": cout * quantite, "valeur_stock": cout * (total_quantite - quantite)}


def sortie_peps(lots, quantite):
    """Sortie valorisée premier entré, premier sorti : les lots les plus anciens partent d'abord."""
    _verifier_quantite(lots, quantite)
    stock, valeur, reste = [], Decimal(0), quantite
    for q, c in lots:
        prise = min(q, reste)
        valeur += prise * c
        reste -= prise
        if q > prise:
            stock.append((q - prise, c))
    return {"valeur_sortie": valeur, "valeur_stock": sum(q * c for q, c in stock), "stock": stock}


def bareme_progressif(base, bareme):
    """Impôt d'un barème par tranches [(plafond ou None, taux %)], chaque tranche à son taux."""
    impot, plancher = Decimal(0), Decimal(0)
    for plafond, taux in bareme:
        haut = base if plafond is None else min(base, plafond)
        if haut > plancher:
            impot += (haut - plancher) * taux / CENT
        if plafond is None or base <= plafond:
            break
        plancher = plafond
    return franc(impot)


def irpp_salaire(brut_annuel, cnps_annuelle, taux_frais, plafond_frais, abattement, bareme, taux_cac):
    """IRPP annuel d'un salarié : frais professionnels forfaitaires plafonnés et cotisations CNPS retraite déduits,
    abattement forfaitaire, barème progressif, puis centimes additionnels communaux."""
    frais = min(franc(brut_annuel * taux_frais / CENT), plafond_frais)
    net = brut_annuel - frais - cnps_annuelle
    imposable = max(net - abattement, Decimal(0))
    irpp = bareme_progressif(imposable, bareme)
    cac = franc(irpp * taux_cac / CENT)
    return {"frais": frais, "net": net, "imposable": imposable, "irpp": irpp, "cac": cac, "total": irpp + cac}


def forfait_par_tranche(base, tranches):
    """Montant forfaitaire de la première tranche [(plafond inclus ou None, montant)] qui contient la base (RAV, TDL)."""
    for plafond, montant in tranches:
        if plafond is None or base <= plafond:
            return montant
    raise ValueError("Barème sans tranche supérieure.")


def credit_foncier(salaire, taux):
    """Contribution au Crédit Foncier (loi 77-10, art. 6) : taux sur le salaire arrondi au millier inférieur."""
    return franc(millier_inferieur(salaire) * taux / CENT)
