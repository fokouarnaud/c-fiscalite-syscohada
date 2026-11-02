"""Règles du contenu (US-71 à US-73, C2, C15, C21), partagées par les tests témoins et test_content_files.py."""
import re

SOURCE_TAG = re.compile(r"\[\[(?:cgi|syscohada|guide):[^\]]+\]\]")
ACCOUNT_TAG = re.compile(r"\[\[syscohada:(\d+)\]\]")
PARAM_TAG = re.compile(r"\[\[param:([a-z0-9_.]+)\]\]")
# Les livres qui servent de trame ne sont jamais nommés (C21) : mots entiers, et tout ISBN.
BOOK = re.compile(r"\b(DCG|Dunod|Disle|Bouvier|Plagnet)\b|ISBN[\s:]*[\d-]+")
# Simulation (US-96, S7, S9) : sigle inconnu du CGI, et régime supprimé par la LF 2026 sauf pour expliquer sa suppression.
VSD = re.compile(r"\bVSD\b")
SIMPLIFIED = re.compile(r"régime simplifié|simplified regime", re.IGNORECASE)
ABOLITION = re.compile(r"supprim|remplac|abolish|replaced", re.IGNORECASE)
WEB_SOURCE_TAG = re.compile(r"\[\[source:([a-z0-9-]{1,40})\]\]")
PIECE_REFS = re.compile(r"\[\[piece:(S-[A-Z0-9-]{1,38})\]\]")
EXAM_MINIMUM, QUIZ_MINIMUM = 12, 8
AMOUNT_UNITS = ("FCFA", "%")


def cites_a_source(body):
    return SOURCE_TAG.search(body) is not None


def unknown_accounts(body, known):
    return [code for code in ACCOUNT_TAG.findall(body) if code not in known]


def unknown_parameters(body, known):
    return [key for key in PARAM_TAG.findall(body) if key not in known]


def book_mentions(text):
    return [match.group(0) for match in BOOK.finditer(text)]


def question_problems(question, prefix, known_accounts):
    """Défauts d'une question de questions.json, sous la forme « <id> : <défaut> »."""
    qid = question.get("id", "?")
    problems = []
    if not qid.startswith(f"{prefix}-"):
        problems.append(f"identifiant sans préfixe {prefix}-")
    for field, label in (("prompt", "énoncé"), ("explanation", "explication")):
        for lang in ("fr", "en"):
            if not (question.get(field) or {}).get(lang, "").strip():
                problems.append(f"{label} {lang.upper()} manquant{'e' if field == 'explanation' else ''}")
    for line in question.get("journal", []):
        if str(line["account"]) not in known_accounts:
            problems.append(f"compte inconnu {line['account']}")
    if (question.get("numeric") or {}).get("unit") in AMOUNT_UNITS and not question.get("exercice"):
        problems.append("question chiffrée sans exercice")
    return [f"{qid} : {problem}" for problem in problems]


def volume_shortfalls(questions):
    """Banque d'un module trop maigre pour l'examen (12 tirées parmi au moins 12) ou le quiz (8)."""
    exam = sum(1 for q in questions if q.get("usage") == "exam")
    quiz = sum(1 for q in questions if q.get("usage", "quiz") == "quiz")
    shortfalls = []
    if exam < EXAM_MINIMUM:
        shortfalls.append(f"{exam} questions d'examen sur {EXAM_MINIMUM}")
    if quiz < QUIZ_MINIMUM:
        shortfalls.append(f"{quiz} questions de quiz sur {QUIZ_MINIMUM}")
    return shortfalls


def vocabulary_problems(text):
    """US-96 : « VSD », et « régime simplifié » hors d'une phrase qui explique sa suppression."""
    problems = ["sigle VSD" for _ in VSD.finditer(text)]
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        if SIMPLIFIED.search(sentence) and not ABOLITION.search(sentence):
            problems.append("régime simplifié présenté comme en vigueur")
    return problems


