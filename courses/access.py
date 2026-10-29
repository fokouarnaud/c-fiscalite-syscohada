from .models import Formation


def accessible_formations(user):
    """Formations qu'un utilisateur peut consulter : celles où il est inscrit, celles de ses promotions, ou toutes."""
    if user.is_platform_admin:
        return Formation.objects.all()
    if user.is_trainer:
        return Formation.objects.filter(promotions__trainers=user).distinct()
    return Formation.objects.filter(enrollments__user=user)
