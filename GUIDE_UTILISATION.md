# Guide d'utilisation — PDF Table Extractor

Ce guide est destiné à **l'équipe métier** qui utilise l'outil au quotidien.
Il explique :
1. Comment lancer un traitement
2. Comment préparer les fichiers d'entrée
3. **Le contenu détaillé de chaque colonne Excel produite** (origine, calcul, format)
4. Les contrôles automatiques (cellules rouges)
5. Les erreurs courantes et leur solution

---

## 1. Lancer un traitement

### Option A — Interface web (recommandée)

1. Ouvrir un terminal dans le dossier du projet
2. Activer l'environnement virtuel :
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Lancer l'interface :
   ```powershell
   streamlit run app.py
   ```
4. Le navigateur s'ouvre sur `http://localhost:8501`
5. Glisser-déposer le **ZIP** contenant les dossiers de demandes
6. Attendre la fin du traitement (barre de progression)
7. Cliquer sur **"Télécharger le ZIP de résultats"**
8. Pour traiter un nouveau dossier, cliquer sur **"Nouveau courrier"** (pas besoin de recharger la page)

### Option B — Ligne de commande
Pour les utilisateurs avancés :
```powershell
python extractor.py extract mon_courrier.pdf --output sortie.xlsx
python extractor.py batch ./dossier/ --output-dir ./resultats/
```

---

## 2. Préparer les fichiers d'entrée

### Structure attendue d'un dossier de demande
Chaque demande doit contenir **3 PDF** avec un **préfixe numérique commun** :

| Type | Exemple de nom | Contient |
|---|---|---|
| Courrier principal | `336-Courrier_AAAA.pdf` | Lettre, motif, adresses, montants |
| Preuve de dépôt | `336-Preuve_de_Depot_xxx.pdf` | N° LR de dépôt postal |
| Accusé de réception | `336-AR_n_xxx.pdf` | N° de recommandé, dates de présentation/distribution |

> ⚠️ **Important** : le préfixe `336` doit être identique sur les 3 fichiers et placé en début de nom. Sans ce préfixe, l'outil ne peut pas regrouper les fichiers.

### Conventions de nommage à respecter
- **Courrier** : nom contient `Courrier`
- **Preuve de dépôt** : nom contient `Preuve` ou `depot`/`dépôt`
- **AR** : nom contient `AR_n` ou commence par `AR_`

### Format du ZIP
Le ZIP peut être :
- **Plat** (tous les PDF à la racine), ou
- **Organisé** en sous-dossiers `mails/` (pour les courriers) et `proof/` (pour AR + dépôt)

---

## 3. Le contenu des Excel produits

À chaque traitement, l'outil génère **3 types de fichiers Excel** par dossier :

### A. `XXX_Annexe_Tableaux.xlsx`
Contient une feuille par tableau extrait du courrier (généralement la liste détaillée des factures par adresse). Les colonnes sont issues directement du PDF, nettoyées et formatées (montants en €, dates en `dd/mm/yyyy`).

### B. `XXX_Métadonnées.xlsx`
Une seule feuille horizontale : ligne 1 = noms de colonnes, ligne 2 = valeurs pour cette demande.

### C. `Recapitulatif_Metadonnees.xlsx` (à la racine du ZIP de sortie)
Une ligne par demande, avec **toutes les colonnes** des fichiers de métadonnées. Permet une vue d'ensemble pour Excel/filtrage rapide.

---

## 4. Détail des colonnes des fichiers de métadonnées

> Les colonnes apparaissent dans cet ordre dans le fichier Excel.

### Identifiants

| Colonne | Origine | Description |
|---|---|---|
| **N° Dossier** | Préfixe numérique du nom de fichier (ex: `336`) ou `demande N° XXXX` dans le courrier | Identifiant unique de la demande |
| **Libellé de la Demande** | Calculé : `Année + Catégorie + N° Programme + Commune` | Libellé synthétique |
| **Responsable** | Valeur fixe : `Amaury MONGONGU` | Responsable du dossier |

### Classification

| Colonne | Origine | Description |
|---|---|---|
| **Type** | Déduit du contenu du courrier | Type de demande (déduit automatiquement) |
| **Categorie** | Déduit du contenu du courrier | Catégorie principale |
| **Sous-categorie** | Déduit du contenu du courrier | Sous-catégorie (peut être vide) |

### Montants