def simulation_problems(base, partie, questions, accounts, rates=None):
    """US-93 et DoD-Parcours : livre officiel, pièces, questions journal et balances d'un parcours de la simulation."""
    import datetime
    import json
    from collections import Counter

    from simulation.models import payload_errors
    from tools.simulation import ledger

    pieces = json.loads((base / partie["pieces"]).read_text(encoding="utf-8")) if partie.get("pieces") else []
    problems_month = pieces_per_month_problems(pieces)
    entries = json.loads((base / partie["ledger"]).read_text(encoding="utf-8")) if partie.get("ledger") else []
    refs = {piece["ref"] for piece in pieces}
    problems = problems_month + [f"{piece['ref']} : {error}" for piece in pieces
                                 for error in payload_errors(piece.get("payload", {}), piece.get("kind"))]
    problems += [f"{piece['ref']} : {problem}" for piece in pieces
                 for problem in vocabulary_problems(json.dumps(piece, ensure_ascii=False))]
    # S19 : l'entité peut ouvrir ses propres sous-comptes (ex. 5521 MTN MoMo) sous un compte du plan révisé.
    sub_accounts = {code for code in partie.get("sous_comptes", {})
                    if any(code.startswith(parent) and code != parent for parent in accounts)}
    problems += [f"sous-compte {code} sans compte parent dans le plan SYSCOHADA"
                 for code in sorted(set(partie.get("sous_comptes", {})) - sub_accounts)]
    problems += ledger.entry_errors(entries, set(accounts) | sub_accounts, refs)
    cited = {ref for question in questions for field in ("prompt", "explanation") for lang in ("fr", "en")
             for ref in PIECE_REFS.findall((question.get(field) or {}).get(lang, ""))}
    used = cited | {piece["ref"] for piece in pieces if piece["kind"] in ("balance", "declaration")}
    problems += [f"{ref} : pièce utilisée par aucune écriture ni question" for ref in ledger.unused_pieces(entries, refs, used)]
    journal = [(q["id"], PIECE_REFS.findall(q["prompt"]["fr"])[0],
                [(line["account"], line["side"], line["amount"]) for line in q["journal"]])
               for q in questions if q.get("type") == "journal" and PIECE_REFS.findall(q["prompt"]["fr"])]
    problems += [f"{qid} : clé différente de l'écriture du livre officiel" for qid in ledger.journal_mismatches(entries, journal)]
    problems += declaration_problems(entries, questions, rates or {})
    problems += reconciliation_problems(entries, questions)
    problems += calculation_problems(questions)
    problems += regime_problems(partie.get("regime", "reel"), entries, questions)
    if partie.get("tva_encaissement"):
        # US-92 : TVA sur prestations exigible à l'encaissement : 4432 n'est crédité que sur une pièce de règlement.
        payments = {piece["ref"] for piece in pieces if piece["kind"] in PAYMENT_KINDS}
        problems += [f"{entry['piece']} : TVA sur prestations (4432) constatée hors encaissement"
                     for entry in entries if entry["piece"] not in payments
                     for line in entry["lines"] if line["account"].startswith("4432") and line["side"] == "credit"]
        suspense = partie.get("compte_tva_attente")
        if suspense and suspense not in accounts:
            # U20 (S24, compte 471 validé) : le compte d'attente est un compte du plan SYSCOHADA révisé.
            problems.append(f"compte_tva_attente {suspense} absent du plan SYSCOHADA")
        for entry in entries:
            if entry["piece"] in payments and suspense:
                credited = sum(l["amount"] for l in entry["lines"] if l["account"].startswith("4432") and l["side"] == "credit")
                released = sum(l["amount"] for l in entry["lines"] if l["account"] == suspense and l["side"] == "debit")
                if credited != released:
                    problems.append(f"{entry['piece']} : TVA exigible {credited} ≠ {released} soldé du compte "
                                    f"d'attente {suspense}")
    if partie.get("centre_impots") in TAX_OFFICES:
        # US-89 (CGI art. 18 (1), art. C 41) : la déclaration de l'exercice est datée au plus tard à son échéance.
        deadline = ledger.tax_return_deadline(partie["centre_impots"], 2026, partie.get("regime", "reel"))
        problems += [f"{piece['ref']} : déclaration du {piece['date']} après l'échéance du {deadline.isoformat()}"
                     for piece in pieces if piece["kind"] == "declaration" and piece["date"] >= "2027-01-01"
                     and datetime.date.fromisoformat(piece["date"]) > deadline]
    bridge = [q for q in questions if q.get("passerelle")]
    if partie["slug"] == "a" and bridge:
        # US-89 (S21, S23) : dès que la passerelle est rédigée, elle met en scène ses six éléments, chacun sur une pièce.
        staged = {q["passerelle"] for q in bridge}
        problems += [f"passerelle : élément {item} absent" for item in BRIDGE_ITEMS if item not in staged]
        problems += [f"{q['id']} : élément {q['passerelle']} sans pièce justificative" for q in bridge
                     if not PIECE_REFS.search((q.get("prompt") or {}).get("fr", ""))]
    if partie.get("regime", "reel") != "reel":
        # US-90 (S14) : à l'IGS, le SMT remplace la DSF normale.
        problems += [f"{piece['ref']} : DSF normale dans un parcours à l'IGS" for piece in pieces if piece.get("dsf")]
    if partie["slug"] == "d":
        # US-92 (S10) : le parcours D explique le contraste de la retenue à 11 % (10 % + CAC, entreprise hors fichier).
        rates = [(q.get("calcul") or {}).get("args", [None, None])[1] for q in questions
                 if (q.get("calcul") or {}).get("fonction") == "retenue_source"]
        if 10 not in rates:
            problems.append("parcours D sans la retenue de contraste à 11 % (taux 10 % + CAC)")
    problems += [f"{piece['ref']} : tableau « {piece['dsf']} » hors des tableaux de DSF retenus (S12)"
                 for piece in pieces if piece.get("dsf") and piece["dsf"] not in DSF_TABLES]
    # US-87 (S6) : les frais de constitution (pièce « statuts ») vont en charges, jamais en immobilisation (classe 2).
    articles = {piece["ref"] for piece in pieces if piece["kind"] == "statuts"}
    if articles and not any(q.get("piege") == "frais_etablissement" for q in questions):
        problems.append("frais de constitution sans question piège sur l'ancienne immobilisation des frais d'établissement")
    # US-88 : toute dotation calculée par une question figure au 31 décembre dans le livre officiel (comptes 681).
    year_end = Counter(line["amount"] for entry in entries if entry["date"] == "2026-12-31"
                       for line in entry["lines"] if line["account"].startswith("681") and line["side"] == "debit")
    for question in questions:
        rule = question.get("calcul") or {}
        if rule.get("fonction", "").startswith("amortissement") and question["numeric"]["value"] not in year_end:
            problems.append(f"{question['id']} : dotation {question['numeric']['value']} absente du livre officiel "
                            f"au 31 décembre (compte 681)")
    # US-88 : le stock final valorisé par une question (CMUP ou PEPS) figure au 31 décembre au débit d'un compte 3.
    closing_stock = Counter(line["amount"] for entry in entries if entry["date"] == "2026-12-31"
                            for line in entry["lines"] if line["account"].startswith("3") and line["side"] == "debit")
    for question in questions:
        rule = question.get("calcul") or {}
        if rule.get("resultat") == ["valeur_stock"] and question["numeric"]["value"] not in closing_stock:
            problems.append(f"{question['id']} : stock final {question['numeric']['value']} absent du livre officiel "
                            f"au 31 décembre (comptes 3)")
    problems += [f"{entry['piece']} : frais de constitution portés au compte {line['account']} au lieu des charges"
                 for entry in entries if entry["piece"] in articles
                 for line in entry["lines"] if line["side"] == "debit" and line["account"].startswith("2")]
    for piece in pieces:
        if piece["kind"] == "balance":
            expected = ledger.balance_piece(entries, before=datetime.date.fromisoformat(piece["date"]), labels=accounts)
            if piece.get("payload", {}).get("lines") != expected["lines"]:
                problems.append(f"{piece['ref']} : balance différente de celle calculée sur le livre officiel")
    return [str(problem) for problem in problems]


