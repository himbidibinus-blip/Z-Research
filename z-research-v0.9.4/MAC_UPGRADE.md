# Z-Research v0.5 — Upgrade from your working Mac installation

These instructions assume your working v0.2 code is at `~/Downloads/quantresearch-ai/` and that you unzip `Z_Research_v0.5_Mac.zip` to `~/Downloads/quantresearch-ai-v05/`.

1. In the Terminal running Uvicorn press **Control+C**.
2. Create a dated backup. If you already have the backup name below, choose another name before running the command.

```bash
cp -R ~/Downloads/quantresearch-ai ~/Downloads/quantresearch-ai-backup-pre-v05
```

3. Extract the new ZIP to `~/Downloads/` using Finder. **Do not overwrite the old project folder.**
4. Run these commands one at a time:

```bash
cp -R ~/Downloads/quantresearch-ai-v05/app/. ~/Downloads/quantresearch-ai/app/
cp ~/Downloads/quantresearch-ai-v05/requirements.txt ~/Downloads/quantresearch-ai/requirements.txt
cd ~/Downloads/quantresearch-ai
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

5. Visit **http://127.0.0.1:8000** in Safari/Chrome and press **Command+Shift+R**.
6. Open **http://127.0.0.1:8000/api/health**. It should say `version: 0.5.0`.

**Do not delete `local_data/`**: this contains uploaded datasets, saved models, AI drafts and prior analyses. Do not delete `.venv/`: it holds your installed Python libraries. New v0.5 tables are automatically created inside the existing SQLite database without replacing existing tables.

### Common issues

- `ModuleNotFoundError: docx` or `No module named 'pypdf'`: run `python -m pip install -r requirements.txt` again in the active `.venv`.
- `Address already in use`: stop the older Uvicorn process with Control+C; do not start two servers on port 8000.
- v0.2 screen remains: restart Uvicorn and hard-refresh the browser; check that `app/static/v05.js` exists in the upgraded project.
- `401 Please log in`: sign in to the local owner account already configured in v0.2.
- AI refuses to draft: reconnect your separate OpenAI API key under Settings; local PLS does not need an AI key.
- Elsevier Scopus query `401/403`: the key lacks authorization, or institutional license/API entitlement is needed. OpenAlex discovery can still work subject to its own access and rate limits.
- Bootstrap slow: start with 50–200 repetitions while testing; 1000–2000 for sensitivity checks when performance permits. Wait for completion.

Rollback: stop Uvicorn and restore the backup folder if a local test fails. Back up a second time before doing a rollback if you've generated new data on v0.5.
