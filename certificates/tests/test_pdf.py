"""Mini-générateur PDF (décision du 2026-10-18 : aucune dépendance) pour le certificat (US-25)."""
import re

from certificates.pdf import build_certificate_pdf

LINES = ["Certificat de réussite", "Awa Nkoulou", "Électronique DC et semi-conducteurs", "Score : 85 %"]


def test_pdf_is_a_complete_pdf_document():
    data = build_certificate_pdf(LINES)

    assert data.startswith(b"%PDF-1.4")
    assert data.rstrip().endswith(b"%%EOF")


def test_startxref_points_at_the_cross_reference_table():
    data = build_certificate_pdf(LINES)

    offset = int(re.search(rb"startxref\s+(\d+)", data).group(1))
    assert data[offset:offset + 4] == b"xref"


def test_every_object_offset_in_the_xref_table_is_exact():
    data = build_certificate_pdf(LINES)

    offset = int(re.search(rb"startxref\s+(\d+)", data).group(1))
    entries = re.findall(rb"(\d{10}) 00000 n", data[offset:])
    for number, entry in enumerate(entries, start=1):
        assert data[int(entry):].startswith(f"{number} 0 obj".encode())


def test_french_accents_are_written_in_winansi():
    data = build_certificate_pdf(LINES)

    assert "réussite".encode("cp1252") in data
    assert b"/WinAnsiEncoding" in data


def test_parentheses_and_backslashes_cannot_break_the_text_operator():
    data = build_certificate_pdf(["Nom (test) \\ fin"])

    assert b"(Nom \\(test\\) \\\\ fin) Tj" in data


def test_characters_outside_winansi_are_replaced_not_crashing():
    data = build_certificate_pdf(["Ω 4,7 kΩ"])

    assert b"? 4,7 k?" in data
