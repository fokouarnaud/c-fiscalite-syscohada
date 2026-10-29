# AGENTS.md — ComptaFisca Acad Ventisax

> Source de vérité du projet. `CLAUDE.md` en est le miroir : toute modification se fait ici d'abord.
> Décisions issues du grill du 2026-10-28 (C1 à C22). La grille complète et les incertitudes d'architecture seront ajoutées après validation de la section GOALS.

## GOALS

Plateforme e-learning bilingue (FR/EN) qui reproduit **toutes les fonctionnalités** d'Electro Acad Ventisax (https://electroacadventisax.pythonanywhere.com/, source `..\electroschool2ventisax`). Le contenu électronique y est remplacé par deux formations :

- **Comptabilité**, adaptée au SYSCOHADA révisé (Cameroun) ;
- **Fiscalité**, adaptée au Code général des impôts du Cameroun, édition 2026.

Le site est déployé sur le compte gratuit PythonAnywhere `comptafiscaventisax`.

### 1. Objectifs fonctionnels prioritaires

**1.1 Plateforme clonée d'electroschool (parité fonctionnelle)** — C1, C8, C17
- Un seul projet Django, une seule base SQLite, un seul login, un catalogue de 2 formations. Le code d'electroschool2ventisax est copié sans son historique git, et le contenu électronique est retiré.
- Toutes les fonctionnalités d'electroschool sont conservées :
  - **Comptes et accès** : comptes (learner / trainer / admin), inscription vérifiée par e-mail, verrouillage anti force brute, réinitialisation du mot de passe, promotions et codes d'accès, import CSV d'apprenants.
  - **Parcours apprenant** : catalogue, programme par partie, inscription gratuite en un clic, lecteur avec sommaire et reprise, progression calculée et parcours guidé.
  - **Évaluation** :
    - quiz de module illimités et corrigés ;
    - examen de partie : 70 %, 3 tentatives, 60 min chronométrées côté serveur, 10 questions tirées par module, sauvegarde HTMX, envoi automatique ;
    - badges ;
    - certificat PDF par partie réussie, avec vérification publique `/verify/<uuid>/`.
  - **Espace formateur** : carnet de notes, détail des tentatives, statistiques par question, export CSV, annonces, échéances.
  - **Exploitation** : back-office Unfold, i18n FR/EN (`/fr/`, `/en/`), import idempotent du contenu, `publish_reviewed`, sauvegarde quotidienne, sécurité et CSP, `deploy.sh`.
