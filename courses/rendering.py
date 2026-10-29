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


def render_references(html):
    """Remplace les balises [[param:]], [[cgi:]], [[syscohada:]] et [[guide:]] d'un HTML déjà nettoyé."""
    html = PARAM_TAG.sub(_parameter, html)
    html = CGI_TAG.sub(_cgi, html)
    html = ACCOUNT_TAG.sub(_account, html)
    return GUIDE_TAG.sub(_guide, html)


def render_markdown(text):
    html = markdown.markdown(text or "", extensions=["tables"])
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, protocols={"http", "https"}, strip=True)
    clean = DIAGRAM.sub(r'<a class="figure-zoom" href="\2">\1</a>', clean)
    clean = render_references(clean)
    return CALC_MARKER.sub(r'<div class="calc" data-calc="\1"></div>', clean)
