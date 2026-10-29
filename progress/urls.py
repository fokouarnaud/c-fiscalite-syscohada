from django.urls import path

from . import views

urlpatterns = [
    path("", views.trainer_table, name="trainer_table"),
    path("export.csv", views.export_csv, name="trainer_export"),
    path("tentatives/<uuid:public_id>/", views.attempt_review, name="trainer_attempt"),
    path("questions/", views.question_stats, name="trainer_questions"),
    path("annonces/", views.announcements, name="trainer_announcements"),
    path("echeances/", views.deadlines, name="trainer_deadlines"),
]
