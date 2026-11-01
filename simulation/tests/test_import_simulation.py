"""US-82, US-93, US-94 : le manifeste de la simulation importe les pièces de chaque parcours, relie les questions aux
pièces de leur énoncé et règle l'examen du parcours (S5, S11)."""
import json

import pytest
from django.core.management import call_command

from assessments.models import Assessment, Question
from courses.models import Partie
from simulation.models import Piece
from simulation.tests.test_real_world_pieces import CUSTOMER, ISSUER

PIECE = {
    "ref": "S-A-01-001", "kind": "facture_achat", "date": "2026-01-05",
    "title": {"fr": "Facture d'achat n° 1", "en": "Purchase invoice no. 1"},
    "payload": {
        "issuer": ISSUER, "customer": CUSTOMER, "number": "FA-2026-0001", "einvoice": "DGI-SFE-2026-000001",
        "lines": [{"label": {"fr": "Chemises", "en": "Shirts"}, "amount": 100000}],
        "totals": [{"label": {"fr": "Total HT", "en": "Total excl. tax"}, "role": "ht", "amount": 100000}],
    },
}

QUESTION = {
    "id": "S-A-M1-001", "type": "numeric", "usage": "quiz",
    "prompt": {"fr": "Montant HT de la pièce ?\n\n[[piece:S-A-01-001]]", "en": "Amount before tax?\n\n[[piece:S-A-01-001]]"},
    "explanation": {"fr": "Total HT.", "en": "Total excl. tax."},
    "numeric": {"value": 100000, "unit": "FCFA"},
    "reviewed": {"fr": True, "en": True},
}


def write_content(root, pieces=(PIECE,), questions=(QUESTION,), exam=None):
    module_dir = root / "a" / "m1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "questions.json").write_text(json.dumps(list(questions)), encoding="utf-8")
    (root / "a" / "pieces.json").write_text(json.dumps(list(pieces)), encoding="utf-8")
    partie = {"slug": "a", "order": 1, "title": {"fr": "Parcours A", "en": "Track A"}, "pieces": "a/pieces.json",
              "modules": [{"order": 1, "dir": "a/m1", "title": {"fr": "Création", "en": "Set-up"}, "sections": []}]}
    if exam:
        partie["exam"] = exam
    manifest = {"slug": "simulation", "prefix": "S", "title": {"fr": "Simulation", "en": "Simulation"},
                "parties": [partie]}
    (root / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root / "formation.json"


def run(manifest):
    call_command("import_content", str(manifest), verbosity=0)


@pytest.mark.django_db
def test_the_pieces_of_a_parcours_are_imported_once_and_updated_in_place(tmp_path):
    manifest = write_content(tmp_path)
    run(manifest)
    changed = {**PIECE, "title": {"fr": "Facture d'achat n° 1 (Sawa Textiles)", "en": "Purchase invoice no. 1"}}
    run(write_content(tmp_path, pieces=[changed]))

    piece = Piece.objects.get()
    assert piece.partie == Partie.objects.get(slug="a")
    assert (piece.kind, piece.issued_on.isoformat()) == ("facture_achat", "2026-01-05")
    assert (piece.title_fr, piece.title_en) == ("Facture d'achat n° 1 (Sawa Textiles)", "Purchase invoice no. 1")


@pytest.mark.django_db
def test_an_incoherent_piece_stops_the_whole_import(tmp_path):
    wrong = {**PIECE, "payload": {**PIECE["payload"], "totals": [
        {"label": {"fr": "Total HT", "en": "Total"}, "role": "ht", "amount": 99000}]}}

    with pytest.raises(ValueError, match="S-A-01-001"):
        run(write_content(tmp_path, pieces=[wrong]))
    assert not Piece.objects.exists() and not Question.objects.exists()


@pytest.mark.django_db
def test_a_question_is_linked_to_the_pieces_of_its_prompt(tmp_path):
    run(write_content(tmp_path))

    assert list(Question.objects.get().pieces.values_list("ref", flat=True)) == ["S-A-01-001"]


@pytest.mark.django_db
def test_a_question_citing_an_unknown_piece_stops_the_import(tmp_path):
    question = {**QUESTION, "prompt": {"fr": "[[piece:S-A-09-999]]", "en": "[[piece:S-A-09-999]]"}}

    with pytest.raises(ValueError, match="S-A-09-999"):
        run(write_content(tmp_path, questions=[question]))


@pytest.mark.django_db
def test_the_manifest_sets_the_questions_drawn_per_module_for_the_parcours_exam(tmp_path):
    """US-94, S11 : 4 questions tirées par module, soit 28 questions pour 7 modules."""
    run(write_content(tmp_path, exam={"questions_per_module": 4}))

    assert Assessment.exam_for(Partie.objects.get(slug="a")).questions_per_module == 4


@pytest.mark.django_db
def test_without_exam_settings_the_exam_keeps_its_defaults(tmp_path):
    run(write_content(tmp_path))

    assert Assessment.exam_for(Partie.objects.get(slug="a")).questions_per_module == 10


@pytest.mark.django_db
def test_the_pieces_cited_by_the_explanation_are_linked_too(tmp_path):
    """US-85 : le formulaire rempli cité par l'explication est importé et relié à la question."""
    form = {**PIECE, "ref": "S-A-02-015", "kind": "declaration", "date": "2026-02-15"}
    question = {**QUESTION, "explanation": {"fr": "Voir [[piece:S-A-02-015]]", "en": "See [[piece:S-A-02-015]]"}}
    run(write_content(tmp_path, pieces=[PIECE, form], questions=[question]))

    assert sorted(Question.objects.get().pieces.values_list("ref", flat=True)) == ["S-A-01-001", "S-A-02-015"]


@pytest.mark.django_db
def test_an_unknown_piece_in_the_explanation_stops_the_import(tmp_path):
    question = {**QUESTION, "explanation": {"fr": "[[piece:S-A-02-999]]", "en": "[[piece:S-A-02-999]]"}}

    with pytest.raises(ValueError, match="S-A-02-999"):
        run(write_content(tmp_path, questions=[question]))


@pytest.mark.django_db
def test_the_declared_sub_accounts_join_the_chart_under_their_parent(tmp_path):
    """S19 : 5521 « MTN MoMo » est créé sous 552 pour que les questions journal puissent l'utiliser."""
    import json

    from referentiel.models import SyscohadaAccount

    SyscohadaAccount.objects.create(code="552", label_fr="Monnaie électronique")
    manifest = write_content(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["parties"][0]["sous_comptes"] = {"5521": {"fr": "MTN MoMo", "en": "MTN MoMo"}}
    manifest.write_text(json.dumps(data), encoding="utf-8")
    run(manifest)

    account = SyscohadaAccount.objects.get(code="5521")
    assert (account.parent_id, account.label_fr) == ("552", "MTN MoMo")


@pytest.mark.django_db
def test_a_sub_account_without_parent_stops_the_import(tmp_path):
    import json

    manifest = write_content(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["parties"][0]["sous_comptes"] = {"9999": {"fr": "Inventé", "en": "Made up"}}
    manifest.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="9999"):
        run(manifest)
