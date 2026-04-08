"""Gestion des jobs d'extraction : persistance fichier + etat en memoire.

Chaque job est stocke dans `jobs/{job_id}/` :
  - state.json       : etat courant (status, progress, results summary, etc.)
  - input/           : fichiers uploades (nom original preserve)
  - output.zip       : resultat final (cree en fin de traitement)
"""

import asyncio
import io
import json
import logging
import shutil
import time
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

JOBS_DIR = Path(__file__).resolve().parent.parent / "jobs"
JOBS_DIR.mkdir(exist_ok=True)


@dataclass
class JobState:
    """Etat d'un job d'extraction."""
    job_id: str
    status: str = "uploaded"  # uploaded | running | done | error
    created_at: float = field(default_factory=time.time)
    input_files: list[dict] = field(default_factory=list)  # [{name, size_mb}]
    pdf_count: int = 0
    warnings: list[str] = field(default_factory=list)
    has_standard_structure: bool = False
    # Progress (pendant running)
    progress_current: int = 0
    progress_total: int = 0
    progress_prefix: str = ""
    progress_message: str = ""
    # Results (apres done)
    total_demandes: int = 0
    avec_tableau: int = 0
    sans_tableau: int = 0
    results_rows: list[dict] = field(default_factory=list)  # [{prefix, libelle, statut}]
    errors: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# Index en memoire : job_id -> JobState
_JOBS: dict[str, JobState] = {}
# File des events SSE : job_id -> asyncio.Queue (pousse les events au fur et a mesure)
_QUEUES: dict[str, asyncio.Queue] = {}


def _job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


def _state_path(job_id: str) -> Path:
    return _job_dir(job_id) / "state.json"


def _save_state(state: JobState) -> None:
    """Persiste l'etat sur disque."""
    path = _state_path(state.job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _load_state(job_id: str) -> JobState | None:
    path = _state_path(job_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return JobState(**data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Impossible de charger %s : %s", path, e)
        return None


def create_job() -> JobState:
    """Cree un nouveau job avec un UUID."""
    job_id = uuid.uuid4().hex[:12]
    state = JobState(job_id=job_id)
    _JOBS[job_id] = state
    _save_state(state)
    (_job_dir(job_id) / "input").mkdir(parents=True, exist_ok=True)
    return state


def get_job(job_id: str) -> JobState | None:
    """Recupere un job, depuis la memoire ou depuis le fichier."""
    if job_id in _JOBS:
        return _JOBS[job_id]
    state = _load_state(job_id)
    if state:
        _JOBS[job_id] = state
    return state


def update_job(job_id: str, **kwargs: Any) -> JobState | None:
    """Met a jour un job et persiste. Pousse aussi un event dans la queue SSE."""
    state = get_job(job_id)
    if not state:
        return None
    for k, v in kwargs.items():
        if hasattr(state, k):
            setattr(state, k, v)
    _save_state(state)
    # Push dans la queue SSE si existante
    queue = _QUEUES.get(job_id)
    if queue:
        try:
            queue.put_nowait(state.to_dict())
        except asyncio.QueueFull:
            pass
    return state


def get_sse_queue(job_id: str) -> asyncio.Queue:
    """Recupere (ou cree) la queue SSE pour un job."""
    if job_id not in _QUEUES:
        _QUEUES[job_id] = asyncio.Queue(maxsize=100)
    return _QUEUES[job_id]


def close_sse_queue(job_id: str) -> None:
    """Ferme la queue SSE (quand le stream se termine)."""
    _QUEUES.pop(job_id, None)


def save_input_file(job_id: str, filename: str, content: bytes) -> Path:
    """Sauvegarde un fichier upload dans jobs/{job_id}/input/."""
    input_dir = _job_dir(job_id) / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    path = input_dir / filename
    path.write_bytes(content)
    return path


def save_output_zip(job_id: str, zip_bytes: bytes) -> Path:
    """Sauvegarde le ZIP de resultat."""
    path = _job_dir(job_id) / "output.zip"
    path.write_bytes(zip_bytes)
    return path


def get_output_zip_path(job_id: str) -> Path | None:
    """Retourne le chemin du ZIP de resultat s'il existe."""
    path = _job_dir(job_id) / "output.zip"
    return path if path.exists() else None


def delete_job(job_id: str) -> None:
    """Supprime un job et tous ses fichiers."""
    _JOBS.pop(job_id, None)
    close_sse_queue(job_id)
    d = _job_dir(job_id)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def check_zip_structure(zip_bytes: bytes) -> tuple[bool, int]:
    """Verifie structure mails/+proof/ et compte les PDF."""
    has_mails = False
    has_proof = False
    pdf_count = 0
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for entry in zf.namelist():
                if entry.endswith("/") or "__MACOSX" in entry:
                    continue
                if entry.lower().endswith(".pdf"):
                    pdf_count += 1
                parts = Path(entry).parts
                if len(parts) >= 2:
                    if parts[0].lower() == "mails" or (len(parts) >= 3 and parts[1].lower() == "mails"):
                        has_mails = True
                    if parts[0].lower() == "proof" or (len(parts) >= 3 and parts[1].lower() == "proof"):
                        has_proof = True
    except zipfile.BadZipFile:
        return False, 0
    return (has_mails and has_proof), pdf_count
