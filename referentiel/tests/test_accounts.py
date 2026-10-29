"""US-63 : le plan comptable SYSCOHADA révisé, référence des citations [[syscohada:]] et des questions `journal`."""
import pytest

from referentiel.models import SyscohadaAccount


@pytest.fixture
def tva_accounts(db):
    for code, label in (("4", "Comptes de tiers"), ("44", "État et collectivités publiques"),
                        ("445", "État, TVA récupérable"), ("4452", "État, TVA récupérable sur achats")):
        SyscohadaAccount.objects.create(code=code, label_fr=label)


def test_an_account_takes_its_class_and_level_from_its_code(tva_accounts):
    account = SyscohadaAccount.objects.get(code="4452")

    assert account.account_class == 4
    assert account.level == 4


def test_an_account_hangs_under_the_longest_existing_prefix(tva_accounts):
    assert SyscohadaAccount.objects.get(code="4452").parent.code == "445"
    assert SyscohadaAccount.objects.get(code="4").parent is None


def write_plan(tmp_path, rows):
    path = tmp_path / "syscohada.csv"
    path.write_text("code;label_fr;label_en\n" + "".join(f"{c};{fr};{en}\n" for c, fr, en in rows), encoding="utf-8")
    return path


def test_the_plan_is_imported_from_a_versioned_csv_parents_first(db, tmp_path):
    from django.core.management import call_command

    # Fils avant parent dans le fichier : l'import doit tout de même rattacher 4452 à 445.
    plan = write_plan(tmp_path, [("4452", "État, TVA récupérable sur achats", "State, recoverable VAT on purchases"),
                                 ("445", "État, TVA récupérable", "State, recoverable VAT")])

    call_command("import_syscohada", str(plan), verbosity=0)

    account = SyscohadaAccount.objects.get(code="4452")
    assert account.parent.code == "445"
    assert account.label_en == "State, recoverable VAT on purchases"


def test_reimporting_the_plan_updates_labels_without_duplicating(db, tmp_path):
    from django.core.management import call_command

    call_command("import_syscohada", str(write_plan(tmp_path, [("571", "Caisse", "Cash")])), verbosity=0)
    call_command("import_syscohada", str(write_plan(tmp_path, [("571", "Caisse siège social", "Cash")])), verbosity=0)

    assert SyscohadaAccount.objects.count() == 1
    assert SyscohadaAccount.objects.get(code="571").label_fr == "Caisse siège social"


def test_the_versioned_plan_imports_whole_and_linked(db):
    """US-63 : content/referentiel/syscohada.csv donne les 1 330 comptes du plan révisé, plus les 9 classes et le
    compte 10 « Capital » (absent du PDF source), chacun rattaché à son parent."""
    from django.conf import settings
    from django.core.management import call_command

    call_command("import_syscohada", str(settings.BASE_DIR / "content" / "referentiel" / "syscohada.csv"), verbosity=0)

    assert SyscohadaAccount.objects.count() == 1340
    assert SyscohadaAccount.objects.get(code="4452").parent.code == "445"
    assert SyscohadaAccount.objects.get(code="10").parent.code == "1"
    assert not SyscohadaAccount.objects.filter(level__gt=1, parent=None).exists()


def test_the_versioned_plan_names_every_account_in_english(db):
    """US-63 (U5) : chaque compte du plan, sous-comptes à 4 chiffres compris, a son libellé anglais."""
    from django.conf import settings
    from django.core.management import call_command

    call_command("import_syscohada", str(settings.BASE_DIR / "content" / "referentiel" / "syscohada.csv"), verbosity=0)

    assert list(SyscohadaAccount.objects.filter(label_en="").values_list("code", flat=True)[:5]) == []
    assert SyscohadaAccount.objects.get(code="445").label_en == "State, recoverable VAT"
    assert SyscohadaAccount.objects.get(code="60").label_fr == "Achats et variations de stocks"  # libellé du PDF réparé
