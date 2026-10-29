from django.urls import path

from . import views

urlpatterns = [
    path("certificats/", views.my_certificates, name="my_certificates"),
    path("certificats/<uuid:public_id>/pdf/", views.certificate_pdf, name="certificate_pdf"),
    path("verify/<uuid:public_id>/", views.verify, name="verify_certificate"),
]
