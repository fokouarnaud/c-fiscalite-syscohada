"""Le paquet tools/schemas refuse une formation qu'il ne connaît pas."""
import subprocess
import sys

from django.conf import settings

ROOT = settings.BASE_DIR


def test_the_command_line_refuses_an_unknown_formation():
    result = subprocess.run([sys.executable, "-m", "tools.schemas", "froid"], cwd=ROOT, capture_output=True, text=True)

    assert result.returncode != 0
    assert "froid" in result.stderr


# --- US-27 (C13) : schémas de la comptabilité et de la fiscalité, en français et en anglais ---------------------------

import pytest  # noqa: E402

from config.uploads import ACTIVE_SVG  # noqa: E402


@pytest.fixture
def written(tmp_path):
    from tools.schemas import common, compta, fisca

    common.write_formation(compta, root=tmp_path)
    common.write_formation(fisca, root=tmp_path)
    return tmp_path / "static" / "content"


@pytest.mark.parametrize("path", ["compta/m1/compte-en-t.svg", "compta/m1/bilan.svg", "compta/m6/circuit-tva.svg",
                                  "compta/m20/frise-amortissement.svg", "fisca/m7/cycle-declaratif.svg"])
def test_each_diagram_is_written_in_french_and_in_english(written, path):
    slug, rest = path.split("/", 1)
    assert (written / path).exists()
    assert (written / slug / "en" / rest).exists()


def test_the_t_account_speaks_the_language_of_its_folder(written):
    assert "Débit" in (written / "compta/m1/compte-en-t.svg").read_text(encoding="utf-8")
    english = (written / "compta/en/m1/compte-en-t.svg").read_text(encoding="utf-8")
    assert "Debit" in english and "Débit" not in english


def test_the_vat_circuit_shows_the_rates_in_force_of_the_versioned_parameters(written):
    """19,25 % = 17,5 % + CAC 10 % (content/referentiel/parametres.csv), jamais un taux recopié à la main."""
    svg = (written / "compta/m6/circuit-tva.svg").read_text(encoding="utf-8")

    assert "19,25 %" in svg and "17,5 %" in svg


def test_the_depreciation_frieze_uses_the_reference_formula(written):
    """10 000 000 sur 5 ans, mise en service en avril : 1 500 000 la 1re année, 500 000 la 6e (referentiel.calculs)."""
    svg = (written / "compta/m20/frise-amortissement.svg").read_text(encoding="utf-8")

    assert "1 500 000" in svg and "500 000" in svg


def test_every_generated_diagram_is_inert(written):
    for path in written.rglob("*.svg"):
        assert not ACTIVE_SVG.search(path.read_bytes()), path


def test_the_command_line_writes_the_compta_diagrams():
    result = subprocess.run([sys.executable, "-m", "tools.schemas", "--help"], cwd=ROOT, capture_output=True, text=True)

    assert "compta" in result.stdout and "fisca" in result.stdout
