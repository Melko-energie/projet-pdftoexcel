"""Application FastAPI — remplace l'interface Streamlit.

Lancement :
    uvicorn web.main:app --reload --port 8000
"""

import asyncio
import io
import json
import logging
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.pipeline import (
    DemandeDossier,
    build_output_zip,
    process_demande,
    process_zip,
)

from . import jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="PDF Table Extractor")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
# Disable Jinja2 cache to work around a Python 3.14 unhashable-key bug
templates.env.cache = None


# --- Pages ---


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Accueil : zone de drop."""
    return templates.TemplateResponse(
        request, "accueil.html", {"active_page": "accueil"}
    )


@app.get("/validation/{job_id}", response_class=HTMLResponse)
async def validation_page(request: Request, job_id: str):
    """Page de validation des fichiers deposes."""
    state = jobs.get_job(job_id)
    if not state:
        raise HTTPException(404, "Job introuvable")
    return templates.TemplateResponse(
        request, "validation.html", {"state": state, "active_page": "accueil"}
    )


@app.get("/traitement/{job_id}", response_class=HTMLResponse)
async def traitement_page(request: Request, job_id: str):
    """Page de traitement en cours avec progression SSE."""
    state = jobs.get_job(job_id)
    if not state:
        raise HTTPException(404, "Job introuvable")
    return templates.TemplateResponse(
        request, "traitement.html", {"state": state, "active_page": "accueil"}
    )


@app.get("/resultats/{job_id}", response_class=HTMLResponse)
async def resultats_page(request: Request, job_id: str):
    """Page de resultats finaux."""
    state = jobs.get_job(job_id)
    if not state:
        raise HTTPException(404, "Job introuvable")
    return templates.TemplateResponse(
        request, "resultats.html", {"state": state, "active_page": "extractions"}
    )


# --- API ---


@app.post("/upload")
async def upload(
    files: list[UploadFile] = File(...),
    min_cols: int = Form(8),
):
    """Receptionne les fichiers deposes, cree un job ET lance l'extraction.

    Retourne un redirect vers /traitement/{job_id}.
    """
    if not files:
        raise HTTPException(400, "Aucun fichier recu")

    state = jobs.create_job()
    warnings: list[str] = []
    input_files_meta: list[dict] = []
    total_pdf_count = 0
    has_structure = False

    for up in files:
        content = await up.read()
        size_mb = len(content) / (1024 * 1024)
        filename = up.filename or "file"

        jobs.save_input_file(state.job_id, filename, content)
        input_files_meta.append({"name": filename, "size_mb": round(size_mb, 2)})

        if size_mb > 50:
            warnings.append(f"`{filename}` fait {size_mb:.0f} MB — le traitement peut prendre du temps.")

        # Si ZIP, analyse la structure
        if filename.lower().endswith(".zip"):
            structure_ok, pdf_count = jobs.check_zip_structure(content)
            total_pdf_count += pdf_count
            if structure_ok:
                has_structure = True
            if pdf_count == 0:
                warnings.append(
                    f"`{filename}` ne contient aucun PDF. "
                    "Verifiez que vos courriers sont dans `mails/` et `proof/`."
                )
            elif not structure_ok:
                warnings.append(
                    f"`{filename}` : structure atypique. "
                    "Les fichiers seront analyses individuellement."
                )
        elif filename.lower().endswith(".pdf"):
            total_pdf_count += 1

    jobs.update_job(
        state.job_id,
        status="running",
        input_files=input_files_meta,
        pdf_count=total_pdf_count,
        warnings=warnings,
        has_standard_structure=has_structure,
    )

    # Lance directement le traitement en arriere-plan
    asyncio.create_task(_run_extraction_task(state.job_id, min_cols))
    return RedirectResponse(url=f"/traitement/{state.job_id}", status_code=303)


@app.post("/start/{job_id}")
async def start_extraction(job_id: str, min_cols: int = Form(8)):
    """Lance le traitement en background et redirige vers la page de progression."""
    state = jobs.get_job(job_id)
    if not state:
        raise HTTPException(404, "Job introuvable")
    if state.status == "running":
        return RedirectResponse(url=f"/traitement/{job_id}", status_code=303)

    jobs.update_job(job_id, status="running", progress_current=0, progress_total=0)
    # Lance la tache en background (thread pour ne pas bloquer la loop async)
    asyncio.create_task(_run_extraction_task(job_id, min_cols))
    return RedirectResponse(url=f"/traitement/{job_id}", status_code=303)


@app.get("/progress/{job_id}")
async def progress_stream(job_id: str):
    """Server-Sent Events : stream du progres en temps reel."""
    state = jobs.get_job(job_id)
    if not state:
        raise HTTPException(404, "Job introuvable")

    queue = jobs.get_sse_queue(job_id)

    async def event_generator():
        # Emet l'etat courant immediatement
        yield f"data: {json.dumps(state.to_dict(), ensure_ascii=False)}\n\n"
        # Puis stream les updates
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # Keep-alive ping
                yield ": ping\n\n"
                continue
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            if data.get("status") in ("done", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/guide")
async def guide():
    """Sert le guide d'utilisation PDF inline dans le navigateur."""
    guide_path = BASE_DIR.parent / "Guide_Utilisation_Melko.pdf"
    if not guide_path.exists():
        raise HTTPException(404, "Guide d'utilisation introuvable")
    return FileResponse(
        path=guide_path,
        filename="Guide_Utilisation_Melko.pdf",
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=Guide_Utilisation_Melko.pdf"},
    )


