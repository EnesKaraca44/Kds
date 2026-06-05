# Tedavi kartlari ve ilgili dosyalari UTF-8 (BOMsuz) olarak yeniden yazar.
param(
    [string]$Root = $PSScriptRoot
)

$files = @(
    "routes\tedavi_kartlari.py",
    "routes\tedavi_kartlari_tr.json",
    "database\tedavi_kartlari_sorgular.py",
    "templates\tedavi_kartlari.html",
    "jinja_loader.py",
    "app.py"
)

foreach ($rel in $files) {
    $path = Join-Path $Root $rel
    if (-not (Test-Path $path)) {
        Write-Warning "Atlaniyor (yok): $path"
        continue
    }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $text = $null
    foreach ($enc in @([System.Text.UTF8Encoding]::new($false), [System.Text.Encoding]::GetEncoding(1254))) {
        try {
            $text = $enc.GetString($bytes)
            if ($text -and $text -notmatch '\uFFFD') { break }
        } catch { }
    }
    if (-not $text) {
        $text = [System.Text.Encoding]::UTF8.GetString($bytes)
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($path, $text, $utf8)
    Write-Host "UTF-8: $path"
}

Write-Host "Tamam. Servisi yeniden baslatin."
