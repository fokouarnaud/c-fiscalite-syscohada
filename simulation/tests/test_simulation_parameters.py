"""US-95 : les taux de la simulation sont dans parametres.csv, chacun avec son article du CGI ; un taux sans article
est refusé à l'import (S10, S15)."""
import csv
from decimal import Decimal
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

CSV = Path(__file__).resolve().parents[2] / "content" / "referentiel" / "parametres.csv"
HEADER = "key;exercice;value;unit;label_fr;label_en;source_article\n"

EXPECTED = {
    "precompte.taux_reel": (Decimal("2"), "CGI art. 21"),
    "precompte.taux_igs": (Decimal("5"), "CGI art. 21"),
    "precompte.taux_hors_fichier": (Decimal("10"), "CGI art. 21"),
    "retenue.commande_publique": (Decimal("5"), "CGI art. 21"),
    "retenue.honoraires": (Decimal("5"), "CGI art. 92 bis"),
    "accises.biere_65cl": (Decimal("75"), "CGI art. 142"),
    "accises.biere_33cl": (Decimal("37.5"), "CGI art. 142"),
    "ircm.taux": (Decimal("15"), "CGI art. 70"),
}
# US-90 (U19) : tarifs de l'IGS, CGI art. C 40 (1) ; le plafond d'une classe en est exclu.
IGS = [(500000, 20000), (1000000, 30000), (1500000, 40000), (2000000, 50000), (2500000, 60000),
       (5000000, 150000), (10000000, 300000), (20000000, 500000), (30000000, 1000000), (50000000, 2000000)]
# Passerelle (S21, U19) : CGI art. 7 : taux d'amortissement maximal, limites des dons, seuil du petit matériel.
EXPECTED.update({
    "amortissement.taux_max_auto_leger_ville": (Decimal("25"), "CGI art. 7"),
    "dons.plafond_interet_general": (Decimal("0.5"), "CGI art. 7"),
    "dons.plafond_sport_elite": (Decimal("5"), "CGI art. 7"),
    "petit_materiel.seuil": (Decimal("500000"), "CGI art. 7"),
    "precompte.taux_loyer": (Decimal("10"), "CGI art. 87"),
})
for number, (ceiling, amount) in enumerate(IGS, start=1):
    EXPECTED[f"igs.classe{number}_plafond"] = (Decimal(ceiling), "CGI art. C 40")
    EXPECTED[f"igs.classe{number}_montant"] = (Decimal(amount), "CGI art. C 40")


def test_a_rate_without_its_article_is_refused(db, tmp_path):
    path = tmp_path / "parametres.csv"
    path.write_text(HEADER + "precompte.taux_reel;2026;2;%;Précompte;Withholding;\n", encoding="utf-8")

    with pytest.raises(CommandError, match="article"):
        call_command("import_parameters", str(path), verbosity=0)


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_the_simulation_rates_are_shipped_with_their_article(key):
    rows = {row["key"]: row for row in csv.DictReader(CSV.open(encoding="utf-8"), delimiter=";")}

    value, article = EXPECTED[key]
    assert key in rows, f"{key} absent de parametres.csv"
    assert Decimal(rows[key]["value"]) == value
    assert rows[key]["source_article"].startswith(article)
    assert rows[key]["exercice"] == "2026"
