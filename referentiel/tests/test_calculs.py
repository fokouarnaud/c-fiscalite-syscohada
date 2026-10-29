"""US-26 (C12) : formules de référence des calculateurs, vérifiées sur des vecteurs calculés à la main.

Les taux sont passés en argument (ils viennent de FiscalParameter) ; les valeurs ci-dessous sont celles du CGI 2026 :
TVA 17,5 % + CAC 10 % (art. 142), IS 30 % ou 25 % (art. 17 et 17 bis), minimum de perception 2 % (art. 21 et 23).
"""
from decimal import Decimal as D

import pytest

from referentiel import calculs


def test_vat_on_a_price_before_tax():
    assert calculs.tva_depuis_ht(D("1000000"), D("17.5"), D("10")) == {
        "ht": D("1000000"), "tva": D("175000"), "cac": D("17500"), "taxes": D("192500"), "ttc": D("1192500"),
    }


def test_vat_extracted_from_a_price_including_tax_is_rounded_to_the_franc():
    result = calculs.tva_depuis_ttc(D("500000"), D("17.5"), D("10"))

    assert (result["ht"], result["taxes"], result["ttc"]) == (D("419287"), D("80713"), D("500000"))


def test_vat_extracted_from_a_round_price_including_tax():
    assert calculs.tva_depuis_ttc(D("1192500"), D("17.5"), D("10"))["ht"] == D("1000000")


@pytest.mark.parametrize("ca, taux", [(D("3000000000"), D("25")), (D("3000000001"), D("30"))])
def test_the_reduced_corporate_tax_rate_applies_up_to_three_billion(ca, taux):
    assert calculs.taux_is(ca, seuil=D("3000000000"), taux_normal=D("30"), taux_reduit=D("25")) == taux


def test_corporate_tax_ignores_the_fraction_below_1000_and_adds_the_communal_cents():
    result = calculs.impot_societes(D("12345678"), D("4000000"), taux_is=D("25"), taux_minimum=D("2"), taux_cac=D("10"))

    assert (result["is"], result["cac"], result["is_total"]) == (D("3086250"), D("308625"), D("3394875"))
    assert (result["minimum"], result["minimum_total"]) == (D("80000"), D("88000"))
    assert result["du"] == D("3394875")


def test_the_minimum_tax_prevails_when_the_profit_is_small():
    """Base du minimum arrondie au millier inférieur (art. 23) : 400 000 999 -> 400 000 000."""
    result = calculs.impot_societes(D("0"), D("400000999"), taux_is=D("25"), taux_minimum=D("2"), taux_cac=D("10"))

    assert (result["minimum"], result["minimum_total"], result["du"]) == (D("8000000"), D("8800000"), D("8800000"))


def test_straight_line_depreciation_is_prorated_from_the_month_of_commissioning():
    plan = calculs.amortissement_lineaire(D("10000000"), annees=5, mois_debut=4)

    assert [row["dotation"] for row in plan] == [D("1500000"), D("2000000"), D("2000000"), D("2000000"),
                                                 D("2000000"), D("500000")]
    assert plan[-1]["vnc"] == 0


def test_declining_balance_switches_to_straight_line_when_it_becomes_higher():
    plan = calculs.amortissement_degressif(D("10000000"), annees=5, coefficient=D("2"))

    assert [row["dotation"] for row in plan] == [D("4000000"), D("2400000"), D("1440000"), D("1080000"), D("1080000")]
    assert [row["vnc"] for row in plan][-1] == 0


def test_trade_then_cash_discounts_apply_in_cascade_before_vat():
    invoice = calculs.facture(D("1000000"), remise=D("10"), rabais=D("5"), ristourne=D("2"), escompte=D("1"),
                              taux_tva=D("19.25"))

    assert invoice == {"brut": D("1000000"), "net_commercial": D("837900"), "escompte": D("8379"),
                       "net_financier": D("829521"), "tva": D("159683"), "ttc": D("989204")}


def test_weighted_average_cost_values_an_issue():
    result = calculs.sortie_cmup([(100, D("1000")), (300, D("1200"))], quantite=250)

    assert (result["cout_unitaire"], result["valeur_sortie"], result["valeur_stock"]) == (D("1150"), D("287500"), D("172500"))


