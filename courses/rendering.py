"""Markdown → HTML nettoyé (bleach) pour le contenu des sections."""
import re

import bleach
import markdown
from django.utils.html import format_html
from django.utils.translation import gettext


ALLOWED_TAGS = {
    "p", "br", "strong", "em", "ul", "ol", "li", "h2", "h3", "h4", "blockquote", "code", "pre",
    "table", "thead", "tbody", "tr", "th", "td", "a", "img", "hr",
}
ALLOWED_ATTRIBUTES = {"a": ["href", "title"], "img": ["src", "alt", "title"]}
# Calculateurs du cours (US-26, C12) : un paragraphe « [[calc:<nom>]] » seul devient un emplacement inerte,
# rempli par static/acad/js/calculators.js. Remplacé APRÈS bleach : seuls ces noms fixes peuvent sortir.
CALCULATORS = ("tva", "amortissement", "paie", "is", "reduction", "stock")
CALC_MARKER = re.compile(r"<p>\[\[calc:(%s)\]\]</p>" % "|".join(CALCULATORS))
# Schémas du cours : ajustés à la largeur et liés à leur fichier pleine taille (agrandissement sur téléphone).
# Seuls les SVG servis par le site (/static/content/) sont concernés, après nettoyage par bleach.
DIAGRAM = re.compile(r'(<img alt="[^"]*" src="(/static/content/[\w/.-]+\.svg)">)')


# Balises de référence (US-23, US-24, C15), remplacées APRÈS bleach : la référence se limite à des caractères sûrs.
REF = r"([\w .,°/-]{1,40}?)"
PARAM_TAG = re.compile(r"\[\[param:([a-z0-9_.]{1,80})\]\]")
CGI_TAG = re.compile(r"\[\[cgi:%s\]\]" % REF)
ACCOUNT_TAG = re.compile(r"\[\[syscohada:(\d{1,12})\]\]")
GUIDE_TAG = re.compile(r"\[\[guide:%s\]\]" % REF)
# Pièces de la simulation (US-82, S5) : seule dans son paragraphe, la balise devient le document entier.
PIECE_REF = r"(S-[A-Z0-9-]{1,38})"
PIECE_BLOCK = re.compile(r"<p>\[\[piece:%s\]\]</p>" % PIECE_REF)
PIECE_TAG = re.compile(r"\[\[piece:%s\]\]" % PIECE_REF)


def _parameter(match):
    from assessments.scoring import format_quantity
    from referentiel.models import FiscalParameter

    parameter = FiscalParameter.objects.current(match.group(1))
    if parameter is None:
        return format_html('<mark class="param-missing">{}</mark>', match.group(1))
    return format_html('<span class="param" title="{}">{}</span>', parameter.source_article,
                       format_quantity(parameter.value, parameter.unit))


def _cgi(match):
    from django.conf import settings

    year = settings.FISCAL_YEAR
    ref = match.group(1).strip()
    if ref.startswith("art. "):
        ref = gettext("art. %(number)s") % {"number": ref[len("art. "):]}
    return format_html('<cite class="source" tabindex="0" title="{}">{}</cite>',
                       gettext("Code général des impôts du Cameroun, édition %(year)s") % {"year": year},
                       gettext("CGI %(year)s, %(ref)s") % {"year": year, "ref": ref})


def _account(match):
    from referentiel.models import SyscohadaAccount

    account = SyscohadaAccount.objects.filter(code=match.group(1)).first()
    if account is None:
        return format_html('<mark class="source-missing">{}</mark>', match.group(1))
    return format_html('<cite class="source" tabindex="0" title="{}">{} · {}</cite>',
                       gettext("Plan comptable SYSCOHADA révisé"), account.code, account.label)


def _guide(match):
    return format_html('<cite class="source" tabindex="0" title="{}">{}</cite>',
                       gettext("Guide d'application du SYSCOHADA révisé (OHADA)"),
                       gettext("Guide SYSCOHADA, %(ref)s") % {"ref": match.group(1).strip()})


def _piece(match):
    from simulation.models import Piece
    from simulation.rendering import render_piece

    piece = Piece.objects.filter(ref=match.group(1)).first()
    if piece is None:
        return format_html('<mark class="piece-missing">{}</mark>', match.group(1))
    return render_piece(piece)


def render_references(html):
    """Remplace les balises [[param:]], [[cgi:]], [[syscohada:]] et [[guide:]] d'un HTML déjà nettoyé."""
    html = PARAM_TAG.sub(_parameter, html)
    html = CGI_TAG.sub(_cgi, html)
    html = ACCOUNT_TAG.sub(_account, html)
    html = GUIDE_TAG.sub(_guide, html)
    return WEB_SOURCE_TAG.sub(_web_source, html)


# Sources officielles hors CGI et Guide (US-97) : pages publiques du MINFI, de la DGI, de l'OHADA…, enregistrées avec leur
# adresse et leur date de consultation dans content/referentiel/sources.csv.
WEB_SOURCE_TAG = re.compile(r"\[\[source:([a-z0-9-]{1,40})\]\]")


def official_sources():
    import csv

    from django.conf import settings

    path = settings.BASE_DIR / "content" / "referentiel" / "sources.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as handle:
        return {row["key"]: row for row in csv.DictReader(handle, delimiter=";")}


def _web_source(match):
    from django.utils.translation import get_language

    source = official_sources().get(match.group(1))
    if source is None:
        return format_html('<mark class="source-missing">{}</mark>', match.group(1))
    title = source["titre_en"] if (get_language() or "fr").startswith("en") and source["titre_en"] else source["titre_fr"]
    return format_html('<cite class="source" tabindex="0" title="{} ({})">{} · {}</cite>',
                       source["url"], gettext("consulté le %(date)s") % {"date": source["consulte_le"]},
                       source["organisme"], title)


def render_markdown(text):
    html = markdown.markdown(text or "", extensions=["tables"])
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols={"http", "https"}, strip=True)
    clean = DIAGRAM.sub(r'<a class="figure-zoom" href="\2">\1</a>', clean)
    clean = render_references(clean)
    clean = CALC_MARKER.sub(r'<div class="calc" data-calc="\1"></div>', clean)
    clean = PIECE_BLOCK.sub(_piece, clean)
    return PIECE_TAG.sub(_piece, clean)
