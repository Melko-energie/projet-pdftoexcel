"""Etape 1 : Extraction brute des metadonnees depuis les PDF."""

import io
import logging
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from . import regex_patterns as P

logger = logging.getLogger(__name__)


def _clean(text: str) -> str:
    """Nettoie le texte : supprime retours a la ligne, espaces multiples."""
    text = text.replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def _search(pattern: re.Pattern, text: str, group: int = 1) -> str:
    """Recherche un pattern, retourne le groupe ou ''."""
    match = pattern.search(text)
    if match:
        return _clean(match.group(group))
    return ""


def _extract_all_text(pdf_bytes: bytes) -> str:
    """Extrait le texte de toutes les pages d'un PDF depuis des bytes."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp.write(pdf_bytes)
        tmp.close()
        with pdfplumber.open(tmp.name) as pdf:
            pages_text = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            return "\n".join(pages_text)
    except Exception as e:
        logger.warning("Impossible de lire le PDF : %s", e)
        return ""
    finally:
        Path(tmp.name).unlink(missing_ok=True)


@dataclass
class RawMetadata:
    """Donnees brutes extraites directement des PDF par regex."""
    # Depuis le courrier
    numero_demande: str = ""
    annee_fiscale: str = ""
    objet_complet: str = ""
    adresses: str = ""
    motif_vacance: str = ""
    responsable: str = ""
    email_responsable: str = ""
    date_courrier: str = ""
    date_limite_envoi: str = ""
    ref_avis_imposition: str = ""
    montant_total_imposition: str = ""
    montant_degrevement: str = ""
    montant_cotisations_sans_frais: str = ""
    frais_gestion: str = ""
    nombre_logements: str = ""
    articles_cgi: list[str] = field(default_factory=list)
    code_postal: str = ""
    commune: str = ""
    nom_destinataire: str = ""

    # Interlocuteur
    interlocuteur_nom: str = ""
    interlocuteur_prenom: str = ""
    interlocuteur_tel: str = ""

    # Champs conditionnels (extraits si sous-categorie existe)
    montant_ht_raw: str = ""
    entreprise_travaux: str = ""
    taux_tva_raw: str = ""
    nature_travaux_raw: str = ""
    montant_ttc_raw: str = ""
    montant_subvention_raw: str = ""

    # Texte complet du courrier (pour classification)
    full_text: str = ""

    # Depuis la preuve de depot
    numero_lr_depot: str = ""
    date_depot: str = ""

    # Depuis l'AR
    numero_lr_ar: str = ""
    date_presentation_ar: str = ""
    date_distribution_ar: str = ""
    receptionnaire_ar: str = ""


def extract_interlocuteur(text: str) -> tuple[str, str]:
    """Extrait nom et prenom de l'interlocuteur (destinataire du courrier).

    Returns:
        (nom, prenom) — nom en MAJUSCULES, prenom avec initiale majuscule.
    """
    match = P.PATTERN_INTERLOCUTEUR.search(text)
    if match:
        prenom = match.group(1) or ""
        nom = match.group(2) or ""
        return nom.strip(), prenom.strip()
    return "", ""


def extract_tel_interlocuteur(text: str) -> str:
    """Extrait le telephone de l'interlocuteur depuis le texte complet du PDF."""
    match = P.PATTERN_TEL.search(text)
    if match:
        return match.group(1).strip()
    return ""


def extract_conditional_fields(text: str) -> dict:
    """Extrait les 6 champs conditionnels depuis le texte du courrier."""
    return {
        "montant_ht_raw": _search(P.PATTERN_MONTANT_HT, text),
        "entreprise_travaux": _search(P.PATTERN_ENTREPRISE_TRAVAUX, text),
        "taux_tva_raw": _search(P.PATTERN_TAUX_TVA, text),
        "nature_travaux_raw": _search(P.PATTERN_NATURE_TRAVAUX, text),
        "montant_ttc_raw": _search(P.PATTERN_MONTANT_TTC, text),
        "montant_subvention_raw": _search(P.PATTERN_MONTANT_SUBVENTION, text),
    }


