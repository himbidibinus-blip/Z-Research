@echo off
setlocal
cd /d "%~dp0"
title Z-Research v0.9.4 - Dua Perangkat - Port 8765
echo ======================================================
echo Z-Research v0.9.4 - Mode Dua Perangkat
 echo Server Windows port 8765 - GraphInsight port 8000 aman
 echo ======================================================
if not exist ".venv-2devices\Scripts\python.exe" (
 echo [1/3] Membuat environment Python khusus Z-Research...
 py -3 -m venv .venv-2devices
 if errorlevel 1 ( echo ERROR: Python 3 tidak ditemukan. Install Python 3.11 atau 3.12. & pause & exit /b 1 )
)
if not exist ".venv-2devices\.requirements-installed" (
 echo [2/3] Memasang library (sekali saja, butuh internet)...
 ".venv-2devices\Scripts\python.exe" -m pip install -r requirements.txt
 if errorlevel 1 ( echo ERROR: Instalasi library gagal. & pause & exit /b 1 )
 type nul > ".venv-2devices\.requirements-installed"
)
echo [3/3] Menjalankan server Z-Research...
echo Device utama: http://127.0.0.1:8765
echo.
echo Di device kedua: http://IP-WINDOWS-ANDA:8765
echo Cari IP Windows lewat perintah: ipconfig
 echo Gunakan Wi-Fi tepercaya yang sama. Jangan buka port ke internet.
echo Jika Windows Firewall meminta izin Python, izinkan di jaringan PRIVATE saja.
echo Jangan tutup jendela ini selama memakai Z-Research.
".venv-2devices\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8765
if errorlevel 1 ( echo Server berhenti karena error. & pause )
endlocal
