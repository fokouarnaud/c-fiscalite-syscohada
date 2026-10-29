from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Enrollment(models.Model):
    """Inscription d'un apprenant à une formation (AGENTS.md, E9) ; sans promotion = « groupe ouvert »."""

    class Source(models.TextChoices):
        CATALOG = "catalog", _("Catalogue")
        CODE = "code", _("Code de promotion")
        IMPORT = "import", _("Import CSV")
        ADMIN = "admin", _("Administrateur")

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="enrollments")
    formation = models.ForeignKey("courses.Formation", on_delete=models.CASCADE, related_name="enrollments")
    promotion = models.ForeignKey(
        "accounts.Promotion", on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments",
        verbose_name=_("promotion"),
    )
    source = models.CharField(_("origine"), max_length=10, choices=Source.choices, default=Source.ADMIN)
    enrolled_at = models.DateTimeField(_("inscrit le"), auto_now_add=True)

    class Meta:
        ordering = ["formation", "user"]
        constraints = [models.UniqueConstraint(fields=["user", "formation"], name="unique_enrollment")]

    def __str__(self):
        return f"{self.user} – {self.formation}"

    @property
    def in_open_group(self):
        return self.promotion_id is None

    def clean(self):
        if self.promotion_id and self.promotion.formation_id != self.formation_id:
            raise ValidationError({"promotion": _("La promotion doit appartenir à la formation choisie.")})