def test_first_in_first_out_values_an_issue_from_the_oldest_lots():
    result = calculs.sortie_peps([(100, D("1000")), (300, D("1200"))], quantite=250)

    assert (result["valeur_sortie"], result["valeur_stock"]) == (D("280000"), D("180000"))
    assert result["stock"] == [(150, D("1200"))]


def test_an_issue_larger_than_the_stock_is_refused():
    with pytest.raises(ValueError):
        calculs.sortie_peps([(100, D("1000"))], quantite=101)


# IRPP sur salaires (CGI 2026) : frais professionnels 30 % plafonnés à 4 800 000 (art. 34), abattement 500 000
# (art. 29), barème annuel (art. 69), CAC 10 % (art. 71).
BAREME = [(D("2000000"), D("10")), (D("3000000"), D("15")), (D("5000000"), D("25")), (None, D("35"))]
SALAIRE = {"taux_frais": D("30"), "plafond_frais": D("4800000"), "abattement": D("500000"), "bareme": BAREME,
           "taux_cac": D("10")}


def test_salary_income_tax_goes_through_the_progressive_scale():
    """6 000 000 brut, 252 000 CNPS : net 3 948 000, imposable 3 448 000 -> 200 000 + 150 000 + 112 000."""
    result = calculs.irpp_salaire(D("6000000"), D("252000"), **SALAIRE)

    assert (result["frais"], result["net"], result["imposable"]) == (D("1800000"), D("3948000"), D("3448000"))
    assert (result["irpp"], result["cac"], result["total"]) == (D("462000"), D("46200"), D("508200"))


def test_professional_expenses_are_capped_and_the_top_bracket_is_35_percent():
    """24 000 000 brut : frais plafonnés à 4 800 000, imposable 18 700 000 -> 850 000 + 35 % × 13 700 000."""
    result = calculs.irpp_salaire(D("24000000"), D("0"), **SALAIRE)

    assert (result["frais"], result["imposable"], result["irpp"]) == (D("4800000"), D("18700000"), D("5645000"))
    assert result["total"] == D("6209500")


def test_a_salary_under_the_allowance_owes_nothing():
    result = calculs.irpp_salaire(D("600000"), D("0"), **SALAIRE)

    assert (result["imposable"], result["total"]) == (D("0"), D("0"))


# Retenues forfaitaires sur salaire : RAV mensuelle selon le brut (loi en annexe du CGI, art. 3 (5)) ; TDL annuelle selon
# le salaire de base mensuel (CGI art. C 86) ; CFC à 1 % salarié et 2,5 % employeur, base au millier inférieur (loi 77-10).
RAV = [(D("50000"), D("0")), (D("100000"), D("750")), (D("200000"), D("1950")), (D("300000"), D("3250")),
       (D("400000"), D("4550")), (D("500000"), D("5850")), (D("600000"), D("7150")), (D("700000"), D("8450")),
       (D("800000"), D("9750")), (D("900000"), D("11050")), (D("1000000"), D("12350")), (None, D("13000"))]
TDL = [(D("61999"), D("0")), (D("75000"), D("3000")), (D("100000"), D("6000")), (D("125000"), D("9000")),
       (D("150000"), D("12000")), (D("200000"), D("15000")), (D("250000"), D("18000")), (D("300000"), D("24000")),
       (D("500000"), D("27000")), (None, D("30000"))]


@pytest.mark.parametrize("brut, rav", [("50000", "0"), ("100000", "750"), ("100001", "1950"), ("350000", "4550"),
                                       ("1000000", "12350"), ("1200000", "13000")])
def test_the_audiovisual_fee_is_a_flat_amount_per_gross_salary_bracket(brut, rav):
    assert calculs.forfait_par_tranche(D(brut), RAV) == D(rav)


@pytest.mark.parametrize("base, tdl", [("61000", "0"), ("62000", "3000"), ("250000", "18000"), ("250001", "24000"),
                                       ("600000", "30000")])
def test_the_local_development_tax_is_a_flat_yearly_amount_per_base_salary_bracket(base, tdl):
    assert calculs.forfait_par_tranche(D(base), TDL) == D(tdl)


def test_the_land_credit_contribution_is_levied_on_the_salary_rounded_down_to_the_thousand():
    assert calculs.credit_foncier(D("351750"), D("1")) == D("3510")
    assert calculs.credit_foncier(D("351750"), D("2.5")) == D("8775")
