"""US-93 (S29) : les générateurs de parcours nomment pièces et questions par la lettre du parcours et fusionnent leur
partie dans formation.json sans écraser les autres parcours, rangés dans l'ordre de livraison (S20)."""
import json

from tools.simulation import build_parcours_a as gen


def test_a_book_names_pieces_and_questions_after_its_parcours():
    book = gen.Book("E")

    piece = book.piece(1, "recu_caisse", gen.d(1, 5), "Reçu", "Receipt", {})
    question = book.numeric(1, "exam", 1, "Montant ?", "Amount?", "Pourquoi.", "Why.", piece=piece)

    assert (piece, question) == ("S-E-01-001", "S-E-M1-001")
    assert gen.Book().piece(1, "recu_caisse", gen.d(1, 5), "Reçu", "Receipt", {}) == "S-A-01-001"


def test_writing_one_parcours_keeps_the_others_in_delivery_order(tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "OUT", tmp_path)
    gen.write(tmp_path / "formation.json", {"slug": "simulation", "parties": [{"slug": "a", "title": "A v1"}]})

    gen.write_manifest({}, {"slug": "e", "title": "E"})
    gen.write_manifest({"slug": "simulation"}, {"slug": "a", "title": "A v2"})

    parties = json.loads((tmp_path / "formation.json").read_text(encoding="utf-8"))["parties"]
    assert [(p["slug"], p["title"], p["order"]) for p in parties] == [("a", "A v2", 1), ("e", "E", 2)]
