# Bouton "Nouveau courrier" — Guide d'implementation

## Contexte

Ajout d'un bouton "Nouveau courrier" dans l'interface Streamlit permettant a l'utilisateur
de reinitialiser l'application et uploader un nouveau fichier a tout moment :
avant l'extraction, pendant l'upload, et apres le telechargement des resultats.

## Probleme resolu

Le `file_uploader` de Streamlit ne se vide pas avec un simple `st.rerun()`.
L'astuce est de changer dynamiquement sa `key` : Streamlit le considere alors
comme un nouveau widget et le recree vide.

---

## Parties ajoutees

### 1. Session state — nouvelle variable `uploader_key`

**Fichier :** `app.py` — dans la fonction `main()`, bloc d'initialisation du session state

```python
# Compteur pour forcer le reset du file_uploader
# Chaque increment genere une nouvelle key, ce qui vide les fichiers uploades
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
```

### 2. File uploader — key dynamique

**Fichier :** `app.py` — widget `file_uploader`

```python
uploaded_files = st.file_uploader(
    "Deposez vos courriers ici",
    type=["pdf", "zip"],
    accept_multiple_files=True,
    help="Glissez un fichier ZIP (lot de demandes) ou des fichiers PDF individuels.",
    # Key dynamique : quand uploader_key change, Streamlit cree un nouveau widget
    # ce qui vide automatiquement les fichiers uploades
    key=f"uploader_{st.session_state.uploader_key}",
)
```

### 3. Bouton — avant upload (quand aucun fichier n'est depose)

**Fichier :** `app.py` — juste apres le `if not uploaded_files:`

```python
if not uploaded_files:
    # Bouton reinitialiser visible meme sans fichier uploade
    if st.button(
        "\U0001f504 Nouveau courrier",
        type="secondary",          # Fond blanc (pas rouge comme "Lancer l'extraction")
        use_container_width=True,
        help="Reinitialiser et deposer de nouveaux fichiers",
    ):
        # Reset complet de l'etat de la session
        st.session_state.results = None
        st.session_state.output_data = None
        st.session_state.processing_done = False
        st.session_state.errors = []
        st.session_state.uploader_key += 1  # Force le vidage du file_uploader
        st.rerun()
    return
```

### 4. Bouton — apres upload, sous "Lancer l'extraction"

**Fichier :** `app.py` — juste apres le bloc `if st.button("Lancer l'extraction", ...):`

```python
# Bouton pour reinitialiser quand des fichiers sont uploades
# mais l'utilisateur veut repartir de zero avant de lancer l'extraction
if st.button(
    "\U0001f504 Nouveau courrier",
    type="secondary",
    use_container_width=True,
    help="Reinitialiser et deposer de nouveaux fichiers",
):
    st.session_state.results = None
    st.session_state.output_data = None
    st.session_state.processing_done = False
    st.session_state.errors = []
    st.session_state.uploader_key += 1  # Force le vidage du file_uploader
    st.rerun()
```

### 5. Bouton — apres extraction, dans `_render_results()`

**Fichier :** `app.py` — dans `_render_results()`, juste avant le footer

```python
# Bouton pour relancer un nouveau processus apres avoir telecharge les resultats
if st.button(
    "\U0001f504 Nouveau courrier",
    type="secondary",
    use_container_width=True,
    help="Reinitialiser et deposer de nouveaux fichiers",
):
    st.session_state.results = None
    st.session_state.output_data = None
    st.session_state.processing_done = False
    st.session_state.errors = []
    st.session_state.uploader_key += 1  # Force le vidage du file_uploader
    st.rerun()
```

---

## Resume

| Etape | Ou le bouton apparait | Fonctionnel |
|-------|----------------------|-------------|
| Aucun fichier uploade | Sous le file_uploader | Oui |
| Fichier uploade, avant extraction | Sous "Lancer l'extraction" | Oui |
| Apres extraction et telechargement | Sous "Telecharger" | Oui |