SIMULATION_MODULES, SIMULATION_EXAM_DRAW = 7, 4
REGIME_WORDS = {"reel": "réel", "igs": "IGS", "igs_puis_reel": "IGS"}
TAX_OFFICES = ("dge", "cime", "cfl")
DELIVERY_ORDER = ("a", "e", "b3", "c", "d", "b1", "b2")  # S20, S29
# US-89 (S21, S23) : éléments de la passerelle de A ; S12 : tableaux de la DSF.
BRIDGE_ITEMS = ("amendes", "amortissement_excedentaire", "dons_excedentaires", "charge_sans_piece",
                "impot_societes", "reprise_provision_taxee")
DSF_TABLES = ("bilan", "compte_resultat", "passage", "liquidation_is")


def manifest_problems(manifest):
    """US-80 (S11, S21, U14) : structure imposée au manifeste de la simulation (préfixe S) ; rien pour les autres."""
    if manifest.get("prefix") != "S":
        return []
    problems = []
    if manifest.get("icon") != "briefcase":
        problems.append("icône de la simulation attendue : briefcase")
    note = manifest.get("prerequisite_note") or {}
    if not (note.get("fr", "").strip() and note.get("en", "").strip()):
        problems.append("prérequis indicatif FR et EN manquant")
    slugs = [partie["slug"] for partie in manifest.get("parties", [])]
    if slugs != list(DELIVERY_ORDER[:len(slugs)]):
        # US-80 (S20) : un parcours par déploiement, dans l'ordre A → B3 → C → D → B1 → B2.
        problems.append(f"ordre des parcours {slugs} ; attendu : {list(DELIVERY_ORDER[:len(slugs)])}")
    if manifest.get("open") and "a" not in slugs:
        problems.append("formation ouverte sans le parcours A (S1, S20)")
    for partie in manifest.get("parties", []):
        description = partie.get("description") or {}
        if not (description.get("fr", "").strip() and description.get("en", "").strip()):
            problems.append(f"{partie['slug']} : description du parcours FR et EN manquante")
        elif REGIME_WORDS.get(partie.get("regime", "reel"), "") not in description["fr"]:
            problems.append(f"{partie['slug']} : la description doit citer le régime "
                            f"« {REGIME_WORDS.get(partie.get('regime', 'reel'))} »")
        if partie.get("centre_impots") not in TAX_OFFICES:
            # US-89 (CGI art. 18 (1)) : le centre de rattachement fixe l'échéance de la DSF.
            problems.append(f"{partie['slug']} : centre_impots attendu parmi {', '.join(TAX_OFFICES)}")
        if partie.get("tva_encaissement") and not partie.get("compte_tva_attente"):
            problems.append(f"{partie['slug']} : compte_tva_attente requis avec la TVA à l'encaissement (U20)")
        if partie["slug"] == "a" and partie.get("centre_impots") != "cime":
            # S25 (validée le 2026-10-30) : Ngono Mode SARL relève du CIME, DSF au plus tard le 15 avril 2027.
            problems.append("a : centre_impots « cime » attendu pour Ngono Mode SARL (S25)")
        if partie.get("regime", "reel") != "reel" and partie.get("systeme_comptable") != "smt":
            # S14, S26 : un parcours à l'IGS tient le SMT ; ses seuils (AUDCIF) ne sont pas codés faute de source.
            problems.append(f"{partie['slug']} : systeme_comptable « smt » attendu pour un parcours à l'IGS")
        if len(partie.get("modules", [])) != SIMULATION_MODULES:
            problems.append(f"{partie['slug']} : {SIMULATION_MODULES} modules attendus "
                            f"(Création, T1 à T4, Inventaire, Passerelle + DSF)")
        if (partie.get("exam") or {}).get("questions_per_module") != SIMULATION_EXAM_DRAW:
            problems.append(f"{partie['slug']} : exam.questions_per_module = {SIMULATION_EXAM_DRAW} attendu")
    return problems


