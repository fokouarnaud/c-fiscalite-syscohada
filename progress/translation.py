from modeltranslation.translator import TranslationOptions, register

from .models import Announcement


@register(Announcement)
class AnnouncementTranslation(TranslationOptions):
    fields = ("title", "body")
