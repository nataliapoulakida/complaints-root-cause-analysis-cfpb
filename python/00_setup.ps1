# One-step setup check. Run from the project folder:
#   powershell -ExecutionPolicy Bypass -File python\00_setup.ps1
$ErrorActionPreference = "Continue"

function Check($name, $cmd) {
    try { $v = & $cmd --version 2>&1 | Select-Object -First 1; Write-Host "OK    $name : $v" -ForegroundColor Green; return $true }
    catch { Write-Host "MISSING $name" -ForegroundColor Red; return $false }
}

Write-Host "`n== Tools =="
$py  = Check "Python" "python"
$git = Check "Git" "git"
if (-not $py)  { Write-Host "  -> Install Python from python.org (tick 'Add Python to PATH'), then rerun." }
if (-not $git) { Write-Host "  -> Install Git for Windows from git-scm.com, then rerun." }

if ($py) {
    Write-Host "`n== Python packages =="
    python -m pip install --quiet duckdb pandas
    python -c "import duckdb, pandas; print('OK    duckdb', duckdb.__version__, '| pandas', pandas.__version__)"
}

if ($git) {
    Write-Host "`n== Git =="
    if (-not (Test-Path ".git")) { git init -b main | Out-Null; Write-Host "Initialised new repository" }
    git add .
    $bad = git diff --cached --name-only | Select-String -Pattern '^data/|\.pbix$'
    if ($bad) {
        Write-Host "WARNING: these files must NOT be committed:" -ForegroundColor Red
        $bad
        Write-Host "Run: git rm -r --cached data   then check .gitignore. Do not push yet."
    } else {
        Write-Host "OK    No data files or .pbix staged. Files that will be committed:" -ForegroundColor Green
        git diff --cached --name-only
    }
}
Write-Host "`nDone. Send me this output if anything is red."
