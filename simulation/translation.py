from modeltranslation.translator import TranslationOptions, register

from .models import Piece


@register(Piece)
class PieceTranslation(TranslationOptions):
    fields = ("title",)
