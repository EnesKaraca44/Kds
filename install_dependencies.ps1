param(
    [string]$PythonCmd = "python",
    [string]$VenvDir = "venv",
    [string]$RequirementsFile = "requirements.txt"
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$CommandName)

    $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return "py -3"
    }

    throw "Python bulunamadi. Python 3 kurup PATH'e ekleyin."
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

if (-not (Test-Path $RequirementsFile)) {
    throw "Bulunamadi: $RequirementsFile"
}

$pythonExec = Resolve-Python -CommandName $PythonCmd

if (-not (Test-Path $VenvDir)) {
    Write-Host "Sanal ortam olusturuluyor: $VenvDir"
    if ($pythonExec -eq "py -3") {
        py -3 -m venv $VenvDir
    } else {
        & $pythonExec -m venv $VenvDir
    }
}

$venvPython = Join-Path $projectRoot "$VenvDir\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Venv Python bulunamadi: $venvPython"
}

Write-Host "pip guncelleniyor..."
& $venvPython -m pip install --upgrade pip

Write-Host "Bagimliliklar yukleniyor..."
& $venvPython -m pip install -r $RequirementsFile

Write-Host ""
Write-Host "Kurulum tamamlandi."
Write-Host "Aktif etmek icin: .\$VenvDir\Scripts\Activate.ps1"
