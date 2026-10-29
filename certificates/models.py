import uuid

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class Badge(models.Model):
    """Badge de module terminé ou de partie réussie (US-23)."""

    class Kind(models.TextChoices):
        MODULE = "module", _("Module terminé")
        PARTIE = "partie", _("Partie réussie")

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="badges")
    kind = models.CharField(max_length=6, choices=Kind.choices)
    module = models.ForeignKey("courses.Module", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    partie = models.ForeignKey("courses.Partie", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["awarded_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind="module", module__isnull=False, partie__isnull=True)
                | Q(kind="partie", module__isnull=True, partie__isnull=False),
                name="badge_target_matches_kind",
            ),
            models.UniqueConstraint(fields=["user", "module"], condition=Q(kind="module"), name="unique_module_badge"),
            models.UniqueConstraint(fields=["user", "partie"], condition=Q(kind="partie"), name="unique_partie_badge"),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} : {self.module or self.partie}"


class Certificate(models.Model):
    """Certificat d'une partie réussie (US-24) ; le numéro public sert à la vérification, le PDF n'est jamais stocké."""

    public_id = models.UUIDField(_("numéro"), default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="certificates")
    partie = models.ForeignKey("courses.Partie", on_delete=models.PROTECT, related_name="certificates")
    attempt = models.ForeignKey("assessments.Attempt", on_delete=models.PROTECT, related_name="+")
    holder_name = models.CharField(_("titulaire"), max_length=300)  # figé à l'émission
    score_pct = models.DecimalField(_("score (%)"), max_digits=5, decimal_places=2)
    issued_at = models.DateTimeField(_("délivré le"), auto_now_add=True)

    class Meta:
        ordering = ["issued_at", "pk"]
        constraints = [models.UniqueConstraint(fields=["user", "partie"], name="unique_certificate")]

    def __str__(self):
        return f"{self.holder_name} – {self.partie}"
