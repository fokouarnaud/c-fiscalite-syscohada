"""US-83 et US-85 : texte d'une question de la simulation sans ses balises [[piece:]], et pièces rendues à part.

Les pièces de l'énoncé s'affichent pendant la tentative ; celles de l'explication (formulaire rempli, écriture
officielle) seulement dans la correction du quiz, que l'examen ne montre jamais.
"""
from django import template
from django.utils.html import format_html_join

from courses.importer import PIECE_REFS
from simulation.rendering import render_piece

register = template.Library()


@register.filter
def prompt_text(text):
    """Texte sans les balises de pièce (énoncé ou explication ; l'espace formateur n'affiche que ce texte)."""
    return PIECE_REFS.sub("", text or "").strip()


def _pieces_cited_in(question, text):
    refs = PIECE_REFS.findall(text or "")
    pieces = {piece.ref: piece for piece in question.pieces.all() if piece.ref in refs}
    return format_html_join("", "{}", ((render_piece(pieces[ref]),) for ref in dict.fromkeys(refs) if ref in pieces))


@register.filter
def prompt_pieces(question):
    """Pièces citées par l'énoncé, dans leur ordre d'apparition."""
    return _pieces_cited_in(question, question.prompt)


@register.filter
def explanation_pieces(question):
    """Pièces citées par l'explication (US-85 : formulaire de déclaration rempli), pour la correction du quiz."""
    return _pieces_cited_in(question, question.explanation)
