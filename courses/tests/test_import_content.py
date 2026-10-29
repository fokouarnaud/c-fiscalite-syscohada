import json

import pytest
from django.core.management import call_command

from assessments.models import Question
from courses.models import Formation, Module, Section

QUESTION = {
    "id": "p1-m1-q01",
    "type": "single",
    "usage": "quiz",
    "prompt": {"fr": "Quel EPI protège les yeux ?", "en": "Which PPE protects the eyes?"},
    "explanation": {"fr": "Les lunettes.", "en": "Goggles."},
    "reviewed": {"fr": True, "en": True},
    "choices": [
        {"text": {"fr": "Lunettes", "en": "Goggles"}, "correct": True},
        {"text": {"fr": "Gants", "en": "Gloves"}, "correct": False},
    ],
}


@pytest.fixture
def content_dir(tmp_path):
    module_dir = tmp_path / "p1" / "m1"
    module_dir.mkdir(parents=True)
    (module_dir / "01-introduction.fr.md").write_text("Le **courant** tue.", encoding="utf-8")
    (module_dir / "01-introduction.en.md").write_text("Current **kills**.", encoding="utf-8")
    (module_dir / "questions.json").write_text(json.dumps([QUESTION]), encoding="utf-8")
    manifest = {
        "slug": "froid",
        "title": {"fr": "Froid et climatisation", "en": "Refrigeration and air conditioning"},
        "parties": [{
            "slug": "p1",
            "order": 1,
            "title": {"fr": "Habilitation et sécurité", "en": "Safety qualification"},
            "modules": [{
                "order": 1,
                "dir": "p1/m1",
                "title": {"fr": "Sécurité dans les travaux", "en": "Safety at work"},
                "duration_hours": 8,
                "competence": {"fr": "Identifier les risques.", "en": "Identify risks."},
                "sections": [
                    {"order": 1, "file": "01-introduction", "kind": "content",
                     "title": {"fr": "Introduction", "en": "Introduction"}},
                ],
            }],
        }],
    }
    (tmp_path / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def run_import(content_dir):
    call_command("import_content", str(content_dir / "formation.json"), verbosity=0)


@pytest.mark.django_db
def test_import_builds_the_bilingual_course_tree(content_dir):
    run_import(content_dir)
    module = Module.objects.get(partie__formation__slug="froid", order=1)
    assert module.title_en == "Safety at work"
    assert module.duration_hours == 8
    section = module.sections.get()
    assert section.body_md_fr == "Le **courant** tue."
    assert section.body_md_en == "Current **kills**."


@pytest.mark.django_db
def test_import_creates_questions_as_drafts_with_their_choices(content_dir):
    run_import(content_dir)
    question = Question.objects.get(external_id="p1-m1-q01")
    assert question.status == Question.Status.DRAFT
    assert question.prompt_en == "Which PPE protects the eyes?"
    assert [(c.text_fr, c.is_correct) for c in question.choices.all()] == [("Lunettes", True), ("Gants", False)]


@pytest.mark.django_db
def test_running_the_import_twice_creates_no_duplicates(content_dir):
    run_import(content_dir)
    run_import(content_dir)
    assert Formation.objects.count() == 1
    assert Section.objects.count() == 1
    assert Question.objects.count() == 1
    assert Question.objects.get().choices.count() == 2


@pytest.mark.django_db
def test_reimport_updates_changed_text(content_dir):
    run_import(content_dir)
    (content_dir / "p1" / "m1" / "01-introduction.fr.md").write_text("Texte corrigé.", encoding="utf-8")
    run_import(content_dir)
    assert Section.objects.get().body_md_fr == "Texte corrigé."


@pytest.mark.django_db
def test_reimport_keeps_a_published_question_published_when_unchanged(content_dir):
    run_import(content_dir)
    Question.objects.get().publish()
    run_import(content_dir)
    assert Question.objects.get().status == Question.Status.PUBLISHED


@pytest.mark.django_db
def test_reimport_sends_a_changed_published_question_back_to_draft(content_dir):
    run_import(content_dir)
    Question.objects.get().publish()
    changed = {**QUESTION, "prompt": {"fr": "Quel EPI protège la tête ?", "en": "Which PPE protects the head?"}}
    (content_dir / "p1" / "m1" / "questions.json").write_text(json.dumps([changed]), encoding="utf-8")
    run_import(content_dir)
    question = Question.objects.get()
    assert question.status == Question.Status.DRAFT
    assert question.prompt_fr == "Quel EPI protège la tête ?"


@pytest.mark.django_db
def test_missing_english_file_leaves_english_body_empty(content_dir):
    (content_dir / "p1" / "m1" / "01-introduction.en.md").unlink()
    run_import(content_dir)
    assert Section.objects.get().body_md_en in ("", None)


@pytest.mark.django_db
def test_import_reads_the_bilingual_description_of_a_partie(content_dir):
    """US-40 : la description d'une partie (ex. « à suivre après la Partie 1 ») vient du manifeste, en FR et en EN."""
    manifest_path = content_dir / "formation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["parties"][0]["description"] = {"fr": "À suivre après la Partie 1.", "en": "Best taken after Part 1."}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    run_import(content_dir)
    run_import(content_dir)

    partie = Formation.objects.get(slug="froid").parties.get()
    assert (partie.description_fr, partie.description_en) == ("À suivre après la Partie 1.", "Best taken after Part 1.")


@pytest.mark.django_db
def test_a_partie_without_description_imports_with_an_empty_one(content_dir):
    run_import(content_dir)
    partie = Formation.objects.get(slug="froid").parties.get()
    assert (partie.description_fr, partie.description_en) == ("", "")


# --- US-59 et US-62 (formation `moteurs`) : icône, plusieurs formations importées sans se toucher --------------------


def write_manifest(content_dir, **changes):
    manifest_path = content_dir / "formation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(changes)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def second_dir(tmp_path_factory):
    """Une seconde formation (`moteurs`) dans son propre dossier, avec sa propre question."""
    root = tmp_path_factory.mktemp("moteurs")
    module_dir = root / "p1" / "m1"
    module_dir.mkdir(parents=True)
    (module_dir / "01-effets.fr.md").write_text("Le corps humain conduit.", encoding="utf-8")
    (module_dir / "01-effets.en.md").write_text("The human body conducts.", encoding="utf-8")
    question = {**QUESTION, "id": "m-p1-m1-q01"}
    (module_dir / "questions.json").write_text(json.dumps([question]), encoding="utf-8")
    manifest = {
        "slug": "moteurs",
        "icon": "receipt",
        "title": {"fr": "Moteurs électriques et commande", "en": "Electric motors and control"},
        "parties": [{
            "slug": "p1", "order": 1,
            "title": {"fr": "Sécurité, schémas et distribution", "en": "Safety, diagrams and distribution"},
            "modules": [{
                "order": 1, "dir": "p1/m1", "duration_hours": 8,
                "title": {"fr": "La sécurité électrique", "en": "Electrical safety"},
                "sections": [{"order": 1, "file": "01-effets", "title": {"fr": "Effets du courant", "en": "Effects of current"}}],
            }],
        }],
    }
    (root / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


@pytest.mark.django_db
def test_import_reads_the_icon_of_the_formation(second_dir):
    run_import(second_dir)
    assert Formation.objects.get(slug="moteurs").icon == "receipt"


@pytest.mark.django_db
def test_import_refuses_an_unknown_icon_and_writes_nothing(content_dir):
    write_manifest(content_dir, icon="rocket")
    with pytest.raises(Exception) as error:
        run_import(content_dir)
    assert "rocket" in str(error.value)
    assert not Formation.objects.exists()


@pytest.mark.django_db
def test_importing_a_second_formation_leaves_the_first_one_untouched(content_dir, second_dir):
    run_import(content_dir)
    run_import(second_dir)
    run_import(second_dir)

    assert Section.objects.filter(module__partie__formation__slug="froid").count() == 1
    assert Question.objects.get(external_id="p1-m1-q01").module.partie.formation.slug == "froid"
    assert Question.objects.get(external_id="m-p1-m1-q01").module.partie.formation.slug == "moteurs"


@pytest.mark.django_db
def test_a_question_id_already_used_by_another_formation_is_refused(content_dir, second_dir):
    run_import(content_dir)
    clash = [{**QUESTION, "id": "p1-m1-q01"}]
    (second_dir / "p1" / "m1" / "questions.json").write_text(json.dumps(clash), encoding="utf-8")

    with pytest.raises(Exception) as error:
        run_import(second_dir)

    assert "p1-m1-q01" in str(error.value)
    assert Question.objects.get(external_id="p1-m1-q01").module.partie.formation.slug == "froid"
    assert not Formation.objects.filter(slug="moteurs").exists()


@pytest.mark.django_db
def test_import_content_takes_every_manifest_given(content_dir, second_dir):
    """US-63 : deploy.sh passe tous les content/*/formation.json en une commande."""
    call_command("import_content", str(content_dir / "formation.json"), str(second_dir / "formation.json"), verbosity=0)

    assert list(Formation.objects.values_list("slug", flat=True).order_by("slug")) == ["froid", "moteurs"]


@pytest.mark.django_db
def test_import_reads_the_legal_reference_of_the_formation(tmp_path):
    """US-25 : la référence juridique vient du manifeste, en français et en anglais."""
    manifest = {"slug": "fisca", "title": {"fr": "Fiscalité", "en": "Taxation"},
                "legal_reference": {"fr": "CGI Cameroun, éd. 2026", "en": "Cameroon GTC, 2026 ed."}, "parties": []}
    (tmp_path / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")

    call_command("import_content", str(tmp_path / "formation.json"), verbosity=0)

    formation = Formation.objects.get(slug="fisca")
    assert (formation.legal_reference_fr, formation.legal_reference_en) == ("CGI Cameroun, éd. 2026", "Cameroon GTC, 2026 ed.")


def prefixed_manifest(tmp_path, question_id):
    module_dir = tmp_path / "p1" / "m1"
    module_dir.mkdir(parents=True)
    (module_dir / "questions.json").write_text(json.dumps([{**QUESTION, "id": question_id}]), encoding="utf-8")
    manifest = {"slug": "compta", "prefix": "C", "title": {"fr": "Comptabilité", "en": "Accounting"},
                "parties": [{"slug": "p1", "order": 1, "title": {"fr": "P1", "en": "P1"},
                             "modules": [{"order": 1, "dir": "p1/m1", "title": {"fr": "M1", "en": "M1"}, "sections": []}]}]}
    (tmp_path / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path / "formation.json"


@pytest.mark.django_db
def test_a_question_without_the_prefix_of_its_formation_is_refused_and_nothing_is_imported(tmp_path):
    """US-70 (U10) : le manifeste déclare son préfixe ; « F-… » dans la compta est une erreur de rangement."""
    with pytest.raises(ValueError) as error:
        call_command("import_content", str(prefixed_manifest(tmp_path, "F-P1-M1-001")), verbosity=0)

    assert "F-P1-M1-001" in str(error.value)
    assert not Formation.objects.filter(slug="compta").exists()


@pytest.mark.django_db
def test_a_question_with_the_prefix_of_its_formation_is_imported(tmp_path):
    call_command("import_content", str(prefixed_manifest(tmp_path, "C-P1-M1-001")), verbosity=0)

    assert Question.objects.filter(external_id="C-P1-M1-001").exists()


@pytest.mark.django_db
def test_us15_import_reads_the_advisory_prerequisite_of_the_formation(tmp_path):
    """US-15 : le prérequis indicatif vient du manifeste, en français et en anglais."""
    manifest = {"slug": "fisca", "title": {"fr": "Fiscalité", "en": "Taxation"},
                "prerequisite_note": {"fr": "Recommandé après", "en": "Recommended after"}, "parties": []}
    (tmp_path / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")

    call_command("import_content", str(tmp_path / "formation.json"), verbosity=0)

    formation = Formation.objects.get(slug="fisca")
    assert (formation.prerequisite_note_fr, formation.prerequisite_note_en) == ("Recommandé après", "Recommended after")
