param(
    [string]$ServiceName = "KDSFlaskService",
    [string]$DisplayName = "KDS Flask Service",
    [string]$Description = "KDS Flask uygulamasini Waitress ile servis olarak calistirir.",
    [int]$Port = 8032,
    [int]$Threads = 8,
    [string]$PythonExe = "",
    [string]$NssmExe = "C:\tools\nssm\nssm.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runServerPath = Join-Path $projectRoot "run_server.py"

function Resolve-PythonExe {
    param([string]$ProvidedPythonExe, [string]$RootPath)

    if (-not [string]::IsNullOrWhiteSpace($ProvidedPythonExe)) {
        return [System.IO.Path]::GetFullPath($ProvidedPythonExe)
    }

    $pythonCandidates = @(
        (Join-Path $RootPath "venv\Scripts\python.exe"),
        (Join-Path $RootPath "..\venv\Scripts\python.exe"),
        (Join-Path $RootPath "..\..\venv\Scripts\python.exe")
    )

    foreach ($candidate in $pythonCandidates) {
        $fullPath = [System.IO.Path]::GetFullPath($candidate)
        if (Test-Path $fullPath) {
            return $fullPath
        }
    }

    return $null
}

$pythonExePath = Resolve-PythonExe -ProvidedPythonExe $PythonExe -RootPath $projectRoot
if (-not $pythonExePath -or -not (Test-Path $pythonExePath)) {
    throw "Python bulunamadi. -PythonExe ile tam yolu verin. Ornek: -PythonExe 'D:\server_manager\deal-kds\flask_app\venv\Scripts\python.exe'"
}

$nssmPath = [System.IO.Path]::GetFullPath($NssmExe)
if (-not (Test-Path $nssmPath)) {
    throw "nssm.exe bulunamadi: $nssmPath. NSSM indirip bu yola koyun veya -NssmExe ile dogru yolu verin."
}

if (-not (Test-Path $runServerPath)) {
    throw "run_server.py bulunamadi: $runServerPath"
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Mevcut servis bulundu, kaldiriliyor: $ServiceName"
    & $nssmPath stop $ServiceName | Out-Null
    & $nssmPath remove $ServiceName confirm | Out-Null
    Start-Sleep -Seconds 1
}

Write-Host "Servis kuruluyor: $ServiceName"
& $nssmPath install $ServiceName $pythonExePath $runServerPath | Out-Null
& $nssmPath set $ServiceName DisplayName $DisplayName | Out-Null
& $nssmPath set $ServiceName Description $Description | Out-Null
& $nssmPath set $ServiceName AppDirectory $projectRoot | Out-Null
& $nssmPath set $ServiceName Start SERVICE_AUTO_START | Out-Null
& $nssmPath set $ServiceName AppEnvironmentExtra "KDS_HOST=127.0.0.1" "KDS_PORT=$Port" "KDS_THREADS=$Threads" "PYTHONUTF8=1" "PYTHONIOENCODING=utf-8" | Out-Null
& $nssmPath set $ServiceName AppStdout (Join-Path $projectRoot "service-stdout.log") | Out-Null
& $nssmPath set $ServiceName AppStderr (Join-Path $projectRoot "service-stderr.log") | Out-Null
& $nssmPath set $ServiceName AppRotateFiles 1 | Out-Null
& $nssmPath set $ServiceName AppRotateOnline 1 | Out-Null
& $nssmPath set $ServiceName AppRotateBytes 10485760 | Out-Null

& $nssmPath start $ServiceName | Out-Null

Write-Host "Servis kuruldu ve baslatildi: $ServiceName"
Write-Host "URL: http://127.0.0.1:$Port"
Write-Host "Durum kontrolu: Get-Service -Name $ServiceName"