def pieces_per_month_problems(pieces, low=8, high=12):
    """DoD-Parcours point 1 (S4) : un parcours qui couvre les douze mois de 2026 a 8 à 12 pièces comptables datées par
    mois ; les démarches (S28) ne sont pas des pièces comptables."""
    counts = {}
    for piece in pieces:
        if piece["kind"] != "demarche" and piece["date"].startswith("2026-"):
            counts[piece["date"][:7]] = counts.get(piece["date"][:7], 0) + 1
    if len(counts) < 12:
        return []
    return [f"{month} : {count} pièces ({low} à {high} attendues, S4)" for month, count in sorted(counts.items())
            if not low <= count <= high]


def turnover_problems(manifest, rates):
    """S25 et S26 : le chiffre d'affaires visé d'un parcours fixe son centre des impôts (DGI : CIME de 50 millions à
    3 milliards, DGE au-delà) et, à l'IGS, son éligibilité au SMT (AUDCIF art. 13 : négoce sous 60 millions)."""
    from tools.simulation import ledger

    if manifest.get("prefix") != "S" or "dgi.seuil_cime" not in rates:
        return []
    problems = []
    for partie in manifest.get("parties", []):
        turnover = partie.get("chiffre_affaires_vise")
        if turnover is None:
            continue
        regime = partie.get("regime", "reel")
        if regime == "reel":
            expected = ledger.tax_office(turnover, rates["dgi.seuil_cime"], rates["dgi.seuil_dge"])
            if partie.get("centre_impots") != expected:
                problems.append(f"{partie['slug']} : centre_impots « {expected} » attendu pour un CA de {turnover}")
        elif "smt.seuil_negoce" in rates and turnover >= rates["smt.seuil_negoce"]:
            problems.append(f"{partie['slug']} : CA de {turnover} hors du SMT (négoce sous "
                            f"{int(rates['smt.seuil_negoce'])}, AUDCIF art. 13)")
    return problems


