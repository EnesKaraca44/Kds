# Sunucuda deploy dogrulama (flask_app klasorunde calistirin)
$root = $PSScriptRoot
$py = Join-Path $root "routes\tedavi_kartlari.py"
$json = Join-Path $root "routes\tedavi_kartlari_tr.json"
$stamp = Join-Path $root "tedavi_kartlari_deploy.stamp"
$stdout = Join-Path $root "service-stdout.log"

Write-Host "=== Tedavi kartlari deploy kontrol ===" -ForegroundColor Cyan
Write-Host "py  var:" (Test-Path $py) " ->" $py
Write-Host "json var:" (Test-Path $json) " ->" $json
if (Test-Path $py) {
    $hit = Select-String -Path $py -Pattern "TEDAVI_KARTLARI_BUILD" -SimpleMatch | Select-Object -First 1
    if ($hit) { Write-Host "BUILD satiri:" $hit.Line.Trim() }
}
if (Test-Path $stamp) {
    Write-Host "`n--- tedavi_kartlari_deploy.stamp ---" -ForegroundColor Green
    Get-Content $stamp
} else {
    Write-Host "`nSTAMP YOK - servis restart sonrasi olusmali (yeni kod yuklenmemis olabilir)" -ForegroundColor Yellow
}
if (Test-Path $stdout) {
    Write-Host "`n--- service-stdout (son 5 TEDAVI satiri) ---"
    Select-String -Path $stdout -Pattern "TEDAVI_KARTLARI" | Select-Object -Last 5 | ForEach-Object { $_.Line }
}
