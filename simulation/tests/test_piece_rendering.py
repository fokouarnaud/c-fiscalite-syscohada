"""US-82 : [[piece:REF]] affiche la pièce en HTML, après bleach, dans la langue courante (S5, C27)."""
import datetime
from decimal import Decimal

import pytest
from django.utils import translation

from assessments.scoring import format_quantity
from courses.rendering import render_markdown
from simulation.models import Piece


@pytest.fixture
def piece(partie):
    return Piece.objects.create(
        partie=partie, ref="S-A-01-001", kind=Piece.Kind.PURCHASE_INVOICE, issued_on=datetime.date(2026, 1, 5),
        title_fr="Facture d'achat n° 1", title_en="Purchase invoice no. 1",
        payload={
            "fields": [{"label": {"fr": "Fournisseur", "en": "Supplier"}, "value": "Sawa <b>Textiles</b> SARL"}],
            "lines": [{"label": {"fr": "Chemises", "en": "Shirts"}, "qty": 20, "unit_price": 5000, "amount": 100000}],
            "totals": [{"label": {"fr": "Total HT", "en": "Total excl. tax"}, "role": "ht", "amount": 100000}],
        },
    )


def test_a_piece_tag_alone_in_its_paragraph_becomes_the_document(piece):
    html = render_markdown("Voici la pièce :\n\n[[piece:S-A-01-001]]\n")

    assert '<figure class="piece"' in html
    assert "<p>[[piece:" not in html
    assert "Facture d'achat n° 1" in html or "Facture d&#x27;achat n° 1" in html
    assert "<caption>" in html
    assert "Chemises" in html and "Fournisseur" in html
    assert format_quantity(Decimal(100000), "FCFA") in html


def test_the_piece_is_shown_in_the_current_language(piece):
    with translation.override("en"):
        html = render_markdown("[[piece:S-A-01-001]]")

    assert "Shirts" in html and "Supplier" in html and "Purchase invoice no. 1" in html
    assert "Chemises" not in html


def test_the_values_of_a_piece_are_escaped(piece):
    html = render_markdown("[[piece:S-A-01-001]]")

    assert "<b>Textiles</b>" not in html
    assert "&lt;b&gt;Textiles&lt;/b&gt;" in html


def test_an_unknown_piece_is_flagged_never_shown_raw(db):
    html = render_markdown("[[piece:S-A-99-999]]")

    assert '<mark class="piece-missing">S-A-99-999</mark>' in html
    assert "[[piece:" not in html


def test_a_wide_piece_scrolls_inside_its_frame_on_a_390px_phone():
    """NFR-09 : un tableau large défile dans son conteneur ; la page ne déborde jamais horizontalement."""
    import re
    from pathlib import Path

    css = (Path(__file__).resolve().parents[2] / "static/acad/css/app.css").read_text(encoding="utf-8")
    frame = re.search(r"\n\.piece \{([^}]*)\}", css)
    scroller = re.search(r"\n\.piece-scroll \{([^}]*)\}", css)
    assert frame and "max-width: 100%" in frame.group(1)
    assert scroller and "overflow-x: auto" in scroller.group(1)


def test_a_piece_in_a_question_never_widens_the_attempt_page():
    """NFR-09, constaté au parcours en navigateur (390 px) : la grille des questions ne s'élargit pas au tableau d'une
    pièce ; sa colonne est bornée à la largeur disponible et le tableau défile dans son cadre."""
    import re
    from pathlib import Path

    css = (Path(__file__).resolve().parents[2] / "static/acad/css/app.css").read_text(encoding="utf-8")
    for selector in (r"\.questions", r"\.review"):  # tentative, puis correction du quiz
        grid = re.search(r"\n%s \{([^}]*)\}" % selector, css)
        assert grid and "grid-template-columns: minmax(0, 1fr)" in grid.group(1), selector


def test_the_fields_of_a_piece_stay_readable_on_a_390px_phone():
    """NFR-09, constaté au parcours en navigateur : un long libellé (« Référence de facturation électronique DGI ») ne
    doit pas écraser la colonne des valeurs ; les deux colonnes sont bornées et les libellés peuvent passer à la ligne."""
    import re
    from pathlib import Path

    css = (Path(__file__).resolve().parents[2] / "static/acad/css/app.css").read_text(encoding="utf-8")
    fields = re.search(r"\n\.piece-fields \{([^}]*)\}", css)
    labels = re.search(r"\n\.piece-fields dt \{([^}]*)\}", css)
    assert fields and "grid-template-columns: minmax(0, 2fr) minmax(0, 3fr)" in fields.group(1)
    assert labels and "overflow-wrap: anywhere" in labels.group(1)


@pytest.mark.django_db
def test_a_piece_with_totals_only_has_no_empty_column_header(partie):
    """Constaté sur les captures de la DoD-Parcours : un relevé ou une déclaration sans lignes n'affiche pas d'en-tête
    « Libellé » au-dessus d'une colonne vide."""
    Piece.objects.create(partie=partie, ref="S-A-01-020", kind=Piece.Kind.MOMO_STATEMENT,
                         issued_on=datetime.date(2026, 1, 31), title_fr="Relevé",
                         payload={"totals": [{"label": {"fr": "Frais", "en": "Fees"}, "amount": 9500}]})

    html = render_markdown("[[piece:S-A-01-020]]")

    assert "<tfoot>" in html and "<thead>" not in html
