import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from config.uploads import RandomFilename


class Formation(models.Model):
    class Icon(models.TextChoices):
        # Icônes Tabler du projet (templates/icons/<nom>.svg), C16 : une par formation, liste fermée.
        LEDGER = "ledger", _("Comptabilité (registre)")
        RECEIPT = "receipt", _("Fiscalité (reçu)")

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # identifiant des URL et formulaires
    title = models.CharField(_("titre"), max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(_("description"), blank=True)
    order = models.PositiveIntegerField(default=0)
    is_open = models.BooleanField(
        _("ouverte au catalogue"), default=False,
        help_text=_("Visible dans le catalogue public et ouverte à l’inscription libre."),
    )
    icon = models.CharField(_("icône"), max_length=20, choices=Icon.choices, default=Icon.LEDGER)
    # US-25 (C3) : texte de référence affiché sur chaque leçon, par exemple « CGI Cameroun, éd. 2026 ».
    legal_reference = models.CharField(_("référence juridique"), max_length=120, blank=True)
    # US-15 (C17) : prérequis indicatif affiché sur le programme, jamais bloquant.
    prerequisite_note = models.CharField(_("prérequis indicatif"), max_length=200, blank=True)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.title


class Partie(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # identifiant des URL et formulaires
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="parties")
    title = models.CharField(_("titre"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    slug = models.SlugField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]
        # E45 : le rang d'une partie est unique dans sa formation (ordre du sommaire, colonnes « Examen P1, P2, P3 »).
        constraints = [models.UniqueConstraint(fields=["formation", "slug"], name="unique_partie_slug"),
                       models.UniqueConstraint(fields=["formation", "order"], name="unique_partie_order")]

    def __str__(self):
        return self.title


class Module(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # identifiant des URL et formulaires
    partie = models.ForeignKey(Partie, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(_("titre"), max_length=200)
    order = models.PositiveIntegerField(default=0)
    duration_hours = models.PositiveIntegerField(_("durée (heures)"), default=0)
    competence = models.TextField(_("compétence visée"), blank=True)
    evaluation_note = models.TextField(_("modalités d'évaluation"), blank=True)

    class Meta:
        ordering = ["order", "pk"]
        constraints = [models.UniqueConstraint(fields=["partie", "order"], name="unique_module_order")]  # E45

    def __str__(self):
        return self.title


class SectionQuerySet(models.QuerySet):
    def content(self):
        return self.filter(kind=Section.Kind.CONTENT)

    def practical(self):
        return self.filter(kind=Section.Kind.PRACTICAL)


class Section(models.Model):
    class Kind(models.TextChoices):
        CONTENT = "content", _("Contenu")
        PRACTICAL = "practical", _("Activités pratiques")

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # identifiant des URL et formulaires
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(_("titre"), max_length=200)
    order = models.PositiveIntegerField(default=0)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.CONTENT)
    body_md = models.TextField(_("contenu (Markdown)"), blank=True)

    objects = SectionQuerySet.as_manager()

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return self.title


class Annexe(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="annexes")
    title = models.CharField(_("titre"), max_length=200)
    file = models.FileField(upload_to=RandomFilename("annexes"))

    def __str__(self):
        return self.title
