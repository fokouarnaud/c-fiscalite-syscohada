from modeltranslation.translator import TranslationOptions, register

from .models import FiscalParameter, SyscohadaAccount


@register(SyscohadaAccount)
class SyscohadaAccountTranslation(TranslationOptions):
    fields = ("label",)


@register(FiscalParameter)
class FiscalParameterTranslation(TranslationOptions):
    fields = ("label",)
