# Z-Research v0.9.3 — Data Consistency & Research Integrity

**Release type:** LOCAL BETA source edition, for macOS and Windows. **Not cleared for public/hosted production.** Built as a remediation release from **v0.9.2**, based on the 19 October 2026 Independent Deep QA Audit. The original tested v0.9.2 source and the QA-provided seven-test independent suite were preserved; these four findings are addressed in the new source.

## Upgrade on macOS

1. **Close** the old Z-Research Terminal (`Ctrl+C`), and **back up the entire old folder**, especially `local_data`, including `quantresearch.db`, working CSVs, `raw_uploads`, and any audit logs.
2. Extract `Z-Research_v0.9.3_Data_Consistency_Research_Integrity_Mac_Windows.zip` into its own `z-research-v0.9.3` folder. **Do not replace your old installation in place**.
3. Before starting the new app, from Terminal:

   ```bash
   cd ~/Downloads/z-research-v0.9.3
   bash UPGRADE_EXISTING_MAC.command
   ```

   Enter the path to the previous application folder. The script refuses to overwrite a nonempty destination `local_data` folder. The old installation is left unchanged.
4. Start:

   ```bash
   bash START_MAC.command
   ```

5. Open `http://127.0.0.1:8765/api/health`; **version should be `0.9.3`**. Then open `http://127.0.0.1:8765` and log in using your migrated *local owner account*.
6. Open an existing project and check **Data & Projects → Edit** and **Integrity & History**. Retest on a **copy** of any critical dataset first.

## Windows

Stop the old app, back up the old `local_data` directory, extract the archive into a new folder, and **before first launch**, manually copy the entire old `local_data` directory into the new directory **only if the destination is empty**. Run `START_WINDOWS.bat`, then open `http://127.0.0.1:8765`. Ensure no older instance still binds port 8765. Windows-native installation was **not** tested in the QA environment.

## Fixes from audit (ZR-QA-092-01 through 04)

- **Concurrent dataset editing (P1):** Every edit obtains an OS-backed, **per-dataset cross-process file lock**; it **re-reads the latest CSV inside the lock**, persists to a unique temporary CSV, `fsync`s the new CSV, and atomically replaces the working file. The SQL edit ledger is recorded as a transaction. If an ordinary database error occurs following file replacement, a best-effort compensating CSV restore runs before releasing the lock. The immutable raw-upload archive remains untouched. Once an edit returns HTTP 200, its changed cell and one edit audit event have committed in the tested path. Editing the same cell concurrently is last-writer-wins; this is not a row revision conflict detection system.
- **Malformed XLSX (P2):** Parser errors from corrupt/unreadable Excel files now generate HTTP 422 with a safe message, **before** any dataset/raw file is created. Valid CSV and XLSX imports and duplicate-header validation are preserved.
- **Python/JavaScript citation formatting (P2):** `AND` author separators are case-insensitive in both engines. New tests compare the **entire render output** of APA/IEEE for a multi-case author corpus, plus saved Word and TXT/browser preview for uppercase `AND`. Python now also accepts `author_parts` where provided.
- **Unlinked plain-text author-year citations (P2):** The integrity audit issues **review** alerts for likely author-year citations such as `(Smith, 2025)` and `Doe (2024)` even with zero selected sources. Mixed linked and manually typed citations still trigger a warning. This is a **heuristic**, not an academic correctness proof; source/model version status remains separate from citation review status. A warning is also displayed in the chapter editor for saved chapters with candidate citations.

## Reproducing QA tests

Install Python >=3.11 and Node.js (for the JavaScript checks):

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q --disable-warnings
python -m pytest tests/test_independent_deep092.py -q --disable-warnings
node --check app/static/studio09.js
node --check app/static/citation09.js
node tests/test_qa_091_citations.js
node tests/test_v092_citations.js
node tests/test_v093_citations.js
```

**Evidence at packaging time (Linux QA environment, isolated test stores):** **84/84** Python tests passed (the original 65 shipped tests, 7 independent adversarial tests copied unchanged from the auditor's evidence, and 12 new v0.9.3 tests). **46** standalone JavaScript checks passed (13 + 20 + 13). Two limited Chromium UI smoke tests passed (1440 px desktop and 390 px mobile; no uncaught page errors on those routes). The app files were retested after clean ZIP extraction; see `qa_evidence/` and `QA_REMEDIATION_V093.md`.

## Workflows preserved

Existing FastAPI APIs, local SQLite workspace, upload CSV/XLSX, project/model builder, SEM-PLS experimental estimator, Chapter 1–4 editor, citation-linked manuscript history, research reference library, Word/TXT export, owner login and Ollama/cloud-provider adapter. No user dataset or API secret is packaged. The installer retains loopback (`127.0.0.1`) binding.

## Important constraints

- **No software can truthfully be certified bug-free from the supplied tests.** This is a release candidate for further independent QA, not a guarantee.
- Database and CSV are separate durability domains. Compensating rollback handles normal detected failures but cannot fully guarantee ledger/file atomicity across sudden OS crashes, disk failures or power loss. Store critical data in backups and consider a single durable transactional storage engine before SaaS/production use. CSV lock coordination requires that editing always passes through this app; external direct edits remain outside the guarantee.
- The local owner/session approach is **not a production-grade multi-user auth system**. No independent penetration test, dependency CVE review, native Windows/Mac installer test, backup/recovery exercise, or Ollama 1-hour inference test has been completed here.
- SEM-PLS **is experimental**: it has not been verified against SmartPLS/cSEM golden outputs for multiple measurement/structural models. Do **not** advertise SmartPLS numerical parity.
- APA/IEEE formatting is a limited custom formatter, **not** a full CSL implementation. A review alert indicates *possible* manually typed citations, not that a real reference was verified. Always check citations and academic claims manually.

---

**Next release gate:** independent retesting of v0.9.3, physical Mac/Windows E2E and installation, crash/backup-recovery validation, security review, and multi-model SEM numerical benchmarking prior to public production.
