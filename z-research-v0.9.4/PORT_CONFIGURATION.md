# Z-Research v0.9.3 — Dedicated local server port

Z-Research runs at **http://127.0.0.1:8765** to avoid conflicting with GraphInsight on port 8000. Both launchers have been changed: `START_MAC.command` and `START_WINDOWS.bat`. The application remains bound to localhost only.

On macOS: `bash START_MAC.command`. On Windows: double-click `START_WINDOWS.bat`. Check `http://127.0.0.1:8765/api/health` (expected `version: 0.9.3`).

GraphInsight is unaffected: no process is stopped and no GraphInsight files are changed. If port 8765 is already occupied, choose another free port and update both the `--port` argument and browser URL in the appropriate launcher.

Existing data remains in `local_data`; this package intentionally does not include any user data. Back up and migrate it before first launch.
