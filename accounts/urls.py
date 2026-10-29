from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .throttling import ThrottledAuthenticationForm

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("connexion/", auth_views.LoginView.as_view(
        template_name="accounts/login.html", authentication_form=ThrottledAuthenticationForm,
    ), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("inscription/", views.signup, name="signup"),
    path("inscription/envoye/", views.signup_done, name="signup_done"),
    path("inscription/verifier/<str:uidb64>/<str:token>/", views.verify_email, name="verify_email"),
    # Mot de passe oublié (US-09) : vues de Django, qui ne révèlent pas si l'adresse existe.
    path("mot-de-passe/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset_form.html",
        email_template_name="accounts/email/password_reset.txt",
        subject_template_name="accounts/email/password_reset_subject.txt",
    ), name="password_reset"),
    path("mot-de-passe/envoye/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ), name="password_reset_done"),
    path("mot-de-passe/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
    ), name="password_reset_confirm"),
    path("mot-de-passe/termine/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
    ), name="password_reset_complete"),
]
