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
| B2 Boissons | IGS en 2026, puis SARL au réel au 1er janvier 2027 | Apport du fonds, bilan d'ouverture | CGI art. 93 quater, C 39 (2), 95 et 96 (S41) |

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

## 5. Récit pédagogique (S33, S34, demande de l'utilisateur du 2026-11-01)

> À valider sur le pilote « janvier du parcours B3 » avant d'étendre le récit à B3 entier, puis de reprendre A et E.

### 5.1 Constat

Les parcours A et E livrés sont **muets** : chaque mois aligne des pièces et des questions, sans dire ce qui s'est passé,
pourquoi la pièce existe, ni pourquoi tel compte ou tel impôt s'applique plutôt qu'un autre. Un débutant voit une
facture mais ne comprend ni la scène ni le choix.

### 5.2 Règles d'écriture du récit (bonnes pratiques retenues)

1. **Des personnages récurrents**, nommés et fictifs, avec un rôle stable : le lecteur suit des gens, pas des comptes.
2. **Une scène par événement, dans l'ordre du calendrier** : jour, lieu, qui fait quoi et pourquoi (besoin concret :
   livrer un client, payer le loyer, réapprovisionner avant le week-end). La pièce apparaît **dans** la scène, au moment
   où elle naît.
3. **Chaque scène suit le même canevas en cinq temps**, pour que le débutant sache toujours où regarder :
   - *Ce qui se passe* : le récit en trois à six phrases, avec la pièce ;
   - *La règle* : le concept du cours et sa source citée (`[[cgi:]]`, `[[syscohada:]]`, `[[guide:]]`) ;
   - *Pourquoi ce choix et pas un autre* : l'option qu'un débutant prendrait (le piège) et pourquoi elle est fausse ;
   - *Ce que ça change* : trésorerie, déclaration du 15, résultat ou bilan ;
   - *Où ça se range* : le classeur ou le registre où finit la pièce et le journal du logiciel où elle est saisie
     (AUDCIF art. 17, 19, 22 et 24 : pièces datées, classées et annotées de leur référence ; journaux auxiliaires
     centralisés chaque mois ; clôture informatique au moins trimestrielle ; conservation dix ans). Le dossier
     d'entreprise décrit les outils (logiciel comptable, classeurs, brouillard de caisse, fiche de stock, cahier des
     vides) et les routines du soir, de la semaine, du mois, du trimestre et de l'année.
