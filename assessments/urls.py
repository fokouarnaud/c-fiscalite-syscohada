from django.urls import path

from . import views

urlpatterns = [
    path("quiz/<uuid:module_id>/", views.start_quiz, name="start_quiz"),
    path("examen/<uuid:partie_id>/", views.exam, name="exam"),
    path("tentatives/<uuid:public_id>/", views.attempt_detail, name="attempt_detail"),
    path("tentatives/<uuid:public_id>/reponse/", views.save_answer_view, name="save_answer"),
    path("tentatives/<uuid:public_id>/envoyer/", views.submit_view, name="submit_attempt"),
    path("tentatives/<uuid:public_id>/resultat/", views.result, name="attempt_result"),
]
