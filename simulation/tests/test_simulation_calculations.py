"""US-92 : retenue à la source subie par le prestataire D, au franc près (CGI art. 21 (2), S10)."""
from decimal import Decimal

from referentiel.calculs import retenue_source


def test_the_public_procurement_withholding_is_five_percent_plus_council_cents():
    """5 % du HT majorés de 10 % de CAC : 5,5 % en tout."""
    assert retenue_source(Decimal("1000000"), Decimal("5"), Decimal("10")) == {
        "principal": Decimal("50000"), "cac": Decimal("5000"), "retenue": Decimal("55000")}


def test_the_off_file_rate_gives_eleven_percent():
    """Contraste (S10) : 10 % + CAC = 11 % pour une entreprise absente du fichier des contribuables actifs."""
    assert retenue_source(Decimal("1000000"), Decimal("10"), Decimal("10"))["retenue"] == Decimal("110000")


def test_each_part_is_rounded_to_the_franc():
    """123 457 × 5 % = 6 172,85 → 6 173 ; CAC 617,3 → 617 ; retenue 6 790."""
    assert retenue_source(Decimal("123457"), Decimal("5"), Decimal("10"))["retenue"] == Decimal("6790")


IGS_BRACKETS = [(500000, 20000), (1000000, 30000), (1500000, 40000), (2000000, 50000), (2500000, 60000),
                (5000000, 150000), (10000000, 300000), (20000000, 500000), (30000000, 1000000), (50000000, 2000000)]


def test_the_igs_is_a_flat_amount_by_turnover_class():
    """US-90 (U19) : CGI art. C 40 (1), chaque borne est exclue de sa classe (« inférieur à »)."""
    from referentiel.calculs import igs_annuel

    brackets = [(Decimal(c), Decimal(m)) for c, m in IGS_BRACKETS]
    assert igs_annuel(Decimal("499999"), brackets) == Decimal("20000")
    assert igs_annuel(Decimal("500000"), brackets) == Decimal("30000")
    assert igs_annuel(Decimal("4999999"), brackets) == Decimal("150000")
    assert igs_annuel(Decimal("5000000"), brackets) == Decimal("300000")
    assert igs_annuel(Decimal("49999999"), brackets) == Decimal("2000000")


def test_a_registered_management_centre_halves_the_igs():
    """CGI art. C 40 (2) : tarif réduit de moitié en cas d'adhésion à un Centre de Gestion Agréé."""
    from referentiel.calculs import igs_annuel

    brackets = [(Decimal(c), Decimal(m)) for c, m in IGS_BRACKETS]
    assert igs_annuel(Decimal("42000000"), brackets, centre_agree=True) == Decimal("1000000")


def test_fifty_million_of_turnover_leaves_the_igs():
    """CGI art. C 39 et 93 quater : à 50 000 000 FCFA, le contribuable relève du réel."""
    import pytest

    from referentiel.calculs import igs_annuel

    brackets = [(Decimal(c), Decimal(m)) for c, m in IGS_BRACKETS]
    with pytest.raises(ValueError, match="réel"):
        igs_annuel(Decimal("50000000"), brackets)


def test_depreciation_above_the_maximum_tax_rate_is_added_back():
    """US-89 (S21, CGI art. 7) : voiture légère de 12 000 000 utilisée en ville, mise en service le 1er avril :
    déductible 12 000 000 × 25 % × 9/12 = 2 250 000 ; dotation comptable de 3 000 000 → 750 000 réintégrés."""
    from referentiel.calculs import reintegration_amortissement

    assert reintegration_amortissement(Decimal("3000000"), Decimal("12000000"), Decimal("25"), 9) == Decimal("750000")
    assert reintegration_amortissement(Decimal("2000000"), Decimal("12000000"), Decimal("25"), 9) == Decimal("0")


def test_gifts_above_half_a_percent_of_turnover_are_added_back():
    """US-89 (S21, CGI art. 7) : dons de 600 000 à une oeuvre d'intérêt général, CA de 90 000 000 :
    limite 450 000 → 150 000 réintégrés."""
    from referentiel.calculs import reintegration_dons

    assert reintegration_dons(Decimal("600000"), Decimal("90000000"), Decimal("0.5")) == Decimal("150000")
    assert reintegration_dons(Decimal("400000"), Decimal("90000000"), Decimal("0.5")) == Decimal("0")
