"""S34 : chaque parcours livré (A, B3, E) est raconté. Dans chaque section mensuelle, toute pièce comptable du mois
(hors balance d'ouverture et fiches d'inventaire, racontées au module Inventaire) apparaît dans une scène qui porte les
cinq temps du canevas, en FR comme en EN ; le dossier d'entreprise présente les personnages et les routines."""
import json

import pytest
from django.conf import settings

SIMULATION = settings.BASE_DIR / "content" / "simulation"
BEATS = {"fr": ("**La règle.**", "**Pourquoi ce choix et pas un autre.**", "**Ce que ça change.**",
                "**Où ça se range.**", "**Revoir :**"),
         "en": ("**The rule.**", "**Why this choice and not another.**", "**What it changes.**",
                "**Where it is filed.**", "**See again:**")}
UNTOLD = ("balance", "fiche_stock", "demarche")
MONTH_FILES = ("janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre",
               "novembre", "decembre")


def _sections(slug):
    for month, name in enumerate(MONTH_FILES, start=1):
        path = next(SIMULATION.joinpath(slug).glob(f"m*/0*-{name}.fr.md"))
        yield month, path


@pytest.mark.parametrize("slug", ["a", "b1", "b2", "b3", "c", "d", "e"])
@pytest.mark.parametrize("lang", ["fr", "en"])
def test_every_accounting_piece_of_a_month_is_told_in_a_full_scene(slug, lang):
    pieces = json.loads((SIMULATION / slug / "pieces.json").read_text(encoding="utf-8"))
    for month, fr_path in _sections(slug):
        body = fr_path.with_name(fr_path.name.replace(".fr.", f".{lang}.")).read_text(encoding="utf-8")
        body = body.replace(" ", " ")
        scenes = body.split("\n### ")[1:]
        expected = [p["ref"] for p in pieces if p["date"].startswith(f"2026-{month:02d}") and p["kind"] not in UNTOLD]
        for ref in expected:
            scene = next((s for s in scenes if f"[[piece:{ref}]]" in s), None)
            assert scene is not None, f"{slug} {fr_path.name} : {ref} sans scène"
            assert all(beat in scene for beat in BEATS[lang]), f"{slug} {fr_path.name} : {ref} sans les cinq temps"


@pytest.mark.parametrize("slug", ["a", "b1", "b2", "b3", "c", "d", "e"])
def test_the_company_file_presents_people_and_routines(slug):
    body = next(SIMULATION.joinpath(slug).glob("m1/01-dossier.fr.md")).read_text(encoding="utf-8")
    assert "### Les personnages" in body
    assert "routines" in body and "dix ans" in body
