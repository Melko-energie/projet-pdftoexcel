"""Etape 2 : Transformation des donnees brutes en donnees metier."""

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .classification import (
    build_libelle,
    deduce_categorie,
    deduce_sous_categorie,
    deduce_type,
)
from .commune_finder import find_commune
from .raw_extractor import RawMetadata, _extract_all_text
from .table_data_extractor import TableExtractedData, extract_from_datasets

logger = logging.getLogger(__name__)


# Detecte une sequence de numeros de maison (separes par , ; "et" &)
# Ex: "9", "14, 16, 18", "9 et 11", "1;3;5"
_NUM_SEQ_RE = re.compile(
    r"\d+(?:\s*(?:,|;|et|&)\s*\d+)*",
    re.IGNORECASE,
)


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _load_abbreviations() -> list[tuple[str, str]]:
    """Charge abbreviations.json (racine projet) et retourne liste (key_norm, abbr)
    triee par longueur decroissante (plus long match d'abord)."""
    path = Path(__file__).resolve().parent.parent / "abbreviations.json"
    if not path.exists():
        logger.warning("abbreviations.json introuvable a %s", path)
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Impossible de charger abbreviations.json : %s", e)
        return []
    flat: dict[str, str] = {}
    for section in data.values():
        if isinstance(section, dict):
            flat.update(section)
    # Normalise les cles (sans accents, majuscules) pour matching
    items = [(_strip_accents(k).upper(), v) for k, v in flat.items()]
    # Trie par longueur de cle decroissante pour que le plus long match gagne
    items.sort(key=lambda kv: -len(kv[0]))
    return items


_ABBREVIATIONS = _load_abbreviations()


def _apply_abbreviations(addr: str) -> str:
    """Remplace les libelles de voie par leur abreviation (abbreviations.json).

    Insensible a la casse et aux accents. Le match le plus long gagne.
    Exemple : "9 Allée des Ecoles" -> "9 ALL des Ecoles"
    """
    if not addr or not _ABBREVIATIONS:
        return addr
    # Travail sur version normalisee (ASCII upper) pour matcher
    norm = _strip_accents(addr).upper()
    consumed = [False] * len(addr)
    replacements: list[tuple[int, int, str]] = []
    for key_norm, val in _ABBREVIATIONS:
        pattern = re.compile(r"\b" + re.escape(key_norm) + r"\b")
        for m in pattern.finditer(norm):
            s, e = m.start(), m.end()
            if any(consumed[s:e]):
                continue
            replacements.append((s, e, val))
            for i in range(s, e):
                consumed[i] = True
    # Applique de droite a gauche pour preserver les indices
    replacements.sort(key=lambda r: -r[0])
    result = addr
    for s, e, val in replacements:
        result = result[:s] + val + result[e:]
    return result


def _expand_address(addr: str) -> list[str]:
    """Dedouble une adresse en adresses individuelles, meme si la cellule
    contient PLUSIEURS voies collees.

    Exemples :
      "9,11,13 et 15 Allée des Ecoles"
        -> ["9 Allée des Ecoles", "11 Allée des Ecoles",
            "13 Allée des Ecoles", "15 Allée des Ecoles"]

      "1 CHE DE BUSSU 14, 16, 18 RUE DE FAY"
        -> ["1 CHE DE BUSSU",
            "14 RUE DE FAY", "16 RUE DE FAY", "18 RUE DE FAY"]

    Strategie : trouve toutes les sequences de numeros ; le texte entre
    une sequence et la suivante (ou la fin) est le libelle de voie.
    Si aucun numero n'est trouve, retourne l'adresse telle quelle.
    """
    if not addr:
        return []
    addr = addr.strip()
    matches = list(_NUM_SEQ_RE.finditer(addr))
    if not matches:
        return [addr]

    results: list[str] = []
    for i, m in enumerate(matches):
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(addr)
        voie = addr[m.end():next_start].strip().rstrip(",;").strip()
        if not voie:
            continue
        numbers = re.findall(r"\d+", m.group(0))
        for n in numbers:
            results.append(f"{n} {voie}")

    return results if results else [addr]

