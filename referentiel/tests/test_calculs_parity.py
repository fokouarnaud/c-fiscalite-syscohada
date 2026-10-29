"""US-26 (U3) : les calculateurs du navigateur (static/acad/js/calc-core.js) donnent exactement les résultats des formules
de référence Python, sur les mêmes vecteurs calculés à la main (vectors.json).

Le moteur JS est exécuté par Node quand il est présent (poste de développement) ; sans Node, seule la moitié Python court.
"""
import json
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings

from referentiel import calculs

VECTORS = json.loads((Path(__file__).parent / "vectors.json").read_text(encoding="utf-8"))
NODE = shutil.which("node")
CORE = settings.BASE_DIR / "static" / "acad" / "js" / "calc-core.js"


def to_python(value):
    if isinstance(value, list):
        return [to_python(v) for v in value]
    return None if value is None else Decimal(value)


def normalized(value):
    """Résultat ramené à des chaînes d'entiers, comme dans vectors.json."""
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(v) for v in value]
    return str(Decimal(value).quantize(Decimal("1")))


def python_args(vector):
    args = [to_python(arg) for arg in vector["args"]]
    if vector["fn"] in ("amortissement_lineaire", "amortissement_degressif"):
        args[1] = int(args[1])
        if vector["fn"] == "amortissement_lineaire":
            args[2] = int(args[2])
    if vector["fn"] in ("sortie_cmup", "sortie_peps"):
        args = [[(int(q), c) for q, c in args[0]], int(args[1])]
    if vector["fn"] == "irpp_salaire":
        args[5] = [tuple(row) for row in args[5]]
    if vector["fn"] == "forfait_par_tranche":
        args[1] = [tuple(row) for row in args[1]]
    return args


@pytest.mark.parametrize("vector", VECTORS, ids=lambda v: v["fn"])
def test_the_python_reference_formula_matches_the_hand_computed_vector(vector):
    assert normalized(getattr(calculs, vector["fn"])(*python_args(vector))) == vector["expected"]


@pytest.mark.skipif(NODE is None, reason="Node absent : la parité JS se vérifie sur le poste de développement")
def test_the_browser_engine_matches_every_hand_computed_vector():
    harness = (
        "const core = require(process.argv[1]);"
        "const vectors = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "process.stdout.write(JSON.stringify(vectors.map(v => core[v.fn](...v.args))));"
    )
    run = subprocess.run([NODE, "-e", harness, str(CORE)], input=json.dumps(VECTORS), capture_output=True, text=True,
                         check=True)

    results = json.loads(run.stdout)
    for vector, result in zip(VECTORS, results):
        assert normalized(result) == vector["expected"], vector["fn"]


NUMBERS = ["1250000", "1 250 000", "1\u00a0250\u00a0000", "1.250.000", "1.250", "19,25", "19.25", "1,000,000",
           "1,250,000.50", "1.250.000,50", "0", "", "abc", "1..250", "4,7 k"]


@pytest.mark.skipif(NODE is None, reason="Node absent : la parité JS se vérifie sur le poste de développement")
def test_the_browser_reads_amounts_like_the_server():
    """Une saisie acceptée (ou refusée) par la correction serveur l'est aussi par les calculateurs (C11)."""
    from assessments.scoring import parse_quantity

    harness = (
        "const core = require(process.argv[1]);"
        "const texts = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "process.stdout.write(JSON.stringify(texts.map(t => { const v = core.lire_nombre(t); "
        "return Number.isNaN(v) ? null : v; })));"
    )
    run = subprocess.run([NODE, "-e", harness, str(CORE)], input=json.dumps(NUMBERS), capture_output=True, text=True,
                         check=True)

    expected = [None if parse_quantity(t) is None or parse_quantity(t)[1] else float(parse_quantity(t)[0]) for t in NUMBERS]
    assert json.loads(run.stdout) == expected
