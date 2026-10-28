# Z-Research v0.9.1 — QA Stabilization (Mac / Windows)

This release patches the 19 October 2026 QA audit. It is a **local beta** and **not approved for public deployment**. Consult `QA_REMEDIATION_V091.md` for bug-by-bug details and test limitations.

## Upgrade from v0.9 or v0.5.x

1. **Stop the old server** (press `Control+C` in the Terminal running Z-Research).
2. Extract this ZIP to **its own folder** `z-research-v0.9.1`. Do not overwrite the existing application.
3. Back up the entire old folder, especially the `local_data` directory and `quantresearch.db`.
4. **Before starting this release**, migrate data:
   - Mac Terminal: `cd ~/Downloads/z-research-v0.9.1` then `bash UPGRADE_EXISTING_MAC.command`. Enter the full path to the old app folder. The script refuses to overwrite existing new data.
   - Windows: copy the old `local_data` folder into the new folder after backing up and while both servers are stopped. Do not overwrite an existing nonempty `local_data` destination.
5. Start this release:
   - macOS: `bash START_MAC.command`
   - Windows: double-click `START_WINDOWS.bat`
6. Visit `http://127.0.0.1:8000/api/health` to verify `"version": "0.9.1"`. Visit the app at `http://127.0.0.1:8000`. If the old UI appears, hard refresh your browser.

## Research integrity changes

- Owner authentication is **required** to upload/preview datasets and to run legacy descriptive, reliability and regression endpoints. If you receive 401, sign in again. Cross-site mutations are denied with 403.
- Chapters linked to deleted references display `broken_citation`; legacy linked drafts without evidence SHA-256 display `needs_review`. Refresh or replace sources and manually check in-text citations. A new saved revision establishes a new evidence snapshot.
- New uploads preserve their original bytes and SHA-256. Open **Data & Projects → Raw integrity** to verify. Datasets imported on older versions cannot retroactively recover original bytes; reupload a source file if verification is required.
- **Citation style** can be selected in each Chapter Studio. APA outputs author-year; IEEE inserts numeric `[n]`, using selected reference order. Changing style does not rewrite existing manually inserted text. Review the full reference list before final submission.
- Ollama and other AI providers remain available through the prior settings; the source still configures an HTTP timeout up to 3,600 seconds. This is not a guarantee of successful generation.

## Developer tests

`python -m pytest -q --disable-warnings` (install `pytest` separately if required).
For JavaScript checks: `node tests/test_qa_091_citations.js`.

## Important scope note

SEM-PLS calculation remains **experimental** and not verified as equivalent to SmartPLS/cSEM. The release closes scoped bugs found in the QA report, but is not a production release or full information-security / statistical audit.
