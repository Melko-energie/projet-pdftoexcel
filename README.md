# PDF Table Extractor

Extracteur de tableaux et de métadonnées de PDF vers Excel, conçu pour les dossiers de dégrèvement fiscal **TFPB** (Taxe Foncière sur les Propriétés Bâties).

L'outil prend en entrée un **ZIP** contenant un ou plusieurs dossiers de demandes (chaque dossier = un courrier + un AR + une preuve de dépôt) et produit en sortie un ZIP structuré contenant pour chaque demande :
- les PDF originaux
- une **annexe Excel** avec les tableaux extraits
- un **fichier Excel de métadonnées** consolidées
- un **récapitulatif global** de toutes les demandes

> Pour comprendre en détail le contenu des Excel produits, voir **[GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)**.

---

## 🚀 Démarrage rapide — UNE seule commande

Après `git clone`, depuis la racine du projet :

**Windows (PowerShell)**
```powershell
.\go.ps1
```

**Linux / macOS / Git Bash**
```bash
bash go.sh
```

Ça :
1. crée `.venv` Python à la racine et installe `requirements.txt`,
2. active le hook git `post-merge` (les futurs `git pull` rejouent l'install tout seuls),
3. lance l'**UI Streamlit** sur http://localhost:8501.

### Sous-commandes utiles
| But | PowerShell | Bash |
|---|---|---|
| Tout (install + Streamlit) | `.\go.ps1` | `bash go.sh` |
| Installer seulement | `.\go.ps1 install` | `bash go.sh install` |
| Streamlit (UI principale) | `.\go.ps1 streamlit` | `bash go.sh streamlit` |
| FastAPI alternative (:8000) | `.\go.ps1 web` | `bash go.sh web` |

> **Pré-requis** : `python` (3.11+ ; **3.12 recommandé** d'après les notes du projet — Python 3.14 et le Python du Microsoft Store peuvent provoquer des erreurs DLL bloquées par Windows Smart App Control), `git`.

---

## 🐳 Docker

Pré-requis : [Docker](https://docs.docker.com/get-docker/) (et Docker Compose, inclus dans Docker Desktop).

### Démarrage rapide avec Docker Compose (recommandé)

Depuis la racine du projet :

```bash
docker compose up --build
```

L'UI Streamlit est ensuite disponible sur http://localhost:8501.

Pour arrêter :
```bash
docker compose down
```

### Lancer aussi l'API FastAPI (port 8000)

L'API FastAPI est en profil optionnel. Pour la lancer en plus de Streamlit :

```bash
docker compose --profile fastapi up --build
```

FastAPI sera alors exposée sur http://localhost:8000.

### Build et run manuels (sans Compose)

```bash
# Build de l'image
docker build -t projet-pdftoexcel .

# Lancer l'UI Streamlit (port 8501)
docker run --rm -p 8501:8501 projet-pdftoexcel

# Lancer l'API FastAPI (port 8000) à la place
docker run --rm -p 8000:8000 projet-pdftoexcel \
  uvicorn web.main:app --host 0.0.0.0 --port 8000
```

### Persistance des fichiers de traitement

Les fichiers d'entrée/sortie en cours de traitement sont stockés dans `/app/jobs` dans le conteneur. Le `docker-compose.yml` monte ce dossier sur `./jobs` sur l'hôte pour que les fichiers survivent aux redémarrages du conteneur.

---

## Installation

### Prérequis
- **Python 3.12** recommandé (3.11+ accepté). Évite Python 3.14 et le Python du Microsoft Store : ils provoquent des erreurs de DLL bloquées par Windows Smart App Control.
- Windows, macOS ou Linux.

### Étapes

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer
venv\Scripts\activate     # Windows (PowerShell)
source venv/bin/activate  # Linux / macOS

# Installer les dépendances
pip install -r requirements.txt
```

### Si Streamlit échoue avec une erreur DLL pandas
Sous Windows, installer une version stable de pandas :
```bash
pip install "pandas<3.0"
```

## Utilisation

### Interface web (recommandée)

```bash
streamlit run app.py
```

Ouvre `http://localhost:8501` dans le navigateur. L'interface permet de :
- glisser-déposer un **ZIP** ou un **PDF unique**
- voir la progression du traitement par demande
- télécharger le **ZIP de sortie** contenant tous les Excel produits
- repartir sur un nouveau dossier via le bouton "Nouveau courrier"

### Ligne de commande (CLI)

```bash
# Analyser un PDF (rapport de détection)
python extractor.py scan mon_fichier.pdf

# Extraire les tableaux d'un PDF en Excel
python extractor.py extract mon_fichier.pdf --output resultat.xlsx

# Traiter un dossier entier de PDF
python extractor.py batch ./dossier_pdfs/ --output-dir ./resultats/
```

### Options CLI
- `--output` / `-o` : chemin du fichier Excel de sortie
- `--output-dir` : dossier de sortie (mode batch)
- `--min-cols` : nombre minimum de colonnes pour qu'un tableau soit considéré comme valide (défaut : 8)
- `--verbose` / `-v` : logs détaillés

## Format d'entrée attendu

Le ZIP doit contenir, pour chaque demande, **3 PDF** identifiés par un **préfixe numérique commun** :

| Type | Convention de nom | Rôle |
|---|---|---|
| Courrier | `XXX-Courrier_*.pdf` | Lettre principale du dossier |
| Preuve de dépôt | `XXX-Preuve_de_Depot_*.pdf` | Justificatif de dépôt postal |
| Accusé de réception | `XXX-AR_n_*.pdf` | Accusé de réception (porte le N° de recommandé) |

Où `XXX` est le numéro de demande (ex: `336`, `338`, `346`).

Le ZIP peut être plat ou organisé en sous-dossiers `mails/` et `proof/`.

## Format de sortie

Un ZIP structuré comme suit :

```
Resultats.zip
├── Demande_336/
│   ├── 336-Courrier_xxx.pdf            (PDF original)
│   ├── 336-AR_n_xxx.pdf                (PDF original)
│   ├── 336-Preuve_de_Depot_xxx.pdf     (PDF original)
│   ├── 336_Annexe_Tableaux.xlsx        (tableaux extraits)
│   └── 336_Métadonnées.xlsx            (métadonnées de la demande)
├── Demande_338/
│   └── ...
└── Recapitulatif_Metadonnees.xlsx      (1 ligne par demande, vue d'ensemble)
```

Le détail de chaque colonne, son origine et les règles de calcul sont décrits dans **[GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)**.

## Architecture du code

```
projet_pdftoexcel/
├── app.py                            # Interface Streamlit
├── extractor.py                      # CLI (scan / extract / batch)
├── abbreviations.json                # Abréviations de libellés de voie (RUE→RUE, AVENUE→AV, etc.)
├── commune_somme.json                # Liste de référence des communes (département 80)
├── core/
│   ├── parser.py                     # Parsing PDF et détection de tableaux
│   ├── scanner.py                    # Scan / rapport de détection
│   ├── excel_writer.py               # Génération Excel avec formatage
│   ├── pipeline.py                   # Pipeline complet ZIP → résultats
│   ├── metadata.py                   # Wrapper compat ancien module
│   └── utils.py                      # Utilitaires
├── scripts/
│   ├── raw_extractor.py              # Étape 1 : extraction brute (regex sur PDF)
│   ├── classification.py             # Classification type/catégorie de demande
│   ├── metadata_transformer.py       # Étape 2 : transformation en données métier
│   ├── regex_patterns.py             # Tous les patterns regex centralisés
│   ├── table_data_extractor.py       # Extraction et agrégation des colonnes du tableau
│   └── commune_finder.py             # Détection de la commune dans le texte
├── requirements.txt
├── README.md
└── GUIDE_UTILISATION.md              # Guide détaillé pour l'équipe
```

## Pipeline de traitement

```
ZIP entrée
   │
   ▼
[1] Dézippage et regroupement par préfixe (336, 338, …)
   │
   ▼
[2] Classification de chaque PDF (courrier / dépôt / AR)
   │
   ▼
[3] Extraction brute (RawMetadata)        ──┐
    via regex sur le texte des PDF          │
   │                                        │
   ▼                                        │
[4] Extraction des tableaux                 │
    de l'annexe (pdfplumber)                │
   │                                        │
   ▼                                        │
[5] Agrégation colonnes (TableExtractedData)│
   │                                        │
   ▼                                        │
[6] Transformation métier (ComputedMetadata)◄─┘
    classification, calculs, formatage
   │
   ▼
[7] Génération des Excel (annexe + métadonnées + récap)
   │
   ▼
ZIP de sortie
```

## Stack technique

- **Python 3.12** (3.11+ supporté, 3.14 déconseillé sous Windows)
- **pdfplumber** — lecture PDF et détection de tableaux
- **openpyxl** — création Excel avec formatage
- **pandas** (`<3.0`) — manipulation de données dans l'interface Streamlit
- **typer** — interface CLI
- **streamlit** — interface web

## Contributeurs

Maintenu pour l'équipe **Melko Énergie**. Voir l'historique git pour les contributions.
