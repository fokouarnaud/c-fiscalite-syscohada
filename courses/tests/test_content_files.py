"""US-71 à US-73 : garde-fous BLOQUANTS du contenu versionné (content/), appliqués à chaque `pytest` avant déploiement."""
import json
import subprocess

from django.conf import settings

from courses.tests.content_rules import scan_content

ROOT = settings.BASE_DIR


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sample_tree(tmp_path, body_fr, questions):
    write(tmp_path / "referentiel" / "syscohada.csv", "code;label_fr;label_en\n601;Achats;Purchases\n401;Fournisseurs;Suppliers\n")
    write(tmp_path / "referentiel" / "parametres.csv",
          "key;exercice;value;unit;label_fr;label_en;source_article\ntva.taux_global;2026;19.25;%;TVA;VAT;CGI art. 142\n")
    manifest = {"slug": "compta", "prefix": "C", "parties": [{"slug": "p1", "modules": [
        {"order": 1, "dir": "p1/m1", "sections": [{"order": 1, "file": "01-principes", "kind": "content"}]}]}]}
    write(tmp_path / "compta" / "formation.json", json.dumps(manifest))
    write(tmp_path / "compta" / "p1" / "m1" / "01-principes.fr.md", body_fr)
    write(tmp_path / "compta" / "p1" / "m1" / "01-principes.en.md", "See [[syscohada:601]].")
    write(tmp_path / "compta" / "p1" / "m1" / "questions.json", json.dumps(questions))
    return tmp_path


def test_the_scanner_reports_every_broken_rule_of_a_sample_tree(tmp_path):
    root = sample_tree(tmp_path, "Selon le DCG, la TVA vaut [[param:tva.inconnu]] ; voir [[syscohada:4019]].", [])

    problems = scan_content(root)

    assert "compta/p1/m1/01-principes.fr.md : aucune source citée" not in problems  # [[syscohada:]] est une source
    assert "compta/p1/m1/01-principes.fr.md : compte inconnu 4019" in problems
    assert "compta/p1/m1/01-principes.fr.md : paramètre inconnu tva.inconnu" in problems
    assert "compta/p1/m1/01-principes.fr.md : livre nommé DCG" in problems
    assert "compta/p1/m1 : 0 questions d'examen sur 12" in problems


def test_a_lesson_without_any_source_is_reported(tmp_path):
    root = sample_tree(tmp_path, "La TVA est exigible à la livraison.", [])

    assert "compta/p1/m1/01-principes.fr.md : aucune source citée" in scan_content(root)


def test_a_clean_sample_tree_passes(tmp_path):
    question = {"id": "C-P1-M1-{:03}", "usage": "exam", "prompt": {"fr": "Q ?", "en": "Q?"},
                "explanation": {"fr": "Car.", "en": "Because."}}
    bank = [{**question, "id": question["id"].format(i)} for i in range(12)]
    bank += [{**question, "usage": "quiz", "id": question["id"].format(100 + i)} for i in range(8)]
    root = sample_tree(tmp_path, "On débite [[syscohada:601]] de [[param:tva.taux_global]].", bank)

    assert scan_content(root) == []


def test_the_versioned_content_breaks_no_rule():
    assert scan_content(ROOT / "content") == []


def test_the_source_books_are_never_tracked_by_git():
    """C21 : reference/ (livres protégés) reste hors du dépôt, donc hors du serveur."""
    tracked = subprocess.run(["git", "ls-files", "reference"], cwd=ROOT, capture_output=True, text=True, check=True)

    assert tracked.stdout == ""
