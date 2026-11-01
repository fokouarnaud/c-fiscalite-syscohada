"""US-82 : une pièce justificative de la simulation, identifiée par sa référence et rattachée à son parcours (S5)."""
import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from simulation.models import Piece
from simulation.tests.test_real_world_pieces import CUSTOMER, ISSUER


def invoice(**changes):
    payload = {
        "issuer": ISSUER, "customer": CUSTOMER, "number": "FA-2026-0001", "einvoice": "DGI-SFE-2026-000001",
        "fields": [{"label": {"fr": "Fournisseur", "en": "Supplier"}, "value": "Sawa Textiles SARL"}],
        "lines": [
            {"label": {"fr": "Chemises", "en": "Shirts"}, "qty": 20, "unit_price": 5000, "amount": 100000},
            {"label": {"fr": "Pantalons", "en": "Trousers"}, "qty": 10, "unit_price": 8000, "amount": 80000},
        ],
        "totals": [
            {"label": {"fr": "Total HT", "en": "Total excl. tax"}, "role": "ht", "amount": 180000},
            {"label": {"fr": "TVA 19,25 %", "en": "VAT 19.25%"}, "role": "tax", "amount": 34650},
            {"label": {"fr": "Net à payer", "en": "Amount due"}, "role": "ttc", "amount": 214650},
        ],
    }
    payload.update(changes)
    return payload


@pytest.fixture
def piece(partie):
    return Piece(partie=partie, ref="S-A-01-001", kind=Piece.Kind.PURCHASE_INVOICE,
                 issued_on=datetime.date(2026, 1, 5), title_fr="Facture d'achat n° 1", payload=invoice())


def test_a_piece_belongs_to_its_parcours_and_keeps_its_reference(piece):
    piece.save()

    assert Piece.objects.get(ref="S-A-01-001").partie == piece.partie
    assert piece.public_id is not None


def test_two_pieces_cannot_share_a_reference(piece):
    piece.save()

    with pytest.raises(IntegrityError):
        Piece.objects.create(partie=piece.partie, ref="S-A-01-001", kind=Piece.Kind.RECEIPT,
                             issued_on=datetime.date(2026, 1, 6), payload=invoice())


def test_a_coherent_invoice_is_valid(piece):
    piece.full_clean()


def test_a_reference_without_the_simulation_prefix_is_refused(piece):
    piece.ref = "C-A-01-001"

    with pytest.raises(ValidationError, match="S-"):
        piece.full_clean()


def test_lines_must_add_up_to_the_total_before_tax(piece):
    piece.payload = invoice(lines=[{"label": {"fr": "Chemises", "en": "Shirts"}, "amount": 100000}])

    with pytest.raises(ValidationError, match="HT"):
        piece.full_clean()


def test_total_before_tax_plus_taxes_must_equal_the_total_due(piece):
    totals = invoice()["totals"]
    totals[2]["amount"] = 214000
    piece.payload = invoice(totals=totals)

    with pytest.raises(ValidationError, match="TTC"):
        piece.full_clean()


def test_quantity_times_unit_price_must_equal_the_line_amount(piece):
    lines = invoice()["lines"]
    lines[0]["qty"] = 21
    piece.payload = invoice(lines=lines)

    with pytest.raises(ValidationError, match="Chemises"):
        piece.full_clean()


def test_amounts_are_whole_fcfa(piece):
    lines = invoice()["lines"]
    lines[0]["amount"] = 100000.5
    piece.payload = invoice(lines=lines)

    with pytest.raises(ValidationError, match="FCFA"):
        piece.full_clean()


def test_a_balance_must_have_equal_debit_and_credit_totals(piece):
    piece.kind = Piece.Kind.BALANCE
    piece.payload = {
        "lines": [{"label": {"fr": "521 Banque", "en": "521 Bank"}, "debit": 5000000, "credit": 0},
                  {"label": {"fr": "101 Capital", "en": "101 Capital"}, "debit": 0, "credit": 4000000}],
    }

    with pytest.raises(ValidationError, match="débit"):
        piece.full_clean()
