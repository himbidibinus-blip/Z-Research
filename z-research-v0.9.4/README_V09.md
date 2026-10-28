> **Historical v0.9.0 document.** For current behavior and QA results, read `README_V091.md` and `QA_REMEDIATION_V091.md`.

# Z-Research 0.9.0 — Connected Research Workspace (local beta)

**Status:** functional local beta for personal research, **not** a validated replacement for SmartPLS or a production multi-tenant service. Python/FastAPI + SQLite + NumPy/Pandas + experimental PLS-SEM + plain HTML/CSS/JS. The existing v0.5.4 workspace remains available at `/legacy`; earlier APIs are preserved.

## Fast start — macOS

1. Stop the previous Z-Research server: `Control + C` in its Terminal window. If port 8000 is occupied, close the old process before starting v0.9.
2. Extract the ZIP into `~/Downloads/z-research-v0.9` (or any other folder).
3. **Before first launch**, if you want to keep previous research data, open Terminal, `cd` to the new folder, then run `bash UPGRADE_EXISTING_MAC.command`. Paste the **old application folder** when asked. The migration copies `local_data` without deleting or replacing the source. Skip this step for a clean install. The migration refuses to overwrite an existing target database.
4. Run `bash START_MAC.command` in the new folder. The launcher creates `.venv`, installs Python dependencies and launches the web server bound to `127.0.0.1:8000`.
5. Browse to **http://127.0.0.1:8000**. `/api/health` must say `0.9.0`.

Manual alternative:

```bash
cd ~/Downloads/z-research-v0.9
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Fast start — Windows 10/11

Install Python 3.11 or 3.12; extract ZIP to a writable folder; double-click `START_WINDOWS.bat` or run it from PowerShell. In the browser, open `http://127.0.0.1:8000`. Back up and manually copy a previous `local_data` folder *before launching* if you are upgrading from a prior Windows installation. Windows launcher has not been interactively tested on a Windows computer in this environment.

## Ollama on a 16-GB Mac

Install Ollama separately; use `ollama pull qwen3:8b` if necessary. Check `curl http://127.0.0.1:11434/api/tags` returns `qwen3:8b`. In Z-Research **AI & Account**, choose **Ollama (local)**, model **qwen3:8b**, and leave the key blank. Ollama calls use a 3600-second HTTP timeout. This timeout does not guarantee generation completes within 1 hour; long chapters may require section-by-section generation.

Other provider APIs require their own credentials and any separate billing. Secret API keys are stored only in the server process memory for the login session (not in SQLite).

## Research workflow

1. **Data & Projects:** upload CSV/XLSX, preview data, create a project and link the dataset. Numeric cell editing is available, with the first-import CSV backed up before the first change.
2. **Research Model:** select dataset constructs as independent/dependent/mediator/moderator and auto-create a proposed path model. Review suggested indicators, measurement modes and hypotheses, then edit. An SVG framework and quick, noninferential calculation provide immediate feedback.
3. **SEM-PLS Analysis:** calculate and inspect path coefficients, R², f², reliability, AVE, HTMT, VIF, mediations/moderations where specified, bootstrap confidence intervals, indicator summaries, and quality flags. Quick preview (0 bootstrap) is not significance testing.
4. **Introduction / Evidence Library / Literature / Methodology / Findings:** collect article metadata and news evidence, drag/click to insert citations into any chapter, select source IDs for AI context, preview model-specific prompts, generate drafts with your AI provider, save version history, and export saved drafts as DOCX or the editor as TXT.
5. **Integrity & History:** source fingerprint (SHA-256 of dataset CSV plus model), stale analysis/draft badges after edits, event history, and reproducibility JSON export. Previously saved outputs are not overwritten.

## Research integrity and limitations

- The SEM-PLS implementation is an **experimental centroid inner-weighting approximation**, reflective Mode A/formative Mode B, with a two-stage moderator interaction. It **has not been independently benchmarked to SmartPLS or cSEM**. No claims of validated equivalence.
- Not implemented: PLSc, rho_A, bootstrap HTMT confidence intervals, blindfolding, PLSpredict, MICOM, MGA, higher-order constructs, SRMR, full missing data imputation, or advanced longitudinal/multilevel designs. For final publication, cross-check with a validated SEM tool.
- AI must not fabricate data collection procedures, sample details, DOI, source content, significance or study findings. Prompts explicitly flag unknown research facts and require verification. Reference metadata discovery via OpenAlex does **not** establish Scopus indexing or support for findings.
- Phenomena suggestions and news discovery are research leads, not verified claims or causal conclusions.
- Draft history stores a *new version* instead of silently overwriting earlier saved work. The DOCX endpoint exports **the latest saved draft**, not unsaved edits in the browser text editor; save before export.
- This is a **single-machine personal local app**. Login/API restrictions are not a hardened, internet-facing security design. Keep the server listening on `127.0.0.1` and do not expose it publicly.
- Project dataset/model audit fingerprints do not verify the factual truth, originality, indexing, journal acceptance or methodological suitability of the underlying study.
- Exact Z-Research logo from another chat is not embedded: use the logo upload in **AI & Account** to supply your approved artwork.

## Tests performed for this build

- Python API/regression suite: `python -m pytest -q` (**25 passed** in this build environment).
- `node --check app/static/studio09.js` passed.
- Interactive Chromium checks via an isolated API bridge (browser traffic to loopback was blocked by test-environment policy): project creation, model construction/diagram, SEM quick preview, manual reference creation, click-to-cite, chapter saving, and audit navigation; **no JS page errors** in this limited simulated run.
- **Not tested on the user's physical Mac/Windows**, nor against their real Ollama `qwen3:8b` inference. Cloud API connection tested only in inherited API suites or mocked paths as applicable. Large-dataset benchmarks, accessibility audits, and end-to-end Mac installation remain to be completed.

## Troubleshooting

- If the old page shows up: stop the old server; check `http://127.0.0.1:8000/api/health` reports `0.9.0`; hard refresh the browser.
- `No module named uvicorn`: activate the right environment or run `./.venv/bin/python -m pip install -r requirements.txt` on Mac. Use the `.venv` Python to start the app.
- Ollama cannot connect: start Ollama, confirm `ollama list` and `curl http://127.0.0.1:11434/api/tags`, then reconnect the provider in Z-Research.
- Analysis stale: intentional. Return to SEM-PLS Analysis and recalculate after data/model changes.

## Folder layout

- `app/main.py`: core FastAPI server and legacy dataset/statistical endpoints.
- `app/v09.py`: connected project state, analysis provenance, evidence and chapter APIs.
- `app/sem_engine.py`: experimental computational estimator.
- `app/v05.py`: compatibility: references, news, data-cell editor and older chapter features.
- `app/providers.py`: AI provider dispatch, including local Ollama.
- `app/static/index.html`, `studio09.js`, `studio09.css`: v0.9 workspace.
- `app/static/legacy.html`: v0.5.4 preserved UI.
- `tests`: automated API/regression tests.
- `local_data` (created at runtime, intentionally **not** packaged): research database, datasets and branding.
