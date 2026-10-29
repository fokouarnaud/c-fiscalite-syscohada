"""Règles de notation (AGENTS.md, C10 et C11). Scores exacts en Fraction, de 0 à 1."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from fractions import Fraction

FCFA, PERCENT, DAYS, MONTHS, YEARS = "FCFA", "%", "jours", "mois", "années"
# Unités saisies (US-35, C11), en minuscules et sans espace -> unité stockée. Aucun préfixe SI.
UNIT_ALIASES = {
    "fcfa": FCFA, "f": FCFA, "cfa": FCFA, "xaf": FCFA,
    "%": PERCENT,
    "j": DAYS, "jour": DAYS, "jours": DAYS, "day": DAYS, "days": DAYS,
    "mois": MONTHS, "month": MONTHS, "months": MONTHS,
    "an": YEARS, "ans": YEARS, "année": YEARS, "années": YEARS, "annee": YEARS, "annees": YEARS,
    "year": YEARS, "years": YEARS,
}
# Un nombre (chiffres, espaces, points, virgules) suivi d'une unité facultative qui ne commence pas par un chiffre.
QUANTITY = re.compile(r"^([+-]?)(\d[\d .,]*?)\s*([^\d\s.,].*)?$")
SPACE_GROUPS = re.compile(r"\d{1,3}( \d{3})+([.,]\d+)?")


def _grouped(digits, thousands):
    return re.fullmatch(r"\d{1,3}(%s\d{3})+" % re.escape(thousands), digits) is not None


def _number(text):
    """« 1 250 000 », « 1.250.000,50 », « 1,250,000.50 », « 19,25 » -> Decimal ; None si la saisie est ambiguë ou fausse."""
    text = re.sub(r" +", " ", text)
    if " " in text:
        if not SPACE_GROUPS.fullmatch(text):
            return None
        return text.replace(" ", "").replace(",", ".")
    dots, commas = text.count("."), text.count(",")
    if dots and commas:
        decimal = "." if text.rfind(".") > text.rfind(",") else ","
        thousands = "," if decimal == "." else "."
        whole, _, fraction = text.rpartition(decimal)
        if not fraction.isdigit() or not _grouped(whole, thousands):
            return None
        return whole.replace(thousands, "") + "." + fraction
    for sep, count in ((".", dots), (",", commas)):
        if count > 1:
            return text.replace(sep, "") if _grouped(text, sep) else None
    # Un seul point suivi de trois chiffres sépare les milliers (usage français) ; sinon, point ou virgule décimale.
    if dots == 1 and re.fullmatch(r"\d{1,3}\.\d{3}", text):
        return text.replace(".", "")
    return text.replace(",", ".")


def score_answer(qtype, correct_ids, selected_ids):
    correct_ids, selected_ids = set(correct_ids), set(selected_ids)
    if qtype == "multiple":
        if not correct_ids:
            return Fraction(0)
        good = len(selected_ids & correct_ids)
        bad = len(selected_ids - correct_ids)
        return max(Fraction(0), Fraction(good - bad, len(correct_ids)))
    return Fraction(1) if selected_ids == correct_ids else Fraction(0)


def parse_quantity(text):
    """« 1 250 000 FCFA » -> (Decimal("1250000"), "FCFA") ; « 19,25 % » -> (Decimal("19.25"), "%") ; None sinon."""
    # NFKC ramène les espaces insécables (fines ou non) à l'espace ; le moins typographique vaut le trait d'union.
    match = QUANTITY.match(unicodedata.normalize("NFKC", text or "").strip().replace("−", "-"))
    if not match:
        return None
    sign, number, rest = match.groups()
    unit = ""
    if rest:
        unit = UNIT_ALIASES.get(rest.replace(" ", "").lower())
        if unit is None:
            return None
    number = _number(number.strip())
    if number is None:
        return None
    try:
        value = Decimal(sign + number)
    except InvalidOperation:
        return None
    return value, unit


def format_quantity(value, unit):
    """Decimal("1250000"), "FCFA" -> « 1 250 000 FCFA » (milliers et décimales au format de la langue active)."""
    from django.utils.formats import number_format
    from django.utils.translation import gettext, pgettext

    number = number_format(Decimal(format(value.normalize(), "f")), use_l10n=True, force_grouping=True)
    if unit == PERCENT:
        # Une espace avant « % » en français, aucune en anglais.
        return pgettext("pourcentage", "%(number)s %%") % {"number": number}
    labels = {FCFA: "FCFA", DAYS: gettext("jours"), MONTHS: gettext("mois"), YEARS: gettext("années")}
    return f"{number} {labels.get(unit, unit)}".strip()


def score_numeric(expected, unit, tolerance_pct, answer, tolerance_abs=Decimal("0")):
    """Juste si l'écart est ≤ tolérance absolue, ou ≤ |attendu| × tolérance relative / 100 ; une unité saisie doit être
    l'unité attendue (C11 : 1 FCFA d'écart par défaut pour les arrondis)."""
    parsed = parse_quantity(answer)
    if parsed is None:
        return Fraction(0)
    value, given_unit = parsed
    if given_unit and given_unit != unit:
        return Fraction(0)
    gap = abs(value - expected)
    return Fraction(1) if gap <= tolerance_abs or gap <= abs(expected) * tolerance_pct / 100 else Fraction(0)


def score_matching(expected_pairs, given_pairs):
    """Part des paires justes : {gauche: droite} attendu contre {gauche: droite} donné."""
    if not expected_pairs:
        return Fraction(0)
    right = sum(1 for left, target in expected_pairs.items() if given_pairs.get(left) == target)
    return Fraction(right, len(expected_pairs))


JOURNAL_EXTRA_PENALTY = Fraction(1, 2)  # U1 : une ligne en trop retire une demi-ligne


def account_matches(expected, match, given):
    """Compte saisi jugé au niveau demandé (C10) : « exact », « class » (1er chiffre) ou les N premiers chiffres."""
    given = (given or "").strip()
    if not given.isdigit():
        return False
    if match == "exact":
        return given == expected
    width = 1 if match == "class" else int(match)
    return len(given) >= width and given[:width] == expected[:width]


def _line_is_right(expected, given):
    if given["side"] != expected["side"] or not account_matches(expected["account"], expected["match"], given["account"]):
        return False
    parsed = parse_quantity(given["amount"])
    return parsed is not None and parsed[1] in ("", FCFA) and parsed[0] == expected["amount"]


def filled_lines(given_lines):
    """Lignes saisies non vides (une ligne blanche du formulaire ne compte ni juste ni en trop)."""
    return [g for g in given_lines if any(str(g.get(k) or "").strip() for k in ("account", "side", "amount"))]


def match_journal(expected_lines, given_lines):
    """Indices des lignes saisies (non vides) appariées à une ligne attendue ; chaque ligne ne sert qu'une fois.
    Appariement maximal par chemins augmentants : quelques lignes, coût négligeable."""
    given = filled_lines(given_lines)
    owner = {}

    def assign(e, seen):
        for g, given_line in enumerate(given):
            if g not in seen and _line_is_right(expected_lines[e], given_line):
                seen.add(g)
                if g not in owner or assign(owner[g], seen):
                    owner[g] = e
                    return True
        return False

    for e in range(len(expected_lines)):
        assign(e, set())
    return set(owner)


def score_journal(expected_lines, given_lines):
    """Part des lignes attendues retrouvées, moins une demi-ligne par ligne en trop ; plancher à 0. L'ordre des lignes et
    le libellé ne comptent pas (US-34)."""
    if not expected_lines:
        return Fraction(0)
    right = len(match_journal(expected_lines, given_lines))
    extra = max(0, len(filled_lines(given_lines)) - len(expected_lines))
    return max(Fraction(0), (right - JOURNAL_EXTRA_PENALTY * extra) / len(expected_lines))
