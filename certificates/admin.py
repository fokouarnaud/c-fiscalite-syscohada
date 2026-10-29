from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Badge, Certificate


@admin.register(Certificate)
class CertificateAdmin(ModelAdmin):
    list_display = ("holder_name", "partie", "score_pct", "issued_at", "public_id")
    list_filter = ("partie",)
    search_fields = ("holder_name", "user__username", "public_id")
    readonly_fields = ("public_id", "user", "partie", "attempt", "holder_name", "score_pct", "issued_at")


@admin.register(Badge)
class BadgeAdmin(ModelAdmin):
    list_display = ("user", "kind", "module", "partie", "awarded_at")
    list_filter = ("kind",)
