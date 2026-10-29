from django.urls import path

from . import views

urlpatterns = [
    path("modules/<uuid:public_id>/", views.module_detail, name="module_detail"),
    path("sections/<uuid:public_id>/", views.section_detail, name="section_detail"),
]
