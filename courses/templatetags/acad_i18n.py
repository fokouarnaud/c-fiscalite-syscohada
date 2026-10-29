from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import get_language

register = template.Library()


@register.filter
def lang_attr(obj, field):
    """Attribut lang="fr" quand le champ traduit est vide dans la langue courante (repli sur le français)."""
    lang = (get_language() or settings.LANGUAGE_CODE)[:2]
    if lang == settings.MODELTRANSLATION_DEFAULT_LANGUAGE or getattr(obj, f"{field}_{lang}", None):
        return ""
    return format_html(' lang="{}"', settings.MODELTRANSLATION_DEFAULT_LANGUAGE)