def extract_raw_from_courrier(pdf_bytes: bytes) -> dict:
    """Extrait toutes les donnees brutes du courrier PDF."""
    text = _extract_all_text(pdf_bytes)
    if not text:
        return {}

    result = {}
    result["full_text"] = text

    result["numero_demande"] = _search(P.PATTERN_NUM_DEMANDE, text)

    # Annee fiscale : chaine de priorite
    annee = ""
    for pattern in [
        P.PATTERN_ANNEE_TFPB,
        P.PATTERN_ANNEE_TITRE,
        P.PATTERN_ANNEE_TITRE_TFPB,
    ]:
        annee = _search(pattern, text)
        if annee:
            break
    # Fallback : premier 20XX entre 2020 et 2030
    if not annee:
        for match in P.PATTERN_ANNEE_FALLBACK.finditer(text):
            try:
                y = int(match.group(1))
                if 2020 <= y <= 2030:
                    annee = match.group(1)
                    break
            except ValueError:
                continue
    result["annee_fiscale"] = annee

    result["objet_complet"] = _search(P.PATTERN_OBJET, text)
    result["adresses"] = _search(P.PATTERN_ADRESSES, text)
    result["motif_vacance"] = _search(P.PATTERN_MOTIF, text)
    result["responsable"] = _search(P.PATTERN_RESPONSABLE, text)
    result["email_responsable"] = _search(P.PATTERN_EMAIL, text, 0)

    # Date courrier : essayer le format principal puis l'alternatif
    date = _search(P.PATTERN_DATE_COURRIER, text)
    if not date:
        date = _search(P.PATTERN_DATE_COURRIER_ALT, text)
    result["date_courrier"] = date

    result["date_limite_envoi"] = _search(P.PATTERN_DATE_LIMITE, text)
    result["ref_avis_imposition"] = _search(P.PATTERN_REF_AVIS, text)
    result["montant_total_imposition"] = _search(P.PATTERN_MONTANT_TOTAL, text)
    result["montant_degrevement"] = _search(P.PATTERN_MONTANT_DEGREVEMENT, text)
    result["montant_cotisations_sans_frais"] = _search(P.PATTERN_MONTANT_COTISATIONS, text)
    result["frais_gestion"] = _search(P.PATTERN_FRAIS_GESTION, text)

    # Nombre de logements : premier match
    result["nombre_logements"] = _search(P.PATTERN_NB_LOGEMENTS, text)

    # Articles CGI : tous les matches
    articles = P.PATTERN_ARTICLES_CGI.findall(text)
    result["articles_cgi"] = list(dict.fromkeys(articles))  # deduplique en gardant l'ordre

    # Code postal et commune
    cp_match = P.PATTERN_CODE_POSTAL.search(text)
    if cp_match:
        result["code_postal"] = cp_match.group(1)
        result["commune"] = cp_match.group(2)
    else:
        result["code_postal"] = ""
        result["commune"] = ""

    result["nom_destinataire"] = _search(P.PATTERN_DESTINATAIRE, text)

    # Interlocuteur (destinataire du courrier)
    nom_inter, prenom_inter = extract_interlocuteur(text)
    result["interlocuteur_nom"] = nom_inter
    result["interlocuteur_prenom"] = prenom_inter
    result["interlocuteur_tel"] = extract_tel_interlocuteur(text)

    # Champs conditionnels (seront utilises si sous-categorie non vide)
    cond = extract_conditional_fields(text)
    result.update(cond)

    return result


def extract_raw_from_ar(pdf_bytes: bytes) -> dict:
    """Extrait N LR, dates, receptionnaire depuis l'AR."""
    text = _extract_all_text(pdf_bytes)
    if not text:
        return {}

    result = {}
    result["numero_lr_ar"] = _search(P.PATTERN_NUM_LR, text)
    result["date_presentation_ar"] = _search(P.PATTERN_PRESENTATION_AR, text)
    result["date_distribution_ar"] = _search(P.PATTERN_DISTRIBUTION_AR, text)
    result["receptionnaire_ar"] = _search(P.PATTERN_RECEPTIONNAIRE, text)

    return result


