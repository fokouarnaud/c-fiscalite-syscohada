from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from unfold.admin import ModelAdmin, TabularInline

from .models import Assessment, Choice, JournalLine, MatchPair, Question


class ChoiceInline(TabularInline, TranslationTabularInline):
    model = Choice
    extra = 0


class MatchPairInline(TabularInline, TranslationTabularInline):
    """Paires d'une question d'appariement (ignorées pour les autres types)."""

    model = MatchPair
    extra = 0
    fields = ("order", "left", "right")


class JournalLineInline(TabularInline, TranslationTabularInline):
    """Écriture attendue d'une question `journal` (US-34), ignorée pour les autres types."""

    model = JournalLine
    extra = 0
    fields = ("order", "account", "account_match", "side", "amount", "label")


@admin.register(Question)
class QuestionAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("__str__", "module", "qtype", "usage", "status", "reviewed_fr", "reviewed_en")
    list_filter = ("status", "usage", "qtype", "module__partie", "module")
    search_fields = ("prompt_fr", "prompt_en", "external_id")
    readonly_fields = ("status",)
    inlines = [ChoiceInline, MatchPairInline, JournalLineInline]
    actions = ["mark_reviewed", "publish_selected"]

    @admin.action(description=_("Marquer comme relues (FR et EN)"))
    def mark_reviewed(self, request, queryset):
        count = queryset.update(reviewed_fr=True, reviewed_en=True)
        self.message_user(
            request,
            ngettext("%(n)d question marquée relue.", "%(n)d questions marquées relues.", count) % {"n": count},
            messages.SUCCESS,
        )

    @admin.action(description=_("Publier les questions sélectionnées"))
    def publish_selected(self, request, queryset):
        published, refused = 0, []
        for question in queryset:
            try:
                question.publish()
                published += 1
            except ValidationError as exc:
                refused.append(f"#{question.pk} : {' '.join(exc.messages)}")
        if published:
            self.message_user(
                request,
                ngettext("%(n)d question publiée.", "%(n)d questions publiées.", published) % {"n": published},
                messages.SUCCESS,
            )
        for reason in refused:
            self.message_user(request, _("Refusée %(reason)s") % {"reason": reason}, messages.WARNING)


@admin.register(Assessment)
class AssessmentAdmin(ModelAdmin):
    list_display = ("__str__", "pass_threshold", "max_attempts", "duration_minutes", "questions_per_module", "shuffle")
    list_filter = ("kind",)