- Identité : **« ComptaFisca Acad Ventisax »**, slogan « Comptabilité SYSCOHADA et fiscalité camerounaise, formation et évaluation ». Charte Ventisax inchangée (navy #0b2d46, teal, Lexend, logo V) et lien vers ventisax.pythonanywhere.com. Icônes Tabler : registre pour la compta, reçu pour la fisca. (C16)

**1.2 Formation Comptabilité SYSCOHADA (priorité 1)** — C7, C9, C18
- Trame : les 30 chapitres du DCG 9, réécrits en SYSCOHADA révisé (comptes OHADA, FCFA, TVA 19,25 %, paie CNPS/IRPP, états financiers SYSCOHADA), plus un chapitre d'introduction OHADA/AUDCIF. Le ch. 18 (Emballages) est fusionné dans les achats et ventes.
- 1 chapitre = 1 module. Les sections sont un rappel de cours et des cas corrigés.
- 5 parties, chacune avec son examen et son certificat :
  1. Fondamentaux
  2. Opérations courantes
  3. Investissement & financement
  4. Travaux d'inventaire
  5. Clôture & états financiers
- Autorité : le Guide d'application du SYSCOHADA (OHADA) et le plan comptable SYSCOHADA révisé.

**1.3 Formation Fiscalité CGI Cameroun (priorité 2, après la compta complète)** — C6, C9, C18
- Plan calqué sur le CGI 2026, en 7 blocs regroupés en 3 parties :
  1. Impôts sur les revenus : système & régimes, IS, IRPP
  2. Taxes sur la dépense & droits : TVA & accises, enregistrement & timbre, fiscalité locale
  3. Procédures fiscales
- Le Plagnet ne sert que de modèle de style. Autorité : CGI Cameroun éd. 2026 (FR ; EN pour la terminologie).
- Recommandée après les Parties 1 et 2 de la compta, sans blocage technique (C17).

**1.4 Socle métier ajouté à la plateforme**
- **Type de question `journal`** (C10) : l'apprenant remplit un mini-journal (compte / libellé / débit / crédit). La correction se fait ligne à ligne, sans ordre imposé. Le compte est jugé au niveau de précision défini par la question, et le montant en FCFA doit être exact. Le score est partiel. Ce type est utilisé en quiz ET en examen, en JS vanilla compatible avec la CSP.
- **Réponses numériques** (C11) :
  - unités FCFA, %, jours/mois/années (les unités électriques et les préfixes SI sont retirés) ;
  - parseur FR qui accepte « 1 250 000 », « 1.250.000 » et « 19,25 » ;
  - `tolerance_abs` à 1 FCFA par défaut, la tolérance relative en % restant optionnelle ;
  - arrondis CGI expliqués dans la correction.
- **Table de paramètres fiscaux** éditable dans l'admin (C3, C14) :
  - taux et seuils de la LF 2026 (TVA, IS, IRPP, CNPS…) ;
  - balises `[[param:clé]]` rendues dynamiquement dans les leçons et les calculateurs ;
  - questions et cas autonomes, datés « exercice 2026 », avec les taux donnés dans l'énoncé ;
  - chaque question est étiquetée avec les `params` qu'elle utilise, pour lister celles à revoir quand un taux change.
- **Citations obligatoires et vérifiables** (C2, C15) :
  - balises `[[cgi:art. N]]`, `[[syscohada:compte]]` et `[[guide:ch.N]]`, rendues en badges ;
  - modèle `SyscohadaAccount` (1 330 comptes importés du plan) ;
  - un test de contenu **bloquant** fait échouer le déploiement si une section ne cite aucune source ou si un compte cité n'existe pas.
- **6 calculateurs `[[calc:]]` non notés** (C12), qui lisent la table de paramètres :
  - `tva`
  - `amortissement`
  - `paie` : CNPS, IRPP, CAC, CCF/CFC, RAV, TDL
  - `is` : avec minimum de perception
  - `reduction`
  - `stock` : CMUP/PEPS

  Les formules de référence sont testées en Python.
- **Schémas SVG générés en Python** (C13) : `tools/schemas/compta.py` produit, en FR et en EN, le compte en T, le bilan SYSCOHADA, le circuit de la TVA, la frise d'amortissement et le cycle déclaratif. Le reste est présenté en tableaux Markdown.

**1.5 Contenu bilingue et publication** — C2, C4, C5, C21
- FR et EN dès la v1, interface et contenu. **Le FR fait foi.** L'EN est traduit en s'alignant sur le CGI-EN 2026 et sur la terminologie OHADA. Si l'EN manque, la page s'affiche en FR avec un bandeau.
- Rédaction **originale** : le DCG 9 et le Plagnet ne servent que de trame. Les entreprises camerounaises sont fictives, les montants en FCFA et les données nouvelles. Seuls les textes officiels sont cités (CGI, AUDCIF, Guide SYSCOHADA), et jamais les livres.
- Publication directe au déploiement, sans workflow de relecture : les questions sont importées avec `reviewed {fr,en} = true`, puis `publish_reviewed`. Les corrections viendront ensuite.

**1.6 Séquence de livraison** — C18, C19
1. **Lot 0** : socle et rebranding, avec le pilote **Compta M1**, déployé en production pour valider `journal`, les citations, les paramètres et l'empreinte disque.
2. **Comptabilité, une partie à la fois** (P1 → P5). Chaque déploiement concerne une partie complète, et son examen et son certificat ouvrent à ce moment-là.
3. **Fiscalité** (P1 → P3). Elle reste **masquée du catalogue** jusqu'à ce qu'elle soit complète.
- Volume cible : environ 40 modules, au moins 12 questions d'examen et 8 questions de quiz par module, soit environ 800 questions et 300 sections bilingues.

### 2. Contraintes techniques

- **Hébergement** :
  - PythonAnywhere gratuit, compte `comptafiscaventisax`, une seule web app ;
  - **quota disque de 512 Mo** (cible < 150 Mo, venv compris) ;
  - environ 100 s de CPU par jour, pas de tâche planifiée (les tâches périodiques sont déclenchées par un middleware) ;
  - le site doit être prolongé manuellement chaque mois.
- **Stack** (héritée, à ne pas enrichir sans décision) :
  - Django 5.2 en rendu serveur et **SQLite** ;
  - 5 dépendances de production : Django, django-modeltranslation, Markdown, bleach, django-unfold ;
  - HTMX vendoré, JS vanilla, CSS écrit à la main, aucun CDN.
- **Sécurité** :
  - CSP stricte, sans script en ligne ;
  - URL en UUID `public_id` ;
  - cookies `__Host-`, HSTS ;
  - Markdown nettoyé par bleach, et balises `[[…]]` substituées **après** le nettoyage ;
  - `check --deploy` vert.
- **Référentiel juridique figé** : CGI Cameroun éd. 2026 (LF 2026) et SYSCOHADA révisé (AUDCIF). La date de référence est affichée sur les leçons de fiscalité.
- **Contenu versionné** dans `content/<slug>/` : `formation.json`, sections `.fr.md` et `.en.md`, `questions.json`. Import idempotent par `import_content`. Les `external_id` sont préfixés `C-` (compta) ou `F-` (fisca).
- **Sources** : `reference/` (97 Mo, livres protégés) est **gitignoré et n'est jamais déployé**. Seul le contenu dérivé et réécrit part en production.
- **Déploiement** :
  - dépôt GitHub `fokouarnaud/c-fiscalite-syscohada` (public), code dans `~/comptafiscaventisax` ;
  - `deploy.sh` enchaîne pull, pip, migrate, import_content, publish_reviewed, collectstatic, check --deploy et touch du WSGI ;
  - branches `develop` → `main`.
- **E-mail** : Gmail SMTP, même boîte expéditrice qu'electroschool. Le mot de passe d'application **dédié** est saisi par l'utilisateur dans le `.env` du serveur, et l'agent ne le manipule jamais.
- **Qualité** : pytest-django vert. Les tests plateforme hérités sont conservés (intrusion, examen, carnet de notes). Les tests propres à l'électronique sont réécrits. Nouveaux tests : scoring FCFA, `journal`, paramètres, citations, calculateurs.

### 3. Périmètre strictement hors scope (v1)

- Paiement, abonnement, mobile money, contenus payants.
- Vidéo, cours en PDF téléchargeables, simulateurs ou figures isométriques interactives. Le pipeline Node des figures et `[[fig:]]` sont supprimés.
- Comptes consolidés et combinés (partie 4 du Guide SYSCOHADA).
- Fiscalités spécifiques non retenues dans le plan, et équivalents de notions françaises sans pendant camerounais : CET, intégration fiscale, ISF.
- Workflow de relecture ou validation éditoriale dans l'application (statuts brouillon → relu → publié côté contenu).
- Recalcul dynamique des réponses de questions selon les taux courants.
- Reprise mot pour mot de textes, cas ou corrigés du DCG 9 ou du Plagnet, et toute citation de ces livres sur le site.
- Fonctionnalités de finaia.co et lefisk.cm (calendrier fiscal, recherche dans le CGI, simulateurs tiers). Ces sites ne servent que d'inspiration ou de contrôle croisé des taux.
- Prérequis bloquant entre formations, et certificat de formation entière (le certificat est délivré par partie uniquement).
- Historique git d'electroschool, et grilles de décisions E, M et F d'electroschool.
- Toute autre formation que Comptabilité et Fiscalité, et une 2e web app ou une autre base que SQLite.

---

## PRD — Product Requirements Document

> Dérivé des GOALS validés. Les identifiants `US-xx` sont stables : un commit ou un test cite l'US qu'il sert. Les US marquées **[H]** sont héritées d'electroschool : on vérifie leur parité, on ne les réécrit pas. Les US marquées **[N]** sont nouvelles ou modifiées.

### P1. Personas

| Persona | Rôle technique | Besoin principal |
|---|---|---|
| **Aïcha, apprenante autonome** | `learner`, groupe ouvert | Se former seule et gratuitement, sur mobile (390 px) avec une connexion instable, et obtenir un certificat vérifiable. |
| **Paul, apprenant en promotion** | `learner` + code de promotion | Suivre le rythme de son centre, voir les annonces et les échéances. |
| **Mme Ngo, formatrice** | `trainer` (staff limité) | Suivre ses promotions, repérer les décrocheurs et les questions mal réussies, exporter les notes. |
| **Administrateur Ventisax** | `admin` / superuser | Publier le contenu, mettre à jour les taux à chaque loi de finances, gérer comptes et promotions. |
| **Recruteur / tiers** | anonyme | Vérifier l'authenticité d'un certificat. |
| **Agent de rédaction (Claude)** | hors application | Produire le contenu FR/EN conforme : sources citées, comptes valides, taux paramétrés. |

### P2. User stories et critères d'acceptation

Format : *En tant que … je veux … afin de …*, suivi des critères d'acceptation (CA) testables.

#### E1 — Comptes et accès [H]
- **US-01 [H] Inscription vérifiée.** En tant que visiteur, je crée un compte (prénom, nom, identifiant, e-mail, mot de passe) afin d'accéder aux formations.
  - CA : le compte est inactif tant que le lien e-mail (usage unique) n'a pas été cliqué ;
  - CA : le champ piège `website` rempli entraîne un rejet silencieux ;
  - CA : au-delà de 5 inscriptions par heure et par IP hachée, réponse 429 ;
  - CA : les comptes non vérifiés sont purgés à J+7.
- **US-02 [H] Connexion protégée.** Je me connecte par identifiant et mot de passe.
  - CA : après 5 échecs en 15 min, l'identifiant est verrouillé (y compris sur `/admin/`) ;
  - CA : aucun message ne révèle si le compte existe ;
  - CA : la déconnexion se fait en POST uniquement.
- **US-03 [H] Mot de passe oublié.**
  - CA : le lien est envoyé par e-mail et valable 24 h ;
  - CA : si le compte n'a pas d'e-mail, un message renvoie vers le formateur.
- **US-04 [H] Rôles.**
  - CA : `trainer` et `admin` deviennent staff automatiquement, avec synchronisation des groupes ;
  - CA : le formateur n'a de permissions admin que sur Question, Choice, MatchPair et `JournalLine` [N].
- **US-05 [H] Langue.** Je bascule entre FR et EN depuis toute page.
  - CA : préfixes `/fr/` et `/en/`, préférence conservée ;
  - CA : les slugs d'URL restent identiques dans les deux langues.

#### E2 — Catalogue et inscription aux formations [H+N]
- **US-10 [H] Catalogue.** En tant que visiteur, je vois les formations listées : titre, résumé, nombre de modules, heures, « Certificat par partie ».
- **US-11 [H] Programme.** Je consulte le programme d'une formation par partie : modules numérotés, heures, mention de l'examen, prérequis indicatifs, langues.
- **US-12 [H] Inscription en un clic** à une formation ouverte (POST).
  - CA : un `Enrollment` unique (user, formation), `source=catalog`.
- **US-13 [H] Code de promotion.** Je saisis un code de 8 caractères pour rejoindre une promotion.
  - CA : je passe du groupe ouvert à la promotion ;
  - CA : un code inactif ou inconnu donne un message neutre.
- **US-14 [N] Formation masquée.** En tant qu'admin, je masque une formation incomplète (la Fiscalité pendant la production de la compta).
  - CA : une formation `is_listed=False` est absente du catalogue ;
  - CA : son URL de programme renvoie 404 aux non-staff ;
  - CA : on ne peut pas s'y inscrire.
- **US-15 [N] Prérequis indicatif.** Le programme de Fiscalité affiche « Recommandé après les Parties 1 et 2 de Comptabilité », sans aucun blocage.

#### E3 — Lecture du cours [H+N]
- **US-20 [H] Tableau de bord apprenant.** Il affiche une formation à la fois, une carte « Reprendre », le plan complet, la progression en % des étapes, les annonces et les échéances (marqueur « en retard »).
- **US-21 [H] Lecteur de section.**
  - CA : sommaire latéral, fil d'Ariane Formation › Partie › Module, pagination, annexes ;
  - CA : la section est marquée vue à l'ouverture ;
  - CA : un non-inscrit est renvoyé vers le programme, ou reçoit une 404 si la formation est fermée.
- **US-22 [H] Parcours guidé.** L'application propose toujours l'étape suivante : section, quiz, module suivant ou examen.
- **US-23 [N] Citations visibles.** Chaque section affiche ses sources sous forme de badges.
  - CA : `[[cgi:art. N]]` donne le badge « CGI 2026, art. N » ;
  - CA : `[[syscohada:4452]]` donne le badge du compte et de son libellé (lu dans `SyscohadaAccount`, dans la langue courante) ;
  - CA : `[[guide:ch.N]]` donne le badge du Guide SYSCOHADA ;
  - CA : une infobulle est accessible au clavier.
- **US-24 [N] Taux à jour.** Dans le texte, `[[param:clé]]` affiche la valeur courante de la table `FiscalParameter`, formatée selon la langue (19,25 % / 19.25%).
  - CA : une clé inconnue fait échouer l'import et les tests, et n'est jamais affichée brute en production.
- **US-25 [N] Date de référence.** Chaque leçon de fiscalité affiche « Référence : CGI Cameroun, éd. 2026 ».
- **US-26 [N] Calculateurs.** Dans une leçon, j'utilise un calculateur non noté (`tva`, `amortissement`, `paie`, `is`, `reduction`, `stock`).
  - CA : les taux sont injectés depuis `FiscalParameter` via `json_script` ;
  - CA : la saisie FR des montants est acceptée ;
  - CA : les résultats sont identiques aux vecteurs de référence Python ;
  - CA : aucun script en ligne.
- **US-27 [N] Schémas.** Les schémas (compte en T, bilan, circuit TVA, frise d'amortissement, cycle déclaratif) s'affichent en SVG dans la langue courante, avec zoom au toucher.
- **US-28 [N] Bandeau de traduction.** Si une section n'a pas de version EN, elle s'affiche en FR avec un bandeau « Traduction en cours ».

#### E4 — Évaluation [H+N]
- **US-30 [H] Quiz de module.**
  - CA : tentatives illimitées, questions `usage=quiz` publiées ;
  - CA : correction et explication affichées, filtre « seulement les erreurs ».
- **US-31 [H] Examen de partie.**
  - CA : il se débloque quand tous les modules de la partie sont terminés ;
  - CA : seuil 70 %, 3 tentatives, 60 min chronométrées côté serveur, 10 questions tirées par module, ordre mélangé ;
  - CA : sauvegarde à chaque clic (HTMX ; 409 si la tentative est close), reprise après coupure, envoi automatique à l'échéance ;
  - CA : la meilleure note est retenue ;
  - CA : seul le score par module est affiché, sans correction.
- **US-32 [H] Envoi avec questions vides.** L'application liste les questions vides et demande confirmation.
- **US-33 [H] Types existants** : choix unique, choix multiple (score (bonnes − mauvaises) / bonnes, plancher 0), vrai/faux, appariement (listes déroulantes sur écran tactile), zone cliquable.
- **US-34 [N] Question `journal`.** Je saisis une écriture : lignes compte / libellé / débit / crédit, ajout et suppression de lignes.
  - CA : correction ligne à ligne, sans ordre imposé ;
  - CA : le compte est comparé au niveau `account_match` de la ligne attendue (classe, 2, 3 ou 4 chiffres, ou exact) ;
  - CA : sens et montant FCFA exacts ;
  - CA : score = lignes justes / lignes attendues, moins une pénalité par ligne en trop, plancher 0 ;
  - CA : le libellé n'est pas noté ;
  - CA : utilisable en quiz et en examen ;
  - CA : utilisable au clavier et à 390 px.
- **US-35 [N] Réponse numérique FCFA/%.**
  - CA : sont acceptés « 1 250 000 », « 1250000 », « 1.250.000 », « 1 250 000 FCFA », « 19,25 », « 19,25 % » ;
  - CA : juste si |écart| ≤ `tolerance_abs` (1 par défaut) ou, si défini, ≤ `tolerance_pct` ;
  - CA : une unité incohérente est fausse ;
  - CA : l'explication détaille l'arrondi CGI appliqué.
- **US-36 [N] Exercices datés.** L'énoncé de toute question chiffrée mentionne « exercice 2026 » et les taux utiles. La réponse reste juste même si la table de taux change.

#### E5 — Certification et gamification [H]
- **US-40 [H] Badges** par module terminé et par partie réussie.
- **US-41 [H] Certificat.**
  - CA : délivré par partie réussie, nom complet exigé avant émission puis figé ;
  - CA : le score peut monter, jamais baisser ;
  - CA : le PDF A4 paysage est généré à la demande et jamais stocké.
- **US-42 [H] Vérification publique.** `/verify/<uuid>/` affiche titulaire, partie, score et date.
  - CA : un UUID inconnu donne 404.
- **US-43 [H] Accès au PDF.** Seuls le titulaire, l'admin et un formateur de sa promotion peuvent télécharger le PDF.

#### E6 — Espace formateur [H]
- **US-50 [H] Carnet de notes.** Tableau apprenants × modules et examens, limité aux promotions du formateur.
- **US-51 [H] Détail d'une tentative** : réponse, juste ou faux, temps passé par question, y compris pour une question `journal` [N].
- **US-52 [H] Statistiques par question.** Taux de réussite, avec les taux faibles mis en évidence.
- **US-53 [H] Export CSV** : séparateur `;`, BOM, formules de tableur neutralisées.
- **US-54 [H] Annonces et échéances** par promotion : affichées sur le tableau de bord, sans e-mail, non bloquantes.
- **US-55 [H] Import CSV d'apprenants** dans une promotion, avec mots de passe générés.

#### E7 — Administration et paramètres [H+N]
- **US-60 [H] Back-office Unfold.** Formations, parties, modules, sections et questions sont éditables en FR et en EN.
- **US-61 [N] Table des paramètres fiscaux.** En tant qu'admin, je modifie un taux ou un seuil (clé, valeur, unité, exercice, article CGI source).
  - CA : la modification est visible immédiatement dans les leçons et les calculateurs ;
  - CA : l'historique est conservé (une ligne par exercice).
- **US-62 [N] Questions à revoir.** Après la modification d'un paramètre, l'admin voit la liste des questions étiquetées avec ce paramètre (filtre admin `params`).
- **US-63 [N] Plan comptable.** Les 1 330 comptes SYSCOHADA sont importés par une commande idempotente, avec libellés FR et EN, et consultables dans l'admin.
- **US-64 [H] Sauvegarde quotidienne** de SQLite, déclenchée par les requêtes (une seule copie), et purge des comptes non vérifiés.

#### E8 — Contenu et publication (agent de rédaction) [N]
- **US-70 [N] Manifeste de formation.**
  - CA : `content/compta/formation.json` et `content/fisca/formation.json` ne listent que les parties livrées ;
  - CA : l'import est idempotent ;
  - CA : une question dont le texte change repasse en brouillon, puis est republiée par `publish_reviewed` puisque `reviewed` vaut vrai.
- **US-71 [N] Garde-fou des citations (bloquant).**
  - CA : `pytest` échoue si une section `content` ne contient aucune balise `[[cgi:]]`, `[[syscohada:]]` ou `[[guide:]]` ;
  - CA : il échoue si un compte cité, ou un compte de réponse `journal`, est absent de `SyscohadaAccount` ;
  - CA : il échoue si une clé `[[param:]]` est inconnue.
- **US-72 [N] Garde-fou de volume.**
  - CA : chaque module publié a au moins 12 questions `exam` et au moins 8 questions `quiz` publiées ;
  - CA : chaque question existe en FR et en EN ;
  - CA : les `external_id` sont préfixés `C-` ou `F-` et uniques.
- **US-73 [N] Garde-fou de droits d'auteur.**
  - CA : `pytest` échoue si le contenu contient « DCG », « Dunod », « Disle », « Plagnet » ou un ISBN ;
  - CA : il échoue si un fichier de `reference/` est suivi par git.
- **US-74 [N] Déploiement par partie.** `deploy.sh` déploie le contenu livré, et l'examen et le certificat de la nouvelle partie deviennent disponibles sans action manuelle.

### P3. Modèle logique des données

Légende : `*` = champ traduit (modeltranslation, FR/EN) ; `PK` = clé ; `FK` = clé étrangère ; `U` = contrainte d'unicité. Toutes les entités exposées par URL portent un `public_id` UUID.

#### P3.1 Entités héritées (inchangées sauf mention)

| App | Entité | Champs clés | Relations / contraintes |
|---|---|---|---|
| accounts | **User** (AbstractUser) | `role` ∈ {learner, trainer, admin}, `email_verified` | `save()` synchronise `is_staff` et les groupes |
| accounts | **Promotion** | `public_id`, `name` U, `start_date`, `join_code` (8 car.), `join_code_active` | FK Formation ; M2M User (`trainers`) |
| accounts | **LoginFailure** | `username`, `created_at` | — |
| accounts | **SignupThrottle** | `ip_hash`, `created_at` | — |
| courses | **Formation** | `public_id`, `title*`, `slug` U, `description*`, `order`, `is_open`, `icon` ∈ {**ledger, receipt**} [N], **`is_listed`** [N], **`prerequisite_note*`** [N] | — |
| courses | **Partie** | `title*`, `description*`, `slug`, `order` | FK Formation ; U(formation, slug), U(formation, order) |
| courses | **Module** | `title*`, `order`, `duration_hours`, `competence*`, `evaluation_note*` | FK Partie ; U(partie, order) |
| courses | **Section** | `title*`, `order`, `kind` ∈ {content, practical}, `body_md*`, **`legal_reference`** [N] (ex. « CGI 2026 ») | FK Module |
| courses | **Annexe** | `title*`, `file` | FK Section |
| assessments | **Question** | `qtype` ∈ {single, multiple, truefalse, numeric, matching, hotspot, **journal** [N]}, `usage` ∈ {quiz, exam}, `status` ∈ {draft, published}, `prompt*`, `explanation*`, `image`, `numeric_value`, `unit` ∈ {**FCFA, %, jours, mois, années**} [N], `tolerance_pct`, **`tolerance_abs`** [N] (défaut 1), **`exercice`** [N] (ex. 2026), `hotspot_svg`, `reviewed_fr`, `reviewed_en`, `external_id` U | FK Section ; M2M **FiscalParameter** (`params`) [N] |
| assessments | **Choice** | `text*`, `is_correct`, `order`, `shape` (JSON) | FK Question |
| assessments | **MatchPair** | `left*`, `right*`, `order` | FK Question |
| assessments | **Assessment** | `kind` ∈ {module_quiz, part_exam}, `pass_threshold`=70, `max_attempts`=3, `duration_minutes`=60, `questions_per_module`=10, `shuffle` | 1-1 Module XOR Partie (CheckConstraint) |
| assessments | **Attempt** | `public_id`, `number`, `started_at`, `deadline`, `submitted_at`, `score_pct`, `auto_submitted` | FK User, FK Assessment |
| assessments | **AttemptQuestion** | `order`, `choice_order` (JSON), `answer_text`, `answer_json` (**réponse `journal`** [N] : `[{account, label, side, amount}]`), `answered_at`, `time_spent_s` | FK Attempt, FK Question ; M2M Choice |
| catalog | **Enrollment** | `source` ∈ {catalog, code, import, admin}, `enrolled_at` | FK User, FK Formation, FK Promotion (null = groupe ouvert) ; U(user, formation) |
| progress | **SectionView** | `viewed_at` | FK User, FK Section ; U(user, section) |
| progress | **Announcement** | `title*`, `body*`, `published_at` | FK Promotion, FK User (auteur) |
| progress | **Deadline** | `due_at` | FK Promotion, FK Assessment ; U |
| certificates | **Badge** | `kind` ∈ {module, partie} | FK User ; FK Module XOR Partie |
| certificates | **Certificate** | `public_id`, `holder_name` (figé), `score_pct`, `issued_at` | FK User, FK Partie, FK Attempt ; U(user, partie) |

#### P3.2 Entités nouvelles [N]

| App | Entité | Champs | Relations / contraintes / règles |
|---|---|---|---|
| assessments | **JournalLine** (clé de correction) | `order`, `account` (code), `account_match` ∈ {class, 2, 3, 4, exact}, `side` ∈ {debit, credit}, `amount` (Decimal, FCFA, ≥ 0), `label*` (indicatif, non noté) | FK Question (`qtype=journal`). Validation de publication : au moins 2 lignes, Σ débits = Σ crédits, chaque `account` existe dans SyscohadaAccount au niveau demandé |
| referentiel | **SyscohadaAccount** | `code` PK (1 à 4 chiffres et plus), `label*`, `account_class` (1–9), `level` (longueur du code) | FK `parent` (préfixe le plus long existant). Import idempotent depuis le plan SYSCOHADA révisé |
| referentiel | **FiscalParameter** | `key` (ex. `tva.taux_global`), `value` (Decimal), `unit` ∈ {%, FCFA, coef}, `exercice` (int), `label*`, `source_article` (ex. « CGI art. 142 ») | U(key, exercice). Valeur courante = exercice le plus récent ≤ exercice de référence du site (setting `FISCAL_YEAR=2026`) |

Les citations `[[cgi:]]`, `[[syscohada:]]` et `[[guide:]]` ne sont **pas** stockées : elles sont résolues au rendu (après bleach) et contrôlées par les tests de contenu.

#### P3.3 Règles dérivées (jamais stockées)
- **Module terminé** : toutes ses sections vues et au moins un quiz envoyé.
- **Examen débloqué** : tous les modules de la partie terminés.
- **Progression** : (sections vues + quiz envoyés) / étapes totales.
- **Numérotation M1…Mn** : continue sur toute la formation.
- **Score `journal`** : `max(0, (justes − pénalité × en_trop) / attendues)`, avec pénalité par défaut de 0,5 (à confirmer, U1).

### P4. Exigences non fonctionnelles

| ID | Exigence | Seuil |
|---|---|---|
| NFR-01 | Disque total sur PythonAnywhere (venv, code, staticfiles, db, sauvegarde) | < 150 Mo (quota 512 Mo) |
| NFR-02 | CPU d'un `deploy.sh` complet | mesuré sur le pilote, < 60 s |
| NFR-03 | Affichage mobile | aucun débordement horizontal à 390 px, cibles tactiles ≥ 44 px |
| NFR-04 | Accessibilité | navigation clavier complète (dont `journal` et calculateurs), contraste AA, `prefers-reduced-motion`, mode sombre |
| NFR-05 | Sécurité | CSP sans `unsafe-inline` (hors `/admin/`), `check --deploy` sans avertissement, tests d'intrusion hérités verts |
| NFR-06 | Robustesse examen | aucune réponse perdue après coupure réseau (sauvegarde par clic, reprise) |
| NFR-07 | Dépendances de production | exactement 5, toute nouvelle dépendance exige une décision consignée |
| NFR-08 | Performance de page | page de section < 300 ms côté serveur sur PythonAnywhere gratuit (hors démarrage à froid) |

### P5. Definition of Done (critères stricts)

Une US, un lot ou un déploiement n'est **terminé** que si **tous** les points applicables sont vrais. Un seul point rouge suffit à refuser.

**DoD-Code** (toute US)
0. Pour une règle existante, `tools/mutation_sweep.py` doit la casser et voir ses tests échouer : une mutation non détectée est un test manquant.
1. `pytest` est vert en local, sans test ignoré (`skip`/`xfail`) ajouté pour l'occasion.
2. Au moins un test cite l'`US-xx` (docstring ou nom) et couvre chacun de ses CA ; un bug corrigé est accompagné d'un test de non-régression.
3. `python manage.py makemigrations --check` ne signale rien ; les migrations sont commitées.
4. `python manage.py check --deploy` ne donne aucun avertissement (avec les réglages de production).
5. Aucun script en ligne et aucun appel à un CDN ; la CSP est inchangée ou durcie.
6. Aucune nouvelle dépendance de production (NFR-07).
7. Toutes les chaînes d'interface passent par gettext ; `makemessages` puis `compilemessages` sont à jour pour FR et EN.

**DoD-Contenu** (toute section ou question livrée)
1. FR présent ; EN présent, ou bandeau de traduction actif (US-28).
2. Chaque section `content` cite au moins une source officielle (US-71) ; chaque compte cité existe dans SyscohadaAccount.
3. Aucun taux en dur dans une leçon : uniquement `[[param:]]`. Toute question chiffrée est datée « exercice 2026 », avec ses taux dans l'énoncé et ses `params` étiquetés.
4. Rédaction originale : aucun nom d'entreprise, chiffre ou phrase repris du DCG 9 ou du Plagnet ; garde-fou US-73 vert.
5. Montants en FCFA, entreprises camerounaises fictives, comptes SYSCOHADA révisé, articles du CGI 2026.
6. Pour chaque question : explication présente, `reviewed_fr` et `reviewed_en` à vrai, et `validate_for_publication()` sans erreur (dont l'équilibre débit/crédit pour `journal`).

**DoD-Partie** (avant de publier une partie et d'ouvrir son examen)
1. Tous les modules de la partie sont présents et publiés, avec au moins 12 questions `exam` et au moins 8 questions `quiz` par module (US-72).
2. Un parcours complet réussi en local avec un compte de test : sections, quiz, examen d'au moins 70 %, badge, certificat PDF, puis `/verify/<uuid>/`. À faire en FR, puis en EN.
3. Rendu vérifié à 390 px et à 1280 px, en mode clair et en mode sombre, avec capture Playwright des écrans section, quiz `journal` et résultat.

**DoD-Déploiement** (chaque mise en production)
1. Fusion `develop` → `main` ; `deploy.sh` s'exécute sans erreur sur `~/comptafiscaventisax`.
2. Test de fumée en production avec un compte de test jetable : connexion, section, quiz, langue EN.
3. Disque mesuré (`du -sh ~`) < 150 Mo et consigné dans le journal de déploiement.
4. `reference/` est absent du serveur et de git (`git ls-files reference` est vide).
5. Le journal des déploiements dans AGENTS.md est mis à jour : date, lot ou partie, mesure disque, écarts.
6. La prochaine échéance de « Run until 1 month from today » est notée.

**DoD-Documentation**
1. AGENTS.md est mis à jour (décisions, écarts, US) ; CLAUDE.md est régénéré comme miroir dans le même commit.
2. Chaque nouvelle décision d'architecture est ajoutée à la grille C avec sa justification.

### P6. Questions ouvertes (incertitudes d'architecture)

À trancher au plus tard pendant le Lot 0 ; chaque réponse devient une décision C-xx.

- **U1 `journal`** :
  - pénalité par ligne en trop (0,5 ?) ;
  - ergonomie tactile de l'ajout et de la suppression de lignes ;
  - affichage de la correction en revue de quiz, sans fuite en examen.
- **U2 Pipeline de rendu** : ordre des substitutions `[[param:]]`, `[[cgi:]]`, `[[syscohada:]]`, `[[guide:]]` et `[[calc:]]` après bleach ; comportement si une clé est inconnue au rendu en production (erreur ou marqueur).
- **U3 Calculateurs** : les formules existent en double (JS et Python) ; il faut définir le format des vecteurs de référence JSON partagés et le test de parité, sans Node en CI.
- **U4 Paie et IRPP** : abattements, tranches, CAC, CCF/CFC, RAV et TDL à extraire précisément du CGI 2026 avant de coder ; risque juridique, puisque le contenu est publié sans relecture.
- **U5 SyscohadaAccount** : traduction EN des 1 330 libellés (absents de la source) ; calcul du `parent` quand des niveaux intermédiaires manquent.
- **U6 Publication par partie** : manifeste partiel (suffisant ?) ou champ `Partie.is_published` ; stabilité de la numérotation M1…Mn et des certificats déjà émis.
- **U7 Masquage** : `is_open` et `is_listed` font-ils doublon ? Vérifier `accessible_formations` et la vue catalogue.
- **U8 CPU d'import** : environ 800 questions à importer avec environ 100 s de CPU par jour ; faut-il un import par formation ou incrémental (hash) ?
- **U9 Disque** : taille réelle du venv Python 3.13 sur PythonAnywhere ; une seule sauvegarde SQLite.
- **U10 Collisions d'identifiants** : convention `external_id` = `C-P2-M07-012`, à confirmer.
- **U11 PCG vers SYSCOHADA** : traitements sans équivalent 1-1 (emballages, frais d'établissement, provisions réglementées, TFT), à arbitrer chapitre par chapitre en suivant le Guide.
- **U12 OCR bruité** de `fiscalite.pdf` : les exemples doivent être reconstruits, sans impact sur le plan.
- **U13 Tests hérités spécifiques à l'électronique** : figures, unités électriques, `content_rules.py`, `test_two_formations.py`. Il faut les supprimer ou les réécrire sans perdre la couverture plateforme.

---

## Grille C — décisions du grill (2026-10-28)

| # | Décision |
|---|---|
| C1 | Un seul projet Django, une seule base SQLite, un login, un catalogue de deux formations. |
| C2 | Citation obligatoire (article du CGI, compte SYSCOHADA, chapitre du Guide) ; publication directe au déploiement, sans workflow de relecture. |
| C3 | Contenu figé sur le CGI Cameroun éd. 2026 et le SYSCOHADA révisé ; taux et seuils dans `FiscalParameter`, éditable en admin. |
| C4 | FR et EN dès la v1, interface et contenu. |
| C5 | Le FR fait foi ; l'EN est aligné sur le CGI-EN 2026 ; repli FR avec bandeau. |
| C6 | Fiscalité : plan en 7 blocs calqué sur le CGI ; le Plagnet ne sert que de modèle de style. |
| C7 | Comptabilité : trame des 30 chapitres du DCG 9 réécrite en SYSCOHADA, plus une introduction OHADA ; consolidation hors v1. |
| C8 | Base de code : copie propre d'electroschool2ventisax, sans historique. |
| C9 | Compta en 5 parties, fisca en 3 ; 1 chapitre = 1 module ; examen et certificat par partie. |
| C10 | Type de question `journal`, en quiz et en examen. |
| C11 | Numérique en FCFA, % et durées ; tolérance absolue (1 FCFA par défaut). |
| C12 | Six calculateurs : `tva`, `amortissement`, `paie`, `is`, `reduction`, `stock`. |
| C13 | Figures interactives supprimées ; schémas SVG générés en Python (`tools/schemas/compta.py`, `fisca.py`). |
| C14 | Leçons dynamiques (`[[param:]]`) ; questions datées « exercice 2026 », étiquetées par paramètre. |
| C15 | Balises `[[cgi:]]`, `[[syscohada:]]`, `[[guide:]]` ; test de contenu bloquant. |
| C16 | Marque « ComptaFisca Acad Ventisax », charte Ventisax, icônes registre et reçu. |
| C17 | Règles d'accès et d'évaluation d'electroschool reprises ; prérequis fisca indicatif. |
| C18 | Comptabilité entière d'abord, puis Fiscalité. |
| C19 | Pilote Compta M1, puis un déploiement par partie complète ; Fiscalité masquée jusqu'à complétude. |
| C20 | Même boîte Gmail qu'electroschool, mot de passe d'application dédié ; dépôt `fokouarnaud/c-fiscalite-syscohada` (le nom `comptafiscaventisax` prévu n'a pas été créé, décision du 2026-10-29). |
| C21 | Rédaction originale ; le DCG 9 et le Plagnet ne sont jamais cités ni recopiés. |
| C22 | finaia.co et lefisk.cm hors périmètre. |
| C23 | (U1) Une ligne en trop dans une écriture coûte une demi-ligne (`JOURNAL_EXTRA_PENALTY`). |
| C24 | (U7) Pas de champ `is_listed` : `is_open=False` masque la formation du catalogue, de sa fiche et de l'inscription. |
| C25 | (U10) Le manifeste déclare `prefix` (`C` ou `F`) ; l'import refuse toute question sans ce préfixe. |
| C26 | (US-25) La référence juridique est portée par la formation (`Formation.legal_reference`), pas par chaque section. |
| C27 | (U2) Balises remplacées après bleach, dans l'ordre param → cgi → syscohada → guide → calc ; une clé ou un compte inconnu devient un `<mark>` signalé, jamais le texte brut. |
| C28 | (U4) La paie calcule l'IRPP (art. 29, 34, 69, 71), la CFC (loi 77-10), la RAV et la TDL (art. C 86) ; les cotisations CNPS relèvent du droit social, absent des sources : elles sont saisies, jamais déduites d'un taux inventé. |

## Journal d'implémentation

### 2026-10-28 — Socle backend (Lot 0), en TDD, non commité
- Copie d'electroschool2ventisax ; suppression des figures, du contenu `electro` et `moteurs`, des schémas et des calculateurs électroniques ; marque ComptaFisca.
- App `referentiel` : `SyscohadaAccount` et `import_syscohada`, `FiscalParameter` et `import_parameters`, `calculs.py` (formules de référence des calculateurs), admin des taux avec les questions à revoir.
- `content/referentiel/syscohada.csv` : 1 330 comptes du plan révisé, 9 classes et le compte 10 « Capital » (absent du PDF source) ; libellés FR corrompus du PDF réparés (54, 60, 603, 65, 66, 667, 75, 291, 599) ; libellés EN de tous les comptes, sous-comptes à 4 chiffres compris (U5 résolue) ; 100 libellés FR nettoyés des artefacts du PDF (préfixe du compte parent, renvois de note, phrases tronquées).
- `content/referentiel/parametres.csv` : taux et barèmes du CGI 2026 (TVA, CAC, IS, minimum de perception, IRPP, CFC, RAV, TDL), chacun avec son article.
- `assessments` : type `journal` (`JournalLine`), notation FCFA et %, `tolerance_abs`, `exercice`, `params`.
- `courses` : balises de sources et de paramètres, référence juridique, registre des six calculateurs avec taux en `json_script`, contrôles de contenu bloquants (`content_rules.py`, `test_content_files.py`), préfixe de manifeste.
- `tools/schemas/compta.py` et `fisca.py` (US-27) : compte en T, bilan, circuit de la TVA (taux lus dans `parametres.csv`), frise d'amortissement (montants de `referentiel.calculs`), cycle déclaratif ; SVG FR et EN générés dans `static/content/`.
- Paie (C28) : IRPP sur salaires, CFC, RAV et TDL dans `referentiel.calculs` et `parametres.csv`.
- Certificat PDF : nomme l'organisme qui le délivre (« par ComptaFisca Acad Ventisax »).
- `deploy.sh` : référentiels importés avant le contenu, compte `comptafiscaventisax` ; skill `deploy` reciblée ; `.mcp.json` (Playwright) générique, conservé tel quel.
- U13 : les tests hérités à deux formations sont gardés et renommés (`test_fisca_formation.py`, `test_fisca_stories.py`, `catalog/tests/test_two_formations.py`) ; ils couvrent exactement le cas compta + fisca.
- Calculateurs (U3 résolue) : `static/acad/js/calc-core.js`, fonctions pures partagées navigateur/Node ; `referentiel/tests/vectors.json`, vecteurs calculés à la main, vérifiés à la fois contre `referentiel/calculs.py` et contre `calc-core.js` (Node, sauté s'il est absent) ; même lecture des nombres que la correction serveur ; `calculators.js` réécrit pour les six calculateurs métier, libellés FR/EN dans `_calc_labels.html`, contrôlé dans Chromium (Playwright) en FR et en EN, sans erreur de console.
- Stories héritées et tests de caractérisation : RED/GREEN démontré par mutation (`tools/mutation_sweep.py`). 32 règles de production cassées une à une (US-01, 02, 03, 04, 05, 10, 12, 13, 14, 22, 26, 28, 30, 31, 33, 40, 41, 42, 43, 50, 52, 53, 54, 55, 63, 64) : chacune fait échouer ses tests, qui repassent après restauration. Le balayage a révélé trois tests manquants dans la suite héritée, ajoutés : le score d'un certificat ne baisse jamais face à une tentative plus faible (US-41), formules de tableur neutralisées dans l'export CSV (US-53), lien de mot de passe oublié expiré après 24 h (US-03).
- Module pilote Compta M1 (C19), écrit après son test (`courses/tests/test_pilot_content.py`) : `content/compta/formation.json` (préfixe C, formation ouverte, référence SYSCOHADA révisé), trois sections FR/EN (cadre OHADA, principes, plan de comptes et partie double), 12 questions d'examen et 8 de quiz, dont trois écritures `journal` ; entreprise fictive Mbarga Distribution SARL (Douala) ; contrôles bloquants du contenu verts.
- US-42 : la page publique de vérification affiche maintenant le score (« 100 % » / « 100% »), exigé par le PRD et absent du gabarit hérité ; test écrit d'abord, rouge, puis vert.
- Partie 1 « Fondamentaux » complète (C9, C19), écrite après son test : M1 cadre OHADA et principes, M2 écriture comptable (débit et crédit, journal, grand livre, balance), M3 actif et passif (bilan), M4 charges et produits (compte de résultat) ; 9 sections FR/EN, 80 questions (48 d'examen, 32 de quiz, 12 écritures `journal`). L'examen de la Partie 1 peut donc ouvrir au prochain déploiement.
- Partie 2 « Opérations courantes » complète (C9, C19), écrite après son test : TVA (CGI art. 133, 134, 142, 143, 144, 149), achats (frais sur achats 6015, consignes 4094), ventes (port refacturé 7071, consignes 4194), réductions et escomptes (6019, 673, 773), frais accessoires (6015, 612, 4454), autres charges et produits (62, 63, 641, 7073), paie (IRPP art. 29, 34, 69, 71 ; CFC, RAV, TDL art. C 86 ; calculateur `paie` intégré), règlements (effets 402/412, virements internes 585, monnaie électronique 552) ; 16 sections FR/EN, 160 questions (96 d'examen, 64 de quiz), montants TVA recalculés au taux global de 19,25 %.
- Parties 3 à 5 de la comptabilité, chacune écrite après son test : P3 « Investissement et financement » (immobilisations et TVA sur immobilisations 4451, titres 26/274/50 et cessions 777/677, emprunts et annuité constante, location-acquisition en 17, subventions 14/799/71, devises 676/776/478/479/194 et parité fixe de l'euro) ; P4 « Travaux d'inventaire » (amortissements, dépréciations, stocks 6031/39, créances douteuses 416/491/651, provisions 19, cessions 812/822 et CGI art. 145, régularisations 476/477/408/418) ; P5 « Clôture et états financiers » (affectation 111/121/465, bilan et FR/BF/TN, soldes intermédiaires 132 à 138, TFT, rapprochement bancaire et contrôles). Formation Comptabilité complète : 5 parties, 29 modules, 580 questions.
- Formation Fiscalité complète (C6, C9), écrite après son test `courses/tests/test_fisca_content.py`, ouverte au catalogue puisque complète (C19) : P1 « Impôts sur les revenus » (CGI, immatriculation L 1, régimes IGS/réel art. 93 quater et quinquies ; IS art. 2, 3, 7, 17, 17 bis, 18, 21, 23 ; IRPP art. 29, 34, 69, 70, 71) ; P2 « Taxes sur la dépense et droits » (TVA art. 125 à 149 et accises art. 142 ; enregistrement et timbre art. 543 à 545 ; fiscalité locale art. C 2, C 4, C 7, C 49, C 53, C 57, C 83, C 86) ; P3 « Procédures fiscales » (obligations art. 18, L 1, L 1 bis ; droit de reprise L 34 ; L 41 ; sanctions L 95, L 97, L 98 ; réclamation L 116, L 118) ; 16 sections FR/EN qui citent toutes le CGI, 160 questions.
- Volume total : 2 formations, 8 parties, 37 modules, 740 questions bilingues ; `content/` 1,4 Mo.
- Audit des CA backend (2026-10-29), en TDD : US-15 implémentée (`Formation.prerequisite_note`, traduit, importé du manifeste, affiché sur le programme, jamais bloquant ; Fiscalité « Recommandé après les Parties 1 et 2 de Comptabilité ») ; trois CA existantes sans test couvertes, RED démontré par mutation : US-21 (non-inscrit renvoyé vers le programme), US-03 (compte sans e-mail renvoyé au formateur), US-53 (BOM de l'export CSV) ; quatre mutations ajoutées à `tools/mutation_sweep.py`.
- Tests : 712 verts ; `makemigrations --check` sans remarque.
- Premier déploiement (2026-10-29) : web app, venv `~/.virtualenvs/comptafisca` (73 Mo), WSGI, `/static/`, HTTPS forcé ; `deploy.sh` EXIT=0 sur `3cdf2a8`, 1 340 comptes, 64 paramètres, 75 sections et 740 questions publiées, disque 87 Mo. Fumée (compte jetable supprimé, LEFT 0) : section FR/EN, quiz jusqu'au résultat ; deux défauts trouvés et corrigés en TDD :
  - US-34 : la grille `journal` n'avait aucun style et imposait ~640 px à 360 px ; table à largeur fixe, champs de 44 px ;
  - US-01 : sans mot de passe Gmail, la production basculait en silence sur le backend `console` et l'inscription annonçait « Vérifiez vos e-mails » pour un message jamais parti. Désormais : repli console réservé au développement, contrôle `accounts.E001` qui fait échouer `check --deploy` sans identifiants SMTP, échec d'envoi affiché à l'inscription (compte retiré, erreur journalisée).
- Écart : `http://` est redirigé en 302 (Force HTTPS de PythonAnywhere), pas en 301.
- Réinscription (US-01, 2026-10-29) : un compte jamais confirmé (inactif, adresse non vérifiée) ne bloque plus son adresse ni son identifiant ; se réinscrire le remplace et envoie un nouveau lien ; un compte confirmé reste protégé ; connexion et « Vérifiez vos e-mails » l'indiquent. Après la saisie du `.env`, le site envoyait encore sans authentification (530) : le `touch` du WSGI n'a pas suffi, le bouton « Reload » a réglé le problème (skill `deploy`).
- Balayage de mutations étendu aux stories backend restantes (US-14, 20, 23 à 25, 32, 34 à 36, 61, 62, 70 à 74) ; il a révélé un test manquant, la carte « Reprendre » du tableau de bord (US-20), ajouté. L'outil restaure désormais les octets d'origine (plus de CRLF réécrit sous Windows).
- Tests : 721 verts ; 65 mutations, toutes détectées sur l'état final (`6de9d69`).
- Couverture de toutes les stories du PRD par le balayage (47 sur 47) : US-51, vrai défaut, corrigé (le détail d'une tentative n'affichait rien pour une écriture `journal`) ; tests ajoutés pour US-11 (examen et langues du programme, mutation jusque-là non détectée) et US-60 (édition FR/EN dans le back-office) ; règle US-27 (format des montants des schémas). L'outil compare désormais en LF (copie de travail parfois en CRLF sous Windows) et restaure les octets d'origine.
- Tests : 726 verts ; 70 mutations, toutes détectées sur l'état final (`f5c25ba`).
- Reste : le premier déploiement (skill `deploy`) ; il exige que l'utilisateur se connecte lui-même à PythonAnywhere et renseigne le `.env` du serveur (clé secrète, mot de passe d'application Gmail).
