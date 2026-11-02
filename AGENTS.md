# AGENTS.md — ComptaFisca Acad Ventisax

> Source de vérité du projet. `CLAUDE.md` en est le miroir : toute modification se fait ici d'abord.
> Décisions issues du grill du 2026-10-28 (C1 à C22) et du grill S du 2026-10-29 sur la formation Simulation (S1 à S21, en attente de validation des GOALS).

## GOALS

Plateforme e-learning bilingue (FR/EN) qui reproduit **toutes les fonctionnalités** d'Electro Acad Ventisax (https://electroacadventisax.pythonanywhere.com/, source `..\electroschool2ventisax`). Le contenu électronique y est remplacé par trois formations :

- **Comptabilité** (Form 1), adaptée au SYSCOHADA révisé (Cameroun) ;
- **Fiscalité** (Form 2), adaptée au Code général des impôts du Cameroun, édition 2026 ;
- **Simulation Compta et Fisca** (Form 3, décisions S1 à S21) : une formation entièrement pratique, qui fait vivre à l'apprenant une année complète d'entreprises camerounaises fictives à partir de pièces justificatives.

Le site est déployé sur le compte gratuit PythonAnywhere `comptafiscaventisax`.

### 1. Objectifs fonctionnels prioritaires

**1.1 Plateforme clonée d'electroschool (parité fonctionnelle)** — C1, C8, C17
- Un seul projet Django, une seule base SQLite, un seul login, un catalogue de 3 formations (S1). Le code d'electroschool2ventisax est copié sans son historique git, et le contenu électronique est retiré.
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
- Identité : **« ComptaFisca Acad Ventisax »**, slogan « Comptabilité SYSCOHADA et fiscalité camerounaise, formation et évaluation ». Charte Ventisax inchangée (navy #0b2d46, teal, Lexend, logo V) et lien vers ventisax.pythonanywhere.com. Icônes Tabler : registre pour la compta, reçu pour la fisca ; celle de la simulation sera fixée au démarrage du parcours A. (C16)

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
4. **Simulation** (S4, S8, S20) :
   - d'abord le document de conception `docs/form3-conception.md` (syllabus, scénario de janvier du parcours A, matrice du plan de comptes et des taux), validé par l'utilisateur avant tout code ou contenu ;
   - puis un parcours par déploiement : A → E → B3 → C → D → B1 → B2 (S20, S29) ;
   - la formation reste fermée jusqu'à ce que le parcours A soit complet.
- Volume cible des formations 1 et 2 : environ 40 modules, au moins 12 questions d'examen et 8 questions de quiz par module, soit environ 800 questions et 300 sections bilingues.
- Volume cible de la simulation : 6 parcours de 7 modules, 8 à 12 pièces datées par mois. Le volume de questions par module sera fixé dans le document de conception.

**1.7 Formation Simulation Compta et Fisca (priorité 3, Form 3)** — S1 à S21
- **Principe** : l'apprenant tient la comptabilité et les obligations fiscales d'une entreprise fictive sur l'exercice 2026, de la création à la DSF de l'exercice, déposée en 2027 à l'échéance de son centre des impôts (CGI art. 18 (1)), à partir de pièces justificatives virtuelles datées : factures, reçus Mobile Money, relevés bancaires, bulletins de paie.
  - Chaque étape repart de l'**état officiel corrigé**, avec la balance officielle affichée en début de mois (S2).
  - Il n'y a pas de grand livre par apprenant, et une erreur ne se reporte pas sur les mois suivants.
- **Structure** (S11) :
  - une formation `simulation`, préfixe `S` ;
  - **une partie par parcours**, chacune avec son examen et son certificat ;
  - **7 modules** par partie : Création, T1, T2, T3, T4, Inventaire, Passerelle + DSF. Les mois sont des sections ;
  - l'examen tire 4 questions par module (`questions_per_module=4`).
- **Phases** :
  1. *Création (jour 1)* : apport du capital, dépôt en banque, frais de constitution passés en **charges par nature**. Le corrigé signale le piège de l'ancienne immobilisation en frais d'établissement (S6).
  2. *Exploitation mensuelle* : achats, ventes, paie, encaissements et décaissements en espèces, banque et Mobile Money ; rapprochement mensuel de la banque et du Mobile Money (S19). L'échéance du **15 du mois suivant** porte les obligations sous leur nom CGI : TVA, acompte d'IS ou d'IRPP (minimum de perception), précompte sur achats, retenues sur salaires (S7).
  3. *Inventaire (décembre)* : stocks finaux, amortissements au prorata temporis, dépréciations et provisions, régularisations.
  4. *Post-clôture* : passerelle du résultat comptable au résultat fiscal, liquidation de l'IS, DSF au plus tard le 15 mars (DGE), le 15 avril (CIME) ou le 15 mai (centre de fiscalité locale), selon le `centre_impots` déclaré par le parcours (CGI art. 18 (1)) ; 15 mars pour la déclaration annuelle à l'IGS (art. C 41).
- **Six parcours sectoriels** (S3, S9) :
  - **A — Boutique de vêtements**, SARL au réel. Profil (S17) :
    - « Ngono Mode SARL », Douala-Akwa, capital de 5 000 000 FCFA en numéraire, créée le 2 janvier 2026 ;
    - chiffre d'affaires d'environ 90 M ; un gérant salarié et 2 vendeuses ; bail commercial ;
    - achats auprès de grossistes et d'importateurs locaux (précompte de 2 %), une importation en T3 ;
    - encaissements en espèces, MTN MoMo, Orange Money et carte ;
    - stocks : inventaire intermittent (6011, variation 6031), fiches CMUP pour 3 familles d'articles, un exercice de contraste en PEPS (S18) ;
    - focus : marges, TVA collectée et déductible ;
    - passerelle (S21) : six éléments, chacun déclenché par une vraie pièce de l'année (amendes, amortissement d'une voiture légère au-delà du taux fiscal maximal de 25 %, dons au-delà de 0,5 % du chiffre d'affaires, charge sans pièce, IS et minimum de perception, reprise d'une provision déjà taxée) ; le minimum de perception est comparé à l'IS.
  - **B1 — Dépôt de boissons à l'IGS**, établissement individuel. Version courte :
    - **SMT** de l'AUDCIF (recettes et dépenses) ;
    - IGS, précompte de 5 % subi ;
    - questions numériques, sans `journal` ni DSF normale (S14).
  - **B2 — Dépôt de boissons, de l'IGS à la SARL au réel** (S13) :
    - année 2026 à l'IGS et au SMT ; le chiffre d'affaires dépasse 50 M en cours d'année ;
    - après la clôture, l'établissement apporte son fonds à une SARL au réel au **1er janvier 2027**, avec un bilan d'ouverture ;
    - aucune bascule de régime en cours d'année (CGI art. 93 quater).
  - **B3 — Dépôt de boissons, SARL au réel** :
    - consignes d'emballages (4094/4194) et emballages récupérables (2493) ;
    - camions immobilisés et amortis ;
    - précompte de 2 % sur les achats auprès des brasseries ;
    - droits d'accises spécifiques sur la bière, payés par le brasseur et compris dans le prix d'achat ;
    - DSF.
  - **C — Commerce d'électronique et pose de climatiseurs**, SARL au réel (S16) :
    - un fonctionnaire est **associé à 80 %** et la gérance est confiée à un tiers non fonctionnaire ;
    - les vacations ponctuelles du fonctionnaire comme formateur sont des honoraires (632), avec la retenue de 5 % de l'art. 92 bis si la SARL figure sur la liste réglementaire ;
    - dividendes et IRCM en fin d'année.
  - **D — Prestataire en froid et climatisation**, établissement individuel au réel (S10) :
    - prestations en 706, TVA exigible à l'encaissement ;
    - retenue à la source de **5,5 %** (5 % + CAC) subie sur les clients publics (art. 21 (2)), imputée sur les acomptes ;
    - une pièce de contraste montre le taux de **11 %** (10 % + CAC), applicable aux entreprises absentes du fichier des contribuables actifs.
  - **E — Prestations de climatisation et froid, et vente de matériel**, SARL à l'IGS (S29 à S31, validé le 2026-11-01) :
    - un gestionnaire, gérant, détient 20 % des parts et un fonctionnaire 80 % ; capital minimal de 100 000 FCFA (20 parts de 5 000 ; loi n° 2016/014 art. 2, qui déroge à l'AUSCGIE art. 311) ; notaire facultatif (art. 4) ;
    - le fonctionnaire finance le démarrage, environ 1 500 000 FCFA au total, par une avance en compte courant d'associé (4621) que la SARL lui rembourse ;
    - le fonctionnaire travaille aussi pour la SARL, mais comme vacataire payé en honoraires (632) : un emploi salarié privé lui est en principe interdit par le statut général de la fonction publique ;
    - chiffre d'affaires visé sous 30 millions : IGS (art. 93 quater, C 39 et C 40) et SMT (AUDCIF art. 13, sous les seuils des services comme du négoce) ;
  - Les profils de B1, B2, B3, C et D sont validés avec l'utilisateur au démarrage de chaque parcours (S20).
- **Réalisme camerounais** (S27, S28, demande du 2026-10-30) :
  - les factures ont le style camerounais réel : identité fiscale complète de l'émetteur (raison sociale, NIU au format de la DGI, RCCM, régime, centre des impôts), numéro, client et référence du système de facturation électronique de la DGI, sans laquelle la TVA n'est pas déductible (CGI art. 143 (1) b) ;
  - toute décision d'un organisme extérieur (DGI, greffe, CNPS, banque, opérateur Mobile Money…) est une pièce « démarche » qui précise l'organisme, l'objet, les documents à fournir, le document obtenu et la source officielle, pour que l'apprenant puisse refaire la démarche en réalité et obtenir les vrais documents ;
  - les entreprises restent fictives (C21) et chaque pièce affichée porte la mention « document pédagogique fictif » : elle ne peut pas passer pour un original.
- **Paie** : les cotisations CNPS figurent en montants sur le bulletin de paie. L'apprenant calcule IRPP, CAC, CFC, RAV et TDL (S15, C28).
- **Déclarations et DSF** (S12) :
  - chaque case clé est une question numérique en FCFA : TVA due, précompte, acompte d'IS, résultat fiscal ;
  - le formulaire s'affiche en lecture seule ;
  - la DSF se limite au bilan, au compte de résultat, au tableau de passage et à la liquidation de l'IS.
- **Accès** : prérequis indicatif « Recommandé après les formations Comptabilité et Fiscalité », sans aucun blocage (S21, C17).
- **Autorité** : CGI Cameroun éd. 2026 (les taux du parcours sont vérifiés article par article avant la rédaction), AUDCIF et Guide SYSCOHADA (SMT, emballages), plan comptable SYSCOHADA révisé.

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
- **Contenu versionné** dans `content/<slug>/` : `formation.json`, sections `.fr.md` et `.en.md`, `questions.json`. Import idempotent par `import_content`. Les `external_id` sont préfixés `C-` (compta), `F-` (fisca) ou `S-` (simulation).
- **Simulation** (S2, S5, S11, S12) :
  - aucun nouveau type de question : `journal` et `numeric` couvrent les écritures, les déclarations et la DSF ;
  - aucun état comptable stocké par apprenant ;
  - les pièces justificatives sont décrites en JSON dans `content/simulation/` et rendues en HTML par une balise `[[piece:ID]]`, substituée après bleach comme les autres balises, en FR et en EN, sans image, PDF ni autre fichier binaire ;
  - l'examen de chaque parcours règle `questions_per_module=4` ;
  - les taux absents de `parametres.csv` (précompte de 2, 5 et 10 %, retenue de 5,5 %, retenue de l'art. 92 bis, accises sur la bière, IGS, IRCM) y sont ajoutés avec leur article avant usage ;
  - les montants CNPS sont toujours donnés dans les pièces, jamais calculés à partir d'un taux.
- **Sources** : `reference/` (97 Mo, livres protégés) est **gitignoré et n'est jamais déployé**. Seul le contenu dérivé et réécrit part en production.
- **Déploiement** :
  - dépôt GitHub `fokouarnaud/c-fiscalite-syscohada` (public), code dans `~/comptafiscaventisax` ;
  - `deploy.sh` enchaîne pull, pip, migrate, import_content, publish_reviewed, collectstatic, check --deploy et touch du WSGI ;
  - branches `develop` → `main`.
- **E-mail** : Gmail SMTP, même boîte expéditrice qu'electroschool. Le mot de passe d'application **dédié** est saisi par l'utilisateur dans le `.env` du serveur, et l'agent ne le manipule jamais.
- **Qualité** : pytest-django vert. Les tests plateforme hérités sont conservés (intrusion, examen, carnet de notes). Les tests propres à l'électronique sont réécrits. Nouveaux tests : scoring FCFA, `journal`, paramètres, citations, calculateurs.

### 3. Périmètre strictement hors scope (v1)

- Paiement, abonnement, paiement des formations par mobile money, contenus payants. La comptabilisation d'opérations Mobile Money dans la simulation est, elle, dans le périmètre.
- Vidéo, cours en PDF téléchargeables, simulateurs ou figures isométriques interactives. Le pipeline Node des figures et `[[fig:]]` sont supprimés.
- Comptes consolidés et combinés (partie 4 du Guide SYSCOHADA).
- Fiscalités spécifiques non retenues dans le plan, et équivalents de notions françaises sans pendant camerounais : CET, intégration fiscale, ISF.
- Workflow de relecture ou validation éditoriale dans l'application (statuts brouillon → relu → publié côté contenu).
- Recalcul dynamique des réponses de questions selon les taux courants.
- Reprise mot pour mot de textes, cas ou corrigés du DCG 9 ou du Plagnet, et toute citation de ces livres sur le site.
- Fonctionnalités de finaia.co et lefisk.cm (calendrier fiscal, recherche dans le CGI, simulateurs tiers). Ces sites ne servent que d'inspiration ou de contrôle croisé des taux.
- Prérequis bloquant entre formations, et certificat de formation entière (le certificat est délivré par partie uniquement).
- Historique git d'electroschool, et grilles de décisions E, M et F d'electroschool.
- Toute autre formation que Comptabilité, Fiscalité et Simulation (S1), et une 2e web app ou une autre base que SQLite.
- Pour la simulation :
  - grand livre ou balance propres à chaque apprenant, et report des erreurs d'un mois sur l'autre (S2) ;
  - nouveau type de question « déclaration » ou formulaire DGI saisissable (S12) ;
  - DSF complète au-delà du bilan, du compte de résultat, du tableau de passage et de la liquidation de l'IS (S12) ;
  - régime simplifié, supprimé par la LF 2026, et bascule de régime en cours d'exercice (S9, S13) ;
  - secteurs Banque et Assurance (plans PCB et CIMA) ;
  - taux CNPS inventés ou calculés (S15, C28) ;
  - le sigle « VSD » (S7) ;
  - pièces justificatives en image, PDF ou autre fichier binaire (S5).

---

## PRD — Product Requirements Document

> Dérivé des GOALS validés (Form 1 et 2 ; Form 3 Simulation ajoutée le 2026-10-29 : E9, P3.4, NFR-09 à 11, DoD-Parcours, U14 à U19). Les identifiants `US-xx` sont stables : un commit ou un test cite l'US qu'il sert. Les US marquées **[H]** sont héritées d'electroschool : on vérifie leur parité, on ne les réécrit pas. Les US marquées **[N]** sont nouvelles ou modifiées.

### P1. Personas

| Persona | Rôle technique | Besoin principal |
|---|---|---|
| **Aïcha, apprenante autonome** | `learner`, groupe ouvert | Se former seule et gratuitement, sur mobile (390 px) avec une connexion instable, et obtenir un certificat vérifiable. |
| **Paul, apprenant en promotion** | `learner` + code de promotion | Suivre le rythme de son centre, voir les annonces et les échéances. |
| **Mme Ngo, formatrice** | `trainer` (staff limité) | Suivre ses promotions, repérer les décrocheurs et les questions mal réussies, exporter les notes. |
| **Administrateur Ventisax** | `admin` / superuser | Publier le contenu, mettre à jour les taux à chaque loi de finances, gérer comptes et promotions. |
| **Recruteur / tiers** | anonyme | Vérifier l'authenticité d'un certificat. |
| **Agent de rédaction (Claude)** | hors application | Produire le contenu FR/EN conforme : sources citées, comptes valides, taux paramétrés. |
| **Brice, futur comptable en simulation** [N] | `learner` | Après Form 1 et 2, tenir sur pièces la comptabilité et les déclarations d'une entreprise réaliste pendant un an, jusqu'à la DSF, et obtenir un certificat par parcours. |

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

#### E9 — Formation Simulation Compta et Fisca (Form 3) [N]
Décisions S1 à S21. Persona principal : Brice. Les CA s'ajoutent à ceux des US héritées réutilisées (US-12, 21, 30, 31, 34, 35, 41, 72, 74).

- **US-80 [N] Programme de la simulation.** En tant qu'apprenant, je vois la formation Simulation et ses parcours afin de choisir l'entreprise que je vais tenir.
  - CA : formation `simulation`, préfixe `S`, fermée (`is_open=False`) tant que le parcours A n'est pas complet (S1, S20) ; ouverte le 2026-11-01 avec A et E ;
  - CA : une partie par parcours livré (A, B3, C, D, B1, B2), avec 7 modules chacune : Création, T1, T2, T3, T4, Inventaire, Passerelle + DSF (S11) ;
  - CA : le programme affiche « Recommandé après les formations Comptabilité et Fiscalité », sans aucun blocage (S21) ;
  - CA : la description de chaque partie résume le profil (forme juridique, régime, secteur, ville).
- **US-81 [N] Dossier d'entreprise.** La première section de chaque parcours présente le profil de l'entreprise fictive, son plan de comptes personnalisé (sous-comptes de trésorerie compris, S19) et la table des taux utiles.
  - CA : chaque compte du plan personnalisé existe dans `SyscohadaAccount` ;
  - CA : chaque taux est affiché par `[[param:]]` avec son article ;
  - CA : le profil du parcours A est Ngono Mode SARL (S17).
- **US-82 [N] Pièce justificative.** Dans une section ou un énoncé, `[[piece:REF]]` affiche la pièce en HTML : facture, reçu de caisse ou Mobile Money, relevé bancaire ou Mobile Money, bulletin de paie, statuts, bail, avis de douane, fiche de stock, balance, formulaire de déclaration.
  - CA : rendu FR ou EN selon la langue ; montants entiers en FCFA formatés selon la langue ;
  - CA : remplacé après bleach, toutes les valeurs échappées ; une référence inconnue devient un `<mark>` signalé (C27) et fait échouer les tests ;
  - CA : aucun fichier binaire (S5) ; tableau lisible au clavier et au lecteur d'écran (`<table>`, `<caption>`) ;
  - CA : aucun débordement horizontal de la page à 390 px.
  - CA (S27) : une facture d'achat ou de vente porte l'identité fiscale complète de l'émetteur (NIU au format de la DGI : M ou P, 12 chiffres, une lettre), son numéro, le client et la référence de facturation électronique de la DGI ; sinon l'import et les tests échouent ;
  - CA (S27) : toute pièce affichée porte la mention « Document pédagogique fictif ».
- **US-97 [N] Démarche auprès d'un organisme (S28).** Avant chaque décision d'un organisme extérieur, l'apprenant voit une pièce « démarche » : où aller, pour quoi, avec quels documents, ce qu'il obtient, et sur quel texte officiel.
  - CA : organisme, objet, documents à fournir, document obtenu et source sont tous obligatoires ;
  - CA : les documents à fournir s'affichent en liste, la source en badge cité (`[[cgi:]]`, etc.) ;
  - CA : une démarche dont la source manque dans `reference/` n'est pas rédigée (U21).
- **US-83 [N] Saisie d'une pièce.** Je passe l'écriture d'une pièce dans une question `journal`.
  - CA : la clé de correction est l'écriture du livre officiel pour cette pièce (US-93) ;
  - CA : en quiz, la correction affiche l'écriture officielle ; en examen, rien (US-31) ;
  - CA : la pièce est visible dans l'énoncé, en quiz comme en examen.
- **US-84 [N] Balance officielle du mois.** Chaque mois commence par la balance officielle arrêtée à la fin du mois précédent.
  - CA : cette balance est générée par l'outil à partir du livre officiel, jamais saisie à la main ;
  - CA : rien ne dépend des réponses de l'apprenant (S2).
- **US-85 [N] Échéance du 15.** Je calcule les montants de la déclaration du mois précédent.
  - CA : une question numérique par case clé : TVA collectée, TVA déductible, TVA due ou crédit, précompte sur achats subi, acompte d'IS (minimum de perception majoré des CAC), retenues sur salaires (IRPP, CAC, CFC, RAV, TDL), retenue subie imputée (S10, S12) ;
  - CA : les obligations portent leur nom du CGI, jamais « VSD » (S7) ;
  - CA : en quiz, la correction affiche le formulaire rempli en lecture seule (`[[piece:]]` de type déclaration) ;
  - CA : chaque réponse est égale au calcul de l'outil sur le livre officiel (US-93).
- **US-86 [N] Rapprochement mensuel.** À la fin du mois, je rapproche le relevé bancaire et le relevé Mobile Money du compte correspondant.
  - CA : questions numériques sur les écarts, puis `journal` pour les régularisations (frais en 631, virements internes par 585) (S19).
- **US-87 [N] Création au jour 1.** Je comptabilise l'apport du capital, son dépôt en banque et les frais de constitution.
  - CA : les frais de constitution sont passés en charges par nature, et une question piège sur l'ancienne immobilisation en frais d'établissement est corrigée avec explication (S6).
- **US-88 [N] Travaux d'inventaire.** En décembre, je valorise le stock final (fiches CMUP, contraste en PEPS pour A, S18), je calcule les amortissements au prorata temporis, les dépréciations, les provisions et les régularisations.
  - CA : les calculateurs `stock` et `amortissement` sont proposés dans les sections, non notés (US-26) ;
  - CA : les écritures d'inventaire figurent dans le livre officiel.
- **US-89 [N] Passerelle et DSF.** Après la clôture, je passe du résultat comptable au résultat fiscal et je remplis les cases clés de la DSF.
  - CA : pour A, six éléments, chacun déclenché par une pièce de l'année (S21) ;
  - CA : l'IS est comparé au minimum de perception, sous déduction des acomptes et précomptes ;
  - CA : la DSF se limite au bilan, au compte de résultat, au tableau de passage et à la liquidation de l'IS (S12), avec une échéance fixée par le centre de rattachement (CGI art. 18 (1) : 15 mars, 15 avril ou 15 mai 2027).
- **US-90 [N] Parcours à l'IGS (B1, B2).** Je tiens le SMT (recettes et dépenses) d'un établissement à l'IGS.
  - CA : uniquement des questions numériques, sans `journal` ni DSF normale (S14) ;
  - CA : IGS et précompte de 5 % subi, avec leurs articles.
- **US-91 [N] Bascule de B2.** Je constate le dépassement du seuil de 50 M sur l'année 2026, puis je prépare l'apport du fonds à une SARL au réel au 1er janvier 2027 et son bilan d'ouverture.
  - CA : aucun changement de régime en cours d'année (S13, art. 93 quater).
- **US-92 [N] Retenues subies par D.** Je comptabilise une prestation en 706, avec la TVA exigible à l'encaissement, et la retenue de 5,5 % subie sur un client public, imputée sur l'acompte.
  - CA : une pièce de contraste à 11 % (entreprise hors fichier) est expliquée (S10).
- **US-93 [N] Livre officiel et garde-fous (agent de rédaction).** Chaque parcours a un livre officiel `content/simulation/<parcours>/ledger.json` : écritures datées, chacune rattachée à une pièce.
  - CA : `pytest` échoue si une écriture n'est pas équilibrée ou cite une pièce ou un compte inconnu ;
  - CA : il échoue si une pièce n'est utilisée par aucune écriture ni aucune question ;
  - CA : il échoue si une question `journal` diffère de l'écriture officielle de sa pièce ;
  - CA : il échoue si une balance ou une déclaration diffère du calcul de l'outil ;
  - CA : il échoue si le bilan de clôture n'est pas équilibré, ou si le résultat du compte de résultat diffère de celui du bilan.
- **US-94 [N] Examen et certificat par parcours.** Chaque parcours a son examen : 70 %, 3 tentatives, 60 min, **4 questions tirées par module** (S11), soit 28 questions.
  - CA : `questions_per_module` vient du manifeste ;
  - CA : le certificat nomme le parcours (« Simulation, parcours A : boutique de vêtements »).
- **US-95 [N] Taux de la simulation.** `parametres.csv` contient, avec leur article, les taux absents aujourd'hui : précompte sur achats (2, 5, 10 %), retenue de 5,5 % sur la commande publique, retenue de 5 % de l'art. 92 bis, droits d'accises spécifiques sur la bière, IGS, IRCM.
  - CA : une clé sans article fait échouer l'import ;
  - CA : les montants CNPS ne sont jamais calculés, ils figurent sur le bulletin (S15).
- **US-96 [N] Garde-fous de vocabulaire.** `pytest` échoue si le contenu de la simulation contient « VSD », ou présente le « régime simplifié » ailleurs que pour expliquer sa suppression (S7, S9).

#### Traçabilité E9 (vérifiée par `simulation/tests/test_prd_traceability.py`)
Chaque story de E9 est citée par au moins un fichier de test, et chacun des 45 critères d'acceptation (« - CA ») est associé, dans l'ordre du PRD, à un test nommé (table `CRITERIA`) ; un critère ou une story ajouté sans test, ou un test renommé, fait échouer `pytest`. Chaque règle est aussi cassée par `tools/mutation_sweep.py`.

| Story | Fichiers de test (`simulation/tests/`) |
|---|---|
| US-80 | `test_simulation_content_rules`, `test_simulation_manifest`, `test_simulation_prd_criteria` |
| US-81 | `test_simulation_content_rules` |
| US-82 | `test_import_simulation`, `test_piece_model`, `test_piece_rendering`, `test_real_world_pieces` |
| US-83 | `test_piece_in_questions` |
| US-84 | `test_ledger_tool`, `test_simulation_content_rules` |
| US-85 | `test_import_simulation`, `test_ledger_tool`, `test_piece_in_questions`, `test_simulation_content_rules` |
| US-86 | `test_ledger_tool`, `test_simulation_content_rules` |
| US-87 | `test_simulation_content_rules` |
| US-88 | `test_simulation_content_rules`, `test_simulation_prd_criteria` |
| US-89 | `test_ledger_tool`, `test_simulation_calculations`, `test_simulation_content_rules`, `test_simulation_prd_criteria` |
| US-90 | `test_simulation_calculations`, `test_simulation_content_rules`, `test_simulation_parameters` |
| US-91 | `test_simulation_content_rules` |
| US-92 | `test_simulation_calculations`, `test_simulation_content_rules` |
| US-93 | `test_import_simulation`, `test_ledger_tool`, `test_simulation_content_rules` |
| US-94 | `test_certificate_parcours`, `test_import_simulation` |
| US-95 | `test_simulation_content_rules`, `test_simulation_parameters` |
| US-96 | `test_simulation_content_rules` |
| US-97 | `test_real_world_pieces` |

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

#### P3.4 Formation Simulation [N] (S1 à S21)

| App | Entité | Champs | Relations / contraintes / règles |
|---|---|---|---|
| simulation | **Piece** (pièce justificative) | `public_id`, `ref` U (ex. `S-A-01-004`), `kind` ∈ {facture_achat, facture_vente, recu_caisse, recu_momo, releve_bancaire, releve_momo, bulletin_paie, statuts, bail, avis_douane, fiche_stock, balance, declaration}, `issued_on` (date), `title*`, `payload` (un seul JSON, textes bilingues `{fr, en}` et montants communs : `fields` [{label, value}], `lines` [{label, qty, unit_price, amount} ou {label, debit, credit}], `totals` [{label, role ∈ {ht, tax, ttc}, amount}]) | FK Partie (le parcours). Importée de `content/simulation/<parcours>/pieces.json`, de façon idempotente. Validation : la somme des lignes donne le HT, HT + taxes = TTC, montants entiers en FCFA, quantité × prix unitaire = montant, débit = crédit pour une balance, `ref` préfixée `S-` (`Piece.clean`). La date dans l'exercice reste à contrôler (U19) |
| assessments | **Question** (modifiée) | + M2M **`pieces`** | Les pièces citées par `[[piece:]]` dans l'énoncé ; permet de lister les questions touchées quand une pièce change |
| courses | **Formation** (modifiée) | `icon` + une 3e valeur (U14) | `prefix` du manifeste = `S` (C25) |
| assessments | **Assessment** (inchangée) | `questions_per_module` = 4 pour la simulation | Valeur lue dans le manifeste (`exam.questions_per_module`, U15) |
| referentiel | **FiscalParameter** (données) | nouvelles clés `precompte.*`, `retenue.*`, `accises.biere_*`, `igs.*`, `ircm.*` | Chaque clé a son `source_article` (US-95) |

**Non stockés en base, contrôlés par les tests** :
- **Livre officiel** `content/simulation/<parcours>/ledger.json` : écritures `{date, piece, journal, lignes [{account, side, amount, label_fr, label_en}]}`, plus le bilan d'ouverture de B2 en 2027. C'est l'unique source de vérité comptable du parcours.
- **Outil** `tools/simulation/ledger.py` (Python pur, sans dépendance) : il calcule les balances mensuelles, les déclarations du 15 (avec `referentiel.calculs`), le tableau de passage, l'IS et les cases clés de la DSF. Il génère les pièces `balance` et `declaration`, et les tests vérifient qu'elles sont à jour.

**Règles dérivées (Simulation)** :
- **Balance officielle au début du mois M** : écritures du livre officiel datées avant le 1er du mois M.
- **Déclaration du 15 du mois M+1** : fonction des écritures du mois M et des paramètres 2026.
- **Résultat fiscal** : résultat comptable + réintégrations − déductions ; IS dû = max(IS calculé, minimum de perception) − acomptes − précomptes et retenues imputables.
- **Aucune donnée comptable par apprenant** (S2) : les réponses vivent uniquement dans `AttemptQuestion`, comme pour les autres formations.

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
| NFR-09 | Pièces à 390 px | aucun débordement horizontal de la page ; un tableau large défile dans son propre conteneur, accessible au clavier |
| NFR-10 | Outils de la simulation | `tools/simulation/` en Python standard, sans nouvelle dépendance (NFR-07), déterministe (même livre, mêmes sorties) |
| NFR-11 | Volume de la simulation | `content/simulation/` < 5 Mo par parcours ; disque total toujours < 150 Mo (NFR-01) |

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

**DoD-Parcours** (avant de publier un parcours de la simulation, en plus de DoD-Contenu et de DoD-Partie)
0. Le profil de l'entreprise a été validé par l'utilisateur avant la rédaction, et la validation est consignée dans le journal (S20). Le parcours A est déjà validé (S17).
1. Les 7 modules sont présents ; chaque mois contient 8 à 12 pièces datées (S4).
2. Le livre officiel est équilibré écriture par écriture ; chaque écriture cite une pièce existante ; chaque pièce sert au moins une fois (US-93).
3. Chaque question `journal` est identique à l'écriture officielle de sa pièce.
4. Les balances, les déclarations du 15, le tableau de passage et les cases de la DSF sont générés par `tools/simulation/ledger.py`, à jour et vérifiés par les tests.
5. Le bilan de clôture est équilibré ; le résultat du compte de résultat est égal à celui du bilan ; pour B2, le bilan d'ouverture du 1er janvier 2027 est équilibré.
6. Chaque taux utilisé est une clé de `parametres.csv` avec son article (US-95) ; aucun montant CNPS n'est calculé (S15).
7. Les garde-fous de vocabulaire (US-96) et de droits d'auteur (US-73) sont verts.
8. Parcours complet réussi en local, en FR puis en EN : sections, pièces, quiz, examen de 28 questions ≥ 70 %, certificat qui nomme le parcours, `/verify/<uuid>/`.
9. Capture Playwright à 390 px et à 1280 px, en mode clair et en mode sombre, d'une facture, d'un relevé Mobile Money, d'une balance et d'un formulaire de déclaration.

**DoD-Déploiement** (chaque mise en production)
1. Fusion `develop` → `main` ; `deploy.sh` s'exécute sans erreur sur `~/comptafiscaventisax`.
2. Test de fumée en production avec un compte de test jetable : connexion, section, quiz, langue EN.
3. Disque mesuré (`du -sh ~`) < 150 Mo et consigné dans le journal de déploiement.
4. `reference/` est absent du serveur et de git (`git ls-files reference` est vide).
5. Le journal des déploiements dans AGENTS.md est mis à jour : date, lot ou partie, mesure disque, écarts.
6. La prochaine échéance de « Run until 1 month from today » est notée.

**DoD-Documentation**
1. AGENTS.md est mis à jour (décisions, écarts, US) ; CLAUDE.md est régénéré comme miroir dans le même commit.
2. Chaque nouvelle décision d'architecture est ajoutée à la grille C (plateforme, Form 1 et 2) ou à la grille S (simulation), avec sa justification.

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

Questions ouvertes de la simulation, à trancher dans `docs/form3-conception.md` avant le premier code :
- **U14 Icône** — *résolue, validée le 2026-10-30* : icône Tabler `briefcase` (mallette), 3e valeur de `Formation.icon` (migration `courses 0010`).
- **U15 Manifeste** — *résolue* : une partie du manifeste peut déclarer `exam.questions_per_module`, `pieces` (chemin de `pieces.json`) et `ledger` (chemin de `ledger.json`).
- **U16 Volume minimal** — *validé le 2026-10-30* : le minimum de US-72 (12 questions d'examen, 8 de quiz par module) vaut aussi pour la simulation, B1 compris, et un test le vérifie ; soit 140 questions par parcours et environ 840 au total. Un minimum réduit pour B1 serait une nouvelle décision, et le coût d'import reste à mesurer (U8).
- **U17 Pièces dans les énoncés** — *résolue* : l'énoncé reste du texte échappé ; les filtres `prompt_text` et `prompt_pieces` (`simulation/templatetags/acad_pieces.py`) retirent la balise et affichent les pièces sous l'énoncé, en tentative comme dans la correction du quiz. L'espace formateur n'affiche que le texte.
- **U18 Identifiants fictifs** : format des NIU, RCCM et numéros Mobile Money, visiblement fictifs, pour ne jamais coïncider avec un vrai contribuable ou abonné.
- **U19 Articles à vérifier** — *résolue (S22 à S26 validées le 2026-10-30)* :
  - TVA des services exigible à l'encaissement : art. 134 (1) b ;
  - échéance de la DSF : art. 18 (1), 15 mars (DGE), 15 avril (CIME), 15 mai (centre de fiscalité locale) ; le « 15 mars » du brief ne vaut que pour la DGE (correction S22, validée) ;
  - l'art. 7 ne plafonne pas la valeur d'un véhicule de tourisme : il fixe des taux maximaux (25 % pour le matériel automobile léger utilisé en ville) ; il ne prévoit pas de limite de « cadeaux », mais la déduction des dons aux organismes d'intérêt général dans la limite de 0,5 % du chiffre d'affaires (5 % pour le sport d'élite) (correction S23 de la passerelle S21, validée) ;
  - IRCM : art. 70 ; IGS : art. C 39 et C 40 (10 classes, plafond exclu, moitié pour un Centre de Gestion Agréé) ;
  - seuils du SMT : absents de `reference/` (le Guide nomme le SMT sans en donner les seuils, l'AUDCIF n'y est pas) ; ils ne sont ni codés ni inventés (S26, validée) ;
  - seuils de rattachement au CIME : fixés par décision ministérielle (arrêté du 17 décembre 2013, art. 3), absente des sources ; chaque parcours déclare donc son `centre_impots`.
- **U20 TVA en attente** (parcours D, TVA à l'encaissement) — *résolue (S24, compte 471, validé le 2026-10-30)* : ni le plan révisé ni le Guide de `reference/` ne prévoient de compte de TVA en attente. Le parcours déclare `compte_tva_attente`, et les tests vérifient qu'il est soldé à l'encaissement du montant crédité en 4432 ; le compte retenu est 471.
- **U21 Sources des démarches hors fiscalité** (S28) — *close le 2026-10-30, recherche par Playwright sur les sites officiels ; la démarche MTN MoMo, sans liste publiée, n'est pas rédigée, conformément au 3e critère de US-97 ; décision validée par l'utilisateur le 2026-10-30* :
  - trouvés et cités par `[[source:clé]]` (registre `content/referentiel/sources.csv`, copies hors git dans `reference/officiel/`) : pièces à fournir au CFCE pour une SARL ou un établissement, et documents délivrés (MINFI) ; administrations compétentes par formalité (MINFI) ; rattachement CIME et DGE (DGI) ; AUDCIF (OHADA) ;
  - CNPS : FAQ officielle récupérée par sa copie archivée (web.archive.org, 10 juillet 2025), cnps.cm étant injoignable le 2026-10-30 : dossiers d'immatriculation employeur et travailleur (`[[source:cnps-faq]]`) ; elle cite le décret n° 2016/072 (pension : 8,4 %, dont 4,2 % salarial, plafond 750 000 FCFA). S15 reste appliquée : la plateforme ne calcule pas la CNPS, les montants viennent du bulletin ;
  - banque et Orange Money : pièces publiées par Société Générale Cameroun (`[[source:sg-cm-compte-entreprise]]`) et Orange Cameroun (`[[source:orange-om-partenaire]]`) ; elles servent de référence aux démarches, mais les pièces de la simulation restent émises par des organismes fictifs (« Banque X ») avec la mention « document pédagogique fictif » ;
  - MTN MoMo : aucune liste de pièces publiée pour le Cameroun (momo.mtn.cm injoignable, archives sans page marchand, page « MoMo Business » de momo.mtn.com générique) ; la démarche MTN n'est pas rédigée, seule celle d'Orange Money l'est ; les frais du CFCE (41 500 et 13 125 FCFA) datent d'une page de 2022 environ et seront marqués « à vérifier » ;
  - état initial : `reference/` ne contient que le CGI, le Guide et le plan SYSCOHADA. Les démarches au greffe (RCCM : AUSCGIE, AUDCG), à la CNPS (code de sécurité sociale), au notaire ou auprès des banques et opérateurs Mobile Money exigent leurs textes officiels ou les listes publiées par ces organismes ; sans eux, la démarche n'est pas rédigée plutôt qu'inventée. Les démarches fiscales (immatriculation art. L 1, déclarations, attestations) s'appuient sur le CGI.

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

## Grill S — Form 3 « Simulation Compta et Fisca » (2026-10-29, clos)

> Brief : simuler sur 12 mois (création, exploitation mensuelle avec échéance fiscale du 15, inventaire, passerelle fiscale et DSF avant le 15 mars) la vie de quatre entreprises camerounaises fictives, à partir de pièces justificatives virtuelles. Livrables demandés : syllabus par phase, scénario de janvier de la boutique de vêtements (pièces et corrigé), matrice plan de comptes et taux 2026.
> Rien n'est implémenté tant que le grill n'est pas clos. Chaque réponse devient une décision S-xx.

Faits établis avant le grill (vérifiés dans le dépôt et le CGI 2026) :
- Le brief contredit le hors-scope v1 (« toute autre formation que Comptabilité et Fiscalité »).
- Form 1 = formation `compta` (5 parties, 29 modules, 174 h) ; Form 2 = formation `fisca` (3 parties).
- Le CGI 2026 traite le régime simplifié, le précompte sur achats, la retenue de 5,5 % (fait générateur : la facturation de la prestation) et la DSF ; « VSD » n'y figure pas, et aucun taux de 11 % n'y a été trouvé.
- `parametres.csv` ne contient ni précompte, ni retenue à la source, ni droits d'accises par produit.
- Le SYSCOHADA révisé n'immobilise plus les frais d'établissement ; le plan contient 4094, 4194 et 2493 (emballages récupérables).

### Tour 1 (frontière)

| # | Question | Recommandation | Réponse |
|---|---|---|---|
| S-Q1 | Form 3 devient-elle une 3e formation de la même plateforme (préfixe `S`), ce qui amende le hors-scope v1 ? | Oui, 3e formation `simulation`, préfixe `S`, masquée (`is_open=False`) jusqu'à complétude. | Oui (S1). |
| S-Q2 | Modèle d'état : les écritures de l'apprenant se propagent-elles (grand livre personnel, erreurs reportées jusqu'à la DSF) ou chaque étape repart-elle de l'état officiel corrigé ? | État officiel à chaque étape : questions `journal` existantes, balance officielle affichée en début de mois ; pas de grand livre par apprenant. | Oui (S2). |
| S-Q3 | Parcours sectoriels : le brief a deux « A » ; la ligne 3 mêle commerce d'électronique et prestations de clim, avec « 1 enseignant fonctionnaire ». Quelle est la liste exacte, et quel est le rôle du fonctionnaire ? | 4 parcours : A vêtements (SARL, réel) ; B boissons (simplifié) ; C commerce d'électronique et pose de clim (SARL, réel) ; D prestataire clim (Ets, personne physique). Le fonctionnaire est un salarié vacataire (formateur), pas un associé. | Corrigée : le fonctionnaire est associé à 80 %, la gérance est confiée à un tiers non fonctionnaire, et il est formateur vacataire ponctuel. B est revu au tour 2 (S3, S9). |
| S-Q4 | Volume et ordre : 4 parcours × 12 mois × pièces quotidiennes dépassent les budgets disque et CPU. Quel ordre de livraison, et combien de pièces par mois ? | Parcours A complet d'abord (création → DSF), 8 à 12 pièces datées par mois ; B, C, D ensuite, un par déploiement. | Oui (S4). |
| S-Q5 | Format des pièces : Markdown, SVG généré en Python ou image/PDF ? | Pièces décrites en JSON structuré et rendues en HTML par une balise `[[piece:ID]]` (facture, reçu Mobile Money, relevé), sans fichier binaire. | Oui (S5). |
| S-Q6 | Jour 1 « frais d'établissement » : charges de l'exercice (SYSCOHADA révisé) et piège pédagogique explicite ? | Oui : charges par nature (frais d'acte, enregistrement, honoraires), et le piège de l'ancienne immobilisation est signalé dans le corrigé. | Oui (S6). |
| S-Q7 | Que désigne « VSD » (absent du CGI 2026) ? | Le retirer et nommer les obligations du CGI : TVA, acompte d'IS (minimum de perception), retenues sur salaires, précompte. | Oui (S7). |
| S-Q8 | Où vont les trois livrables demandés : document de conception (`docs/`) ou directement en contenu importable (`content/simulation/`) ? | Document de conception `docs/form3-conception.md` à valider d'abord, puis conversion en contenu. | Oui (S8). |

### Tour 2

| # | Question | Recommandation | Réponse |
|---|---|---|---|
| S-Q9 | Le régime simplifié a été supprimé par la LF 2026 et remplacé par l'IGS (art. 69, 91, 93 nonies). Quel régime pour le dépôt de boissons ? | SARL au réel. | Trois cas : B1 à l'IGS, B2 de l'IGS à la SARL au réel, B3 SARL au réel (S9). |
| S-Q10 | Retenues subies par D : 5,5 % (5 % + CAC, clients publics, art. 21 (2)) ; 11 % (10 % + CAC) est réservé aux entreprises absentes du fichier. | 5,5 % au réel, avec une pièce de contraste à 11 %. | Oui (S10). |
| S-Q11 | Découpage : avec 10 questions tirées par module, l'examen compterait 150 questions. | Une partie par parcours, 7 modules, les mois en sections, 4 questions tirées par module. | Oui (S11). |
| S-Q12 | Déclarations et DSF : nouveau type de question ou questions numériques ? Quelle étendue pour la DSF ? | Questions numériques sur les cases clés, formulaire en lecture seule ; DSF limitée au bilan, au compte de résultat, au tableau de passage et à l'IS. | Oui (S12). |

### Tour 3

| # | Question | Recommandation | Réponse |
|---|---|---|---|
| S-Q13 | Le régime se fixe sur le chiffre d'affaires annuel, sans bascule en cours d'année (art. 93 quater). Comment construire B2 ? | Année 2026 à l'IGS, puis bascule après la clôture vers une SARL au réel au 1er janvier 2027 ; B1 est la même année sous le seuil. | Oui (S13). |
| S-Q14 | Système comptable de B1 ? | SMT de l'AUDCIF, questions numériques. | Oui (S14). |
| S-Q15 | Les taux CNPS n'ont pas de source officielle (C28). Comment les traiter ? | Montants CNPS sur le bulletin ; l'apprenant calcule les impôts du CGI. | Oui (S15). |
| S-Q16 | Vacations du fonctionnaire de C ? | Honoraires (632), avec la retenue de 5 % de l'art. 92 bis si la SARL figure sur la liste ; dividendes et IRCM. | Oui (S16). |

### Tour 4

| # | Question | Recommandation | Réponse |
|---|---|---|---|
| S-Q17 | Profil de la SARL A ? | Ngono Mode SARL, Douala-Akwa, capital de 5 M, chiffre d'affaires d'environ 90 M, 3 salariés, une importation en T3. | Oui (S17). |
| S-Q18 | Système d'inventaire de A ? | Intermittent, avec des fiches CMUP et un exercice de contraste en PEPS. | Oui (S18). |
| S-Q19 | Trésorerie ? | Un sous-compte par moyen de paiement, frais en 631, virements internes en 585, rapprochement mensuel. | Oui (S19). |
| S-Q20 | Ordre de livraison ? Quand fixer les profils de B, C et D ? | A → B3 → C → D → B1 → B2 ; chaque profil est validé au début de son parcours. | Oui (S20). |
| S-Q21 | Passerelle de A ? Prérequis ? | Jeu standard de 6 éléments ; prérequis indicatif après Form 1 et 2. | Oui (S21). |

Frontière vide : grill clos. Les décisions S1 à S21 sont reportées dans GOALS (1.6, 1.7, 2 et 3), en attente de validation.

### Décisions après vérification des sources (2026-10-30)
Ce sont des corrections imposées par le CGI et des choix par défaut, validés par l'utilisateur le 2026-10-30 (« garde les réponses par défaut »).

| # | Décision | Statut |
|---|---|---|
| S22 | La DSF est datée selon le centre de rattachement (CGI art. 18 (1) : 15 mars DGE, 15 avril CIME, 15 mai centre de fiscalité locale) et non toujours au 15 mars. | Validée (2026-10-30) |
| S23 | Passerelle de A : « amortissement d'une voiture légère au-delà du taux fiscal maximal de 25 % » et « dons au-delà de 0,5 % du CA » remplacent le plafond du véhicule et les cadeaux (CGI art. 7). | Validée (2026-10-30) |
| S24 | TVA à l'encaissement de D : compte d'attente 471 « Débiteurs et créditeurs divers », soldé en 4432 à l'encaissement (U20). | Validée (2026-10-30) |
| S25 | Ngono Mode SARL relève du CIME ; DSF 2026 au plus tard le 15 avril 2027. Confirmé par la DGI : CIME de 50 millions à 3 milliards de CA, DGE au-delà (impots.cm, 2026-10-30) ; chaque parcours déclare son `chiffre_affaires_vise`, et le centre déclaré doit lui correspondre. | Validée, confirmée par la source |
| S26 | Un parcours à l'IGS déclare `systeme_comptable: "smt"` et reste sous le seuil du SMT de l'AUDCIF art. 13 (négoce sous 60 millions, artisanat 40, services 30), trouvé le 2026-10-30 au JO OHADA du 15 février 2017. | Validée, seuils codés |
| S27 | Factures au style camerounais réel (identité fiscale complète, NIU au format DGI, référence de facturation électronique DGI, CGI art. 143 (1) b) ; entreprises fictives, mention « document pédagogique fictif » sur chaque pièce. | Demande de l'utilisateur, 2026-10-30 |
| S28 | Décisions d'organismes extérieurs décrites en pièces « démarche » (organisme, objet, documents à fournir, document obtenu, source officielle) pour être refaites en réalité. | Demande de l'utilisateur, 2026-10-30 |
| S29 | Nouveau parcours E, livré juste après A : SARL à l'IGS de prestations de climatisation et froid et de vente de matériel ; gérant 20 %, fonctionnaire 80 % ; CA visé sous 30 millions (IGS et SMT). | Validée (2026-11-01) |
| S30 | Le fonctionnaire travaille pour la SARL comme vacataire payé en honoraires (632), jamais comme salarié (statut général de la fonction publique). | Validée (2026-11-01) |
| S31 | Capital minimal de 100 000 FCFA (loi n° 2016/014 art. 2) ; le fonctionnaire finance le démarrage, environ 1 500 000 FCFA au total, en compte courant d'associé (4621). | Validée (2026-11-01) |
| S32 | Profil de B3 : Ateba Boissons SARL, Yaoundé-Mvog-Ada, capital de 10 000 000 FCFA, réel, CIME (CA visé environ 280 millions ; prix et volumes réalistes : marge de quelques centaines de francs par casier, d'où un IS inférieur au minimum de perception) ; brasserie fictive, accises comprises dans le prix (art. 142 (9)), précompte de 2 % (art. 21 (3)) ; la bière n'est pas un produit à marge administrée (art. 21 (1) c), acompte normal ; consignes 4094 et 4194, mali 6224 et boni 7074 (Guide, 1re partie, ch. 2) ; casiers propres en **243** (2493 est la ligne « en cours » du plan révisé, ce qui corrige le libellé de GOALS) ; camion 2451 et emprunt de 12 000 000 (162) ; passerelle : amende, charge sans pièce, dons au-delà de 0,5 %, IS comparé au minimum de perception. | Validée (2026-11-01) |
| S33 | Visuels de la simulation : scènes isométriques dessinées avec le skill anatomy, exportées en SVG statiques FR et EN (`static/content/simulation/<parcours>/`, générateur `tools/figures/`), sans script ; Node sert seulement à écrire le contenu, jamais en production. Amende C13 : toujours aucune figure interactive. | Demande et choix de l'utilisateur (2026-11-01) |
| S34 | Récit pédagogique : chaque mois est raconté scène par scène (personnages récurrents ; ce qui se passe, la règle et sa source, pourquoi ce choix plutôt qu'un autre, ce que ça change, renvoi au module du cours), suivi d'un bilan ; règles dans `docs/form3-conception.md`, section 5. Pilote : janvier de B3, à valider avant d'étendre à B3, puis de reprendre A et E. | Demande et choix de l'utilisateur (2026-11-01) |
| S35 | Profil de C : Tech Clim Bonamoussadi SARL, Douala, capital de 2 000 000 FCFA (fonctionnaire associé à 80 %, tiers à 20 %, statuts notariés), gérance confiée à un tiers non fonctionnaire salarié ; réel, CIME (CA visé environ 120 millions) ; vente d'appareils (7011) et pose de climatiseurs (706) ; vacations du fonctionnaire en honoraires (632), sans retenue de l'art. 92 bis (la SARL n'est pas sur la liste), expliquée en contraste ; inventaire CMUP, provision pour garantie (192, déductible : CGI art. 7 E) ; IS au taux réduit comparé au minimum ; assemblée de juin 2027 (AUSCGIE art. 346 et 348) : réserve légale, dividendes, IRCM de 15 % + CAC (CGI art. 70). | Validée (2026-11-02) |
| S36 | Profil de D : Ets Tchinda Froid, établissement individuel de Jean-Claude Tchinda, technicien frigoriste, à Yaoundé-Biyem-Assi ; réel, CIME (CA visé environ 65 millions, au-dessus du seuil de 50 millions de l'IGS, art. C 39) ; un aide-technicien salarié et une camionnette ; entretien et dépannage (706) pour des clients publics et privés ; TVA à l'encaissement (art. 134 (1) b, compte d'attente 471, S24) ; retenue de 5,5 % sur les factures publiques de moins de 5 millions (art. 21 (2)) et pièce de contraste à 11 % ; IRPP sur les BIC au barème, comparé au minimum ; prélèvements de l'exploitant ; DSF au 15 avril 2027. | Validée (2026-11-02) |

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

### 2026-10-29 — Socle backend de la formation Simulation (Form 3), en TDD, non commité
Chaque règle a été écrite après un test rouge, puis vérifiée par mutation.
- US-82, modèle `Piece` (app `simulation`, migration `0001_piece`) :
  - validation arithmétique (`Piece.clean`, `payload_errors`) ;
  - rendu `[[piece:REF]]` après bleach, valeurs échappées, langue courante, référence inconnue en `<mark class="piece-missing">` ;
  - CSS NFR-09 (défilement dans le cadre).
- Import :
  - pièces de `pieces.json`, de façon idempotente, une pièce incohérente annulant tout l'import ;
  - `Question.pieces` (migration `assessments 0010`) renseigné depuis l'énoncé, une pièce inconnue annulant l'import ;
  - `exam.questions_per_module` lu dans le manifeste (US-94, U15).
- US-83 (U17) : pièce affichée sous l'énoncé pendant la tentative et dans la correction du quiz ; balise retirée dans l'espace formateur.
- US-95 :
  - un taux sans article est refusé par `import_parameters` ;
  - 8 taux ajoutés à `parametres.csv` et vérifiés dans le CGI 2026 : précompte de 2, 5 et 10 % (art. 21 (3)), retenue sur la commande publique (art. 21 (2)), retenue sur honoraires (art. 92 bis), accises sur la bière de 65 et 33 cl (art. 142 (9)), IRCM (art. 70).
  - Les tarifs IGS ne sont pas encore ajoutés (U19).
- US-93, US-84, US-85, US-89 : outil `tools/simulation/ledger.py`, en Python standard :
  - contrôle des écritures, pièces inutilisées, balance avant une date et pièce `balance` générée ;
  - déclaration du 15 (TVA avec crédit reporté, acompte d'IS au minimum de perception CAC compris, précompte 4492 imputé, retenues 447) ;
  - résultat comptable, passerelle, cohérence des questions `journal` avec le livre officiel.
- Garde-fous de contenu (`scan_content`, préfixe `S`) :
  - livre officiel équilibré, pièces cohérentes et toutes utilisées ;
  - clé `journal` égale à l'écriture officielle, balances publiées égales au calcul ;
  - réponses de déclaration (`declaration: {period, field}` dans `questions.json`) égales au calcul de l'outil ;
  - vocabulaire « VSD » et « régime simplifié » (US-96).
- Écarts par rapport au PRD :
  - un seul `payload` bilingue au lieu de `payload_fr` et `payload_en`, pour ne jamais dupliquer les montants ;
  - la balise `[[piece:]]` est remplacée après `[[calc:]]`, en fin de pipeline (C27 étendu) ;
  - US-94, le certificat affiche déjà « Formation : Partie », le parcours est donc nommé par le titre de sa partie, sans code nouveau ;
  - US-80 : icône `briefcase` retenue pour régler U14, validée le 2026-10-30.
- i18n : chaînes EN ajoutées, `makemessages` et `compilemessages` à jour.
- Stories restantes, ajoutées après un contrôle de complétude, chacune en TDD :
  - US-80 : `manifest_problems` exige pour le préfixe S l'icône `briefcase`, un prérequis FR et EN, 7 modules par parcours et `exam.questions_per_module` = 4 ;
  - US-81 : la première section d'un parcours (dossier d'entreprise) affiche ses taux par `[[param:]]` et son plan par `[[syscohada:]]`, en FR et en EN ;
  - US-86 : `ledger.account_balance` et `ledger.reconciliation_gap` ; une question `rapprochement: {account, date[, releve]}` attend le solde comptable ou l'écart avec le relevé ;
  - US-87 : les frais portés par une pièce `statuts` ne sont jamais débités en classe 2 ;
  - US-88 et US-92 : une question `calcul: {fonction, args, resultat}` attend le résultat d'une formule de `referentiel.calculs` (liste fermée) ; nouvelle formule `retenue_source` (5 % + CAC = 5,5 % ; 10 % + CAC = 11 %, CGI art. 21 (2)) ;
  - US-92 : avec `tva_encaissement`, le compte 4432 n'est crédité que sur une pièce de règlement ;
  - US-90 et US-91 : `regime` ∈ {reel, igs, igs_puis_reel} ; à l'IGS, ni question `journal` ni compte de TVA ; B2 n'a en 2027 que des écritures du 1er janvier (bilan d'ouverture).
- Clés de manifeste ajoutées par partie : `pieces`, `ledger`, `exam`, `regime`, `tva_encaissement`. Clés de question ajoutées : `declaration`, `rapprochement`, `calcul`.
- Critères d'acceptation restants, après un second contrôle de complétude, chacun en TDD :
  - US-83 : en examen, ni écriture officielle ni formulaire corrigé ; pendant la tentative, seules les pièces de l'énoncé s'affichent ;
  - US-85 : la correction du quiz affiche les pièces citées par l'explication (formulaire rempli, filtre `explanation_pieces`) ; l'import relie aussi ces pièces, et une pièce inconnue de l'explication annule l'import ;
  - US-87 : un parcours qui a des frais de constitution porte une question `piege: "frais_etablissement"` ;
  - US-88 : toute dotation calculée par une question figure au 31 décembre dans le livre officiel (débit 681) ;
  - US-89 : `ledger.corporate_tax` retient le plus élevé de l'IS et du minimum de perception (`referentiel.calculs.impot_societes`), impute les acomptes et sépare l'excédent ;
  - US-90 : le dossier d'un parcours à l'IGS cite `[[param:precompte.taux_igs]]` et `[[cgi:art. 93 quater]]` ; les tarifs de l'IGS restent à vérifier (U19) ;
  - US-95 : aucune clé `cnps.*` n'est admise dans `parametres.csv` ;
  - US-80 : la description FR et EN de chaque parcours cite son régime ;
  - US-81 : le dossier du parcours A présente Ngono Mode SARL, en FR et en EN ;
  - US-94 : la vérification publique et le PDF nomment « Formation : Parcours » ; ce comportement existait déjà et il est prouvé par mutation.
- `tools/mutation_sweep.py` accepte un filtre par préfixe de story ; 51 mutations de la simulation, toutes détectées.
- Troisième contrôle de complétude, en TDD :
  - US-90 (U19) : `referentiel.calculs.igs_annuel` (art. C 40 : plafond de classe exclu, moitié pour un Centre de Gestion Agréé, réel à partir de 50 000 000) et 20 paramètres `igs.classeN_plafond` et `igs.classeN_montant`, chacun avec son article ; formule ouverte aux questions `calcul` ;
  - US-88 : le stock final valorisé par une question (CMUP ou PEPS) figure au 31 décembre au débit d'un compte 3 ;
  - US-89 : une question `calcul` sur `impot_societes` est contrôlée, minimum de perception compris ;
  - U16 : un test vérifie que les modules de la simulation sont soumis au minimum de US-72 ;
  - US-73 et US-96 revérifiés par mutation ; 15 mutations de ce passage, toutes détectées.
- Balayage complet du 2026-10-30 : 121 mutations (plateforme et simulation), toutes détectées ; les stories plateforme [N] (US-14, 15, 23 à 28, 34 à 36, 61 à 63, 70 à 74) sont donc revérifiées.
- Quatrième contrôle de complétude, en TDD, après vérification des sources (U19, U20) :
  - 4 paramètres de l'art. 7 (taux maximal du véhicule léger en ville, limites des dons, seuil du petit matériel) ;
  - `referentiel.calculs.reintegration_amortissement` et `reintegration_dons`, ouvertes aux questions `calcul` ;
  - `ledger.tax_return_deadline` (art. 18 (1), art. C 41) ; chaque parcours déclare `centre_impots` et sa déclaration de l'exercice est datée au plus tard à l'échéance ;
  - `compte_tva_attente` exigé avec la TVA à l'encaissement et soldé à chaque encaissement ;
  - 7 mutations de ce passage, toutes détectées.
- Décisions par défaut S24 à S26 codées en TDD : le compte d'attente doit exister au plan, A doit être rattaché au CIME, un parcours à l'IGS déclare le SMT ; 3 mutations, toutes détectées.
- S27 et S28 (demande de l'utilisateur du 2026-10-30), en TDD : type de pièce `demarche` (migration `simulation 0002`), `realism_errors` (identité de l'émetteur, NIU au format DGI, numéro, client, référence de facturation électronique, champs d'une démarche), rendu de l'identité fiscale, de la liste des documents et de la mention « Document pédagogique fictif », contrôle de réalisme appliqué au contenu ; 6 mutations, toutes détectées. Critères restants du PRD (ordre et ouverture des parcours, calculateurs du module Inventaire, six éléments de la passerelle de A, tableaux de la DSF) : 5 mutations, toutes détectées.
- Traçabilité E9 automatisée (`test_prd_traceability.py`) : elle a révélé que US-97 n'était citée par aucun test (seulement S28) ; corrigé.
- Traçabilité au niveau des critères : elle a révélé trois critères sans test, codés en TDD : US-97 (la source d'une démarche cite un texte officiel), US-90 (pas de DSF normale à l'IGS), US-92 (contraste de la retenue à 11 % dans le parcours D) ; 5 mutations, toutes détectées.
- Sources officielles (demande de l'utilisateur du 2026-10-30, Playwright) : paramètres `smt.*` (AUDCIF art. 13) et `dgi.seuil_cime`, `dgi.seuil_dge` ; `ledger.tax_office` ; balise `[[source:clé]]` et registre `sources.csv` ; contrôles du centre déclaré et du seuil du SMT selon `chiffre_affaires_vise` ; 8 mutations, toutes détectées.
- Contrôle de contenu : toute balise `[[source:]]` doit figurer au registre `sources.csv` (US-97) ; 1 mutation, détectée.
- Sources Orange Money et Société Générale Cameroun enregistrées (test d'abord en échec).
- S19 : sous-comptes propres à l'entité (`sous_comptes` du manifeste, ex. 5521 MTN MoMo, 5522 Orange Money) admis s'ils subdivisent un compte du plan, créés dans `SyscohadaAccount` à l'import, utilisables par le livre officiel et les questions `journal` ; 3 mutations, toutes détectées.
- Traçabilité renforcée : chaque test associé à un critère d'acceptation doit contenir des assertions et ne pas être ignoré (`test_every_criterion_test_makes_assertions`, mutation détectée). Document de conception : CNPS patronale de la branche pensions (4,2 %, décret n° 2016/072) ajoutée au bulletin et au corrigé ; prestations familiales et accidents du travail non simulés faute de source ; section 4 entièrement réglée.
- Parcours A rédigé (validation du document de conception par l'utilisateur le 2026-10-30) : générateur déterministe `tools/simulation/build_parcours_a.py` → `content/simulation/` (178 pièces, 157 écritures, 209 questions bilingues, 7 modules, 492 Ko). Tous les montants viennent des outils testés ; les contrôles bloquants ne signalent rien ; `simulation/tests/test_parcours_a_content.py` importe les référentiels et le parcours, publie toutes les questions et vérifie qu'aucune section ne rend de balise inconnue. Chiffres 2026 : CA 90 000 000, résultat avant impôt 34 604 175, IS 9 788 350 (taux réduit de 25 %, art. 17 bis).
  - correction de l'outil, en TDD : la déclaration du 15 compte la TVA facturée au crédit, la TVA déductible au débit et les retenues au crédit ; le règlement du mois précédent ne la fausse plus (mutation détectée) ;
  - taux `precompte.taux_loyer` (10 %, CGI art. 87) ajouté en TDD pour le bail ;
  - écarts au profil S17 : pas d'importation au T3 (droits de douane non sourcés) ; CNPS patronale limitée à la branche pensions (4,2 %, décret n° 2016/072) ; démarche MTN MoMo non rédigée (U21) ;
  - DoD-Parcours, parcours sur une base jetable avec un compte de test local (2026-11-01) :
    - point 8 fait : sections et quiz du module 1 en navigateur à 390 px (Playwright) ; six autres quiz et examen de 28 questions répondus par les services de l'application (100 %) ; certificat émis ; vérification publique et PDF servis en FR et en EN, parcours nommé, score affiché ; les 17 sections servies en FR et en EN sans balise inconnue ;
    - trois défauts d'affichage trouvés à 390 px et corrigés en TDD (NFR-09, mutations détectées) : la grille des questions et celle de la correction s'élargissaient au tableau d'une pièce (débordement de la page) ; l'identité d'une facture écrasait la colonne des valeurs (une lettre par ligne) ;
    - point 9 fait : 16 captures (facture, relevé Mobile Money, balance, déclaration ; 390 et 1280 px ; clair et sombre) prises avec Chrome sans interface sur les pages réelles, Playwright s'étant déconnecté ; elles ont révélé un en-tête « Libellé » vide sur les pièces sans lignes, retiré en TDD ;
    - point 1 tenu, en TDD : `pieces_per_month_problems` exige 8 à 12 pièces comptables par mois sur un parcours complet (démarches exclues) ; le parcours A en avait 13 à 17 ; le relevé bancaire mensuel porte désormais le virement au fournisseur, les salaires, le transfert Mobile Money et les échéances de la voiture, et une seule fiche de stock couvre les trois familles (137 pièces, mêmes 157 écritures et mêmes chiffres) ;
  - la DoD-Parcours du parcours A est remplie ; la formation reste fermée (`open: false`) jusqu'à la décision de l'ouvrir.
- Parcours E (S29 à S31) : ordre de livraison A → E → B3 → C → D → B1 → B2 codé en TDD ; capital minimum de la SARL (100 000 FCFA, loi n° 2016/014 art. 2), part minimale (5 000) et seuil du notaire facultatif (1 000 000, art. 4) ajoutés en paramètres, en TDD, avec les sources `loi-2016-014` (Assemblée nationale, copie certifiée conforme) et `ohada-auscgie` (art. 311 et 311-1).
- Parcours E rédigé (2026-11-01) : générateur déterministe `tools/simulation/build_parcours_e.py` (il réutilise `Book` du parcours A, désormais paramétré par la lettre du parcours, et `write_manifest`, qui fusionne la partie dans `formation.json` sans écraser les autres) → `content/simulation/e/` (104 pièces, 87 écritures, 178 questions bilingues, 7 modules, 303 Ko). Froid Équipe Services SARL, Douala-Logbaba, IGS et SMT, centre de fiscalité locale : capital de 100 000 (1013), avance de 1 400 000 en 4621 remboursée par 100 000 de juillet à décembre, outillage en 6056, achats au fournisseur au réel avec TVA non déductible et précompte de 5 % (4492), interventions sans TVA (7061) encaissées par banque et Orange Money (5522), ventes au comptant (7011), vacations du fonctionnaire en 632, rapprochements, fiche de stock (CMUP et contraste PEPS), déclaration annuelle de l'IGS au 15 mars 2027. Chiffres 2026 : CA 18 960 000, IGS 500 000 (art. C 40). Aucune question `journal` (S14) ; contrôles bloquants sans défaut ; `simulation/tests/test_parcours_e_content.py` importe et publie A et E.
- Tests : 942 verts ; `makemigrations --check` et `check` sans remarque. `check --deploy` n'a pas été relancé (il exige les réglages de production).
- Reste : DoD-Parcours en navigateur du parcours E (points 8 et 9) ; la formation reste fermée (`open: false`).
- Déploiement de la formation Simulation, fermée (2026-11-01) : `main` = `d454acf`, `deploy.sh` EXIT=0 ; migrations `simulation 0001` et `0002`, `assessments 0010`, `courses 0010` appliquées ; 1 340 comptes, 105 paramètres ; compta 59 sections et 580 questions, fisca 16 et 160, simulation 33 sections et 387 questions publiées (A et E) ; `check` sans problème ; disque 92 Mo. Fumée : `/fr/`, `/en/` et catalogue en 200 sans la Simulation, sa fiche en 404 (fermée), vérification d'un UUID inconnu en 404, aucune erreur console ; avec un compte jetable (supprimé, LEFT 0), section en FR et en EN puis quiz de Compta M1 jusqu'au résultat, à 360 px, sans débordement. Pages de la Simulation non vérifiées en production, la formation étant fermée. Prochaine échéance « Run until 1 month from today » à vérifier dans l'onglet Web.
- Ouverture de la Simulation (décision de l'utilisateur, 2026-11-01), en TDD : le test du parcours A attend une formation ouverte (rouge), puis `open: true` dans le générateur et le manifeste (vert). Générateurs couverts par `test_parcours_generators.py` (pièces et questions nommées par la lettre du parcours ; `write_manifest` garde les autres parcours dans l'ordre de livraison) : chaque règle cassée fait échouer son test, puis le restaure ; deux mutations ajoutées à `tools/mutation_sweep.py`. Le balayage US-80 à US-97 a été interrompu par la fin de session et a laissé une mutation dans `content_rules.py`, restaurée avant tout commit. Tests : 944 verts. Le parcours E est ouvert sans ses points 8 et 9 de DoD-Parcours en navigateur, à faire.
- Déploiement de l'ouverture (2026-11-01) : `main` = `f90edb6`, `deploy.sh` EXIT=0 (rien de nouveau à publier) ; disque 92 Mo. Fumée : la Simulation figure au catalogue ; son programme répond en 200 en FR et en EN, avec A, E et le prérequis indicatif, sans débordement à 360 px ; avec un compte jetable (supprimé, LEFT 0), trois sections de E (dossier d'entreprise, démarches, janvier) servies en FR et en EN à 390 px : 4 démarches et 10 pièces rendues, mention « fictif » sur chacune, aucune balise brute ni inconnue, aucune erreur console. Quiz et examen de la Simulation non joués en production.

### 2026-11-01 (soir) — Parcours B3 et récit des parcours A, B3 et E, non commité
- Mutation laissée par le balayage interrompu dans `courses/tests/content_rules.py` (`if False:`), restaurée. Un balayage `tools/mutation_sweep.py US-8 US-9`, lancé à 18 h 47 par l'agent avant une remise à zéro de son contexte, tournait encore en fin de session : les tests ont été exécutés sur une copie propre de l'arbre (sources de règles reprises de `HEAD`), et chaque génération a été encadrée d'un contrôle `git diff` de `ledger.py` et `calculs.py`.
- Parcours B3 (S32) : `tools/simulation/build_parcours_b3.py` → `content/simulation/b3/` (138 pièces, 164 écritures, 236 questions bilingues, 7 modules). Vérification de la réalité camerounaise : prix ramenés à la marge réelle d'un dépôt (65 cl vendu 6 580 HT, environ 654 FCFA la bouteille TTC ; prix conseillé de 650 FCFA au bar, presse 2024) ; droit d'accises de 25 % et droit spécifique additionnel de l'art. 142 (9), la facture ne montrant que le second ; livraisons en plusieurs tournées ; fonds du capital bloqués jusqu'à l'immatriculation (AUSCGIE art. 313 et 314), d'où loyer et notaire payés le 6 janvier. Chiffres 2026 : CA 286 098 000, résultat avant impôt 1 890 280, IS calculé 562 100 inférieur au minimum de perception 6 294 156 (dû), perte nette 4 403 876. Consignes au montant fictif (aucune source publiée) ; ristournes des brasseries non modélisées.
- Récit (S34) : `tools/simulation/narrative_b3.py`, `narrative_a.py`, `narrative_e.py`. Chaque mois de chaque parcours est raconté scène par scène en cinq temps (ce qui se passe, la règle et sa source, pourquoi ce choix plutôt qu'un autre en encadré, ce que ça change, où ça se range, renvoi au module du cours), avec accroche, balance d'ouverture et bilan ; inventaire, passerelle et DSF (ou IGS annuel pour E) aussi. Dossier d'entreprise : personnages, outils (logiciel comptable, classeurs, brouillard de caisse, fiches de stock, cahier des vides ou cahier des recettes et dépenses au SMT) et routines du soir, de la semaine, du mois, du trimestre et de l'année, d'après l'AUDCIF art. 17, 19, 20, 22 et 24. Les explications des questions `journal` reprennent le « pourquoi » de la scène. Test `simulation/tests/test_simulation_narrative.py` : toute pièce comptable d'un mois est dans une scène aux cinq temps, en FR et en EN.
- Figures (S33) : `tools/figures/b3_scenes.mjs` (kit anatomy recopié dans `tools/figures/kit/`) → `static/content/simulation/b3/circuit-casiers` et `trois-caisses`, FR et EN, SVG statiques sans script, qui suivent le thème du système.
- Interface (skill design-taste-frontend) : titres de scène séparés, « pourquoi » en encadré teal, figures de la simulation en pleine largeur, espace fine insécable avant `; : ? !` en français ; vérifié à 1280 et 390 px, clair et sombre, sans débordement.
- Réalisme de A et E : litige de A avec le propriétaire voisin (et non un « ancien bailleur » d'une société créée en janvier) ; recette en espèces de A versée chaque semaine et récapitulée en fin de mois (au lieu du 25 du mois suivant) ; pièces commerciales et bancaires d'un dimanche reportées au lundi (`workday`). Chiffres de A inchangés (CA 90 000 000, résultat 34 604 175, IS 9 788 350).
- Point à vérifier avant B2 : le CGI 2026, art. C 39 (2), prévoit le reclassement d'office au réel en cas de dépassement du seuil de l'IGS « au cours d'un exercice fiscal », ce qui semble contredire S13 (aucune bascule en cours d'année, art. 93 quater).
- Reste : contrôle bloquant du récit dans `content_rules.py` (à écrire une fois le balayage terminé) ; DoD-Parcours points 8 et 9 en navigateur pour B3 ; commit et déploiement.
- Déploiement de B3 et du récit des parcours A, B3 et E (2026-11-01) : `main` = `b6ff09e`, `deploy.sh` EXIT=0 (première frappe perdue par la console, commande retapée) ; aucune migration ; 1 340 comptes, 105 paramètres ; compta 59 sections et 580 questions, fisca 16 et 160, simulation 50 sections et 623 questions (A 209, E 178, B3 236), 359 republiées ; `check` sans problème ; disque 98 Mo. Fumée : accueil redirigé vers la connexion (comportement existant), catalogue 200, programme de la Simulation avec le parcours B3 en FR et en EN, vérification d'un UUID inconnu en 404, figures SVG et CSS servies (200), `http://` redirigé vers `https://` (302) ; avec un compte jetable (supprimé, LEFT 0), janvier de B3, A et E servi en FR et en EN à 360 px : 11 ou 12 scènes, encadrés présents, aucune balise inconnue, figures de B3 chargées, aucun débordement, aucune erreur console. Quiz, examen et certificat de B3 non joués en production.
- Balayage de mutations US-8 et US-9 terminé : 61 mutations détectées ; 14 signalées parce que la suite témoin (GREEN) était elle-même rouge pendant la génération en cours de B3, et un motif périmé (US-90, liste des formules ouvertes au contenu) corrigé dans `tools/mutation_sweep.py`. Les stories concernées (US-80, 81, 87 à 90, 95, 97) ont été rejouées sur l'arbre stable : 39 mutations, toutes détectées, suite témoin verte à chaque fois.
- Contrôle bloquant du récit (S33, S34), en TDD : `narrative_problems` dans `courses/tests/content_rules.py` refuse, dans une section mensuelle, toute pièce comptable affichée hors d'une scène aux cinq temps (FR et EN), tout renvoi « Revoir » vers un module inexistant et toute figure absente de `static/` ; cinq tests, quatre mutations ajoutées à `tools/mutation_sweep.py`, toutes détectées.
- DoD-Parcours de B3 (2026-11-02), base locale, compte de test local : points 8 et 9 faits. Sections vues, quiz des sept modules et examen de 28 questions répondus par les services de l'application (100 %) ; certificat émis au nom du titulaire ; vérification publique en FR et en EN qui nomme « Parcours B3 : dépôt de boissons (Ateba Boissons SARL) » ; PDF servi en FR et en EN. Le premier passage a révélé une question peu claire en M7 (« Excédent d'acomptes », valeur 0) : remplacée par « Solde d'IS à payer avec la DSF (0 si tout est déjà réglé) », avec l'explication du solde nul (les douze acomptes de 2 % couvrent exactement le minimum de perception). Seize captures (facture, relevé Orange Money, balance, déclaration ; 390 et 1280 px ; clair et sombre) dans `.playwright-mcp/dod-b3/`, hors dépôt, sans débordement de page.
- Parcours C (S35, profil validé le 2026-11-02), en TDD (`simulation/tests/test_parcours_c_content.py`, rouge puis vert) : `tools/simulation/build_parcours_c.py` et `narrative_c.py` → `content/simulation/c/` (140 pièces, 156 écritures, 230 questions bilingues, 7 modules, récit complet). Tech Clim Bonamoussadi SARL, Douala : ventes d'appareils (7011) et poses (706), outillage de 1 600 000 HT en 2412 amorti sur cinq ans (20 %, taux maximal des machines-outils légers, CGI art. 7), payé à 30 jours (4812) pour que la banque ne passe jamais en négatif ; honoraires du fonctionnaire associé en 632, sans retenue de l'art. 92 bis ; provision pour garantie de 450 000 (192), déductible (CGI art. 7 E) ; assemblée du 25 juin 2027 (AUSCGIE art. 346 et 348) : réserve légale plafonnée au cinquième du capital, dividendes de 6 000 000, IRCM de 16,5 % (CGI art. 70) reversé en août. Chiffres 2026 : CA 123 576 000, résultat avant impôt 15 007 120, IS 4 126 925 supérieur au minimum de perception 2 718 672. DoD-Parcours points 8 et 9 en local (quiz et examen à 100 %, certificat, vérification et PDF en FR et en EN, seize captures sans débordement dans `.playwright-mcp/dod-c/`). Tests : 977 verts. Non déployé.
- Déploiement du parcours C et du correctif de B3 (2026-11-02) : `main` = `cdba4cc`, `deploy.sh` EXIT=0 ; aucune migration ; simulation 68 sections et 853 questions, 231 publiées ; disque 99 Mo. Fumée avec un compte jetable (supprimé, LEFT 0) : janvier de C servi en FR et en EN à 360 px (12 scènes, 11 pièces, aucune balise inconnue, aucun débordement, aucune erreur console), catalogue 200.
