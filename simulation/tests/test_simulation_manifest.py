"""US-80 : programme de la simulation : icône propre, prérequis indicatif bilingue, 7 modules par parcours et examen à
4 questions tirées par module (S11, S21, U14)."""
import json
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from courses.models import Formation
from courses.tests.content_rules import manifest_problems


def test_the_simulation_has_its_own_tabler_icon():
    assert "briefcase" in Formation.Icon.values
    svg = Path(settings.BASE_DIR, "templates", "icons", "briefcase.svg").read_text(encoding="utf-8")
    assert svg.lstrip().startswith("<!-- Tabler Icons") and 'aria-hidden="true"' in svg


@pytest.mark.django_db
def test_the_import_accepts_the_simulation_icon(tmp_path):
    manifest = {"slug": "simulation", "prefix": "S", "icon": "briefcase", "title": {"fr": "Simulation", "en": "Simulation"}}
    (tmp_path / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")

    call_command("import_content", str(tmp_path / "formation.json"), verbosity=0)

    assert Formation.objects.get(slug="simulation").icon == "briefcase"


def manifest(**changes):
    modules = [{"order": n, "dir": f"a/m{n}", "sections": []} for n in range(1, 8)]
    data = {"slug": "simulation", "prefix": "S", "icon": "briefcase",
            "prerequisite_note": {"fr": "Recommandé après Comptabilité et Fiscalité.",
                                  "en": "Recommended after Accounting and Taxation."},
            "parties": [{"slug": "a", "exam": {"questions_per_module": 4}, "modules": modules, "centre_impots": "cime",
                         "description": {"fr": "SARL au réel, boutique de vêtements.", "en": "Actual-regime LLC."}}]}
    data.update(changes)
    return data


def test_a_complete_simulation_manifest_has_no_problem():
    assert manifest_problems(manifest()) == []


def test_a_parcours_needs_its_seven_modules():
    data = manifest()
    data["parties"][0]["modules"] = data["parties"][0]["modules"][:6]

    assert any("a" in p and "7 modules" in p for p in manifest_problems(data))


def test_a_parcours_exam_draws_four_questions_per_module():
    data = manifest()
    del data["parties"][0]["exam"]

    assert any("questions_per_module" in p for p in manifest_problems(data))


def test_the_prerequisite_note_is_bilingual_and_never_blocking():
    assert any("prérequis" in p for p in manifest_problems(manifest(prerequisite_note={"fr": "Après Form 1."})))


def test_the_simulation_uses_its_own_icon():
    assert any("icône" in p for p in manifest_problems(manifest(icon="ledger")))


def test_other_formations_are_not_held_to_the_simulation_structure():
    assert manifest_problems({"slug": "compta", "prefix": "C", "parties": [{"slug": "p1", "modules": []}]}) == []


def test_parcours_a_is_attached_to_the_medium_enterprise_tax_office():
    """S25 (par défaut) : Ngono Mode SARL (90 millions de CA) relève du CIME ; DSF au plus tard le 15 avril 2027."""
    data = manifest()
    data["parties"][0]["centre_impots"] = "dge"

    assert any("a" in p and "cime" in p for p in manifest_problems(data))


def test_an_igs_parcours_declares_the_minimal_cash_system():
    """S14, S26 : un parcours à l'IGS tient le SMT ; ses seuils (AUDCIF, absent des sources) ne sont pas codés."""
    data = manifest()
    data["parties"][0].update(slug="b1", regime="igs",
                              description={"fr": "Établissement à l'IGS, dépôt de boissons.", "en": "IGS sole trader."})

    assert any("b1" in p and "systeme_comptable" in p for p in manifest_problems(data))
    data["parties"][0]["systeme_comptable"] = "smt"
    assert [p for p in manifest_problems(data) if "ordre des parcours" not in p] == []
