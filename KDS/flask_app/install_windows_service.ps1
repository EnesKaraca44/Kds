param(
    [string]$ServiceName = "KDSFlaskService",
    [string]$DisplayName = "KDS Flask Service",
    [string]$Description = "KDS Flask uygulamasini Waitress ile servis olarak calistirir.",
    [int]$Port = 5000,
    [int]$Threads = 8
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot "..\..\venv\Scripts\python.exe"
$pythonExe = [System.IO.Path]::GetFullPath($pythonExe)

if (-not (Test-Path $pythonExe)) {
    throw "Python bulunamadi: $pythonExe. Önce venv olusturup bagimliliklari yukleyin."
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Mevcut servis bulundu, kaldiriliyor: $ServiceName"
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 1
}

$binPath = "`"$pythonExe`" `"$projectRoot\run_server.py`""

sc.exe create $ServiceName binPath= $binPath start= auto DisplayName= $DisplayName | Out-Null
sc.exe description $ServiceName $Description | Out-Null

sc.exe failure $ServiceName reset= 60 actions= restart/5000/restart/5000/restart/5000 | Out-Null

sc.exe config $ServiceName obj= LocalSystem | Out-Null

[Environment]::SetEnvironmentVariable("KDS_HOST", "0.0.0.0", "Machine")
[Environment]::SetEnvironmentVariable("KDS_PORT", "$Port", "Machine")
[Environment]::SetEnvironmentVariable("KDS_THREADS", "$Threads", "Machine")

Start-Service -Name $ServiceName

Write-Host "Servis kuruldu ve baslatildi: $ServiceName"
Write-Host "Durum kontrolu: Get-Service -Name $ServiceName"
