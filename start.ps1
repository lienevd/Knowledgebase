param(
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$SkipInstall,
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectRoot ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Find-SystemPython {
    $candidates = @("python", "py")

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }

        try {
            if ($candidate -eq "py") {
                & $candidate -3 --version *> $null
            } else {
                & $candidate --version *> $null
            }

            return $candidate
        } catch {
            continue
        }
    }

    throw "No working Python was found. Install Python 3.10+ and make sure it is available as 'python' or 'py'."
}

function Test-VenvPython {
    if (-not (Test-Path $PythonExe)) {
        return $false
    }

    try {
        & $PythonExe --version *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function New-ProjectVenv {
    $systemPython = Find-SystemPython

    if (Test-Path $VenvDir) {
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backupDir = Join-Path $ProjectRoot ".venv-broken-$timestamp"
        Write-Step "Existing virtual environment is not usable; moving it to $backupDir"
        Move-Item -LiteralPath $VenvDir -Destination $backupDir
    } else {
        Write-Step "Creating virtual environment"
    }

    if ($systemPython -eq "py") {
        & py -3 -m venv $VenvDir
    } else {
        & $systemPython -m venv $VenvDir
    }
}

Set-Location $ProjectRoot

if (-not (Test-VenvPython)) {
    New-ProjectVenv
}

if (-not $SkipInstall) {
    Write-Step "Installing dependencies"
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r $RequirementsFile
}

if ($SetupOnly) {
    Write-Step "Setup complete"
    exit 0
}

$reloadArgs = @()
if (-not $NoReload) {
    $reloadArgs += "--reload"
}

Write-Step "Starting app at http://127.0.0.1:$Port"
& $PythonExe -m uvicorn app:app --host 127.0.0.1 --port $Port @reloadArgs
