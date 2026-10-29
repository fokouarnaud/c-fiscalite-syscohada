import pytest

from courses.rendering import render_markdown


def test_markdown_emphasis_becomes_html():
    assert render_markdown("**EPI**") == "<p><strong>EPI</strong></p>"


def test_script_tags_are_neutralised():
    html = render_markdown("<script>alert(1)</script>")
    assert "<script>" not in html


def test_javascript_links_are_dropped():
    assert "javascript:" not in render_markdown("[x](javascript:alert(1))")


def test_tables_and_images_are_kept():
    html = render_markdown("| a |\n|---|\n| 1 |\n\n![EPI](/media/epi.webp)")
    assert "<table>" in html
    assert '<img alt="EPI" src="/media/epi.webp">' in html


def test_calculator_marker_becomes_an_inert_widget_slot():
    html = render_markdown("Essayez :\n\n[[calc:tva]]")

    assert '<div class="calc" data-calc="tva"></div>' in html
    assert "[[calc" not in html


@pytest.mark.parametrize("kind", ["tva", "amortissement", "paie", "is", "reduction", "stock"])
def test_every_business_calculator_is_accepted(kind):
    """US-26 (C12) : les six calculateurs métier."""
    assert f'<div class="calc" data-calc="{kind}"></div>' in render_markdown(f"[[calc:{kind}]]")


def test_the_electronics_calculators_are_gone():
    assert "data-calc" not in render_markdown("[[calc:ohm]]")


def test_unknown_calculator_stays_plain_text():
    html = render_markdown("[[calc:rm-rf]]")

    assert "data-calc" not in html
    assert "[[calc:rm-rf]]" in html


def test_calculator_marker_inside_a_sentence_is_not_expanded():
    assert "data-calc" not in render_markdown("Le marqueur [[calc:tva]] doit être seul sur sa ligne.")


def test_markup_cannot_forge_a_calculator_slot():
    html = render_markdown('<div class="calc" data-calc="tva" onclick="alert(1)"></div>')

    assert "data-calc" not in html and "onclick" not in html


def test_diagrams_link_to_their_full_size_file():
    html = render_markdown("![Loi d'Ohm](/static/content/electro/m1/ohm-circuit.svg)")

    assert '<a class="figure-zoom" href="/static/content/electro/m1/ohm-circuit.svg">' in html
    assert '<img alt="Loi d\'Ohm" src="/static/content/electro/m1/ohm-circuit.svg"></a>' in html


def test_other_images_are_not_wrapped():
    assert "figure-zoom" not in render_markdown("![Photo](/media/epi.webp)")


def test_external_svg_is_never_linked():
    assert "figure-zoom" not in render_markdown("![x](https://evil.example/x.svg)")
