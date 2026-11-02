"""US-97, S25, S26 : sources officielles trouvées le 2026-10-30 hors de reference/ initial.

- AUDCIF art. 13 (JO OHADA, numéro spécial du 15 février 2017) : seuils du SMT (60, 40 et 30 millions).
- DGI (impots.cm, CIME) : rattachement au CIME de 50 millions à 3 milliards de CA, à la DGE au-delà.
- MINFI (CFCE) : pièces à fournir pour créer une SARL ou un établissement, citées par [[source:clé]].
"""
import csv
import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError

from courses.rendering import render_markdown
from simulation.models import Piece
from simulation.tests.test_real_world_pieces import PROCEDURE
from simulation.tests.test_simulation_content_rules import simulation_problems, tree
from tools.simulation import ledger

ROOT = Path(__file__).resolve().parents[2]


def shipped_parameters():
    with open(ROOT / "content" / "referentiel" / "parametres.csv", encoding="utf-8", newline="") as handle:
        return {row["key"]: row for row in csv.DictReader(handle, delimiter=";")}


@pytest.mark.parametrize("key, value, source", [
    ("smt.seuil_negoce", "60000000", "AUDCIF art. 13"),
    ("smt.seuil_artisanat", "40000000", "AUDCIF art. 13"),
    ("smt.seuil_services", "30000000", "AUDCIF art. 13"),
    ("dgi.seuil_cime", "50000000", "DGI"),
    ("dgi.seuil_dge", "3000000000", "DGI"),
])
def test_the_thresholds_found_in_official_sources_are_parameters(key, value, source):
    row = shipped_parameters()[key]

    assert Decimal(row["value"]) == Decimal(value) and row["source_article"].startswith(source)


def test_the_tax_office_follows_the_turnover():
    """S25 : CIME de 50 millions à 3 milliards (DGI) ; Ngono Mode, environ 90 millions, relève du CIME."""
    cime, dge = Decimal("50000000"), Decimal("3000000000")

    assert ledger.tax_office(90000000, cime, dge) == "cime"
    assert ledger.tax_office(49999999, cime, dge) == "cfl"
    assert ledger.tax_office(3000000000, cime, dge) == "dge"


def thresholds_tree(tmp_path, **kwargs):
    root = tree(tmp_path, **kwargs)
    with open(root / "referentiel" / "parametres.csv", "a", encoding="utf-8") as handle:
        handle.write("dgi.seuil_cime;2026;50000000;FCFA;Seuil CIME;MTO threshold;DGI\n"
                     "dgi.seuil_dge;2026;3000000000;FCFA;Seuil DGE;LTO threshold;DGI\n"
                     "smt.seuil_negoce;2026;60000000;FCFA;Seuil SMT négoce;SMT trading;AUDCIF art. 13\n")
    return root


def set_turnover(root, turnover):
    import json

    path = root / "simulation" / "formation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["parties"][0]["chiffre_affaires_vise"] = turnover
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return root


def test_the_declared_tax_office_matches_the_target_turnover(tmp_path):
    assert not any("centre" in p for p in simulation_problems(set_turnover(thresholds_tree(tmp_path, slug="b3"), 90000000)))
    problems = simulation_problems(set_turnover(thresholds_tree(tmp_path, centre="dge", slug="b3"), 90000000))
    assert any("centre_impots" in p and "cime" in p for p in problems)


def test_an_igs_parcours_stays_under_the_smt_threshold(tmp_path):
    """S26 (AUDCIF art. 13) : le SMT n'est ouvert à une entité de négoce que sous 60 millions de CA."""
    from simulation.tests.test_simulation_content_rules import IGS, SMT_Q

    def igs_tree(turnover):
        return set_turnover(thresholds_tree(tmp_path, questions=[SMT_Q], regime="igs", centre="cfl", **IGS), turnover)

    # « hors du SMT » : le seuil de l'AUDCIF ; la DSF du SMT exigée dès 10 millions (S38) a son propre test.
    assert not any("hors du SMT" in p for p in simulation_problems(igs_tree(42000000)))
    assert any("hors du SMT" in p and "60000000" in p for p in simulation_problems(igs_tree(65000000)))


