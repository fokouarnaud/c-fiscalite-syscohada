from modeltranslation.translator import TranslationOptions, register

from .models import Choice, JournalLine, MatchPair, Question


@register(Question)
class QuestionTranslation(TranslationOptions):
    fields = ("prompt", "explanation")


@register(Choice)
class ChoiceTranslation(TranslationOptions):
    fields = ("text",)


@register(MatchPair)
class MatchPairTranslation(TranslationOptions):
    fields = ("left", "right")


@register(JournalLine)
class JournalLineTranslation(TranslationOptions):
    fields = ("label",)
