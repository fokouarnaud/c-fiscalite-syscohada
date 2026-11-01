"""Rendu HTML d'une pièce justificative (US-82) : toutes les valeurs sont échappées, montants au format de la langue."""
from decimal import Decimal

from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from assessments.scoring import format_quantity


def _text(value):
    """Texte bilingue {"fr", "en"} ou texte unique ; repli sur le français (C5)."""
    if isinstance(value, dict):
        lang = (get_language() or "fr")[:2]
        return value.get(lang) or value.get("fr", "")
    return "" if value is None else str(value)


def _fcfa(amount):
    return format_quantity(Decimal(amount), "FCFA")


def _columns(lines):
    keys = [key for key in ("qty", "unit_price", "amount", "debit", "credit") if any(key in line for line in lines)]
    return keys


def render_piece(piece):
    from django.utils.translation import gettext

    payload = piece.payload or {}
    lines = payload.get("lines", [])
    headers = {"qty": gettext("Qté"), "unit_price": gettext("Prix unitaire"), "amount": gettext("Montant"),
               "debit": gettext("Débit"), "credit": gettext("Crédit")}
    columns = _columns(lines)

    def cell(line, key):
        if key not in line:
            return ""
        return str(line[key]) if key == "qty" else _fcfa(line[key])

    fields = format_html_join("", "<dt>{}</dt><dd>{}</dd>",
                              ((_text(f.get("label")), _text(f.get("value"))) for f in payload.get("fields", [])))
    head = format_html_join("", "<th scope=\"col\">{}</th>", ((headers[key],) for key in columns))
    body = format_html_join("", "<tr><th scope=\"row\">{}</th>{}</tr>", (
        (_text(line.get("label")), format_html_join("", "<td>{}</td>", ((cell(line, key),) for key in columns)))
        for line in lines))
    totals = format_html_join("", "<tr><th scope=\"row\" colspan=\"{}\">{}</th><td>{}</td></tr>", (
        (max(len(columns), 1), _text(total.get("label")), _fcfa(total["amount"])) for total in payload.get("totals", [])))
    table = ""
    if lines or totals:
        # Une pièce sans lignes (relevé, déclaration) n'a que des totaux : pas d'en-tête au-dessus d'une colonne vide.
        thead = format_html('<thead><tr><th scope="col">{}</th>{}</tr></thead>', gettext("Libellé"), head) if lines else ""
        table = format_html('<div class="piece-scroll" tabindex="0"><table><caption>{}</caption>'
                            '{}<tbody>{}</tbody><tfoot>{}</tfoot></table></div>',
                            piece.title, thead, body, totals)
    return format_html('<figure class="piece" data-kind="{}"><figcaption>{} · {} · {}</figcaption>'
                       '<p class="piece-fictitious">{}</p>{}<dl class="piece-fields">{}</dl>{}{}</figure>',
                       piece.kind, piece.ref, piece.get_kind_display(), piece.issued_on.isoformat(),
                       gettext("Document pédagogique fictif"), _identity(payload), fields, table, _procedure(payload))


def _identity(payload):
    """S27 : identité fiscale camerounaise de l'émetteur et du client d'une facture (CGI art. 143 (1) b)."""
    from django.utils.translation import gettext

    issuer, customer = payload.get("issuer"), payload.get("customer")
    if not issuer:
        return ""
    rows = [(gettext("Émetteur"), issuer.get("name", "")), (gettext("Adresse"), issuer.get("address", "")),
            (gettext("NIU"), issuer.get("niu", "")), (gettext("RCCM"), issuer.get("rccm", "")),
            (gettext("Régime"), issuer.get("regime", "")), (gettext("Centre des impôts"), issuer.get("centre", "")),
            (gettext("Facture n°"), payload.get("number", "")),
            (gettext("Référence de facturation électronique DGI"), payload.get("einvoice", ""))]
    if customer:
        rows += [(gettext("Client"), customer.get("name", "")), (gettext("NIU du client"), customer.get("niu", ""))]
    return format_html('<dl class="piece-fields piece-identity">{}</dl>',
                       format_html_join("", "<dt>{}</dt><dd>{}</dd>", ((k, v) for k, v in rows if v)))


def _procedure(payload):
    """S28 : où aller, quoi apporter, ce que l'on obtient, et sur quel texte officiel, pour refaire la démarche."""
    from django.utils.translation import gettext

    from courses.rendering import render_references

    if "organisme" not in payload:
        return ""
    documents = format_html_join("", "<li>{}</li>", ((_text(item),) for item in payload.get("documents_a_fournir", [])))
    # Texte échappé d'abord, puis balises [[cgi:]] remplacées : le résultat est sûr, comme dans le cours (C27).
    source = mark_safe(render_references(format_html("{}", payload.get("source", ""))))
    return format_html('<dl class="piece-fields"><dt>{}</dt><dd>{}</dd><dt>{}</dt><dd>{}</dd></dl>'
                       '<p>{}</p><ul class="piece-checklist">{}</ul><dl class="piece-fields"><dt>{}</dt><dd>{}</dd>'
                       '<dt>{}</dt><dd>{}</dd></dl>',
                       gettext("Organisme"), _text(payload["organisme"]), gettext("Objet"), _text(payload.get("objet")),
                       gettext("Documents à fournir"), documents, gettext("Document obtenu"),
                       _text(payload.get("document_obtenu")), gettext("Source"), source)
