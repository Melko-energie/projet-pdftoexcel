# projet-pdftoexcel — commande unique "Go" (Windows / PowerShell)
#
# Usage :
#   .\go.ps1            -> install si necessaire + lance Streamlit (:8501)
#   .\go.ps1 install    -> installe seulement
#   .\go.ps1 streamlit  -> lance l'UI Streamlit (par defaut)
#   .\go.ps1 web        -> lance l'alternative FastAPI (:8000)
#
# Particularites :
#   - app.py a la racine = UI Streamlit (entry point principal)
#   - web/main.py = alternative FastAPI/Uvicorn
#   - requirements.txt et .venv a la RACINE (pas de sous-dossier backend)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cmd  = if ($args.Count -gt 0) { $args[0] } else { "dev" }

function Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Info($m) { Write-Host "    $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "!!  $m" -ForegroundColor Red; exit 1 }

function Check-ExitCode($what) {
    if ($LASTEXITCODE -ne 0) { Fail "$what a echoue (exit code $LASTEXITCODE)." }
}
function Require($cmd) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { Fail "Commande manquante : $cmd" }
}

# -------- Install (recette validee Python 3.14 / Windows) --------
function Install-Backend {
    Step "Backend Python : venv + pip install"
    Require "python"
    Push-Location $Root
    try {
        $py = Join-Path $Root ".venv\Scripts\python.exe"
        # Detecte venv inexistant OU corrompu (python.exe present mais ne s'execute pas).
        $venvOk = $false
        if (Test-Path $py) {
            try {
                & $py -c "import sys" *> $null
                if ($LASTEXITCODE -eq 0) { $venvOk = $true }
            } catch { $venvOk = $false }
        }
        if (-not $venvOk) {
            if (Test-Path ".venv") {
                Info ".venv corrompu -> suppression."
                Remove-Item -Recurse -Force ".venv"
            }
            # --without-pip : evite le hang d'ensurepip avec Python 3.14 / Windows.
            python -m venv .venv --without-pip
            Check-ExitCode "python -m venv --without-pip"
            & $py -m ensurepip --upgrade
            Check-ExitCode "ensurepip"
        }
        # Pas de pip upgrade : ensurepip n'ecrit pas de RECORD file -> uninstall plante.
        & $py -m pip install --prefer-binary -r requirements.txt
        Check-ExitCode "pip install -r requirements.txt"
    } finally { Pop-Location }
}

function Enable-GitHooks {
    if (-not (Test-Path (Join-Path $Root ".git"))) { return }
    if (-not (Test-Path (Join-Path $Root ".githooks\post-merge"))) { return }
    Push-Location $Root
    try {
        $current = (git config --get core.hooksPath) 2>$null
        if ($current -ne ".githooks") {
            git config core.hooksPath .githooks
            Info "Hook git post-merge active (auto-install apres chaque git pull)."
        }
    } finally { Pop-Location }
}

function Install-All {
    Install-Backend
    Enable-GitHooks
}

function Need-Install {
    $py = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { return $true }
    try {
        & $py -c "import streamlit" *> $null
        if ($LASTEXITCODE -ne 0) { return $true }
    } catch { return $true }
    return $false
}

# -------- Run --------
function Start-Streamlit {
    $py = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { Fail "venv introuvable. Lance : .\go.ps1 install" }
    Push-Location $Root
    try {
        Info "Streamlit demarre sur http://localhost:8501  (Ctrl+C pour arreter)"
        & $py -m streamlit run app.py
    } finally { Pop-Location }
}
function Start-Web {
    $py = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { Fail "venv introuvable. Lance : .\go.ps1 install" }
    Push-Location $Root
    try {
        Info "FastAPI demarre sur http://localhost:8000  (Ctrl+C pour arreter)"
        & $py -m uvicorn web.main:app --reload --port 8000
    } finally { Pop-Location }
}

# -------- Dispatch --------
switch ($Cmd) {
    "install"   { Install-All; Write-Host "`nInstallation OK." -ForegroundColor Green; break }
    "streamlit" { if (Need-Install) { Install-All }; Start-Streamlit; break }
    "web"       { if (Need-Install) { Install-All }; Start-Web; break }
    "dev"       {
        if (Need-Install) { Install-All }
        if (-not (Test-Path (Join-Path $Root ".venv\Scripts\python.exe"))) {
            Fail "Le backend n'est pas installe correctement. Corrige les erreurs ci-dessus puis relance."
        }
        Start-Streamlit
        break
    }
    default { Fail "Commande inconnue : $Cmd. Utilise: install | dev | streamlit | web" }
}
