@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo  KDS Windows Servisi Kurulumu
echo  (PowerShell gerekmez)
echo ========================================
echo.
echo Bu pencereyi YONETICI olarak acmis olmalisiniz.
echo.
if not exist "venv\Scripts\python.exe" (
    echo HATA: venv\Scripts\python.exe bulunamadi.
    echo Once sanal ortam ve paketleri kurun.
    pause
    exit /b 1
)
if not exist "tools\nssm\win64\nssm.exe" (
    if not exist "tools\nssm\win32\nssm.exe" (
        echo HATA: nssm.exe bulunamadi.
        echo tools\nssm\win64\nssm.exe konumuna kopyalayin.
        echo Indirme: https://nssm.cc/download
        pause
        exit /b 1
    )
)
"venv\Scripts\python.exe" "%~dp0install_service.py"
set ERR=%ERRORLEVEL%
echo.
if %ERR% neq 0 (
    echo Kurulum basarisiz. Yukaridaki mesaji okuyun.
) else (
    echo Tamamlandi.
)
pause
exit /b %ERR%