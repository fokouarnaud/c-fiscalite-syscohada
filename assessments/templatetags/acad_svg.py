"""Affichage en ligne des schémas SVG : contrôlé à chaque rendu, pas seulement à la publication."""
from django import template
from django.utils.safestring import mark_safe

from config.uploads import ACTIVE_SVG

register = template.Library()


@register.filter
def inert_svg(svg):
    """Le SVG tel quel s'il est inerte, sinon rien : une modification après publication ne peut pas injecter de script."""
    svg = svg or ""
    if not svg.lstrip().startswith("<svg") or ACTIVE_SVG.search(svg.encode("utf-8")):
        return ""
    return mark_safe(svg)