def extract_raw_from_depot(pdf_bytes: bytes) -> dict:
    """Extrait N LR, date depuis la preuve de depot."""
    text = _extract_all_text(pdf_bytes)
    if not text:
        return {}

    result = {}
    result["numero_lr_depot"] = _search(P.PATTERN_NUM_LR, text)

    # Premiere date au format dd/mm/yyyy
    result["date_depot"] = _search(P.PATTERN_DATE_DDMMYYYY, text)

    return result


def build_raw_metadata(
    courrier_bytes: bytes | None = None,
    ar_bytes: bytes | None = None,
    depot_bytes: bytes | None = None,
    courrier_filename: str = "",
) -> RawMetadata:
    """Combine les 3 sources en un seul RawMetadata."""
    raw = RawMetadata()

    if courrier_bytes:
        data = extract_raw_from_courrier(courrier_bytes)
        raw.full_text = data.get("full_text", "")
        raw.numero_demande = data.get("numero_demande", "")
        raw.annee_fiscale = data.get("annee_fiscale", "")
        raw.objet_complet = data.get("objet_complet", "")
        raw.adresses = data.get("adresses", "")
        raw.motif_vacance = data.get("motif_vacance", "")
        raw.responsable = data.get("responsable", "")
        raw.email_responsable = data.get("email_responsable", "")
        raw.date_courrier = data.get("date_courrier", "")
        raw.date_limite_envoi = data.get("date_limite_envoi", "")
        raw.ref_avis_imposition = data.get("ref_avis_imposition", "")
        raw.montant_total_imposition = data.get("montant_total_imposition", "")
        raw.montant_degrevement = data.get("montant_degrevement", "")
        raw.montant_cotisations_sans_frais = data.get("montant_cotisations_sans_frais", "")
        raw.frais_gestion = data.get("frais_gestion", "")
        raw.nombre_logements = data.get("nombre_logements", "")
        raw.articles_cgi = data.get("articles_cgi", [])
        raw.code_postal = data.get("code_postal", "")
        raw.commune = data.get("commune", "")
        raw.nom_destinataire = data.get("nom_destinataire", "")

        # Interlocuteur
        raw.interlocuteur_nom = data.get("interlocuteur_nom", "")
        raw.interlocuteur_prenom = data.get("interlocuteur_prenom", "")
        raw.interlocuteur_tel = data.get("interlocuteur_tel", "")

        # Champs conditionnels
        raw.montant_ht_raw = data.get("montant_ht_raw", "")
        raw.entreprise_travaux = data.get("entreprise_travaux", "")
        raw.taux_tva_raw = data.get("taux_tva_raw", "")
        raw.nature_travaux_raw = data.get("nature_travaux_raw", "")
        raw.montant_ttc_raw = data.get("montant_ttc_raw", "")
        raw.montant_subvention_raw = data.get("montant_subvention_raw", "")

    # Fallback N demande depuis le nom de fichier
    if not raw.numero_demande and courrier_filename:
        match = re.match(r"^(\d+)", courrier_filename)
        if match:
            raw.numero_demande = match.group(1)

    if ar_bytes:
        data = extract_raw_from_ar(ar_bytes)
        raw.numero_lr_ar = data.get("numero_lr_ar", "")
        raw.date_presentation_ar = data.get("date_presentation_ar", "")
        raw.date_distribution_ar = data.get("date_distribution_ar", "")
        raw.receptionnaire_ar = data.get("receptionnaire_ar", "")

    if depot_bytes:
        data = extract_raw_from_depot(depot_bytes)
        raw.numero_lr_depot = data.get("numero_lr_depot", "")
        raw.date_depot = data.get("date_depot", "")

    return raw
