# Z-Research v0.5.2 | Mac & Windows

Research workspace with AI drafting (multi-provider), automatic diagram/hypothesis builder and local experimental PLS-SEM. This is a research-support prototype, not validated statistical publication software.

## Mac — clean installation

1. Extract the ZIP into a **new folder**. Keep the previous installation untouched if it holds research data.
2. Open Terminal, go to the folder containing `requirements.txt` and run:

```bash
cd ~/Downloads/z-research
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Open http://127.0.0.1:8000. Or double-click `START_MAC.command` in Finder after extracting (if blocked by Gatekeeper, right-click → Open).
4. If the virtual environment was created with a broken/interrupted install, in the extracted folder delete just `.venv` and repeat commands 2–4. **Do not delete `local_data`**; it contains datasets, backups and the research account database.

## Windows 10/11

Install Python 3.11/3.12, then double-click `START_WINDOWS.bat`. Or in PowerShell:

```powershell
cd C:\path\to\z-research
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Existing installation with research datasets

**Never delete the old installation or its `local_data`.** Extract v0.5.2 to a separate folder. With Z-Research server stopped, on Mac run `UPGRADE_EXISTING_MAC.command` in the new folder and give it the *old* application's folder path when asked. It copies `local_data` only and refuses to overwrite a populated destination. Alternatively manually copy the complete `local_data` folder while the server is stopped. Previous credentials and research history are kept in SQLite.

## How to use the new features

1. In **AI Connection & Account**, create or log in to the *local* Z-Research account. Choose the provider (Google Gemini, OpenAI, Claude, etc.), paste that provider's API secret, and enter an actual model ID supported by your account. Click Connect.
2. Upload CSV/XLSX in Dashboard. Go to **Research Model Builder**: pick X (independent), Y (dependent), optional M (mediator) and W (moderator). The model and hypothesis paths appear automatically. Grouped indicators use column-name heuristics: check constructs and theory carefully.
3. Edit construct indicators, labels and measurement modes, edit or delete paths in **Hypothesis editor**, or add a path manually. Changes will trigger **live PLS preview** if you are logged in and auto recalculation is enabled. Statistical previews do **not** require a cloud AI API key.
4. In **PLS-SEM Lab**, edit numeric dataset observations using row pagination if needed, and watch live recalculation. The first edit saves an `.original.csv` backup next to the dataset in `local_data`. Click **Run PLS-SEM** for a saved final analysis using your selected bootstrap replications; only a saved run should be linked to Chapter 4.
5. Open **Chapter Studio** or **AI Methodology**, with your AI provider connected, to generate cautious academic drafts. AI writing must not invent respondent attributes, statistical results or citations.

See `CHANGELOG_V052.md` for limitations and `README.md` for baseline features.