| Colonne | Origine | Calcul / Format |
|---|---|---|
| **Montant HT** | Somme de la colonne *Montant HT facture* du tableau de l'annexe | `float`, formaté en € dans Excel |
| **Taux de TVA** | Toutes les valeurs distinctes de la colonne *Taux de TVA* du tableau | Une seule valeur → `20%` ; plusieurs valeurs → `5,5%;10%;20%` (séparées par `;`) |
| **Montant TTC** | **Recalculé** ligne par ligne : `Σ (HT_ligne × (1 + TVA_ligne))` | Les lignes sans TVA renseignée sont ignorées du calcul |
| **Montant de la subvention** | Somme de la colonne *Montant subvention* du tableau | `float`, € |
| **Montant de la demande** | Identique au Montant HT (par défaut) | `float`, € |

> ⚠️ **Changement récent** : le Montant TTC n'est plus la somme directe de la colonne TTC du PDF — il est **recalculé** à partir de HT × (1 + TVA) ligne par ligne. Cela permet de détecter les incohérences dans les factures fournies. Si la colonne TTC du PDF diverge du recalcul, **il n'y a plus d'alerte rouge** (vérification désactivée). Pour comparer manuellement, ouvrir l'annexe et faire la somme.

### Entreprise et travaux

| Colonne | Origine | Description |
|---|---|---|
| **Nom de l'entreprise** | Colonne *Installateur* du tableau de l'annexe | Liste des entreprises distinctes, séparées par `;` |
| **Nature des travaux** | Colonne *Nature travaux* du tableau | Liste des natures distinctes, séparées par `;` |
| **Nature de dépenses** | Valeur fixe : `Degrevement taxe fonciere` | — |

### Références et adresses

| Colonne | Origine | Description |
|---|---|---|
| **Référence(s) Avis** | Colonne *Référence avis* du tableau (13 chiffres) ou texte du courrier | Références fiscales, sans espaces, séparées par `;` si multiples |
| **Adresse** | Colonne *Adresse des travaux* du tableau (en priorité) ou texte du courrier | Voir la **règle de mise en forme spéciale** ci-dessous |
| **N° Programme** | Colonne *Programme* du tableau ou texte du courrier | N° de programme immobilier |
| **Nombre de logements** | Texte du courrier | Entier |
| **N° d'opération** | Colonne *N° opération* du tableau | Opération associée |

#### 📐 Règle de mise en forme spéciale de la colonne **Adresse**

L'adresse est dédoublée par numéro et par voie, dédupliquée, puis **mise en forme selon la parité des numéros** :

- **Tous pairs** → tout sur une ligne, séparés par `;` (comportement standard)
  ```
  2 RUE DU PARC;4 RUE DU PARC;6 RUE DU PARC
  ```

- **Tous impairs** → chaque adresse sur sa propre ligne (avec retour à la ligne)
  ```
  1 RUE DU PARC;
  3 RUE DU PARC;
  5 RUE DU PARC
  ```

- **Mixte (pairs + impairs)** → pairs d'abord sur une seule ligne, puis impairs chacun sur sa ligne
  ```
  2 RUE X;4 RUE X;
  3 RUE X;
  5 RUE X
  ```

> 💡 Les libellés de voie sont **automatiquement abrégés** via `abbreviations.json` :
> - `Avenue` ou `Av.` → `AV`
> - `Boulevard` → `BD`
> - `Allée` → `ALL`
> - `Rue` → `RUE`
> - `Place` → `PL`
> - … (62 abréviations au total)
>
> Pour ajouter une nouvelle abréviation, modifier `abbreviations.json` à la racine du projet (clé = forme longue en MAJUSCULE, valeur = abréviation).

### Envoi

| Colonne | Origine | Description |
|---|---|---|
| **Date limite d'envoi** | **Extrait** de la phrase `Fait à Paris, le ...` du courrier | Format `dd/mm/yyyy`. Exemple : `Fait à Paris, le mardi 30 décembre 2025` → `30/12/2025` |
| **Type d'envoi** | Valeur fixe : `RecommandeAvecAR` | — |
| **Numero de recommande** | Extrait du PDF AR (`XXX-AR_n_xxx.pdf`) | N° de la lettre recommandée (15 chiffres) |

> ⚠️ **Changement récent** : la Date limite d'envoi n'est plus calculée comme `31/12/(année+2)` mais extraite directement du courrier. Si la phrase `Fait à Paris, le ...` est introuvable, la cellule sera vide.

### Interlocuteur (valeurs fixes)

