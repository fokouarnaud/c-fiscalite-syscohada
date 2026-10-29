from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline, TranslationTabularInline
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import Annexe, Formation, Module, Partie, Section

# Onglets de traduction écartés : ils chargent jQuery UI depuis un CDN, interdit par la CSP.


class PartieInline(TabularInline, TranslationTabularInline):
    model = Partie
    extra = 0
    prepopulated_fields = {"slug": ("title_fr",)}


@admin.register(Formation)
class FormationAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "is_open", "order")
    list_filter = ("is_open",)
    prepopulated_fields = {"slug": ("title_fr",)}
    inlines = [PartieInline]


class ModuleInline(TabularInline, TranslationTabularInline):
    model = Module
    extra = 0
    fields = ("order", "title", "duration_hours")


@admin.register(Partie)
class PartieAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "formation", "order")
    inlines = [ModuleInline]


class SectionInline(StackedInline, TranslationStackedInline):
    model = Section
    extra = 0


@admin.register(Module)
class ModuleAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "partie", "order", "duration_hours")
    list_filter = ("partie",)
    inlines = [SectionInline]


class AnnexeInline(TabularInline, TranslationTabularInline):
    model = Annexe
    extra = 0


@admin.register(Section)
class SectionAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "module", "kind", "order")
    list_filter = ("kind", "module__partie", "module")
    inlines = [AnnexeInline]
