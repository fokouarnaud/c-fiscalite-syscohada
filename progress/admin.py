from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import Announcement, Deadline


@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin, TranslationAdmin):
    list_display = ("title", "promotion", "author", "published_at")
    list_filter = ("promotion",)


@admin.register(Deadline)
class DeadlineAdmin(ModelAdmin):
    list_display = ("assessment", "promotion", "due_at")
    list_filter = ("promotion",)