def declaration_problems(entries, questions, rates):
    """US-85 : une question « declaration » {period, field} attend le montant calculé par l'outil sur le livre officiel ;
    le crédit de TVA d'un mois est reporté sur le suivant (CGI art. 21 pour l'acompte, CAC compris)."""
    from decimal import Decimal

    from tools.simulation import ledger

    asked = [q for q in questions if q.get("declaration")]
    if not asked:
        return []
    computed, credit = {}, 0
    for month in range(1, 13):
        period = f"2026-{month:02d}"
        computed[period] = ledger.monthly_declaration(
            entries, 2026, month, minimum_rate=rates.get("is.taux_minimum_perception", Decimal(0)),
            cac_rate=rates.get("cac.taux", Decimal(0)), credit_reporte=credit)
        credit = computed[period]["credit_tva"]
    problems = []
    for question in asked:
        period, field = question["declaration"]["period"], question["declaration"]["field"]
        if field not in computed.get(period, computed["2026-01"]):
            problems.append(f"{question['id']} : case de déclaration inconnue « {field} »")
            continue
        expected = computed.get(period, {}).get(field)
        if Decimal(str(question["numeric"]["value"])) != expected:
            problems.append(f"{question['id']} : {question['numeric']['value']} au lieu de {expected} calculé sur le livre officiel")
    return problems


def reconciliation_problems(entries, questions):
    """US-86 : une question « rapprochement » {account, date[, releve]} attend le solde comptable à cette date, ou son
    écart avec le solde du relevé."""
    import datetime
    from decimal import Decimal

    from tools.simulation import ledger

    problems = []
    for question in questions:
        rule = question.get("rapprochement")
        if not rule:
            continue
        upto = datetime.date.fromisoformat(rule["date"])
        expected = ledger.reconciliation_gap(entries, rule["account"], upto, rule.get("releve", 0))
        if Decimal(str(question["numeric"]["value"])) != expected:
            problems.append(f"{question['id']} : {question['numeric']['value']} au lieu de {expected} calculé sur le livre officiel")
    return problems


REGIMES = ("reel", "igs", "igs_puis_reel")
PAYMENT_KINDS = ("recu_caisse", "recu_momo", "releve_bancaire", "releve_momo")
VAT_ACCOUNTS = ("443", "445", "4441", "4449")


def regime_problems(regime, entries, questions):
    """US-90 et US-91 (S13, S14) : un parcours à l'IGS tient le SMT (aucune question journal) et n'enregistre jamais de
    TVA ; B2 (igs_puis_reel) reste à l'IGS toute l'année 2026 et bascule au réel le 1er janvier 2027 seulement."""
    if regime not in REGIMES:
        return [f"régime « {regime} » inconnu (réel, igs ou igs_puis_reel ; le régime simplifié est supprimé)"]
    if regime == "reel":
        return []
    problems = [f"{q['id']} : question journal dans un parcours à l'IGS (SMT, S14)"
                for q in questions if q.get("type") == "journal"]
    for entry in entries:
        if entry["date"] < "2027-01-01":
            problems += [f"{entry['piece']} : compte de TVA {line['account']} chez un contribuable à l'IGS"
                         for line in entry["lines"] if line["account"].startswith(VAT_ACCOUNTS)]
        elif regime == "igs" or entry["date"] != "2027-01-01":
            problems.append(f"{entry['piece']} : écriture du {entry['date']} ; la bascule au réel se fait au "
                            f"1er janvier 2027 (bilan d'ouverture) et le parcours s'arrête là")
    return problems


