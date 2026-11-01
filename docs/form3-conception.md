# Form 3 : Simulation Compta et Fisca — document de conception

> Livrable S8, à valider avant tout contenu importable (`content/simulation/`). Décisions S1 à S28 d'AGENTS.md.
> Tous les montants sont calculés avec `referentiel/calculs.py` et `tools/simulation/ledger.py` à partir de
> `content/referentiel/parametres.csv` ; tous les comptes existent dans `content/referentiel/syscohada.csv`.
> Les entreprises sont fictives ; chaque pièce affichée porte la mention « Document pédagogique fictif ».

## 1. Syllabus

Une formation `simulation` (préfixe `S`, icône `briefcase`). Elle compte une partie par parcours, livrées dans l'ordre
A → B3 → C → D → B1 → B2. Chaque partie a 7 modules, avec un examen de 28 questions (4 par module, 70 %, 3 tentatives,
60 min) et un certificat. Prérequis indicatif : « Recommandé après les formations Comptabilité et Fiscalité ».

| Module | Phase | Contenu | Évaluation |
|---|---|---|---|
| M1 Création | Jour 1 et janvier | Démarches (statuts, enregistrement, immatriculation et NIU), capital, frais de constitution en charges (S6), premières opérations | `journal`, question piège sur l'ancienne immobilisation des frais d'établissement |
| M2 T1 | Février à mars | Achats, ventes, paie, trésorerie (espèces, banque, Mobile Money), rapprochements, déclarations du 15 | `journal`, questions numériques des déclarations |
| M3 T2 | Avril à juin | Idem, plus l'importation (T3 pour A) préparée | Idem |
| M4 T3 | Juillet à septembre | Idem, plus l'importation (avis de douane, précompte en douane) | Idem |
| M5 T4 | Octobre à décembre | Idem, opérations de décembre | Idem |
| M6 Inventaire | 31 décembre | Stock final (fiches CMUP, contraste PEPS), amortissements au prorata temporis, dépréciations, provisions, régularisations ; calculateurs `stock` et `amortissement` | Écritures au livre officiel, questions `calcul` |
| M7 Passerelle + DSF | Janvier à avril 2027 | Six éléments de la passerelle (S21, S23), IS comparé au minimum de perception, DSF limitée au bilan, au compte de résultat, au tableau de passage et à la liquidation de l'IS, déposée à l'échéance du centre (S22) | Questions `calcul` et numériques |

### Spécificités par parcours

| Parcours | Forme, régime, centre | Points propres | Références |
|---|---|---|---|
| A Vêtements | SARL au réel, CIME, DSF au 15 avril 2027 (S25) | CMUP/PEPS, marges, TVA collectée et déductible, précompte de 2 % sur achats | CGI art. 21 (3), 142, 143 |
| B3 Boissons | SARL au réel | Consignes 4094/4194, emballages 2493, camions, accises comprises dans le prix d'achat | CGI art. 142 (9) |
| C Électronique et climatisation | SARL au réel ; associé fonctionnaire à 80 %, gérant tiers | Vacations en honoraires (632) avec retenue de 5 %, dividendes et IRCM | CGI art. 70, 92 bis |
| D Prestataire froid | Établissement au réel | Prestations 706, TVA à l'encaissement (compte d'attente 471, S24), retenue de 5,5 % et contraste à 11 % | CGI art. 21 (2), 134 (1) b |
| B1 Boissons | Établissement à l'IGS, SMT (S26) | Tarif IGS, précompte de 5 %, questions numériques seulement | CGI art. 21 (3), C 39, C 40 |
| B2 Boissons | IGS en 2026, puis SARL au réel au 1er janvier 2027 | Apport du fonds, bilan d'ouverture | CGI art. 93 quater |

## 2. Scénario du mois 1 (janvier 2026) : Ngono Mode SARL

**Profil (S17).** Ngono Mode SARL, boutique de vêtements à Douala-Akwa. Capital de 5 000 000 FCFA en numéraire, créée le
2 janvier 2026, au réel, rattachée au CIME. Une vendeuse au brut mensuel de 150 000 FCFA. Fournisseur : Sawa
Textiles SARL, grossiste au réel.

### 2.1 Pièces justificatives fournies à l'apprenant

