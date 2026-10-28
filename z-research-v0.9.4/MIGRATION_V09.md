> **Historical v0.9.0 document.** For current behavior and QA results, read `README_V091.md` and `QA_REMEDIATION_V091.md`.

# Safe upgrade from v0.5.4 to v0.9.0

The new ZIP extracts to a SEPARATE folder called `z-research-v0.9`. It will not overwrite your existing app.

**Before upgrade:** Close the old server (Ctrl+C), keep a complete backup of the old app folder and especially `local_data`.

**Mac:** in Terminal navigate to the NEW `z-research-v0.9` folder and run `bash UPGRADE_EXISTING_MAC.command`. Enter the path of the old folder, for example `~/Downloads/z-research-v0.5.4`. The script copies your old `local_data` into the new application folder. It refuses to overwrite a destination that already contains files. Then run `bash START_MAC.command`.

**Windows:** Stop both servers. Copy the old app's `local_data` folder into the new version **before** running `START_WINDOWS.bat`. Do not overwrite a newer nonempty destination directory. Make a backup first.

**Migration contents:** local owner account/session DB, uploaded datasets and analysis history, reference/news records, and logo if they were in local data. On startup the new version initializes additional SQLite tables without replacing old data. Existing old UI remains accessible at `/legacy`.

**Old v0.5 projects vs new v0.9 projects:** The v0.9 Project Manager creates newly linked projects and their snapshot history. Previously uploaded datasets and references survive migration but you must create/link a new v0.9 project to organize them into the connected workflow. Existing old saved chapter drafts remain accessible in `/legacy` rather than automatically being converted to v0.9 project versions.

**Problem: still seeing the old version?** Check `http://127.0.0.1:8000/api/health` for `version=0.9.0`. If not, stop other old Python/uvicorn processes using the port, then run the launcher inside the new folder. Hard refresh Chrome with Command+Shift+R on macOS.

**Problem: Ollama does not connect?** Confirm `ollama list` includes `qwen3:8b`, and `curl http://127.0.0.1:11434/api/tags` works in a second Terminal. Choose 'Ollama (local)' in the AI connection settings and leave the API key empty. AI generation can take a long time on a 16GB laptop; keep the app and Ollama running.
