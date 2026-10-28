# Z-Research v0.9.1 — QA Stabilization Report

**Audit baseline:** independent QA report 19 October 2026; seven findings ZR-QA-001–007.  
**Release classification:** LOCAL BETA ONLY. **NO-GO public production.**

| ID | Severity | Fix implemented | Regression proof |
|---|---|---|---|
| ZR-QA-001 | Critical/P0 | Owner session dependency on **all old** `/api/datasets`, `/api/analyze/*`, `/api/reports/methodology`, `/api/analyses/*` routes including exports and provenance. Local-host and Origin/Fetch Metadata cross-site request checks. | `test_qa_001_*` (401/403 and authenticated success) |
| ZR-QA-002 | High/P1 | Each chapter stores an evidence SHA-256 of selected bibliographic records. Deleted sources show `broken_citation` in project, chapter history, audit, reproducibility JSON and Word export warning; edited metadata sets `stale`. Legacy versions without evidence hash show `needs_review` when references are attached. | `test_qa_002_*`, `test_reference_metadata_*`, `test_old_chapters_*` |
| ZR-QA-003 | High/P1 | Validate all selected reference IDs exist within owner's library, both on draft preview/generation and save. Reject missing/duplicate IDs with HTTP 422. | `test_qa_003_*` |
| ZR-QA-004 | High/P1 | Replace simplistic comma-splitting author formatter with parser for `Surname, Given`, multi-author semicolon / `and`, given-family names, corporate authors, 1/2/3+ authors, and missing year. **Limited formatter**, not full CSL-APA 7 certification. | `tests/test_qa_091_citations.js` plus bridged Chromium citation check |
| ZR-QA-005 | High/P1 | Remove duplicate indicator input and use one DOM binding, persisting edits through model PATCH. | Chromium test: edit first construct indicators, save and verify refreshed value |
| ZR-QA-006 | Medium/P2 | Store new uploads byte-for-byte in `local_data/raw_uploads`, separate from normalized working CSV. Persist SHA-256, original filename, byte size and format. Add authenticated `GET /api/datasets/{id}/provenance` and 'Raw integrity' UI. Existing imported files explicitly marked `LEGACY_ORIGINAL_NOT_AVAILABLE`. | `test_qa_006_*` |
| ZR-QA-007 | Medium/P2 | Switch APA in-text citations to author/year and IEEE to `[n]` following selected reference order; bibliography uses matching selected format. Save chapter citation style. Earlier manually inserted in-text citations are **not auto-rewritten** when switching. | Node citation cases plus Chromium IEEE insertion |

## Verification (Linux test environment)

- `python -m pytest -q --disable-warnings`: **31 passed** (baseline 25, 6 new independent backend tests).
- `node tests/test_qa_091_citations.js`: **13 assertions passed**.
- Chromium + live FastAPI through isolated JS/Python API bridge: **12 recorded checks passed** — includes indicator persistence, APA, IEEE, desktop 1440px and mobile 390px. Not native browser localhost navigation.
- `python -m compileall -q app`, `node --check app/static/studio09.js` and `node --check app/static/citation09.js`: pass.
- Test accounts and datasets are fixture-only, not included in distributable ZIP.

## Residual risk / not independently verified

1. **Security:** single-owner loopback desktop application; localhost binding and session checks are not a full pen-test or a hosted/multi-tenant authorization design. CSRF and Host header checks are layered mitigations, not a substitute for formal deployment security testing.
2. **Statistics:** experimental SEM-PLS remains **NOT VALIDATED against SmartPLS/cSEM** for multi-indicator, formative, mediation/moderation, missingness, confidence intervals, or several independent golden datasets. **Do not claim parity.**
3. **References:** APA/IEEE functionality covers reported cases; complete style compliance would benefit from a standards-based CSL processor and diverse bibliographic fixtures. Only references explicitly linked to chapters are checked, not arbitrary manually typed claims/citations.
4. **Source provenance:** new uploads retain raw bytes (not a write-protected WORM archive). Before-v0.9.1 normalized CSVs cannot reconstruct original spreadsheet bytes; require users to re-upload original source if needed.
5. **Hardware/ops:** Ollama 1-hour inference on real 16GB Mac not executed. Mac/Windows launchers source-checked only; no physical OS test, backup/restore, load, concurrency, accessibility or CVE scan.
6. **Production release gate:** continue **NO-GO** until independent P0/P1 retest, real-device tests, security review and statistical qualification. Candidate is only for local beta testing with non-sensitive data.

## How to retest

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q --disable-warnings
node tests/test_qa_091_citations.js
```

`node` is only required to run frontend unit tests, **not** to run Z-Research.