| Réf. | Date | Pièce | Contenu |
|---|---|---|---|
| S-A-01-000 | 02/01 | Démarche : création de la SARL au CFCE de Douala (guichet unique) | Documents : 5 + N exemplaires des statuts sous seing privé (N = nombre d'associés) ; 5 + N déclarations de régularité et de conformité ; 2 extraits de casier judiciaire de chaque associé et du gérant, ou une déclaration sur l'honneur ; photocopie de la CNI de chaque associé, 2 pour le gérant associé ; plan de localisation ; boîte postale ; contact téléphonique ; frais de création 41 500 FCFA, annonce légale 13 125 FCFA, timbres selon le nombre de pages des statuts (montants à vérifier au CFCE). Obtenu en 72 heures : registre de commerce, carte de contribuable, attestation de création. Source : `[[source:minfi-cfce]]` |
| S-A-01-001 | 02/01 | Attestation de dépôt du capital (banque) | 5 000 000 FCFA versés |
| S-A-01-002 | 02/01 | Démarche : immatriculation fiscale et rattachement | Faite au CFCE (carte de contribuable avec le NIU) ; dossier suivi par le centre de rattachement : CIME, car le CA visé (90 millions) est compris entre 50 millions et 3 milliards. Sources : `[[cgi:art. L 1]]`, `[[source:dgi-cime]]` |
| S-A-01-003 | 03/01 | Facture du notaire | Honoraires HT 200 000, TVA 35 000, CAC 3 500, débours d'enregistrement 25 000 ; total 263 500, payé par virement |
| S-A-01-004 | 05/01 | Démarches : déclaration d'existence à la CNPS (agence régionale) et à la délégation régionale du travail ; compte marchand Mobile Money | Administrations compétentes : `[[source:minfi-formalites]]`. CNPS, immatriculation de l'employeur : demande sur imprimé CNPS, copie du registre de commerce ou des statuts, patente en cours de validité, carte de contribuable, plan de localisation, liste du personnel ; puis immatriculation de la vendeuse dans les 8 jours suivant l'embauche (demande, avis d'embauche sur imprimé CNPS, copie certifiée de l'acte de naissance ou de la CNI) ; obtenu : numéro matricule employeur et numéro d'assuré. Source : `[[source:cnps-faq]]`. Compte bancaire d'entreprise (banque fictive « Banque X », compte 5211) : demande d'ouverture, RCCM, carte de contribuable, plan de localisation, pièces d'identité du gérant, extrait du journal d'annonces légales, statuts, procès-verbal de nomination du gérant ; obtenu : RIB (liste publiée par une banque réelle, `[[source:sg-cm-compte-entreprise]]`, la liste exacte se demandant en agence). Compte marchand Orange Money : RCCM, carte de contribuable, patente, statuts, CNI du gérant ou d'un mandataire, RIB ; obtenu : code marchand (`[[source:orange-om-partenaire]]`). MTN MoMo : site momo.mtn.cm injoignable le 2026-10-30, pièces à vérifier en agence MTN |
| S-A-01-005 | 08/01 | Facture FA-2026-0007 de Sawa Textiles SARL (NIU, RCCM, régime, CIME, référence de facturation électronique DGI) | HT 3 000 000 ; TVA 17,5 % 525 000 ; CAC 52 500 ; TTC 3 577 500 ; précompte 2 % 60 000 ; net à payer 3 637 500 |
| S-A-01-006 | 12/01 | Avis de virement au fournisseur | 3 637 500 |
| S-A-01-007 | 25/01 | Bordereau de sortie de caisse vers la banque | 2 000 000 |
| S-A-01-008 | 26/01 | Bordereau de versement bancaire | 2 000 000 |
| S-A-01-009 | 31/01 | Récapitulatif des ventes au comptant (journal de caisse) | TTC 2 385 000 (HT 2 000 000, TVA et CAC 385 000) |
| S-A-01-010 | 31/01 | Relevé Orange Money de janvier (compte marchand) | Encaissements TTC 1 192 500 (HT 1 000 000) ; frais de l'opérateur 5 000 |
| S-A-01-011 | 31/01 | Bulletin de paie de la vendeuse | Brut 150 000 ; CNPS salariale indiquée par le bulletin 6 300 (C28) ; IRPP et CAC 6 274 ; RAV 1 950 ; TDL 1 000 ; CFC 1 500 ; net 132 976 ; CFC patronale 3 750 ; CNPS patronale, branche pensions 4,2 % : 6 300 (décret n° 2016/072, `[[source:cnps-faq]]`) |
| S-A-01-012 | 31/01 | Ordre de virement du salaire | 132 976 |
| S-A-01-013 | 31/01 | Relevé bancaire de janvier | Solde du relevé 2 962 524, dont 3 500 de frais de tenue de compte non encore comptabilisés |

### 2.2 Corrigé : écritures du livre officiel

| Date | Pièce | Compte | Débit | Crédit |
|---|---|---|---|---|
| 2026-01-02 | S-A-01-001 | 521 Banques locales | 5 000 000 | |
| | | 1013 Capital souscrit, appelé, versé, non amorti | | 5 000 000 |
| 2026-01-03 | S-A-01-003 | 6324 Honoraires des professions réglementées | 200 000 | |
| | | 4454 TVA récupérable sur services extérieurs | 38 500 | |
| | | 646 Droits d'enregistrement | 25 000 | |
| | | 521 Banques locales | | 263 500 |
| 2026-01-08 | S-A-01-005 | 6011 Achats de marchandises | 3 000 000 | |
| | | 4452 TVA récupérable sur achats | 577 500 | |
| | | 4492 État, avances et acomptes versés sur impôts (précompte) | 60 000 | |
| | | 401 Fournisseurs | | 3 637 500 |
| 2026-01-12 | S-A-01-006 | 401 Fournisseurs | 3 637 500 | |
| | | 521 Banques locales | | 3 637 500 |
| 2026-01-25 | S-A-01-007 | 585 Virements de fonds | 2 000 000 | |
| | | 5711 Caisse en monnaie nationale | | 2 000 000 |
| 2026-01-26 | S-A-01-008 | 521 Banques locales | 2 000 000 | |
| | | 585 Virements de fonds | | 2 000 000 |
| 2026-01-31 | S-A-01-009 | 5711 Caisse en monnaie nationale | 2 385 000 | |
| | | 7011 Ventes de marchandises | | 2 000 000 |
| | | 4431 TVA facturée sur ventes | | 385 000 |
| 2026-01-31 | S-A-01-010 | 5522 Orange Money (sous-compte de 552) | 1 192 500 | |
| | | 7011 Ventes de marchandises | | 1 000 000 |
| | | 4431 TVA facturée sur ventes | | 192 500 |
| 2026-01-31 | S-A-01-010 | 631 Frais bancaires | 5 000 | |
| | | 5522 Orange Money (sous-compte de 552) | | 5 000 |
| 2026-01-31 | S-A-01-011 | 6611 Appointements, salaires et commissions | 150 000 | |
| | | 4472 Impôts sur salaires | | 10 724 |
| | | 431 Sécurité sociale | | 6 300 |
| | | 422 Personnel, rémunérations dues | | 132 976 |
| 2026-01-31 | S-A-01-011 | 6413 Taxes sur appointements et salaires (CFC patronale) | 3 750 | |
| | | 4472 Impôts sur salaires | | 3 750 |
| 2026-01-31 | S-A-01-011 | 6641 Charges sociales sur rémunération du personnel national | 6 300 | |
| | | 431 Sécurité sociale | | 6 300 |
| 2026-01-31 | S-A-01-012 | 422 Personnel, rémunérations dues | 132 976 | |
| | | 521 Banques locales | | 132 976 |
| 2026-01-31 | S-A-01-013 | 631 Frais bancaires | 3 500 | |
| | | 521 Banques locales | | 3 500 |

Points de correction :
- **Frais de constitution (S6) :** honoraires et droits sont des charges ; aucune immobilisation de « frais d'établissement ».
- **Précompte de 2 % (CGI art. 21 (3)) :** il est versé au fournisseur avec la facture, hors CAC. Il est imputable sur l'acompte d'IS.
- **Rapprochement de fin de mois :** solde comptable avant régularisation 2 966 024 ; solde du relevé 2 962 524 ; écart de 3 500, régularisé en 631.
- **Paie :** IRPP selon le barème (CGI art. 29, 34, 69), CAC ; RAV et TDL selon leurs barèmes (TDL annuelle de 12 000, retenue par douzièmes) ; CFC (loi 77-10). La CNPS est un montant du bulletin, jamais calculé par la plateforme (S15, C28) : 4,2 % salarial et 4,2 % patronal pour la branche pensions (décret n° 2016/072, FAQ de la CNPS). Les prestations familiales et les accidents du travail ne sont pas simulés en janvier : leurs taux ne figurent dans aucune source consultée (même règle que US-97, 3e critère).

### 2.3 Déclaration du 15 février 2026 (période de janvier)

Calculée par `ledger.monthly_declaration` :

| Case | Montant (FCFA) |
|---|---|
| Chiffre d'affaires HT | 3 000 000 |
| TVA collectée (TVA et CAC) | 577 500 |
| TVA déductible (achats et notaire) | 616 000 |
| TVA due | 0 |
| Crédit de TVA à reporter | 38 500 |
| Acompte d'IS : 2 % du CA, majoré de 10 % de CAC (CGI art. 21) | 66 000 |
| Précompte imputé | 60 000 |
| Acompte d'IS net à payer | 6 000 |
| Retenues sur salaires (IRPP, CAC, RAV, TDL, CFC salariale et patronale) | 14 474 |

## 3. Matrice des données de base

### 3.1 Plan de comptes de Ngono Mode SARL (extrait, comptes du plan révisé)

| Compte | Libellé | Usage |
|---|---|---|
| 1013 | Capital souscrit, appelé, versé, non amorti | Capital |
| 401 | Fournisseurs, dettes en compte | Grossistes |
| 411 | Clients | Ventes à crédit |
| 422 | Personnel, rémunérations dues | Salaires nets |
| 431 | Sécurité sociale | CNPS |
| 4431 / 4452 / 4454 | TVA facturée, récupérable sur achats, sur services | TVA |
| 4472 | Impôts sur salaires | IRPP, CAC, RAV, TDL, CFC |
| 4492 | État, avances et acomptes versés sur impôts | Précompte, acomptes |
| 521 | Banques locales | Compte bancaire |
| 552 | Monnaie électronique | Compte parent des sous-comptes Mobile Money |
| 5521 / 5522 | MTN MoMo / Orange Money | Sous-comptes propres à l'entreprise (S19), déclarés dans le manifeste (`sous_comptes`) et créés sous 552 à l'import |
| 5711 | Caisse en monnaie nationale | Caisse de la boutique |
| 585 | Virements de fonds | Virements internes |
| 6011 / 6031 | Achats de marchandises, variation des stocks | Stocks (inventaire intermittent) |
| 6324 / 646 | Honoraires, droits d'enregistrement | Constitution |
| 631 | Frais bancaires | Frais bancaires et Mobile Money |
| 6413 / 6611 | Taxes sur salaires, appointements | Paie |
| 7011 | Ventes de marchandises | Ventes |

**Sous-comptes (S19).** Le plan révisé n'a pas de 5521 ni de 5522 ; l'entreprise les ouvre sous 552, comme le plan l'autorise. Ils sont déclarés par le parcours, créés à l'import et contrôlés : un sous-compte sans parent dans le plan est refusé. Le corrigé de janvier (section 2.2) passe les encaissements Orange Money sur 5522.

### 3.2 Taux 2026 utilisés (table `FiscalParameter`)

| Clé | Valeur | Source |
|---|---|---|
| `tva.taux_principal` | 17,5 % | CGI art. 142 |
| `cac.taux` | 10 % | CGI art. C 83 (1) |
| `tva.taux_global` | 19,25 % | CGI art. 142 et C 83 |
| `precompte.taux_reel` / `_igs` / `_hors_fichier` | 2 % / 5 % / 10 % | CGI art. 21 (3) |
| `is.taux` / `is.taux_reduit` | 30 % / 25 % | CGI art. 17, 17 bis |
| `is.taux_minimum_perception` | 2 % | CGI art. 21 (2) |
| `retenue.commande_publique` | 5 % (+ CAC) | CGI art. 21 (2) |
| `retenue.honoraires` | 5 % | CGI art. 92 bis |
| `irpp.taux_frais_professionnels` / `irpp.abattement_salaires` | 30 % / 500 000 | CGI art. 34, 29 |
| `cfc.taux_salarie` / `cfc.taux_employeur` | 1 % / 2,5 % | Loi 77-10 art. 6 |
| `ircm.taux` | 15 % | CGI art. 70 |
| `amortissement.taux_max_auto_leger_ville` | 25 % | CGI art. 7 |
| `dons.plafond_interet_general` | 0,5 % du CA | CGI art. 7 |
| `accises.biere_65cl` / `accises.biere_33cl` | 75 / 37,5 FCFA | CGI art. 142 (9) |
| `igs.classe1_montant` … `igs.classe10_montant` | 20 000 … 2 000 000 FCFA | CGI art. C 40 (1) |

## 4. Points réglés avant la rédaction du contenu (2026-10-30)

Le parcours A est généré par `tools/simulation/build_parcours_a.py` dans `content/simulation/`. Écarts au profil : pas d'importation au T3 (droits de douane non sourcés) ; loyer de 300 000 FCFA avec précompte de 10 % (CGI art. 87) ; un gérant salarié et deux vendeuses ; CNPS patronale limitée à la branche pensions.

1. **Sous-comptes Mobile Money :** réglé (5521, 5522 déclarés par le parcours, S19).
2. **Démarches hors fiscalité (U21) :** CFCE, greffe et rattachement fiscal sont sourcés (MINFI, DGI). La CNPS est sourcée par sa FAQ officielle (copie archivée, le site étant injoignable le 2026-10-30) ; elle confirme le taux salarial de la branche pensions (4,2 %, plafond 750 000 FCFA, décret n° 2016/072), cohérent avec les 6 300 FCFA du bulletin. La banque et Orange Money sont sourcés par leurs pages publiques. MTN ne publie pas de liste de pièces pour le Cameroun (momo.mtn.cm injoignable, page « MoMo Business » générique) : le parcours A encaisse sur MTN MoMo, mais seule la démarche Orange Money est rédigée.
3. **Bulletin type de paie :** réglé pour la branche pensions (6 300 patronal, source CNPS) ; prestations familiales et accidents du travail non simulés faute de source.
