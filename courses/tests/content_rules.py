"""Règles du contenu (US-71 à US-73, C2, C15, C21), partagées par les tests témoins et test_content_files.py."""
import re

SOURCE_TAG = re.compile(r"\[\[(?:cgi|syscohada|guide):[^\]]+\]\]")
ACCOUNT_TAG = re.compile(r"\[\[syscohada:(\d+)\]\]")
PARAM_TAG = re.compile(r"\[\[param:([a-z0-9_.]+)\]\]")
# Les livres qui servent de trame ne sont jamais nommés (C21) : mots entiers, et tout ISBN.
BOOK = re.compile(r"\b(DCG|Dunod|Disle|Bouvier|Plagnet)\b|ISBN[\s:]*[\d-]+")
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
    problems, seen_ids = [], set()

    def rel(path):
        return path.relative_to(root).as_posix()

    for manifest_path in sorted(root.glob("*/formation.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        base = manifest_path.parent
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
                        problems += [f"{rel(path)} : livre nommé {b}" for b in book_mentions(body)]
                questions_path = folder / "questions.json"
                questions = json.loads(questions_path.read_text(encoding="utf-8")) if questions_path.exists() else []
                for question in questions:
                    problems += question_problems(question, manifest.get("prefix", ""), accounts)
                    if question.get("id") in seen_ids:
                        problems.append(f"{question['id']} : identifiant en double")
                    seen_ids.add(question.get("id"))
                if questions_path.exists():
                    problems += [f"{rel(questions_path)} : livre nommé {b}"
                                 for b in book_mentions(questions_path.read_text(encoding="utf-8"))]
                problems += [f"{rel(folder)} : {shortfall}" for shortfall in volume_shortfalls(questions)]
    return problems
