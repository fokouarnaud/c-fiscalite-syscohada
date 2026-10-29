from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Enrollment


class OpenGroupFilter(admin.SimpleListFilter):
    """Groupe ouvert (US-36) : inscrits libres, sans promotion."""

    title = _("groupe")
    parameter_name = "promotion__isnull"

    def lookups(self, request, model_admin):
        return [("True", _("Groupe ouvert (sans promotion)")), ("False", _("En promotion"))]

    def queryset(self, request, queryset):
        if self.value() in ("True", "False"):
            return queryset.filter(promotion__isnull=self.value() == "True")
        return queryset


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = ("user", "formation", "promotion", "source", "enrolled_at")
    list_filter = (OpenGroupFilter, "formation", "promotion", "source")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    autocomplete_fields = ("user",)
