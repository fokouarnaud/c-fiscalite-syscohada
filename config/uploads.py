"""Fichiers téléversés : noms impossibles à deviner et SVG sans contenu actif.

Les médias sont servis tels quels (sans passer par Django) : un nom prévisible permettrait de les retrouver
sans lien, et un SVG avec du script s'exécuterait dans l'origine du site (XSS stocké).
"""
import re
import uuid
from pathlib import PurePath

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class RandomFilename:
    """upload_to : `<dossier>/<uuid hex>.<extension en minuscules>`, le nom d'origine n'est pas gardé."""

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        return f"{self.folder}/{uuid.uuid4().hex}{PurePath(filename).suffix.lower()}"

    def __eq__(self, other):
        return isinstance(other, RandomFilename) and other.folder == self.folder


# Éléments, attributs et URL qui rendent un SVG actif quand il est ouvert directement dans le navigateur.
ACTIVE_SVG = re.compile(
    rb"<\s*(?:script|foreignobject|iframe|embed|object|handler|listener)\b"
    rb"|<!\s*(?:doctype|entity)"
    rb"|\son[a-z]+\s*="
    rb"|(?:javascript|vbscript|data)\s*:"
    rb"|<\s*(?:set|animate)\b[^>]*\battributename\s*=\s*[\"']?\s*(?:href|xlink:href)",
    re.IGNORECASE,
)


def validate_inert_svg(file):
    if not file.name.lower().endswith(".svg"):
        return
    file.seek(0)
    content = file.read()
    file.seek(0)
    if ACTIVE_SVG.search(content):
        raise ValidationError(_("Ce SVG contient du script ou un lien actif : il est refusé."))