# US-88 et US-92 : formules de référence qu'une question « calcul » peut invoquer (liste fermée).
REFERENCE_FORMULAS = ("amortissement_lineaire", "amortissement_degressif", "sortie_cmup", "sortie_peps",
                      "retenue_source", "tva_depuis_ht", "impot_societes", "igs_annuel",
                      "reintegration_amortissement", "reintegration_dons")


def _decimals(value):
    from decimal import Decimal

    if isinstance(value, list):
        return [_decimals(item) for item in value]
    if isinstance(value, bool):
        return value  # option d'une formule (adhésion à un Centre de Gestion Agréé), pas un montant
    return Decimal(str(value)) if isinstance(value, (int, float)) else value


def calculation_problems(questions):
    """Une question « calcul » {fonction, args, resultat} attend le résultat de la formule de referentiel.calculs ;
    `resultat` est le chemin (index ou clé) jusqu'au montant attendu."""
    from decimal import Decimal

    from referentiel import calculs

    problems = []
    for question in questions:
        rule = question.get("calcul")
        if not rule:
            continue
        if rule["fonction"] not in REFERENCE_FORMULAS:
            problems.append(f"{question['id']} : formule inconnue « {rule['fonction']} »")
            continue
        expected = getattr(calculs, rule["fonction"])(*_decimals(rule["args"]))
        for step in rule["resultat"]:
            expected = expected[step]
        if Decimal(str(question["numeric"]["value"])) != expected:
            problems.append(f"{question['id']} : {question['numeric']['value']} au lieu de {expected} "
                            f"calculé par {rule['fonction']}")
    return problems


def _rates(path):
    import csv
    from decimal import Decimal

    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as handle:
        rows = sorted(csv.DictReader(handle, delimiter=";"), key=lambda row: int(row["exercice"]))
    return {row["key"]: Decimal(row["value"]) for row in rows if int(row["exercice"]) <= 2026}


def _labels(path):
    import csv

    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as handle:
        return {row["code"]: {"fr": row.get("label_fr", ""), "en": row.get("label_en", "")}
                for row in csv.DictReader(handle, delimiter=";")}


def _codes(path, column):
    import csv

    if not path.exists():
        return set()
    with open(path, encoding="utf-8", newline="") as handle:
        return {row[column] for row in csv.DictReader(handle, delimiter=";")}


