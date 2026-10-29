from django import forms
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import formats
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

from accounts.models import User
from catalog.models import Enrollment

from .models import Badge, Certificate
from .pdf import build_certificate_pdf
from .services import refresh_all_certificates


class FullNameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


@login_required
def my_certificates(request):
    """Certificats et badges de l'apprenant ; le nom complet est demandé s'il manque (US-24)."""
    form = FullNameForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        refresh_all_certificates(request.user)
        return redirect("my_certificates")
    return render(request, "certificates/mine.html", {
        "form": form,
        "certificates": Certificate.objects.filter(user=request.user).select_related("partie__formation"),
        "badges": list(Badge.objects.filter(user=request.user).select_related("module", "partie")),
    })


def _can_download(user, certificate):
    if user.pk == certificate.user_id or user.is_platform_admin:
        return True
    return user.is_trainer and Enrollment.objects.filter(
        user_id=certificate.user_id, formation_id=certificate.partie.formation_id, promotion__trainers=user
    ).exists()


@login_required
def certificate_pdf(request, public_id):
    """PDF généré à la demande, jamais stocké (US-25) ; 404 pour qui n'y a pas droit."""
    certificate = get_object_or_404(Certificate.objects.select_related("partie__formation"), public_id=public_id)
    if not _can_download(request.user, certificate):
        raise Http404
    lines = [
        _("Certificat de réussite"),
        certificate.holder_name,
        _("a réussi l'examen de la partie"),
        f"{certificate.partie.formation.title} : {certificate.partie.title}",
        _("Score : %(score)s %%") % {"score": formats.number_format(certificate.score_pct, 0)},
        _("Délivré le %(date)s par ComptaFisca Acad Ventisax") % {
            "date": formats.date_format(certificate.issued_at, "DATE_FORMAT")
        },
        _("Vérification : %(url)s") % {
            "url": request.build_absolute_uri(f"/{request.LANGUAGE_CODE}/verify/{certificate.public_id}/")
        },
    ]
    response = HttpResponse(build_certificate_pdf(lines), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="certificat-{certificate.public_id}.pdf"'
    return response


def verify(request, public_id):
    """Vérification publique d'un certificat par son numéro (US-26)."""
    certificate = get_object_or_404(Certificate.objects.select_related("partie__formation"), public_id=public_id)
    # US-42 : score au format de la langue (« 100 % » en français, « 100% » en anglais), comme les montants en %.
    score = pgettext("pourcentage", "%(number)s %%") % {"number": formats.number_format(certificate.score_pct, 0)}
    return render(request, "certificates/verify.html", {"certificate": certificate, "score": score})
