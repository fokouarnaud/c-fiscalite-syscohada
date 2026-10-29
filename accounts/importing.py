"""Import d'une liste d'apprenants (CSV) dans une promotion (US-17)."""
import csv
import io
import secrets
from dataclasses import dataclass, field

from catalog.models import Enrollment

from .models import User


@dataclass
class ImportReport:
    created: list = field(default_factory=list)  # [{"username", "password"}] : mot de passe affiché une seule fois
    skipped: list = field(default_factory=list)


def import_learners(text, promotion):
    dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=";,")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if "username" not in (reader.fieldnames or []):
        raise ValueError("La colonne « username » est obligatoire.")
    report = ImportReport()
    for line in reader:
        username = (line.get("username") or "").strip()
        if not username:
            continue
        if User.objects.filter(username=username).exists():
            report.skipped.append(username)
            continue
        password = secrets.token_urlsafe(9)
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=(line.get("first_name") or "").strip(),
            last_name=(line.get("last_name") or "").strip(),
            email=(line.get("email") or "").strip(),
            role=User.Role.LEARNER,
        )
        Enrollment.objects.create(
            user=user, formation=promotion.formation, promotion=promotion, source=Enrollment.Source.IMPORT
        )
        report.created.append({"username": username, "password": password})
    return report
