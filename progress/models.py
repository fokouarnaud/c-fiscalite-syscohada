from django.db import models
from django.utils.translation import gettext_lazy as _


class SectionView(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="section_views")
    section = models.ForeignKey("courses.Section", on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "section"], name="unique_section_view")]


class Announcement(models.Model):
    """Annonce d'un formateur à une de ses promotions, affichée sur le tableau de bord (US-31)."""

    promotion = models.ForeignKey("accounts.Promotion", on_delete=models.CASCADE, related_name="announcements")
    author = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="+")
    title = models.CharField(_("titre"), max_length=200)
    body = models.TextField(_("message"))
    published_at = models.DateTimeField(_("publiée le"), auto_now_add=True)

    class Meta:
        ordering = ["-published_at", "-pk"]

    def __str__(self):
        return self.title


class Deadline(models.Model):
    """Date limite indicative d'un quiz ou d'un examen pour une promotion (US-32) : elle ne bloque rien."""

    promotion = models.ForeignKey("accounts.Promotion", on_delete=models.CASCADE, related_name="deadlines")
    assessment = models.ForeignKey("assessments.Assessment", on_delete=models.CASCADE, related_name="deadlines")
    due_at = models.DateTimeField(_("date limite"))

    class Meta:
        ordering = ["due_at"]
        constraints = [models.UniqueConstraint(fields=["promotion", "assessment"], name="unique_deadline")]

    def __str__(self):
        return f"{self.assessment} – {self.due_at:%Y-%m-%d}"