| Colonne | Valeur |
|---|---|
| **Nom interlocuteur** | `JOUHANNET` |
| **Prénom interlocuteur** | `Alexis` |
| **Mail interlocuteur** | `alexis.jouhannet@dgfip.finances.gouv.fr` |
| **Tel interlocuteur** | `0322468319` |

### Divers

| Colonne | Description |
|---|---|
| **Commentaire** | Vide par défaut, à compléter manuellement si besoin |
| **Lien escale** | Vide par défaut |

---

## 5. Contrôles automatiques (cellules rouges)

Actuellement, **aucune cellule n'est colorée en rouge** dans les fichiers de métadonnées.

> 💡 Le code conserve l'infrastructure pour ajouter de futurs contrôles. Si un nouveau contrôle est demandé, il pourra être ajouté dans la fonction `computed_metadata_red_keys` de `scripts/metadata_transformer.py`.

---

## 6. Erreurs courantes et solutions

### "Aucune demande trouvée dans le ZIP"
**Cause** : les PDF n'ont pas de préfixe numérique en début de nom, ou le ZIP est vide.
**Solution** : vérifier que chaque fichier commence par un nombre suivi d'un tiret (ex: `336-Courrier_xxx.pdf`).

### Une cellule de métadonnée est vide alors que l'info est dans le PDF
**Causes possibles** :
- Le pattern regex ne correspond pas exactement à la formulation du PDF
- Le PDF est scanné (image) et non textuel → l'OCR n'est pas supporté
- La colonne du tableau a un nom différent de ce qui est attendu

**Solution** : me signaler le numéro du dossier et la colonne concernée.

### Le N° de recommandé est vide
**Causes possibles** :
- Le fichier AR n'est pas nommé selon la convention `XXX-AR_n_xxx.pdf`
- Le N° dans le PDF ne fait pas exactement 15 chiffres consécutifs
- Le PDF AR n'est pas dans le ZIP

**Solution** : vérifier le nom du fichier AR et son contenu.

### Adresse mal formée ou abréviation non appliquée
**Cause** : le libellé de voie n'est pas dans `abbreviations.json`, ou il a une variante orthographique non prévue.
**Solution** : ajouter la variante dans `abbreviations.json` (voir la section Adresse plus haut).

### Streamlit ne démarre pas — erreur "DLL load failed"
**Cause** : version de pandas incompatible avec Windows Smart App Control.
**Solution** :
```powershell
pip install "pandas<3.0"
```

### Le venv ne s'active pas sous PowerShell
**Cause** : la stratégie d'exécution PowerShell bloque les scripts.
**Solution** (une seule fois) :
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## 7. Résumé visuel : d'où vient chaque donnée ?

```
┌────────────────────────────────────────────────────────┐
│  Courrier PDF                                          │
│  ├── Texte → numéro demande, date, motif, montants    │
│  │                                                     │
│  └── Tableau (annexe)                                  │
│      ├── colonne HT     → Montant HT (somme)          │
│      ├── colonne TVA    → Taux de TVA (uniques)       │
│      ├── colonne HT+TVA → Montant TTC (recalcul)      │
│      ├── colonne adr.   → Adresse (formatée parité)   │
│      ├── colonne ent.   → Nom de l'entreprise         │
│      └── colonne nat.   → Nature des travaux          │
│                                                        │
│  Phrase "Fait à Paris, le ..." → Date limite d'envoi  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  AR PDF (XXX-AR_n_xxx.pdf)                             │
│  └── 15 chiffres consécutifs → Numero de recommande   │
│  └── "Présentée le ..."      → Date présentation AR   │
│  └── "Distribuée le ..."     → Date distribution AR   │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Preuve de dépôt PDF                                   │
│  └── 15 chiffres consécutifs → N° LR Dépôt            │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Valeurs fixes (codées en dur)                         │
│  ├── Responsable        → Amaury MONGONGU              │
│  ├── Type d'envoi       → RecommandeAvecAR             │
│  ├── Nature de dépenses → Degrevement taxe fonciere    │
│  └── Interlocuteur      → JOUHANNET Alexis (DGFiP)     │
└────────────────────────────────────────────────────────┘
```

---

## 8. À qui s'adresser

- **Bug, valeur incorrecte, nouvelle abréviation** → ouvrir une issue GitHub ou contacter l'équipe technique avec le numéro de dossier concerné
- **Évolution fonctionnelle** → décrire le besoin métier en précisant la colonne concernée et la règle attendue

---

*Dernière mise à jour : avril 2026 — branche `fix/339-metadata-corrections`*
