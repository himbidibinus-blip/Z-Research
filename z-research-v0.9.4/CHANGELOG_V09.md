# Changelog — v0.9.0 local beta

## Phase A — Connected research foundation
- New project-oriented database with user-owned project list, linked dataset, model revision, event timeline, SHA-256 dataset/model fingerprint, stale statuses and reproducibility JSON.
- Backwards-compatible v0.5.4 API and `/legacy` UI.
- Model auto-generation based on dataset indicator names, theoretical construct roles, modifiable hypothesis paths, editable measurement type and indicator columns.

## Phase B — Analysis and provenance
- Project-specific SEM-PLS estimator with missingness summaries, bootstrap settings and random seed; experimental-quality warning and diagnostic flags.
- Rapid noninferential preview after model load/edit; saved bootstrap analysis remains deliberate to avoid expensive recomputation on every keystroke.
- Edited dataset numeric cells preserve original backup and invalidate saved run/draft provenance.

## Phase C — Research & writing studio
- Clean standalone Overview/Data/Model/SEM/Chapter 1–4/Evidence/Integrity/Settings UI.
- Shared deduplicated article library, selected citations in AI prompt, drag/click-to-cite, chapter versioning, saved DOCX export, local text export.
- Chapter 1 Phenomena Finder and scroll-limited external news discovery; Chapter 2 evidence mapping with title-only disclosure; Chapter 3 methodological checklist; Chapter 4 requires current analysis for AI generation.
- Ollama `qwen3:8b` default on user-installed 16-GB Mac; 3600-second local inference timeout. Cloud providers remain optional.

## QA status
- 25 Python tests passed, JavaScript syntax check passed, isolated Chromium UI test passed for the central workflow. Actual Mac/Windows/Ollama end-to-end tests still required.
- SEM-PLS remains unbenchmarked experimental code and is not represented as equivalent to SmartPLS.
