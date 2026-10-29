from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import FiscalParameter, SyscohadaAccount


@admin.register(FiscalParameter)
class FiscalParameterAdmin(ModelAdmin, TranslationAdmin):
    """Taux et seuils du CGI (US-61) : une ligne par exercice ; la fiche liste les questions à revoir (US-62)."""

    list_display = ("key", "exercice", "value", "unit", "source_article")
    list_filter = ("exercice", "unit")
    search_fields = ("key", "label_fr", "source_article")
    readonly_fields = ("questions_a_revoir",)

    @admin.display(description=_("Questions à revoir"))
    def questions_a_revoir(self, parameter):
        if parameter.pk is None:
            return "—"
        questions = parameter.questions_to_review()
        if not questions:
            return _("Aucune question n'utilise ce paramètre.")
        return format_html("<ul>{}</ul>", format_html_join(
            "", '<li><a href="{}">{}</a></li>',
            ((reverse("admin:assessments_question_change", args=[q.pk]), q) for q in questions),
        ))


@admin.register(SyscohadaAccount)
class SyscohadaAccountAdmin(ModelAdmin, TranslationAdmin):
    """Plan comptable SYSCOHADA révisé (US-63), importé par manage.py import_syscohada."""

    list_display = ("code", "label", "account_class", "level")
    list_filter = ("account_class", "level")
    search_fields = ("code", "label_fr", "label_en")
