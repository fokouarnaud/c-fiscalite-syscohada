from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .importing import import_learners
from .models import Promotion, User
from .throttling import ThrottledAdminAuthenticationForm

admin.site.login_form = ThrottledAdminAuthenticationForm


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "first_name", "last_name", "role", "email_verified", "is_active")
    list_filter = ("role", "enrollments__promotion", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + ((_("ComptaFisca Acad Ventisax"), {"fields": ("role", "email_verified")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + ((_("ComptaFisca Acad Ventisax"), {"fields": ("role",)}),)


class LearnerImportForm(forms.Form):
    file = forms.FileField(label=_("Fichier CSV (username;first_name;last_name;email)"))


@admin.register(Promotion)
class PromotionAdmin(ModelAdmin):
    list_display = ("name", "formation", "start_date", "join_code", "join_code_active", "import_link")
    list_filter = ("formation", "join_code_active")
    readonly_fields = ("join_code",)
    fields = ("name", "formation", "start_date", "trainers", "join_code", "join_code_active")
    filter_horizontal = ("trainers",)
    actions = ["regenerate_join_codes", "deactivate_join_codes", "activate_join_codes"]

    @admin.action(description=_("Régénérer le code d'accès"))
    def regenerate_join_codes(self, request, queryset):
        for promotion in queryset:
            promotion.regenerate_join_code()
        self.message_user(request, ngettext(
            "%(n)d code régénéré : l'ancien ne fonctionne plus.", "%(n)d codes régénérés : les anciens ne fonctionnent plus.",
            queryset.count()) % {"n": queryset.count()}, messages.SUCCESS)

    @admin.action(description=_("Désactiver le code d'accès"))
    def deactivate_join_codes(self, request, queryset):
        queryset.update(join_code_active=False)

    @admin.action(description=_("Activer le code d'accès"))
    def activate_join_codes(self, request, queryset):
        queryset.update(join_code_active=True)

    def get_urls(self):
        return [
            path("<int:pk>/import/", self.admin_site.admin_view(self.import_view), name="accounts_promotion_import"),
        ] + super().get_urls()

    @admin.display(description=_("Apprenants"))
    def import_link(self, obj):
        return format_html('<a href="{}">{}</a>', reverse("admin:accounts_promotion_import", args=[obj.pk]), _("Importer un CSV"))

    def import_view(self, request, pk):
        promotion = get_object_or_404(Promotion, pk=pk)
        if not self.has_change_permission(request, promotion):
            raise PermissionDenied
        report, error = None, None
        form = LearnerImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            try:
                report = import_learners(form.cleaned_data["file"].read().decode("utf-8-sig"), promotion)
            except (ValueError, UnicodeDecodeError) as exc:
                error = str(exc)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "promotion": promotion,
            "form": form,
            "report": report,
            "error": error,
            "title": _("Importer des apprenants"),
        }
        return render(request, "admin/accounts/promotion/import.html", context)