MOIS_FR = {
    "janvier": "01", "février": "02", "fevrier": "02", "mars": "03",
    "avril": "04", "mai": "05", "juin": "06", "juillet": "07",
    "août": "08", "aout": "08", "septembre": "09", "octobre": "10",
    "novembre": "11", "décembre": "12", "decembre": "12",
}


@dataclass
class ComputedMetadata:
    """Donnees metier calculees a partir des donnees brutes."""
    # Identifiant
    numero_dossier: str = ""
    libelle_demande: str = ""
    responsable: str = ""

    # Classification
    type_demande: str = ""
    categorie: str = ""
    sous_categorie: str = ""

    # Montants
    montant_ht: object = ""
    taux_tva: str = ""
    montant_ttc: object = ""
    montant_demande: object = ""

    # Entreprise
    nom_entreprise: str = ""
    nature_travaux: str = ""
    nature_depenses: str = "Degrevement taxe fonciere"

    # References
    ref_avis: str = ""
    adresse: str = ""
    numero_programme: str = ""
    nombre_logements: int = 0
    numero_operation: str = ""

    # Envoi
    date_limite_envoi: str = ""
    type_envoi: str = ""
    numero_recommande: str = ""

    # Interlocuteur
    nom_interlocuteur: str = ""
    prenom_interlocuteur: str = ""
    mail_interlocuteur: str = ""
    tel_interlocuteur: str = ""

    # Divers
    commentaire: str = ""
    lien_escale: str = ""
    montant_subvention: object = ""

    # Flags de verification (non ecrits en cellule, utilises pour styling)
    montant_ttc_check_ok: bool = True


def parse_montant(raw: str) -> float:
    """Convertit '55 245' ou '106 281,50' en float."""
    if not raw or not raw.strip():
        return 0.0
    text = raw.strip()
    text = re.sub(r"\s+", "", text)
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def format_date_fr(raw: str) -> str:
    """Convertit '29 decembre 2025' en '29/12/2025'."""
    if not raw or not raw.strip():
        return ""
    text = raw.strip()

    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", text):
        return text

    match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if match:
        day = match.group(1).zfill(2)
        month_str = match.group(2).lower()
        year = match.group(3)
        month = MOIS_FR.get(month_str, "")
        if month:
            return f"{day}/{month}/{year}"

    return text


