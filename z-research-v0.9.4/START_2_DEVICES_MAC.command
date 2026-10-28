#!/bin/bash
set -e
cd "$(dirname "$0")"
echo '=== Z-Research v0.9.4 | 2 Devices | Port 8765 ==='
if ! command -v python3 >/dev/null; then echo 'Python3 belum terpasang. Install Python 3.11/3.12.'; read -r -p 'Enter untuk keluar...' || true; exit 1; fi
if ! [ -x .venv-2devices/bin/python ]; then
 echo 'Membuat environment baru khusus Z-Research...'
 python3 -m venv .venv-2devices
fi
PY='./.venv-2devices/bin/python'
if ! [ -f .venv-2devices/.requirements-installed ]; then
 echo 'Menginstal library (hanya saat pertama kali)...'
 "$PY" -m pip install -r requirements.txt || { echo 'Instalasi gagal. Cek internet dan pesan error.'; read -r -p 'Enter...' || true; exit 1; }
 touch .venv-2devices/.requirements-installed
fi
if lsof -nP -iTCP:8765 -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
 echo 'Port 8765 sedang dipakai. Tutup server Z-Research sebelumnya (jangan hentikan GraphInsight).'
 lsof -nP -iTCP:8765 -sTCP:LISTEN || true
 read -r -p 'Enter untuk keluar...' || true; exit 1
fi
IP=$(ipconfig getifaddr en0 2>/dev/null || true)
if [ -z "$IP" ]; then IP=$(route -n get default 2>/dev/null | awk '/interface:/{print $2}' | head -1 | xargs -I {} ipconfig getifaddr {} 2>/dev/null || true); fi
echo ''
echo 'MacBook: http://127.0.0.1:8765'
if [ -n "$IP" ]; then echo "Device kedua (Wi-Fi sama): http://$IP:8765"; else echo 'IP Wi-Fi tidak ditemukan; cek System Settings > Wi-Fi > Details > TCP/IP'; fi
echo 'JANGAN TUTUP TERMINAL. Ctrl+C untuk berhenti.'
(sleep 3; open 'http://127.0.0.1:8765' >/dev/null 2>&1) &
"$PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8765
