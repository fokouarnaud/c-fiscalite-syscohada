---
name: deploy
description: Livre ComptaFisca Acad Ventisax en production sur PythonAnywhere - contrôles locaux, commits sur `develop`, fusion dans `main`, `deploy.sh` lancé dans une console Bash du navigateur (Playwright MCP), fumée en production, disque mesuré, AGENTS.md et CLAUDE.md mis à jour. À utiliser quand l'utilisateur dit « commit et deploy », « déploie », « mets en ligne », « livre », ou après une livraison (partie, schémas, correctif) prête à partir.
---

# Déployer ComptaFisca Acad Ventisax

Production : https://comptafiscaventisax.pythonanywhere.com/ (compte gratuit `comptafiscaventisax`), code dans `~/comptafiscaventisax`, environnement virtuel `~/.virtualenvs/comptafisca`, branche suivie : `main`.
Règles du projet : AGENTS.md (source de vérité), section P5 « DoD-Déploiement ».

## Règles qui ne se négocient pas
- **Aucun secret** : aucun identifiant PythonAnywhere n'est stocké ni saisi par Claude. L'utilisateur se connecte lui-même dans la fenêtre Playwright ; aucun jeton d'API.
- **Rien ne part en rouge** : pytest, `node --test` et `makemigrations --check` verts avant tout commit.
- **`develop` puis `main`** : on commite sur `develop`, `main` avance seulement en avance rapide (`--ff-only`). Jamais de `--force`.
- **Comptes de test temporaires** : créés dans `manage.py shell`, avec un mot de passe jetable généré pour l'occasion (jamais un mot de passe réel), puis supprimés avec leurs données, `history -c` dans la console et fichier local du mot de passe effacé.
- **Production intacte** : aucune donnée d'apprenant lue, modifiée ou affichée pendant la fumée.

- **Quota de CPU** (plan gratuit, 100 s par jour) : un déploiement avec fumée lance quatre processus Python sur le serveur (`deploy.sh`, mesure du disque, création puis suppression du compte de test) et consomme à lui seul une large part du quota. Au-delà, PythonAnywhere ouvre sa page « tarpit » et bride le compte jusqu'à la remise à zéro (le site reste servi, la console devient très lente). Regrouper les livraisons : plusieurs figures ou correctifs commités sur `develop`, puis un seul déploiement et une seule fumée par jour ; vérifier le compteur « CPU Usage » en haut de la page des consoles avant de lancer. Quota épuisé : ne lancer que la suppression d'un compte de test déjà créé, et remettre le reste au lendemain.

## Étapes

### 1. Contrôles locaux (poste Windows)
```bash
.venv/Scripts/python -m pytest -o addopts="" -q | tail -1      # « N passed », aucun failed ni skipped injustifié
node --test "tools/figures/**/*.test.mjs"                        # si des figures ont changé
.venv/Scripts/python manage.py makemigrations --check --dry-run  # « No changes detected »
diff <(tail -n +7 AGENTS.md) <(tail -n +8 CLAUDE.md)             # vide
```
Fichiers écrits par Python sous Windows : vérifier les fins de ligne (`Path.write_text` sans `newline="\n"` écrit du CRLF) et les remettre en LF.

### 2. Commits sur `develop`
Découpage des commits : `feat(<portée>)` (code et tests, ou code + contenu pour des schémas), `feat(content)`, `style(ui)` après un audit, `docs`. Message en anglais, corps en puces, terminé par la ligne `Co-Authored-By` demandée par le système. Ajouter les fichiers par nom (jamais `git add -A` : `.playwright-mcp/` et `.env` restent hors du dépôt).

### 3. Fusion et envoi
```bash
git fetch -q origin
git checkout -q main && git merge --ff-only -q origin/main && git merge --ff-only develop
git push origin main develop
git checkout -q develop
```
Si `--ff-only` refuse, s'arrêter et le dire : `main` a divergé.

