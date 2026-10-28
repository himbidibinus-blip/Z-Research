# Z-Research v0.9.2 · QA Remediation Report

**Basis:** `ZResearch_v091_QA_Master_Package.zip` audit dated 19 October 2026.
**Decision:** Scoped QA remediation **PASS** for the three independently documented P1 regressions under tested conditions; overall **NO-GO for public production**.

| Bug | Code change | Acceptance tests |
|---|---|---|
| ZR-QA-091-01 | `app/main.py` validates raw CSV and XLSX header row before Pandas | HTTP 422 duplicates and whitespace/BOM/case collisions, accept valid headers, no retained failed upload |
| ZR-QA-091-02 | New authenticated `POST /api/v09/projects/{pid}/chapters/{chapter}/versions/{revision_id}/restore`; single SQLite transaction for body + source IDs + style + event | Restore two contrasting versions, stale evidence, missing reference blocks, cross-chapter and anonymous rejection, client-side restored selection |
| ZR-QA-091-03 | `app/static/citation09.js` linked citation tokens, live preview and first-appearance numbering; `app/citations.py` export renderer; save checks token selection | Insert, reorder, delete, style switch, multiple citations, bibliography consistent, Word export and legacy warning |

Additional defence in depth:
- Chapter status separately reports `citation_integrity`; plain-text citation content is not certified by the presence of selected reference IDs.
- Legacy manually entered IEEE numeric citations are `needs_review` and Word export carries a warning; these are not auto-renumbered because their source IDs are unknown.
- New citation tokens referencing an unselected source are rejected with HTTP 422 during save.
- Previously repaired v0.9.1 tests for auth, origin, original raw file checksums, ref deletion and indicator binding remain in the suite.

## QA execution ledger

- Python original and adapted independent API suites plus new v0.9.2 cases: **65 passed**.
- JavaScript shipped v0.9.1 formatter assertions: **13 checks passed**.
- JavaScript v0.9.2 token and versioning invariants: **20 checks passed**.
- Chromium browser test against live local Uvicorn via original HTML/CSS/JS with isolated fetch bridge: **14/14 passed**, at desktop 1440 px and mobile 390 px. See `QA_RESULTS_V092.json`.
- Python compile checks and Node syntax checks passed.
- Tests executed on Linux testing environment. Browser access to native localhost navigation is sandbox-restricted, therefore this is **not** native Mac/Windows browser E2E.

**Independence note:** The v0.9.1 independent suite is included as `tests/test_independent_qa_091_retest.py`; its defect-characterization #13 intentionally expected HTTP 200 in the old broken release. This expectation has been explicitly changed to the remediation acceptance HTTP 422; the other independent probes remain unchanged.

## Outstanding release gates

- Formal SmartPLS/cSEM parity testing on independent benchmark datasets.
- Real installations and manual usability testing on Mac and Windows, including migrated user data and backup/restore.
- Real Ollama one-hour request, limits and failure/retry behavior on representative hardware.
- Security penetration testing, dependency vulnerability and concurrency/data-loss auditing.
- Full CSL citation formatting and semantic verification of literature claims.

**No claim of total absence of bugs or public-release readiness.**
