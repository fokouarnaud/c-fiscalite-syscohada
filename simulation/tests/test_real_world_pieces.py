"""US-82 (S27) et US-97 (S28), demande du 2026-10-30 : pièces au style camerounais réel et démarches réelles auprès
des organismes.

- Une facture porte l'identité fiscale complète de l'émetteur (raison sociale, NIU au format de la DGI, RCCM, régime,
  centre des impôts), son numéro, le client et la référence du système de facturation électronique de la DGI, sans
  laquelle la TVA n'est pas déductible (CGI art. 143 (1) b).
- Une décision prise par un organisme extérieur (immatriculation, affiliation, ouverture de compte…) est une pièce
  « démarche » qui précise l'organisme, les documents à fournir, le document obtenu et la source officielle, pour que
  l'apprenant puisse la refaire en réalité.
- Toute pièce affichée porte la mention « document pédagogique fictif » : elle ne peut pas passer pour un original.
"""
import datetime

import pytest
from django.core.exceptions import ValidationError

from courses.rendering import render_markdown
from simulation.models import Piece

ISSUER = {"name": "Sawa Textiles SARL", "niu": "M012600001234X", "rccm": "RC/DLA/2026/B/0042",
          "regime": "réel", "centre": "CIME Douala", "address": "Akwa, Douala"}
CUSTOMER = {"name": "Ngono Mode SARL", "niu": "M012600005678Y"}


def invoice_payload(**changes):
    payload = {
        "issuer": ISSUER, "customer": CUSTOMER, "number": "FA-2026-0007", "einvoice": "DGI-SFE-2026-000781",
        "lines": [{"label": {"fr": "Chemises", "en": "Shirts"}, "qty": 20, "unit_price": 5000, "amount": 100000}],
        "totals": [{"label": {"fr": "Total HT", "en": "Total excl. tax"}, "role": "ht", "amount": 100000},
                   {"label": {"fr": "TVA 17,5 %", "en": "VAT 17.5%"}, "role": "tax", "amount": 17500},
                   {"label": {"fr": "CAC 10 %", "en": "Council cents 10%"}, "role": "tax", "amount": 1750},
                   {"label": {"fr": "Net à payer", "en": "Amount due"}, "role": "ttc", "amount": 119250}],
    }
    payload.update(changes)
    return payload


@pytest.fixture
def invoice(partie):
    return Piece(partie=partie, ref="S-A-01-003", kind=Piece.Kind.PURCHASE_INVOICE,
                 issued_on=datetime.date(2026, 1, 5), title_fr="Facture FA-2026-0007", payload=invoice_payload())


def test_a_cameroonian_invoice_with_its_full_tax_identity_is_valid(invoice):
    invoice.full_clean()


@pytest.mark.parametrize("field", ["name", "niu", "rccm", "regime", "centre"])
def test_an_invoice_names_its_issuer_fully(invoice, field):
    invoice.payload = invoice_payload(issuer={k: v for k, v in ISSUER.items() if k != field})

    with pytest.raises(ValidationError, match=field):
        invoice.full_clean()


def test_the_issuer_niu_follows_the_dgi_format(invoice):
    """Format du NIU de la DGI : une lettre (M morale, P physique), 12 chiffres, une lettre de contrôle."""
    invoice.payload = invoice_payload(issuer={**ISSUER, "niu": "123456"})

    with pytest.raises(ValidationError, match="NIU"):
        invoice.full_clean()


@pytest.mark.parametrize("field", ["number", "customer", "einvoice"])
def test_an_invoice_has_its_number_its_customer_and_its_dgi_e_invoicing_reference(invoice, field):
    """CGI art. 143 (1) b : sans facture du système de facturation électronique de la DGI, pas de TVA déductible."""
    payload = invoice_payload()
    del payload[field]
    invoice.payload = payload

    with pytest.raises(ValidationError, match=field):
        invoice.full_clean()


PROCEDURE = {
    "organisme": {"fr": "Centre des impôts de rattachement (DGI)", "en": "Tax office (DGI)"},
    "objet": {"fr": "Immatriculation et obtention du NIU", "en": "Registration and taxpayer number"},
    "documents_a_fournir": [{"fr": "Statuts enregistrés", "en": "Registered articles"},
                            {"fr": "Plan de localisation du siège", "en": "Head office location map"}],
    "document_obtenu": {"fr": "Attestation d'immatriculation portant le NIU", "en": "Registration certificate"},
    "source": "[[cgi:art. L 1]]",
}


@pytest.fixture
def procedure(partie):
    return Piece(partie=partie, ref="S-A-01-000", kind=Piece.Kind.PROCEDURE, issued_on=datetime.date(2026, 1, 2),
                 title_fr="Démarche : immatriculation", payload=PROCEDURE)


def test_a_complete_procedure_is_valid(procedure):
    procedure.full_clean()


@pytest.mark.parametrize("field", ["organisme", "objet", "documents_a_fournir", "document_obtenu", "source"])
def test_a_procedure_says_where_to_go_what_to_bring_what_you_get_and_on_what_basis(procedure, field):
    """US-97 : organisme, objet, documents à fournir, document obtenu et source sont obligatoires."""
    procedure.payload = {k: v for k, v in PROCEDURE.items() if k != field}

    with pytest.raises(ValidationError, match=field):
        procedure.full_clean()


@pytest.mark.django_db
def test_every_displayed_piece_is_marked_as_a_fictitious_teaching_document(invoice):
    invoice.save()

    html = render_markdown("[[piece:S-A-01-003]]")

    assert "Document pédagogique fictif" in html
    assert "M012600001234X" in html and "RC/DLA/2026/B/0042" in html and "DGI-SFE-2026-000781" in html


@pytest.mark.django_db
def test_a_procedure_is_shown_as_a_checklist_of_documents(procedure):
    """US-97 : documents à fournir en liste, source en badge cité."""
    procedure.save()

    html = render_markdown("[[piece:S-A-01-000]]")

    assert "Centre des impôts de rattachement (DGI)" in html
    assert "<li>Statuts enregistrés</li>" in html and "Attestation d&#x27;immatriculation portant le NIU" in html
    assert '<cite class="source"' in html and "CGI 2026, art. L 1</cite>" in html


def test_a_procedure_source_is_an_official_citation(procedure):
    """US-97 (U21) : la source est une balise de texte officiel ([[cgi:]], [[syscohada:]], [[guide:]]) ; une démarche
    sans texte officiel disponible n'est pas rédigée."""
    procedure.payload = {**PROCEDURE, "source": "site internet du greffe"}

    with pytest.raises(ValidationError, match="source"):
        procedure.full_clean()
