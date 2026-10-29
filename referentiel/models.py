"""Référentiels juridiques : plan comptable SYSCOHADA révisé et paramètres fiscaux du CGI (C3, C15)."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SyscohadaAccount(models.Model):
    """Un compte du plan SYSCOHADA révisé (US-63). Classe, niveau et parent se déduisent du code."""

    code = models.CharField(_("numéro"), max_length=12, primary_key=True)
    label = models.CharField(_("libellé"), max_length=255)
    account_class = models.PositiveSmallIntegerField(_("classe"), editable=False)
    level = models.PositiveSmallIntegerField(_("niveau"), editable=False)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, editable=False,
                               related_name="children")

    class Meta:
        ordering = ["code"]
        verbose_name = _("compte SYSCOHADA")
        verbose_name_plural = _("comptes SYSCOHADA")

    def __str__(self):
        return f"{self.code} {self.label}"

    def save(self, *args, **kwargs):
        self.account_class = int(self.code[0])
        self.level = len(self.code)
        prefixes = [self.code[:n] for n in range(len(self.code) - 1, 0, -1)]
        self.parent = SyscohadaAccount.objects.filter(code__in=prefixes).order_by("-level").first()
        super().save(*args, **kwargs)


class FiscalParameterQuerySet(models.QuerySet):
    def current(self, key):
        """Valeur en vigueur : l'exercice le plus récent qui ne dépasse pas l'exercice de référence du site."""
        from django.conf import settings

        return self.filter(key=key, exercice__lte=settings.FISCAL_YEAR).order_by("-exercice").first()

    def in_force(self):
        """{clé: valeur en vigueur} de tous les paramètres, pour les calculateurs (US-26)."""
        from django.conf import settings

        values = {}
        for parameter in self.filter(exercice__lte=settings.FISCAL_YEAR).order_by("key", "-exercice"):
            values.setdefault(parameter.key, str(parameter.value.normalize()))
        return values


class FiscalParameter(models.Model):
    """Un taux ou un seuil du CGI pour un exercice (US-61) : changer de loi de finances = ajouter une ligne."""

    class Unit(models.TextChoices):
        PERCENT = "%", "%"
        FCFA = "FCFA", "FCFA"
        COEF = "coef", _("coefficient")

    key = models.CharField(_("clé"), max_length=80, help_text=_("Par exemple tva.taux_global ; utilisée par [[param:clé]]."))
    exercice = models.PositiveSmallIntegerField(_("exercice"))
    value = models.DecimalField(_("valeur"), max_digits=16, decimal_places=4)
    unit = models.CharField(_("unité"), max_length=4, choices=Unit.choices)
    label = models.CharField(_("libellé"), max_length=200, blank=True)
    source_article = models.CharField(_("article source"), max_length=80, blank=True)

    objects = FiscalParameterQuerySet.as_manager()

    class Meta:
        ordering = ["key", "-exercice"]
        verbose_name = _("paramètre fiscal")
        verbose_name_plural = _("paramètres fiscaux")
        constraints = [models.UniqueConstraint(fields=["key", "exercice"], name="unique_parameter_exercice")]

    def __str__(self):
        return f"{self.key} ({self.exercice})"

    def questions_to_review(self):
        """Questions étiquetées avec cette clé (US-62) : la clé entière, jamais une clé qui la prolonge."""
        import re

        from assessments.models import Question

        return Question.objects.filter(params__regex=rf"(^| ){re.escape(self.key)}( |$)")
