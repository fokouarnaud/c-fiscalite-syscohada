"""Formation Simulation (Form 3) : pièces justificatives virtuelles des parcours (S5, US-82)."""
import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Piece(models.Model):
    """Une pièce justificative fictive (facture, reçu, relevé…), rendue par [[piece:REF]]."""

    class Kind(models.TextChoices):
        PURCHASE_INVOICE = "facture_achat", _("Facture d'achat")
        SALES_INVOICE = "facture_vente", _("Facture de vente")
        RECEIPT = "recu_caisse", _("Reçu de caisse")
        MOMO_RECEIPT = "recu_momo", _("Reçu Mobile Money")
        BANK_STATEMENT = "releve_bancaire", _("Relevé bancaire")
        MOMO_STATEMENT = "releve_momo", _("Relevé Mobile Money")
        PAYSLIP = "bulletin_paie", _("Bulletin de paie")
        ARTICLES = "statuts", _("Statuts")
        LEASE = "bail", _("Bail")
        CUSTOMS = "avis_douane", _("Avis de douane")
        STOCK_CARD = "fiche_stock", _("Fiche de stock")
        BALANCE = "balance", _("Balance")
        DECLARATION = "declaration", _("Déclaration")
        PROCEDURE = "demarche", _("Démarche auprès d'un organisme")

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    partie = models.ForeignKey("courses.Partie", on_delete=models.CASCADE, related_name="pieces",
                               verbose_name=_("parcours"))
    ref = models.CharField(_("référence"), max_length=40, unique=True)
    kind = models.CharField(_("type"), max_length=20, choices=Kind.choices)
    issued_on = models.DateField(_("date"))
    title = models.CharField(_("titre"), max_length=200, blank=True)
    payload = models.JSONField(_("contenu"), default=dict)

    class Meta:
        ordering = ["issued_on", "ref"]
        verbose_name = _("pièce justificative")
        verbose_name_plural = _("pièces justificatives")

    def __str__(self):
        return self.ref

    def clean(self):
        errors = []
        if not self.ref.startswith("S-"):
            errors.append(_("La référence d'une pièce commence par S- (formation Simulation)."))
        errors += payload_errors(self.payload or {}, self.kind)
        if errors:
            raise ValidationError(errors)


def _amount_errors(value, label):
    if not isinstance(value, int) or isinstance(value, bool):
        return [_("%(label)s : montant en FCFA entiers attendu.") % {"label": label}]
    return []


def _label(item):
    label = item.get("label", "")
    return label.get("fr", "") if isinstance(label, dict) else str(label)


INVOICE_KINDS = ("facture_achat", "facture_vente")
ISSUER_FIELDS = ("name", "niu", "rccm", "regime", "centre")
PROCEDURE_FIELDS = ("organisme", "objet", "documents_a_fournir", "document_obtenu", "source")
# Format du NIU de la DGI : M (personne morale) ou P (personne physique), 12 chiffres, une lettre de contrôle.
OFFICIAL_SOURCE = re.compile(r"\[\[(?:cgi|syscohada|guide|source):[^\]]+\]\]")
NIU = re.compile(r"^[MP]\d{12}[A-Z]$")


def realism_errors(payload, kind):
    """S27 et S28 : facture au style camerounais réel (CGI art. 143 (1) b) et démarche reproductible en réalité."""
    errors = []
    if kind in INVOICE_KINDS:
        issuer = payload.get("issuer") or {}
        errors += [_("Facture : émetteur sans %(field)s.") % {"field": field}
                   for field in ISSUER_FIELDS if not issuer.get(field)]
        if issuer.get("niu") and not NIU.match(issuer["niu"]):
            errors.append(_("Facture : NIU de l'émetteur hors du format de la DGI."))
        errors += [_("Facture sans %(field)s.") % {"field": field}
                   for field in ("number", "customer", "einvoice") if not payload.get(field)]
    if kind == "demarche":
        errors += [_("Démarche sans %(field)s.") % {"field": field}
                   for field in PROCEDURE_FIELDS if not payload.get(field)]
        if payload.get("source") and not OFFICIAL_SOURCE.search(payload["source"]):
            # US-97 (U21) : une démarche s'appuie sur un texte officiel cité, sinon elle n'est pas rédigée.
            errors.append(_("Démarche : la source doit citer un texte officiel ([[cgi:]], [[syscohada:]], [[guide:]], "
                             "[[source:]])."))
    return errors


def payload_errors(payload, kind=None):
    """Cohérence arithmétique d'une pièce : quantités, total HT, taxes et TTC, équilibre d'une balance ; réalisme
    camerounais d'une facture ou d'une démarche (S27, S28)."""
    realism = realism_errors(payload, kind)
    errors = []
    lines, totals = payload.get("lines", []), payload.get("totals", [])
    for line in lines:
        for key in ("amount", "unit_price", "debit", "credit"):
            if key in line:
                errors += _amount_errors(line[key], _label(line))
        if {"qty", "unit_price", "amount"} <= line.keys() and line["qty"] * line["unit_price"] != line["amount"]:
            errors.append(_("%(label)s : quantité × prix unitaire ≠ montant.") % {"label": _label(line)})
    for total in totals:
        errors += _amount_errors(total.get("amount"), _label(total))
    if errors:
        return errors + realism
    by_role = {}
    for total in totals:
        by_role.setdefault(total.get("role"), []).append(total["amount"])
    if "ht" in by_role and any("amount" in line for line in lines):
        if sum(line.get("amount", 0) for line in lines) != by_role["ht"][0]:
            errors.append(_("La somme des lignes ne donne pas le total HT."))
    if "ttc" in by_role and "ht" in by_role:
        if by_role["ht"][0] + sum(by_role.get("tax", [])) != by_role["ttc"][0]:
            errors.append(_("Total HT + taxes ≠ total TTC."))
    if any("debit" in line or "credit" in line for line in lines):
        if sum(line.get("debit", 0) for line in lines) != sum(line.get("credit", 0) for line in lines):
            errors.append(_("Total débit ≠ total crédit."))
    return errors + realism
