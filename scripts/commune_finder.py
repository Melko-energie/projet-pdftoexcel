"""Recherche de commune dans le texte du courrier via la liste officielle."""

import json
import re
from pathlib import Path

_COMMUNES_CACHE: list[str] | None = None


def load_communes() -> list[str]:
    """Charge la liste des communes depuis le JSON, triee par longueur decroissante."""
    global _COMMUNES_CACHE
    if _COMMUNES_CACHE is not None:
        return _COMMUNES_CACHE

    json_path = Path(__file__).parent.parent / "commune_somme.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    communes = [c["nom"].upper() for c in data["communes"]]
    # Trier par longueur decroissante pour matcher les noms composes en priorite
    communes.sort(key=len, reverse=True)
    _COMMUNES_CACHE = communes
    return _COMMUNES_CACHE


def find_commune(text_page1: str, objet: str) -> str:
    """Cherche un nom de commune dans l'objet puis dans le texte de la page 1.

    Recherche insensible a la casse, avec word boundary pour eviter les faux positifs.
    Retourne le nom en MAJUSCULES ou "" si aucune commune trouvee.
    """
    communes = load_communes()

    # Chercher d'abord dans l'objet (plus fiable)
    objet_upper = objet.upper()
    for commune in communes:
        if re.search(r"\b" + re.escape(commune) + r"\b", objet_upper):
            return commune

    # Sinon dans le texte de la page 1
    text_upper = text_page1.upper()
    for commune in communes:
        if re.search(r"\b" + re.escape(commune) + r"\b", text_upper):
            return commune

    return ""