def extract_entreprise(courrier_bytes: bytes | None) -> str:
    """Extrait le nom de l'entreprise/bailleur depuis le texte du courrier."""
    if not courrier_bytes:
        return ""
    text, _ = _extract_all_text(courrier_bytes)
    if not text:
        return ""

    match = re.search(
        r"mandataire\s+de\s+(?:la\s+)?(.+?)(?:\n|,|\.)",
        text, re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    match = re.search(
        r"pour\s+le\s+compte\s+de\s+(?:la\s+)?(.+?)(?:\n|,|\.)",
        text, re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    return ""


def extract_numero_programme_from_tables(datasets) -> str:
    """Extrait le N de programme depuis la premiere ligne du tableau annexe."""
    if not datasets:
        return ""

    for ds in datasets:
        headers_lower = [h.lower().replace("\n", " ") for h in ds.headers]
        prog_idx = None
        for i, h in enumerate(headers_lower):
            if "programme" in h:
                prog_idx = i
                break

        if prog_idx is not None and ds.data_rows:
            for row in ds.data_rows:
                if prog_idx < len(row) and row[prog_idx]:
                    val = str(row[prog_idx]).strip()
                    if val:
                        return val

    return ""


def compute_metadata(
    raw: RawMetadata,
    datasets=None,
    courrier_bytes: bytes | None = None,
    table_data: TableExtractedData | None = None,
    prefix: str = "",
) -> ComputedMetadata:
    """Transforme RawMetadata en ComputedMetadata.

    Args:
        raw: Donnees brutes extraites des PDF.
        datasets: Datasets du parser (fallback si table_data absent).
        courrier_bytes: Bytes du courrier pour extraction entreprise.
        table_data: Donnees extraites des colonnes des tableaux (prioritaire).
        prefix: Prefixe numerique du dossier (N° Dossier).
    """
    c = ComputedMetadata()
    c.numero_dossier = prefix

    # Extraire table_data depuis datasets si pas fourni
    if table_data is None and datasets:
        table_data = extract_from_datasets(datasets)

    # --- Classification (basee sur le texte, pas le nom de fichier) ---
    full_text = raw.full_text or ""
    c.type_demande = deduce_type(raw.objet_complet, full_text)
    c.categorie = deduce_categorie(c.type_demande, raw.motif_vacance, raw.objet_complet, full_text)

    # Sous-categorie : chercher dans l'objet + nature travaux du tableau (pas full_text)
    nature_from_table = table_data.nature_travaux if table_data else ""
    c.sous_categorie = deduce_sous_categorie(c.type_demande, c.categorie, raw.objet_complet, nature_from_table)

    # --- Commentaire = objet exact du courrier ---
    c.commentaire = raw.objet_complet

    # --- Numero programme et commune (tableau prioritaire, puis fallback texte) ---
    if table_data and table_data.numero_programme:
        c.numero_programme = table_data.numero_programme
    else:
        c.numero_programme = extract_numero_programme_from_tables(datasets)

    # Commune : chercher dans le texte du courrier via la liste officielle
    commune = find_commune(raw.text_page1, raw.objet_complet)
    # Fallback sur le tableau si pas trouve
    if not commune and table_data:
        commune = table_data.commune
    if not commune:
        commune = raw.commune

    # --- Libelle ---
    # Libelle avec categorie (pas type)
    cat_label = f"{c.type_demande} {c.categorie}".strip() if c.categorie else c.type_demande
    c.libelle_demande = build_libelle(raw.annee_fiscale, cat_label, c.numero_programme, commune)

    # --- Responsable (valeur fixe) ---
    c.responsable = "Amaury MONGONGU"

    # --- Champs extraits du tableau (remplis si disponibles) ---
    if table_data:
        # Montant HT = somme du tableau extrait, stocke en float (pas str) pour Excel
        c.montant_ht = float(table_data.montant_ht_total) if table_data.montant_ht_total else ""
        c.nom_entreprise = table_data.nom_entreprise if table_data.nom_entreprise else ""
        c.taux_tva = table_data.taux_tva if table_data.taux_tva else ""
        c.nature_travaux = table_data.nature_travaux if table_data.nature_travaux else ""
        # Montant TTC = somme du tableau extrait (float pour format Excel)
        c.montant_ttc = float(table_data.montant_ttc_total) if table_data.montant_ttc_total else ""
        c.montant_ttc_check_ok = table_data.montant_ttc_check_ok
        c.montant_subvention = table_data.montant_subvention if table_data.montant_subvention else ""
    else:
        c.montant_ht = ""
        c.nom_entreprise = ""
        c.taux_tva = ""
        c.nature_travaux = ""
        c.montant_ttc = ""
        c.montant_subvention = ""

    c.nature_depenses = "Degrevement taxe fonciere"

    # Montant demande : tableau (somme) prioritaire, sinon texte courrier
    if table_data and table_data.montant_degrevement > 0:
        c.montant_demande = table_data.montant_degrevement
    else:
        c.montant_demande = parse_montant(raw.montant_degrevement)

    # --- References (tableau prioritaire, sinon texte courrier) ---
    if table_data and table_data.references_avis:
        c.ref_avis = table_data.references_avis
    else:
        c.ref_avis = raw.ref_avis_imposition.strip()
    # Supprime les espaces a l'interieur de chaque reference (ex: "24 80 4122964 12" -> "2480412296412")
    c.ref_avis = ";".join(part.replace(" ", "") for part in c.ref_avis.split(";"))

    # Adresse : tableau prioritaire (plus fiable), sinon texte courrier
    if table_data and table_data.adresse:
        c.adresse = table_data.adresse
    else:
        c.adresse = raw.adresses
    # Remplace toutes les apostrophes (droites et typographiques) par un espace
    c.adresse = c.adresse.replace("\u2019", " ").replace("'", " ")
    # Dedoublage des adresses multi-numeros, multi-voies, puis abreviation,
    # puis deduplication en preservant l'ordre.
    if c.adresse:
        seen: set[str] = set()
        unique: list[str] = []
        for part in c.adresse.split(";"):
            for sub in _expand_address(part):
                final = _apply_abbreviations(sub)
                if final and final not in seen:
                    seen.add(final)
                    unique.append(final)
        # Mise en forme selon la parite du numero en tete d'adresse :
        # - Numeros pairs : restent groupes sur une meme ligne, separes par ";"
        # - Numeros impairs : chaque adresse sur sa propre ligne (";\n" entre chacune)
        # - Cas mixte : pairs d'abord (meme ligne), puis retour ligne, puis impairs
        # - Adresses sans numero en tete : conservees en fin, separees par ";" (inchange)
        pairs_list: list[str] = []
        odds_list: list[str] = []
        others_list: list[str] = []
        for adr in unique:
            m = re.match(r"\s*(\d+)", adr)
            if m:
                if int(m.group(1)) % 2 == 0:
                    pairs_list.append(adr)
                else:
                    odds_list.append(adr)
            else:
                others_list.append(adr)
        groups: list[str] = []
        if pairs_list:
            groups.append(";".join(pairs_list))
        if odds_list:
            groups.append(";\n".join(odds_list))
        if others_list:
            groups.append(";".join(others_list))
        c.adresse = ";\n".join(groups) if len(groups) > 1 else (groups[0] if groups else "")

    try:
        c.nombre_logements = int(raw.nombre_logements) if raw.nombre_logements else 0
    except ValueError:
        c.nombre_logements = 0
    c.numero_operation = table_data.n_operation if table_data else ""

    # --- Envoi ---
    # Date limite = 31/12 de l'annee suivant l'annee fiscale
    if raw.annee_fiscale:
        try:
            c.date_limite_envoi = f"31/12/{int(raw.annee_fiscale) + 2}"
        except ValueError:
            c.date_limite_envoi = format_date_fr(raw.date_limite_envoi)
    else:
        c.date_limite_envoi = format_date_fr(raw.date_limite_envoi)

    # Type d'envoi (valeur fixe)
    c.type_envoi = "RecommandeAvecAR"

    # Numero de recommande : exclusivement depuis l'AR (accuse de reception)
    c.numero_recommande = raw.numero_lr_ar

    # --- Interlocuteur (valeurs fixes) ---
    c.nom_interlocuteur = "JOUHANNET"
    c.prenom_interlocuteur = "Alexis"
    c.mail_interlocuteur = "alexis.jouhannet@dgfip.finances.gouv.fr"
    c.tel_interlocuteur = "0322468319"

    # --- Divers ---
    c.lien_escale = ""

    return c


def computed_metadata_to_rows(c: ComputedMetadata) -> list[tuple[str, object]]:
    """Convertit ComputedMetadata en liste ordonnee de (label, valeur) pour Excel."""
    return [
        ("N° Dossier", c.numero_dossier),
        ("Libelle de la Demande", c.libelle_demande),
        ("Responsable", c.responsable),
        ("Type", c.type_demande),
        ("Categorie", c.categorie),
        ("Sous-categorie", c.sous_categorie),
        ("Montant HT", c.montant_ht),
        ("Nom de l'entreprise", c.nom_entreprise),
        ("Taux de TVA", c.taux_tva),
        ("Nature des travaux", c.nature_travaux),
        ("Montant TTC", c.montant_ttc),
        ("Montant de la subvention", c.montant_subvention),
        ("Reference(s) Avis", c.ref_avis),
        ("Adresse", c.adresse),
        ("Montant de la demande", c.montant_demande),
        ("Date limite d'envoi", c.date_limite_envoi),
        ("Type d'envoi", c.type_envoi),
        ("Numero de recommande", c.numero_recommande),
        ("Commentaire", c.commentaire),
        ("Lien escale", c.lien_escale),
        ("Nom interlocuteur", c.nom_interlocuteur),
        ("Prenom interlocuteur", c.prenom_interlocuteur),
        ("Mail interlocuteur", c.mail_interlocuteur),
        ("Tel interlocuteur", c.tel_interlocuteur),
        ("N° Programme", c.numero_programme),
        ("Nombre de logements", c.nombre_logements),
        ("Nature de depenses", c.nature_depenses),
        ("N° d'operation", c.numero_operation),
    ]


def computed_metadata_red_keys(c: ComputedMetadata) -> set[str]:
    """Retourne l'ensemble des labels de cellules a colorer en rouge (verifications echouees)."""
    red: set[str] = set()
    if not c.montant_ttc_check_ok:
        red.add("Montant TTC")
    return red
