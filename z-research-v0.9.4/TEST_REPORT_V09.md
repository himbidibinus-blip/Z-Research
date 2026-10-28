> **Historical v0.9.0 document.** For current behavior and QA results, read `README_V091.md` and `QA_REMEDIATION_V091.md`.

# Test and limitations report — Z-Research v0.9.0

## Automated tests

- Python API and regression suite: **25 tests passed** in the release candidate environment, using `python -m pytest -q --disable-warnings`.
- Coverage examples: login, dataset upload, construct inference, role-based model construction, structural equation preview, bootstrap calculation, seed reproducibility metadata, chapter prompt generation, current/stale state changes after model edits, Chapter 4 blocked when source analysis stale, reference DOI deduplication, owner scope, DOCX export and dataset cell-edit backup/invalidation.
- Static JavaScript syntax checked with `node --check`.
- FastAPI Uvicorn health endpoint responded with `version=0.9.0` locally.
- UI simulation with Chromium rendered the new dashboard and executed login/project/upload/model/evidence/chapter steps against a live server via controlled API bridge, with no JavaScript errors or horizontal overflow observed in test viewports.

## Validation boundaries

- The environment blocked Chromium navigation directly to the localhost server, so the browser test used an HTML/JS injection and API bridge rather than native browser localhost navigation.
- No live end-to-end performance run was completed against a real Mac with Ollama Qwen3 8B installed. API adapters were previously tested under simulation; test the model on the target machine.
- No formal statistical parity benchmark against SmartPLS/cSEM has been completed; quality-rule warnings and tests of code behavior **do not establish numeric PLS-SEM validity**.
- Reference-title matching and news suggestions are discovery aids, not source verification.
- Windows launcher was packaged and source-reviewed, but not executed on a real Windows machine within this Linux test environment.
