# Z-Research v0.5.3 — Research First, Then Analysis, Then Writing

**Local-first, experimental research workspace for macOS and Windows.** Ollama is an optional local AI backend that does not require a subscription or secret key. Other cloud providers remain supported with their own API credentials. This version does **not** change any existing saved research dataset when first installed.

## New workflow

1. **Dashboard** — import CSV/XLSX and choose the active dataset.
2. **Research Model Builder** — choose independent, dependent, mediating and moderating constructs. The structure and hypotheses are generated automatically and stay editable.
3. **SEM-PLS Analysis** — model changes trigger live **provisional** PLS estimation with 40 bootstrap replications. Choose `Run PLS-SEM` for a saved run using your chosen bootstrap settings. A collapsible panel in the same SEM-PLS workspace contains **Descriptive Statistics**, **OLS Regression**, and **Cronbach Alpha**. Explanations under and alongside the computed tables clarify their meaning and limitations. Dataset cell edits create an `.original.csv` backup and trigger live PLS re-estimation.
4. **Chapter 1 — Phenomena Finder** — uses numeric column names to propose research QUESTIONS. The optional news discovery browser searches Google News RSS, or open Google News in a browser. Save real source URLs and optionally attach news PDF/DOCX/TXT. News evidence must be read and verified by the researcher before citing.
5. **Reference Library** — manage unverified bibliographic metadata, RIS/BibTeX, uploaded papers, OpenAlex discovery and optional institutional Scopus checks.
6. **Chapter 2 — Literature Review** — live reference evidence matrix and AI generator from saved references. Metadata alone is not evidence of an article's results; source content requires researcher review.
7. **Chapter 3 — Methodology** — complete chapter drafting, prompt preview, actual research model context, uploaded writing guides, shared references, editable output, history, Word/Markdown export.
8. **Chapter 4 — Findings Writer** — complete Chapter 4 drafting from SAVED computed analysis, uploaded writing guides, references, editable output, history, Word/Markdown export. Live provisional PLS preview does NOT automatically become a saved finding.

## Mac: run the new version, not the old server

**Stop Z-Research v0.5.2** in its original Terminal with `Control+C`. If forgotten, find the specific process using `lsof -nP -iTCP:8000 -sTCP:LISTEN` and terminate **only that specific PID** with `kill PID`. Never kill an unrelated process.

Extract the new ZIP. The folder is named **`z-research-v0.5.3`**, deliberately not `z-research`, to avoid accidentally running the old code. Inside the new folder either double-click `START_MAC.command` or use:

```bash
cd ~/Downloads/z-research-v0.5.3
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000`. Confirm **version 0.5.3** with `http://127.0.0.1:8000/api/health`.

### Keep your existing datasets, analyses, account and earlier chapters

While **both old and new servers are STOPPED**, open Terminal in the new folder and run `bash UPGRADE_EXISTING_MAC.command`. When prompted for the OLD application's folder, enter its exact path (for example `~/Downloads/z-research`). It copies all of the old `local_data` into the new folder, without overwriting a populated destination. It never deletes source data. Run this before starting the new version for the first time, if migrating an existing project. Keep a separate backup of the old folder. If you already started the new version and it now has a populated `local_data`, the safety check refuses to overwrite it; reconcile manually after backing up both directories.

## Ollama setup (Mac, 16 GB RAM, Qwen3 8B)

1. Open Ollama on your Mac; verify the model exists: `ollama list` (`qwen3:8b`). Download only if needed with `ollama pull qwen3:8b`.
2. Check local health in a second Terminal: `curl http://127.0.0.1:11434/api/tags`.
3. Open Z-Research, sign in using your existing **local Z-Research owner account**, then go to **AI Connection & Account**.
4. Select **Ollama — Local (FREE, no key)**, model `qwen3:8b`, **leave Secret API key blank**, and click **Connect provider**.
5. Draft from Chapter 1, 2, 3, or 4. Qwen3 8B on 16GB may take minutes to draft a large section; use smaller prompts/sections if it runs slowly. Keep Ollama running.

No ChatGPT Plus subscription or OpenAI API key is required for Ollama. The AI engine runs on the Mac; all numerical calculations are handled by Python, not AI.

## Windows

Install supported Python (3.11 or 3.12 recommended), extract the ZIP to a path without unusual permissions, and double-click `START_WINDOWS.bat`, or run from PowerShell:

```powershell
cd C:\path\to\z-research-v0.5.3
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On Windows the **local Ollama app must also be installed on the same computer** if you want that AI mode. For older user data, stop both servers and copy `local_data` into the new folder **only after backing up both sides**.

## Scientific validity limitations

- The SEM-PLS estimator remains **experimental** (Mode A/B, centroid weighting, two-stage interaction; not certified equivalent to SmartPLS, cSEM, ADANCO or commercial software). Independently benchmark all estimates and bootstrap intervals before publication.
- The live preview uses 40 bootstrap resamples, is not persisted, and is unsuitable as a final publication analysis.
- Editing data creates an audit log and preserves the original CSV. Never edit input values to reach desired significance. Report preprocessing transparently.
- Research models reflect user-selected theory; variables/roles cannot be inferred scientifically from filenames alone.
- News search results and paper metadata are research leads, not verified evidence; citation and Scopus claims must be independently checked.
- No artificial data collection, fabricated publications, invented p-values, or unverifiable consent/ethics claims.
- AI generation can time out, hallucinate, or truncate, especially with smaller local models. Every draft requires human review.
- Access is **localhost only**, personal owner login, not a deployed multi-user research service.

## Validation performed in packaging environment

15 local automated tests passed, including mocked Ollama API connection and four chapter draft endpoints, model/SEM regression tests, news storage, chapter Word export and static navigation IDs. A live Ollama request and full graphical browser session on the user's Mac **have not** been tested by the packaging environment.