@app.get("/download/{job_id}")
async def download(job_id: str):
    """Telecharge le ZIP resultat."""
    path = jobs.get_output_zip_path(job_id)
    if not path:
        raise HTTPException(404, "ZIP de resultat introuvable (traitement en cours ou echec ?)")
    return FileResponse(
        path=path,
        filename="resultats_extraction.zip",
        media_type="application/zip",
    )


@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Supprime un job (utilise par 'Nouveau courrier')."""
    jobs.delete_job(job_id)
    return {"status": "deleted"}


# --- Background task ---


async def _run_extraction_task(job_id: str, min_cols: int) -> None:
    """Execute le pipeline en thread pool et met a jour le job."""
    try:
        await asyncio.to_thread(_process_job_sync, job_id, min_cols)
    except Exception as e:
        logger.exception("Erreur dans le traitement du job %s", job_id)
        jobs.update_job(job_id, status="error", error=str(e))


def _process_job_sync(job_id: str, min_cols: int) -> None:
    """Traitement synchrone (execute dans un thread)."""
    state = jobs.get_job(job_id)
    if not state:
        return

    input_dir = jobs.JOBS_DIR / job_id / "input"
    if not input_dir.exists():
        jobs.update_job(job_id, status="error", error="Repertoire d'entree introuvable")
        return

    all_files = list(input_dir.iterdir())
    zip_files = [f for f in all_files if f.suffix.lower() == ".zip"]
    pdf_files = [f for f in all_files if f.suffix.lower() == ".pdf"]

    results = []
    errors: list[str] = []

    def on_progress(current: int, total: int, prefix: str) -> None:
        jobs.update_job(
            job_id,
            progress_current=current + 1 if current + 1 <= total else total,
            progress_total=total,
            progress_prefix=prefix,
            progress_message=f"Traitement de la demande {prefix} ({current + 1}/{total})",
        )

    # Traite le premier ZIP trouve (comme l'ancienne app Streamlit)
    if zip_files:
        zip_data = zip_files[0].read_bytes()
        jobs.update_job(
            job_id,
            progress_message="Analyse du lot de demandes…",
        )
        results = process_zip(zip_data, min_cols=min_cols, on_progress=on_progress)
        for r in results:
            if r.error:
                errors.append(f"Dossier {r.prefix} : {r.error}")
            if not r.datasets and r.source_pdfs.get("courrier"):
                errors.append(f"Dossier {r.prefix} : aucun tableau fiscal trouve.")

    elif pdf_files:
        total = len(pdf_files)
        for idx, f in enumerate(pdf_files):
            prefix = f.stem.split("-")[0]
            on_progress(idx, total, prefix)
            try:
                dossier = DemandeDossier(
                    prefix=prefix,
                    courrier_pdf=f.read_bytes(),
                    courrier_filename=f.name,
                )
                result = process_demande(dossier, min_cols=min_cols)
                results.append(result)
                if result.error:
                    errors.append(f"`{f.name}` : {result.error}")
                if not result.datasets:
                    errors.append(f"`{f.name}` : aucun tableau fiscal trouve.")
            except Exception as e:
                errors.append(f"Erreur sur `{f.name}` : {e}")

    # Construit le ZIP de sortie
    if results:
        output_zip = build_output_zip(results)
        jobs.save_output_zip(job_id, output_zip)

    # Prepare le resume
    total_demandes = len(results)
    avec_tableau = sum(1 for r in results if r.annexe_excel)
    sans_tableau = total_demandes - avec_tableau
    results_rows = []
    for r in results:
        libelle = r.computed_metadata.libelle_demande if r.computed_metadata else ""
        statut = "Annexe" if r.annexe_excel else "Info seule"
        results_rows.append({
            "prefix": r.prefix,
            "libelle": libelle,
            "statut": statut,
        })

    jobs.update_job(
        job_id,
        status="done",
        total_demandes=total_demandes,
        avec_tableau=avec_tableau,
        sans_tableau=sans_tableau,
        results_rows=results_rows,
        errors=errors,
        progress_current=max(1, state.progress_total),
        progress_message="Extraction terminee.",
    )
