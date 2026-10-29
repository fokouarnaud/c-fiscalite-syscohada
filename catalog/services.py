"""Inscriptions (AGENTS.md, E7/E9) : libre au catalogue, ou par code de promotion."""
from accounts.models import Promotion

from .models import Enrollment


class InvalidJoinCode(Exception):
    """Code de promotion inconnu ou désactivé."""


def enroll_open(user, formation):
    """Inscription libre (groupe ouvert) ; sans effet si l'apprenant est déjà inscrit."""
    enrollment, _ = Enrollment.objects.get_or_create(
        user=user, formation=formation, defaults={"source": Enrollment.Source.CATALOG}
    )
    return enrollment


def join_with_code(user, code):
    """Rattache l'apprenant à la promotion du code ; un inscrit du groupe ouvert y est déplacé."""
    code = "".join(code.split()).upper()
    promotion = Promotion.objects.filter(join_code=code, join_code_active=True).select_related("formation").first()
    if promotion is None:
        raise InvalidJoinCode
    enrollment, created = Enrollment.objects.get_or_create(
        user=user, formation=promotion.formation,
        defaults={"promotion": promotion, "source": Enrollment.Source.CODE},
    )
    if not created and enrollment.promotion_id != promotion.pk:
        enrollment.promotion = promotion
        enrollment.save(update_fields=["promotion"])
    return enrollment
