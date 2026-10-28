# Z-Research v0.9.2 — Research Integrity Stabilization

**Release type:** Local Beta · macOS and Windows source edition. **Not approved for hosted/public production.** This release addresses the three High/P1 defects recorded in the independent v0.9.1 QA master package. It builds directly on v0.9.1 and preserves its previous QA repairs, research workflows and Ollama provider.

## Installation / upgrade

1. Stop the **old** Z-Research server (Control+C in the Terminal), and back up the entire previous application folder, particularly `local_data` and `quantresearch.db`.
2. Extract `Z-Research_v0.9.2_Research_Integrity_Mac_Windows.zip` into its own `z-research-v0.9.2` folder. Do not overwrite v0.9.1.
3. **Before running** the new version, migrate your existing research workspace:
   - macOS: `cd ~/Downloads/z-research-v0.9.2` then `bash UPGRADE_EXISTING_MAC.command`. Enter the full old folder path when asked. The script will not overwrite nonempty destination data.
   - Windows: while both apps are stopped, **back up first**, then copy the old `local_data` folder to the new `z-research-v0.9.2` directory if it does not already contain data.
4. Start with `bash START_MAC.command` on macOS, or `START_WINDOWS.bat` on Windows. The launcher installs dependencies into its own `.venv`.
5. Open `http://127.0.0.1:8000/api/health`; expected version is `0.9.2`. Then open `http://127.0.0.1:8000` and refresh the browser if needed.
6. To verify Ollama: keep `qwen3:8b` installed and start Ollama; choose **AI & Account → Ollama Local**. The configured HTTP timeout remains 3,600 s, **not** a completion guarantee.

## Three release-gate fixes

**ZR-QA-091-01: Dataset header integrity.** CSV/Excel original headers are validated **before Pandas**. Empty and duplicate labels (including BOM, leading/trailing whitespace, Unicode normalization and case collisions) now trigger HTTP 422 instead of implicit renaming. No working dataset, database row or original archive is created for a rejected upload. Raw accepted bytes are preserved and SHA-256 verified as in v0.9.1.

**ZR-QA-091-02: Atomic historical chapter restoration.** Under **View draft versions**, click **Load into editor**; the server creates a new revision containing the exact historical text, selected reference IDs and citation style in one database transaction. The original revision remains intact. If a linked source was removed, restoration is refused; if the current project/reference evidence differs from the historical snapshot, the restored revision is marked **stale** and a warning appears. This action now saves a *new version* automatically (not merely an unsaved browser buffer).

**ZR-QA-091-03: Linked APA / IEEE citation rendering.** Citation insertion uses `[@ref:<reference-id>]` source tokens inside the editable draft; the **Live citation preview**, downloaded TXT and Word export resolve these tokens to final APA or IEEE citations. IEEE numbering is recalculated from **first appearance in the draft** every time it is rendered; deleting/reordering citations and changing citation style cannot leave outdated numbers for these tokens. The `[@bibliography]` placeholder is a live bibliography, not frozen text; without a placeholder the export automatically appends references for cited sources. Only cited references appear in the bibliography. The application rejects a new saved draft if a linked citation ID is not in its selected sources.

**Important backwards compatibility:** Previously typed `(Author, 2025)` or `[2]` are plain text; an old numeric citation cannot safely be attributed to a particular source ID. Those drafts are preserved and numeric citations are flagged as **needs_review** until manually replaced via **Cite +**. The system does not invent a mapping. Citation **ID integrity** is separate from verifying source content, bibliographic accuracy or full APA 7 / IEEE CSL compliance.

## Developer / QA checks

```sh
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q --disable-warnings
node --check app/static/studio09.js
node --check app/static/citation09.js
node tests/test_qa_091_citations.js
node tests/test_v092_citations.js
```

The ZIP includes a detailed `QA_REMEDIATION_V092.md` and the new automated test sources. Test fixtures create temporary databases and **do not modify your research data**.

## Remaining limits

- **Never claim bug-free:** Automated checks cover known cases and a constrained browser simulation, not every possible input or device.
- SEM-PLS remains experimental without independent golden-data parity for multi-indicator, formative, mediation/moderation or bootstrap confidence intervals vs SmartPLS/cSEM.
- Native physical Mac/Windows launch, actual long-duration Ollama inference, comprehensive dependency/pentest, storage durability and disaster recovery are still outside the validated scope.
- Not suitable yet for hosted SaaS or sensitive multi-user research deployments. Keep local loopback binding, back up your research data and verify final manuscript text independently.
