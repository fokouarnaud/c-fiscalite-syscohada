from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SimulationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "simulation"
    verbose_name = _("Simulation")
