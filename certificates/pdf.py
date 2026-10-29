"""Générateur PDF minimal, sans dépendance (fpdf2 tirerait Pillow et fonttools : ~40 Mo, AGENTS.md).

Une page A4 paysage, polices Helvetica standard du PDF (aucune police embarquée) en WinAnsi : les accents
français passent, un caractère hors WinAnsi est remplacé par « ? ».
"""
PAGE_W, PAGE_H = 842, 595  # A4 paysage, en points
TITLE_SIZE, BODY_SIZE = 28, 16
AVG_CHAR_WIDTH = 0.5  # largeur moyenne d'un glyphe Helvetica, en fraction de la taille (centrage approché)


def _pdf_string(text):
    raw = text.encode("cp1252", errors="replace")
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def _content(lines):
    ops = [b"0.11 0.30 0.55 RG 3 w 30 30 782 535 re S", b"0.11 0.30 0.55 RG 1 w 40 40 762 515 re S", b"0 g"]
    y = PAGE_H - 150
    for i, line in enumerate(lines):
        font, size = (b"/F2", TITLE_SIZE) if i == 0 else (b"/F1", BODY_SIZE)
        x = max(50, (PAGE_W - len(line) * size * AVG_CHAR_WIDTH) / 2)
        ops.append(b"BT " + font + b" %d Tf %.1f %d Td " % (size, x, y) + _pdf_string(line) + b" Tj ET")
        y -= 70 if i == 0 else 36
    return b"\n".join(ops)


def build_certificate_pdf(lines):
    """Renvoie les octets d'un PDF d'une page ; la première ligne est le titre."""
    stream = _content(lines)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] " % (PAGE_W, PAGE_H)
        + b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)
