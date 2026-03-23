"""Interface Streamlit pour PDF Table Extractor."""

import io
import tempfile
from pathlib import Path

import streamlit as st

from core.parser import process_tables
from core.pipeline import build_output_zip, process_zip
from core.scanner import scan_pdf

MIN_COLS = 8


def main():
    st.set_page_config(
        page_title="PDF Table Extractor",
        page_icon="📄",
    )

    st.title("📄 PDF Table Extractor")

    with st.sidebar:
        st.header("PDF Table Extractor")
        st.divider()
        run_button = st.button(
            "Lancer l'extraction",
            type="primary",
            use_container_width=True,
        )

    uploaded_files = st.file_uploader(
        "Glissez-déposez vos fichiers PDF ou un fichier ZIP",
        type=["pdf", "zip"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Uploadez un fichier ZIP ou des fichiers PDF pour commencer.")
        return

    if not run_button:
        return

    # Detect mode
    zip_files = [f for f in uploaded_files if f.name.lower().endswith(".zip")]

    if zip_files:
        zip_data = zip_files[0].getvalue()
        progress = st.progress(0, text="Traitement en cours...")

        def on_progress(current, total, prefix):
            if total > 0 and prefix:
                progress.progress(current / total, text=f"Demande {prefix}...")

        results = process_zip(zip_data, min_cols=MIN_COLS, on_progress=on_progress)
        progress.progress(1.0, text="Terminé !")

        if not results:
            st.warning("Aucune demande trouvée dans le ZIP.")
            return

        st.markdown("**Demandes traitées :**")
        for r in results:
            st.markdown(f"- Demande {r.prefix}")

        output_data = build_output_zip(results)
        st.download_button(
            label="Télécharger le résultat (.zip)",
            data=output_data,
            file_name="resultats_extraction.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )

    else:
        # Mode PDF simple — même logique, packagé en ZIP
        from core.pipeline import (
            DemandeDossier,
            process_demande,
        )

        progress = st.progress(0, text="Traitement en cours...")
        results = []

        for idx, f in enumerate(uploaded_files):
            progress.progress(idx / len(uploaded_files), text=f"Traitement de {f.name}...")
            prefix = Path(f.name).stem.split("-")[0]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(f.getbuffer())
            tmp.close()

            dossier = DemandeDossier(
                prefix=prefix,
                courrier_pdf=Path(tmp.name).read_bytes(),
                courrier_filename=f.name,
            )
            result = process_demande(dossier, min_cols=MIN_COLS)
            results.append(result)
            Path(tmp.name).unlink(missing_ok=True)

        progress.progress(1.0, text="Terminé !")

        if not results:
            st.warning("Aucun résultat.")
            return

        st.markdown("**Demandes traitées :**")
        for r in results:
            st.markdown(f"- Demande {r.prefix}")

        output_data = build_output_zip(results)
        st.download_button(
            label="Télécharger le résultat (.zip)",
            data=output_data,
            file_name="resultats_extraction.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
