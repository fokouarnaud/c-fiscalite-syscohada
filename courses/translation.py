from modeltranslation.translator import TranslationOptions, register

from .models import Annexe, Formation, Module, Partie, Section


@register(Formation)
class FormationTranslation(TranslationOptions):
    fields = ("title", "description", "legal_reference", "prerequisite_note")


@register(Partie)
class PartieTranslation(TranslationOptions):
    fields = ("title", "description")


@register(Module)
class ModuleTranslation(TranslationOptions):
    fields = ("title", "competence", "evaluation_note")


@register(Section)
class SectionTranslation(TranslationOptions):
    fields = ("title", "body_md")


@register(Annexe)
class AnnexeTranslation(TranslationOptions):
    fields = ("title",)
