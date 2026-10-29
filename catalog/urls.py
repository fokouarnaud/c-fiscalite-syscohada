from django.urls import path

from . import views

urlpatterns = [
    path("catalogue/", views.catalogue, name="catalogue"),
    path("catalogue/<uuid:public_id>/", views.formation_detail, name="formation_detail"),
    path("catalogue/<uuid:public_id>/inscription/", views.enroll, name="formation_enroll"),
    path("rejoindre/", views.join, name="join_promotion"),
]