def scan_content(root):
    """Défauts de tout l'arbre content/ : « <chemin relatif> : <défaut> » ; liste vide si tout est conforme."""
    import json

    accounts = _codes(root / "referentiel" / "syscohada.csv", "code")
    params = _codes(root / "referentiel" / "parametres.csv", "key")
    web_sources = _codes(root / "referentiel" / "sources.csv", "key")
    rates = _rates(root / "referentiel" / "parametres.csv")
    labels = _labels(root / "referentiel" / "syscohada.csv")
    problems, seen_ids = [], set()
    # US-95 (S15, C28) : la CNPS relève du droit social, absent des sources ; ses montants sont donnés par les pièces.
    problems += [f"referentiel/parametres.csv : taux CNPS {key} interdit (montants CNPS sur le bulletin)"
                 for key in sorted(params) if key.startswith("cnps.")]

    def rel(path):
        return path.relative_to(root).as_posix()

    for manifest_path in sorted(root.glob("*/formation.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        base = manifest_path.parent
        problems += [f"{rel(manifest_path)} : {p}" for p in manifest_problems(manifest)]
        problems += [f"{rel(manifest_path)} : {p}" for p in turnover_problems(manifest, rates)]
        for partie in manifest.get("parties", []):
            for module in partie.get("modules", []):
                folder = base / module.get("dir", "")
                for section in module.get("sections", []):
                    for lang in ("fr", "en"):
                        path = folder / f"{section['file']}.{lang}.md"
                        if not path.exists():
                            continue
                        body = path.read_text(encoding="utf-8")
                        if section.get("kind", "content") == "content" and not cites_a_source(body):
                            problems.append(f"{rel(path)} : aucune source citée")
                        problems += [f"{rel(path)} : compte inconnu {c}" for c in unknown_accounts(body, accounts)]
                        problems += [f"{rel(path)} : paramètre inconnu {k}" for k in unknown_parameters(body, params)]
                        # US-97 : une source web citée figure au registre content/referentiel/sources.csv.
                        problems += [f"{rel(path)} : source inconnue {k}" for k in WEB_SOURCE_TAG.findall(body)
                                     if k not in web_sources]
                        problems += [f"{rel(path)} : livre nommé {b}" for b in book_mentions(body)]
                        if manifest.get("prefix") == "S":
                            problems += [f"{rel(path)} : {p}" for p in vocabulary_problems(body)]
                questions_path = folder / "questions.json"
                questions = json.loads(questions_path.read_text(encoding="utf-8")) if questions_path.exists() else []
                for question in questions:
                    # S19 : les sous-comptes déclarés par le parcours sont des comptes valides pour ses questions.
                    known = accounts | {code for code in partie.get("sous_comptes", {})
                                        if any(code.startswith(parent) and code != parent for parent in accounts)}
                    problems += question_problems(question, manifest.get("prefix", ""), known)
                    if question.get("id") in seen_ids:
                        problems.append(f"{question['id']} : identifiant en double")
                    seen_ids.add(question.get("id"))
                if questions_path.exists():
                    problems += [f"{rel(questions_path)} : livre nommé {b}"
                                 for b in book_mentions(questions_path.read_text(encoding="utf-8"))]
                problems += [f"{rel(folder)} : {shortfall}" for shortfall in volume_shortfalls(questions)]
                if manifest.get("prefix") == "S" and questions_path.exists():
                    problems += [f"{rel(questions_path)} : {p}"
                                 for p in vocabulary_problems(questions_path.read_text(encoding="utf-8"))]
            if manifest.get("prefix") == "S":
                partie_questions = []
                for module in partie.get("modules", []):
                    path = base / module.get("dir", "") / "questions.json"
                    if path.exists():
                        partie_questions += json.loads(path.read_text(encoding="utf-8"))
                problems += [f"{partie['slug']} : {p}"
                             for p in simulation_problems(base, partie, partie_questions, labels, rates)]
                problems += [f"{partie['slug']} : {p}" for p in company_file_problems(base, partie)]
                problems += [f"{partie['slug']} : {p}" for p in inventory_module_problems(base, partie)]
                problems += [f"{partie['slug']} : {p}" for p in narrative_problems(base, partie, root)]
    return problems


MONTH_SECTION = re.compile(r"^\d\d-(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|"
                           r"decembre)$")
SCENE_BEATS = {"fr": ("**La règle.**", "**Pourquoi ce choix et pas un autre.**", "**Ce que ça change.**",
                      "**Où ça se range.**", "**Revoir :**"),
               "en": ("**The rule.**", "**Why this choice and not another.**", "**What it changes.**",
                      "**Where it is filed.**", "**See again:**")}
UNTOLD_KINDS = ("balance", "fiche_stock", "demarche")  # balance d'ouverture ; fiches racontées au module Inventaire
COURSE_REFERENCE = re.compile(r"(Comptabilité|Fiscalité|Accounting|Taxation) M(\d+)")
FIGURE = re.compile(r"!\[[^\]]*\]\((/static/content/[\w/.-]+\.svg)\)")


def _module_counts(root):
    """Nombre de modules des formations Comptabilité et Fiscalité, pour contrôler les renvois « Revoir »."""
    import json

    counts = {}
    for slug, names in (("compta", ("Comptabilité", "Accounting")), ("fisca", ("Fiscalité", "Taxation"))):
        path = root / slug / "formation.json"
        if path.exists():
            total = sum(len(p.get("modules", [])) for p in json.loads(path.read_text(encoding="utf-8")).get("parties", []))
            counts.update({name: total for name in names})
    return counts


def narrative_problems(base, partie, root):
    """S34 : dans une section mensuelle d'un parcours, toute pièce comptable affichée l'est dans une scène (titre ###)
    aux cinq temps, en FR et en EN ; « Revoir » désigne un module existant ; S33 : toute figure citée existe."""
    import json

    kinds = {}
    if partie.get("pieces") and (base / partie["pieces"]).exists():
        kinds = {p["ref"]: p["kind"] for p in json.loads((base / partie["pieces"]).read_text(encoding="utf-8"))}
    modules = _module_counts(root)
    problems = []
    for module in partie.get("modules", []):
        for section in module.get("sections", []):
            for lang in ("fr", "en"):
                path = base / module.get("dir", "") / f"{section['file']}.{lang}.md"
                if not path.exists():
                    continue
                body = path.read_text(encoding="utf-8").replace(" ", " ")
                for src in FIGURE.findall(body):
                    if not (root.parent / src.lstrip("/")).exists():
                        problems.append(f"{section['file']}.{lang} : figure {src} absente de static/")
                for name, number in COURSE_REFERENCE.findall(body):
                    if name in modules and not 1 <= int(number) <= modules[name]:
                        problems.append(f"{section['file']}.{lang} : Revoir {name} M{number}, module inexistant")
                if not MONTH_SECTION.match(section["file"]):
                    continue
                scenes = body.split("\n### ")
                for ref in PIECE_REFS.findall(body):
                    if kinds.get(ref) in UNTOLD_KINDS:
                        continue
                    scene = next((s for s in scenes[1:] if f"[[piece:{ref}]]" in s), None)
                    if scene is None:
                        problems.append(f"{section['file']}.{lang} : pièce {ref} sans scène (S34)")
                        continue
                    problems += [f"{section['file']}.{lang} : pièce {ref}, scène sans « {beat.strip('*: .')} »"
                                 for beat in SCENE_BEATS[lang] if beat not in scene]
    return problems


def inventory_module_problems(base, partie):
    """US-88 : dès qu'il est rédigé, le module Inventaire (6e) d'un parcours au réel propose les calculateurs non
    notés [[calc:stock]] et [[calc:amortissement]]."""
    if partie.get("regime", "reel") != "reel":
        return []
    module = next((m for m in partie.get("modules", []) if m.get("order") == 6), None)
    if not module or not module.get("sections"):
        return []
    bodies = "\n".join((base / module.get("dir", "") / f"{section['file']}.fr.md").read_text(encoding="utf-8")
                       for section in module["sections"]
                       if (base / module.get("dir", "") / f"{section['file']}.fr.md").exists())
    return [f"module Inventaire sans [[calc:{name}]]" for name in ("stock", "amortissement")
            if f"[[calc:{name}]]" not in bodies]


def company_file_problems(base, partie):
    """US-81 : la première section du parcours (dossier d'entreprise) affiche ses taux par [[param:]] et son plan de
    comptes par [[syscohada:]], en FR comme en EN."""
    modules = sorted(partie.get("modules", []), key=lambda module: module.get("order", 0))
    sections = sorted(modules[0].get("sections", []), key=lambda section: section.get("order", 0)) if modules else []
    if not sections:
        return ["dossier d'entreprise absent (première section du premier module)"]
    problems = []
    for lang in ("fr", "en"):
        path = base / modules[0].get("dir", "") / f"{sections[0]['file']}.{lang}.md"
        body = path.read_text(encoding="utf-8") if path.exists() else ""
        if not PARAM_TAG.search(body):
            problems.append(f"dossier d'entreprise {lang.upper()} sans taux [[param:]]")
        if not ACCOUNT_TAG.search(body):
            problems.append(f"dossier d'entreprise {lang.upper()} sans plan de comptes [[syscohada:]]")
        if partie["slug"] == "a" and "Ngono Mode SARL" not in body:
            # US-81 (S17) : profil validé du parcours A.
            problems.append(f"dossier d'entreprise {lang.upper()} du parcours A sans « Ngono Mode SARL »")
        if partie.get("regime", "reel") != "reel":
            # US-90 : un parcours à l'IGS cite son régime et le précompte de 5 % qu'il subit.
            if "[[param:precompte.taux_igs]]" not in body:
                problems.append(f"dossier d'entreprise {lang.upper()} à l'IGS sans [[param:precompte.taux_igs]]")
            if "[[cgi:art. 93 quater]]" not in body:
                problems.append(f"dossier d'entreprise {lang.upper()} à l'IGS sans [[cgi:art. 93 quater]]")
    return problems