4. **Un renvoi au cours** : « Revoir : Comptabilité M7 (Les ventes) » ou « Fiscalité M4 (La TVA et les droits
   d'accises) », en numérotation continue de la plateforme ; le récit applique le cours, il ne le remplace pas.
5. **Le récit précède la question** : on n'interroge l'apprenant qu'après lui avoir montré la scène ; l'explication de
   la question reprend le « pourquoi pas un autre ».
6. **Un bilan de fin de mois** : trois à cinq points « ce qu'il faut retenir », et l'échéance du 15 que le mois prépare.
7. **Tension utile, sans fiction gratuite** : un événement n'existe que s'il porte une règle ; jamais d'anecdote qui
   n'aboutit à aucune écriture ni décision.
8. **Aucune règle inventée** : une scène qui touche une règle absente de nos sources n'est pas écrite (U21). Par exemple,
   le traitement fiscal des repas offerts au personnel reste à vérifier dans le CGI.
9. **Phrases courtes, et vocabulaire du métier expliqué à sa première apparition** (consigne, vide, casier, précompte).

### 5.3 Visuels (S33)

Des scènes isométriques sont dessinées avec le skill anatomy et **exportées en SVG statique**, en FR et en EN, sans
script : `static/content/simulation/<parcours>/<scene>.<lang>.svg`. Elles sont insérées par une image Markdown, que le
rendu agrandit déjà au toucher (`courses/rendering.py`, `DIAGRAM`). Node ne sert qu'à l'écriture du contenu et n'est
jamais déployé ; la CSP reste inchangée. S33 amende C13 (« figures interactives supprimées ») : aucune figure
interactive, seulement des SVG statiques. Budget : au plus deux figures par mois et 1 Mo par parcours (NFR-11).

### 5.4 Distribution du parcours B3

| Personnage | Rôle |
|---|---|
| Rose Ateba | Associée majoritaire, ancienne revendeuse de boissons au marché Mvog-Mbi |
| Serge Mballa | Gérant salarié : achats, banque, déclarations |
| Didier | Magasinier : réception, vides, comptage |
| Paul | Chauffeur-livreur : tournées avec le camion (à partir de février) |
| Mme Ngah | Propriétaire du Snack-Bar Le Rond-Point, cliente à crédit |
| M. Fouda | Commercial des Brasseries de la Sanaga (fictives) |

### 5.5 Pilote : janvier 2026 du parcours B3

| Jour | Scène (ce qui se passe) | Pièce | Règle et source | Pourquoi pas autre chose | Revoir |
|---|---|---|---|---|---|
| 2 | Rose et Serge déposent 10 millions en banque : les fonds sont déposés avant l'immatriculation | Attestation de dépôt | Capital souscrit, appelé, versé 1013 | Pas un produit : un apport n'est pas un revenu ; pas une dette envers Rose (4621) : c'est du capital, rémunéré par les dividendes | Compta M3 |
| 2 | Le dépôt ouvre dans un entrepôt loué ; Serge paie le loyer en retenant 10 %, qu'il reversera aux impôts | Quittance de loyer | Précompte sur loyer, CGI art. 87 | Pas tout le loyer à la propriétaire : le locataire au réel collecte pour l'État (4478, dette) | Fisca M3 |
| 3 | Le notaire remet les statuts : au-delà d'un million de capital, la SARL passe chez lui | Facture du notaire | Charges par nature 6324 et 646 (S6), TVA 4454 | Pas des « frais d'établissement » à l'actif : le SYSCOHADA révisé les a supprimés | Compta M1 |
| 5 | Les camions de la brasserie ont rempli l'entrepôt en plusieurs tournées (3 570 casiers) ; M. Fouda récapitule les bons de livraison sur une facture ; bouteilles et casiers sont consignés | Facture des Brasseries | 6011 (droit d'accises de 25 % et droit spécifique additionnel compris, art. 142 (9)), 4452, 4492 (art. 21 (3)), 4094 (Guide, 1re partie, ch. 2) | Accises : pas de compte à part, elles sont dans le prix ; consigne : pas un achat, une créance récupérée au retour des vides ; précompte : pas une charge, une avance d'impôt | Compta M6, Fisca M4 |
| 6 | Didier reçoit 400 casiers marqués « Ateba », qui serviront des années | Facture Plasti-Centre | Matériel d'emballage récupérable 243, TVA 4451 | Pas 6082 (consommé) : durable et identifiable ; pas 2493 : c'est la ligne des immobilisations en cours | Compta M13 |
| 20 | Mme Ngah commande pour sa soirée de fin de mois ; le dépôt lui consigne les casiers | Facture au Snack-Bar | 411, 7011, 4431, 4194 ; consigne hors base de TVA (art. 139 (2)) | Consigne : pas une vente, une dette remboursable au retour ; pas de TVA dessus, l'emballage est identifiable | Compta M7 |
| 31 | Les clients du comptoir paient en espèces et échangent leurs vides | Récapitulatif des ventes | 5711, 7011, 4431 | Pas de consigne : l'échange vide contre plein est immédiat | Compta M7 |
| 31 | Les bars du quartier paient par Orange Money ; l'opérateur prélève ses frais | Relevé Orange Money | 5522, 631, 585 (S19) | Frais : pas une réduction de la vente, un service bancaire (631) ; transfert : par 585, jamais directement de 5522 à 521 | Compta M12 |
| 31 | Serge prépare la paie des trois salariés | Journal de paie | 6611, 6413, 6641, 4472, 431, 422 | IRPP et CNPS salariale retenus : pas des charges de l'entreprise, des dettes envers l'État et la CNPS | Compta M11, Fisca M3 |
| 31 | Didier porte la recette du mois à la banque | Bordereau de versement | 585, 5711 | Pas 521 directement depuis la caisse : le virement interne transite par 585 jusqu'au relevé | Compta M12 |
| 31 | Le relevé de la banque arrive | Relevé bancaire | 521, 422, 585, 631 | Le solde du relevé et celui du 521 se rapprochent : un écart s'explique, il ne se « corrige » pas | Compta M29 |

**Bilan de janvier** : un apport n'est pas un produit ; une consigne n'est ni un achat ni une vente ; les accises sont
dans le prix ; le précompte et la retenue sur loyer sont des créances ou des dettes envers l'État ; tout ce qui passe
entre la caisse, Orange Money et la banque transite par 585. Prochaine étape : la déclaration du 15 février.

**Figures du pilote** (anatomy, SVG statique) :
1. *Le circuit des casiers* : brasserie → dépôt → snack-bar, casiers pleins à l'aller et vides au retour, avec la
   consigne qui suit chaque casier (4094 côté brasserie, 4194 côté snack-bar).
2. *Les trois caisses du dépôt* : comptoir (5711), téléphone Orange Money (5522) et banque (521), reliés par le
   virement interne 585.

### 5.6 Mise en œuvre prévue

- Le générateur porte le récit en données : chaque pièce reçoit une scène `{jour, récit, règle, pourquoi_pas, effet,
  revoir}` en FR et en EN ; la section du mois devient récit, pièces et bilan.
- Contrôle bloquant ajouté en TDD : dans un parcours narré, chaque pièce comptable d'une section mensuelle est précédée
  de sa scène (rubriques « Pourquoi ce choix » et « Revoir », au moins une source citée) ; chaque renvoi « Revoir »
  désigne un module existant ; chaque figure citée existe en FR et en EN.
- Les explications des questions `journal` reprennent le « pourquoi pas autre chose » de leur scène.
