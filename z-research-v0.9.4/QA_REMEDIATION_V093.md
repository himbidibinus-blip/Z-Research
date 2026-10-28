# QA Remediation: Z-Research v0.9.3

**Date:** 19 October 2026  
**Input audit:** `ZResearch_v092_IndependentDeepQA_Report.md`, master package and the original auditor-written `test_independent_deep092.py`.  
**Decision:** Known defects closed for the tested scenarios; **NOT cleared for hosted/public production**. Further independent audit still needed.

## Audit issue closure matrix

| ID | Audit severity | Root cause | Remediation | Verification |
|---|---|---|---|---|
| ZR-QA-092-01 | High / P1 | Shared `.editing.csv`; stale concurrent read and uncoordinated read-modify-write | OS-backed per-dataset cross-process FileLock, fresh read while locked, unique temporary CSV, fsync and atomic replace, transactional edit log, detected-failure rollback | Original auditor concurrency test PASS; 24 parallel thread edits PASS; 6 multi-process edits PASS; 1 audit log per edit |
| ZR-QA-092-02 | Medium / P2 | `BadZipFile` and other openpyxl errors escape `validate_original_headers` | Catch workbook reader/parser exceptions as 422 before any persistence | Original auditor negative test PASS; corrupt workbook variants PASS; no partial database/files |
| ZR-QA-092-03 | Medium / P2 | Python author splitter case-sensitive; JS case-insensitive | Python split is `re.I`, structured author parts supported | Original auditor APA test PASS; full Python/JS render corpus PASS; saved Word/TXT/JS preview PASS |
| ZR-QA-092-04 | Medium / P2 | Audit warning required nonempty selected source IDs | Heuristic author-year detection independent of selected source IDs | Original auditor audit test PASS; selected=0 and mixed linked+plain citation cases PASS; chapter UI warning |

## Automated test record

- Original v0.9.2 shipped Python suite: **65 PASS**.
- Original independent QA probes: **7 PASS, 0 FAIL** (file supplied by auditor copied into `tests/test_independent_deep092.py` without changes).
- New v0.9.3 Python tests: **12 PASS**.
- Combined `python -m pytest -q --disable-warnings`: **84 PASS**.
- JavaScript suites: **13 + 20 + 13 = 46 checks PASS**; JS source syntax PASS.
- Chromium **limited API-bridge smoke**: desktop 1440 px PASS, mobile 390 px PASS; chapter editor visible, IEEE citation preview displayed, no page errors, no horizontal overflow. Browser did not navigate a native `localhost` URL due to test-environment restriction.
- Mac/Windows native hardware tests: **NOT TESTED**. Windows process-lock support comes from the `filelock` library; the concurrency stress tests ran on Linux.

## Storage semantics and caveats

All writes through `/api/v05/datasets/{id}/edit-cell` serialize per dataset via an advisory OS file lock. The second edit reads the newly written CSV before applying its own change. Unique temporary files are created in the same directory to keep `os.replace` atomic. A transaction records one edit audit row before a successful response. Fsync is performed on the CSV and, where supported, its directory. The first working CSV copy is backed up and raw archives from the importer remain immutable. No changes to the archived original file or source data were required to test these fixes.

A CSV rename and a SQLite commit **cannot be a single ACID transaction**. Normal detectable failures receive best-effort compensation. Sudden power loss or termination between commit/replace operations, external edits or a nonlocal filesystem may require recovery. Moving working datasets into transactional storage would be required for a stronger crash-consistency guarantee; it is explicitly outside this v0.9.3 QA closure.

## Academic integrity semantics

`status=current` remains a statement about model/data/reference fingerprints, not a guarantee every manually typed citation has a bibliographic match. The separate `citation_integrity` field and the audit checklist mark possible legacy author-year cites for human review. The detection intentionally has false positive/false negative possibilities. Linked token citations are checked against selected source IDs; this is distinct from checking whether the research findings are supported by the source.

## Still unverified

Independent parity of complex SEM-PLS vs SmartPLS/cSEM; actual native Mac/Windows installation; long-running Ollama inference; disaster recovery after disk failure; multi-user public security; full citation CSL conformance; full browser E2E; exhaustive race/error injection. Neither 84 passing tests nor the previous 65 passing tests prove the absence of all bugs.
