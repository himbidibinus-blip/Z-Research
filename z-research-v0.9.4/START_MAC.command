#!/bin/bash
# Double-click to launch Z-Research v0.9.4 on macOS. Never publishes localhost externally.
set -e
cd "$(dirname "$0")"
printf '\n Z-Research v0.9.4 · Mode lokal satu perangkat\n ----------------------------------------------\n'
if ! command -v python3 >/dev/null 2>&1; then
  echo 'ERROR: Python3 not found. Install Python 3.11 or 3.12 from https://www.python.org/downloads/macos/'
  read -r -p 'Press Enter to close...' || true
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo 'Creating fresh Python virtual environment...'
  rm -rf .venv
  python3 -m venv .venv
fi
PYTHON='./.venv/bin/python'
echo 'Installing/verifying required libraries in the Z-Research environment...'
if ! "$PYTHON" -m pip install -r requirements.txt; then
  echo 'ERROR: Dependencies did not install. Check the pip error above and your internet connection.'
  read -r -p 'Press Enter to close...' || true
  exit 1
fi
if ! "$PYTHON" -m uvicorn --version; then
  echo 'ERROR: Uvicorn unavailable. Try: ./.venv/bin/python -m pip install "uvicorn[standard]"'
  read -r -p 'Press Enter to close...' || true
  exit 1
fi
if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:8765 -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; then
  echo 'ERROR: Z-Research port 8765 is occupied by another process.'
  echo 'Stop only the process using port 8765 or choose a different Z-Research port.'
  lsof -nP -iTCP:8765 -sTCP:LISTEN || true
  read -r -p 'Press Enter to close...' || true
  exit 1
fi
printf '\nOpening browser at http://127.0.0.1:8765\nKeep this Terminal open. Press Ctrl+C to stop the local server.\n'
(sleep 3; open 'http://127.0.0.1:8765' >/dev/null 2>&1) &
"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8765
