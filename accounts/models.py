import secrets
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Code de promotion (US-06) : sans 0/O ni 1/I/L, pour être dicté ou recopié sans erreur.
JOIN_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_join_code():
    return "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(8))


class User(AbstractUser):
    class Role(models.TextChoices):
        LEARNER = "learner", _("Apprenant")
        TRAINER = "trainer", _("Formateur")
        ADMIN = "admin", _("Administrateur")

    role = models.CharField(_("rôle"), max_length=10, choices=Role.choices, default=Role.LEARNER)
    email_verified = models.BooleanField(_("e-mail vérifié"), default=False)

    def save(self, *args, **kwargs):
        self.is_staff = self.is_superuser or self.role in (self.Role.TRAINER, self.Role.ADMIN)
        super().save(*args, **kwargs)
        from .roles import sync_role_groups

        sync_role_groups(self)

    @property
    def is_learner(self):
        return self.role == self.Role.LEARNER

    @property
    def is_trainer(self):
        return self.role == self.Role.TRAINER

    @property
    def is_platform_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN


class PromotionQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_platform_admin:
            return self.all()
        if user.is_trainer:
            return self.filter(trainers=user)
        return self.filter(enrollments__user=user)


class Promotion(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # identifiant des URL et formulaires
    name = models.CharField(_("nom"), max_length=100, unique=True)
    formation = models.ForeignKey("courses.Formation", on_delete=models.PROTECT, related_name="promotions")
    start_date = models.DateField(_("date de début"), null=True, blank=True)
    trainers = models.ManyToManyField(
        User,
        blank=True,
        related_name="taught_promotions",
        limit_choices_to={"role": User.Role.TRAINER},
        verbose_name=_("formateurs"),
    )
    join_code = models.CharField(_("code d'accès"), max_length=8, unique=True, default=new_join_code, editable=False)
    join_code_active = models.BooleanField(_("code d'accès actif"), default=True)

    objects = PromotionQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def regenerate_join_code(self):
        self.join_code = new_join_code()
        self.save(update_fields=["join_code"])


class LoginFailure(models.Model):
    """Échec de connexion, compté par identifiant pour bloquer la force brute (voir accounts/throttling.py)."""

    username = models.CharField(max_length=150, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class SignupThrottle(models.Model):
    """Une inscription publique, comptée par adresse IP hachée pour limiter les faux comptes (US-03)."""

    ip_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