### 4. Console PythonAnywhere (Playwright MCP)
1. `browser_navigate` vers `https://www.pythonanywhere.com/user/comptafiscaventisax/consoles/`. Si la page de connexion s'affiche, demander à l'utilisateur (AskUserQuestion) de se connecter dans la fenêtre Playwright, puis recharger.
2. Le plan gratuit limite à **2 consoles** : réutiliser une console Bash listée sous « Your consoles » (`/consoles/<id>/`) au lieu d'en ouvrir une.
3. Le terminal est dans l'iframe `…/consoles/<id>/frame/`. Passer la fenêtre à **1280 px** (`page.setViewportSize`) : à 360 px, l'iframe n'est pas cliquable. Cliquer au centre du cadre (`const b = await page.locator("iframe").first().boundingBox(); await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2)` ; un clic sur le `body` de l'iframe échoue, « element is not visible »), puis taper avec `page.keyboard.type(…, { delay: 5 })`.
4. Lancer, en journalisant :
   ```bash
   clear; cd ~/comptafiscaventisax; bash deploy.sh > ~/deploy.log 2>&1; echo EXIT=$? >> ~/deploy.log; tail -n 30 ~/deploy.log; git log --oneline -1; du -sh ~ 2>/dev/null | tail -1
   ```
   Attendre (30 à 90 s), puis lire l'écran par une capture (`browser_take_screenshot`) : le terminal est dessiné, son texte n'est pas toujours dans le DOM.
   Sur une console tout juste chargée, les premières lettres tapées se perdent : attendre 500 ms après le clic et commencer la commande par une espace (` clear; …`), qui la garde aussi hors de l'historique. Après plusieurs déploiements dans la journée, le quota de CPU du plan gratuit ralentit tout : `manage.py shell` met 30 à 100 s, `deploy.sh` jusqu'à 5 min. Un écran vide avec le curseur en haut à gauche veut dire « encore en cours » : reprendre une capture plus tard plutôt que relancer. Un appel Playwright qui attend plus de 120 s passe en arrière-plan ; attendre sa notification avant de lire la capture.
5. Attendus : `EXIT=0`, « Déploiement terminé. », le commit de `main` attendu, les compteurs des imports (comptes SYSCOHADA, paramètres fiscaux, puis sections et questions de `compta` et `fisca`, à comparer au contenu livré), disque < 150 Mo.
6. **`deploy.sh` modifié par ce déploiement** : il s'est exécuté dans son ancienne version (il se met à jour par `git pull`) ; le relancer une seconde fois.
7. **Environnement virtuel, dépendances ou `.env` modifiés** : toucher le fichier WSGI ne suffit pas ; bouton « Reload » de l'onglet Web. Constaté le 2026-10-29 : après la saisie des identifiants Gmail, le site envoyait encore sans authentification (`530 Authentication Required` dans `/var/log/comptafiscaventisax.pythonanywhere.com.error.log`) malgré le `touch` de `deploy.sh`, alors qu'un envoi depuis la console réussissait ; le « Reload » a réglé le problème.

### 5. Fumée en production
- Publique, sans compte : `/fr/` et `/en/` (200), fiche du catalogue, `/fr/verify/00000000-0000-0000-0000-000000000000/` en 404, `http://` redirigé en 301 vers `https://`, fichiers statiques nouveaux servis (200).
- Contenu derrière connexion (section, figure) : compte de test temporaire. Générer en local un mot de passe jetable (`python -c "import secrets;print('Fx-'+secrets.token_urlsafe(18))"`), puis, dans la console (les identifiants publics diffèrent d'une base à l'autre : retrouver la section par son titre) :
  ```bash
  clear; ~/.virtualenvs/comptafisca/bin/python manage.py shell -c "from django.contrib.auth import get_user_model as G; from courses.models import Formation, Section; from catalog.models import Enrollment; u=G().objects.create(username='fumee_x', is_active=True, email_verified=True); u.set_password('<jetable>'); u.save(); Enrollment.objects.create(user=u, formation=Formation.objects.get(slug='compta'), source='admin'); print('SECTION', Section.objects.get(module__partie__formation__slug='compta', title_fr='<titre>').public_id)"; history -c
  ```
  Se connecter dans un **contexte de navigateur séparé** (`page.context().browser().newContext({ viewport: { width: 360, height: 800 } })`), pour garder la session PythonAnywhere de la page principale. Le contexte Playwright n'a pas `require` : passer le mot de passe dans le code.
  Pour un quiz ou un examen, faire la fumée par les services dans `manage.py shell` (`start_attempt`, `save_answer`, `submit_attempt`), comme au critère 45.
  Toujours terminer par `G().objects.filter(username='fumee_x').delete()` (résultat `LEFT 0`), `history -c`, et l'effacement du fichier local du mot de passe.
- Navigateur : FR et EN, 360 px, statut 200, aucune erreur console, aucun débordement (`scrollWidth > clientWidth`) ; pour une figure, relevé aux repères, Lecture puis Pause.

### 6. Consigner
- AGENTS.md : écart d'implémentation « Déploiement de … (date) » : commit de `main`, code de sortie, migrations, compteurs, questions publiées, `check`, disque, fumée, restes mineurs. Puis CLAUDE.md = ses 4 lignes d'en-tête + AGENTS.md à partir de la ligne 4 ; `diff` vide.
- Commit `docs: record the deployment of …` sur `develop`, avance rapide de `main`, push. Ce commit de documentation n'appelle pas de nouveau `deploy.sh` (aucun code servi ne change), sauf demande.
- Rappel à l'utilisateur si la date approche : le plan gratuit désactive le site un mois après le dernier clic « Run until 1 month from today » (onglet Web).

## Rapport final
Commit déployé, code de sortie, compteurs, disque, ce que la fumée a vérifié (et comment), ce qui ne l'a pas été, comptes de test supprimés.