def test_a_procedure_may_cite_a_registered_official_web_source(partie):
    """US-97 : une démarche hors CGI cite une page officielle enregistrée dans content/referentiel/sources.csv."""
    piece = Piece(partie=partie, ref="S-A-01-004", kind=Piece.Kind.PROCEDURE, issued_on=datetime.date(2026, 1, 2),
                  payload={**PROCEDURE, "source": "[[source:minfi-cfce]]"})

    piece.full_clean()


@pytest.mark.django_db
def test_an_official_web_source_is_rendered_with_its_body_and_address():
    html = render_markdown("Voir [[source:minfi-cfce]].")

    assert '<cite class="source"' in html and "MINFI" in html and "minfi.gov.cm" in html


@pytest.mark.django_db
def test_an_unknown_web_source_is_flagged():
    assert '<mark class="source-missing">inconnue</mark>' in render_markdown("[[source:inconnue]]")


def test_the_cnps_faq_is_a_registered_source():
    """US-97 : dossiers d'immatriculation employeur et travailleur (FAQ officielle de la CNPS, copie archivée)."""
    with open(ROOT / "content" / "referentiel" / "sources.csv", encoding="utf-8", newline="") as handle:
        sources = {row["key"]: row for row in csv.DictReader(handle, delimiter=";")}

    assert sources["cnps-faq"]["organisme"] == "CNPS" and "cnps.cm" in sources["cnps-faq"]["url"]


def test_an_unknown_source_key_in_the_content_is_reported(tmp_path):
    """US-97 : une balise [[source:]] absente du registre fait échouer les contrôles de contenu."""
    root = tree(tmp_path, body="Ngono Mode SARL. [[syscohada:6011]] [[param:tva.taux_global]] [[source:inventee]]")
    (root / "referentiel" / "sources.csv").write_text("key;organisme;titre_fr;titre_en;url;consulte_le\n", encoding="utf-8")

    assert any("inventee" in p and "source" in p for p in simulation_problems(root))


@pytest.mark.parametrize("key, body, host", [
    ("orange-om-partenaire", "Orange Cameroun", "orange.cm"),
    ("sg-cm-compte-entreprise", "Société Générale Cameroun", "societegenerale.cm"),
])
def test_the_payment_and_bank_requirements_are_registered_sources(key, body, host):
    """US-97 : compte marchand Orange Money (RCCM, carte de contribuable, patente, statuts, CNI du gérant, RIB) et
    compte bancaire d'entreprise ; les pièces de la simulation restent émises par des organismes fictifs."""
    with open(ROOT / "content" / "referentiel" / "sources.csv", encoding="utf-8", newline="") as handle:
        sources = {row["key"]: row for row in csv.DictReader(handle, delimiter=";")}

    assert sources[key]["organisme"] == body and host in sources[key]["url"]


@pytest.mark.parametrize("key, value, source", [
    ("sarl.capital_minimum", "100000", "Loi n° 2016/014 art. 2"),
    ("sarl.part_minimum", "5000", "Loi n° 2016/014 art. 2"),
    ("sarl.seuil_notaire_facultatif", "1000000", "Loi n° 2016/014 art. 4"),
])
def test_the_cameroonian_llc_minimums_are_parameters(key, value, source):
    """S29 : capital minimum d'une SARL au Cameroun (loi n° 2016/014, qui déroge à l'AUSCGIE art. 311 : 1 000 000)."""
    row = shipped_parameters()[key]

    assert Decimal(row["value"]) == Decimal(value) and row["source_article"].startswith(source)


def test_the_llc_law_and_the_auscgie_are_registered_sources():
    with open(ROOT / "content" / "referentiel" / "sources.csv", encoding="utf-8", newline="") as handle:
        sources = {row["key"]: row for row in csv.DictReader(handle, delimiter=";")}

    assert "assnat.cm" in sources["loi-2016-014"]["url"] and "biblio.ohada.org" in sources["ohada-auscgie"]["url"]
