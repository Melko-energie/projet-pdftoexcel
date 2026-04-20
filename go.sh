#!/usr/bin/env bash
# projet-pdftoexcel — commande unique "Go" (Linux / macOS / Git Bash)
#
# Usage :
#   bash go.sh            -> install si necessaire + lance Streamlit (:8501)
#   bash go.sh install    -> installe seulement
#   bash go.sh streamlit  -> lance l'UI Streamlit (par defaut)
#   bash go.sh web        -> lance l'alternative FastAPI (:8000)
#
# Particularites :
#   - app.py a la racine = UI Streamlit (entry point principal)
#   - web/main.py = alternative FastAPI
#   - requirements.txt et .venv a la RACINE

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
CMD="${1:-dev}"

step() { printf "\033[36m==> %s\033[0m\n" "$1"; }
info() { printf "\033[33m    %s\033[0m\n" "$1"; }
fail() { printf "\033[31m!!  %s\033[0m\n" "$1"; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || fail "Commande manquante : $1"; }

venv_python() {
  if   [ -x "$ROOT/.venv/Scripts/python.exe" ]; then echo "$ROOT/.venv/Scripts/python.exe"
  elif [ -x "$ROOT/.venv/bin/python" ];          then echo "$ROOT/.venv/bin/python"
  fi
}

install_backend() {
  step "Backend Python : venv + pip install"
  require python
  PY="$(venv_python)"
  # Recree le venv s'il est absent OU corrompu (python ne s'execute pas).
  local venvOk=0
  if [ -n "$PY" ]; then
    "$PY" -c "import sys" >/dev/null 2>&1 && venvOk=1
  fi
  if [ "$venvOk" -eq 0 ]; then
    if [ -d "$ROOT/.venv" ]; then
      info ".venv corrompu -> suppression."
      rm -rf "$ROOT/.venv"
    fi
    # --without-pip : evite le hang d'ensurepip avec Python 3.14 / Windows.
    ( cd "$ROOT" && python -m venv .venv --without-pip )
    PY="$(venv_python)"
    "$PY" -m ensurepip --upgrade
  fi
  # Pas de pip upgrade : ensurepip n'ecrit pas de RECORD file -> uninstall plante.
  "$PY" -m pip install --prefer-binary -r "$ROOT/requirements.txt"
}

enable_git_hooks() {
  [ -d "$ROOT/.git" ] || return 0
  [ -f "$ROOT/.githooks/post-merge" ] || return 0
  local current
  current="$(cd "$ROOT" && git config --get core.hooksPath 2>/dev/null || true)"
  if [ "$current" != ".githooks" ]; then
    ( cd "$ROOT" && git config core.hooksPath .githooks )
    chmod +x "$ROOT/.githooks/post-merge" 2>/dev/null || true
    info "Hook git post-merge active (auto-install apres chaque git pull)."
  fi
}

install_all() {
  install_backend
  enable_git_hooks
}

need_install() {
  local py
  py="$(venv_python)"
  [ -z "$py" ] && return 0
  "$py" -c "import streamlit" >/dev/null 2>&1 || return 0
  return 1
}

start_streamlit() {
  PY="$(venv_python)"
  [ -z "$PY" ] && fail "venv introuvable. Lance : bash go.sh install"
  info "Streamlit demarre sur http://localhost:8501  (Ctrl+C pour arreter)"
  ( cd "$ROOT" && "$PY" -m streamlit run app.py )
}
start_web() {
  PY="$(venv_python)"
  [ -z "$PY" ] && fail "venv introuvable. Lance : bash go.sh install"
  info "FastAPI demarre sur http://localhost:8000  (Ctrl+C pour arreter)"
  ( cd "$ROOT" && "$PY" -m uvicorn web.main:app --reload --port 8000 )
}

case "$CMD" in
  install)   install_all ;;
  streamlit) need_install && install_all; start_streamlit ;;
  web)       need_install && install_all; start_web ;;
  dev|"")
    need_install && install_all
    start_streamlit
    ;;
  *) fail "Commande inconnue : $CMD. Utilise: install | dev | streamlit | web" ;;
esac
