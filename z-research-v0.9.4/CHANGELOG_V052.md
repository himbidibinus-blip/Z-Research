# Z-Research v0.5.2 — Implementation notes

## Changes from v0.5.1

1. **Provider choice, not OpenAI-only**: OpenAI Responses, Google Gemini native `generateContent`, Anthropic native Messages, OpenRouter/Groq/DeepSeek/Mistral/Together OpenAI-compatible Chat Completions, and HTTPS custom OpenAI-compatible endpoints. Choose provider, secret key and **provider-specific model ID** from Settings. API keys are accepted from the selected vendor, not sent to OpenAI for validation. Secrets held only in server RAM for logged-in sessions. A key test does not prove model entitlement; custom provider keys are not verified until generation.
2. **Research-role model builder**: upload CSV/XLSX, map independent (X), dependent (Y), mediators (M), and moderators (W) from detected numeric indicator groups. Constructs, arrow paths and initial labeled hypotheses are auto-built. Manually modify indicators, measurement modes, edge source/target, direct versus interaction type, and edge hypotheses.
3. **PLS-SEM auto-preview**: debounced 850 ms on substantive changes, 40 bootstrap replications, not persisted. For final reproducible analysis click **Run PLS-SEM** and choose a larger bootstrap count. The authoritative PLS estimator remains experimental, and outputs are not equivalent to commercially validated SmartPLS.
4. **Moderation**: experimental two-stage standardized latent-score interaction. The moderator main effect is included automatically if missing. This is an approximation, not full SmartPLS latent interaction validation.
5. **Editable numeric dataset values**: paginated numeric editor in PLS-SEM Lab; changing an input cell writes CSV, creates an original-dataset backup on first edit and logs the edit. Live preview recalculates from updated data. **Computed coefficients and significance are intentionally not directly editable**, because they must be derived from observations, measurement and path specifications.
6. **Mac launcher improved** to always use the same isolated Python executable to install dependencies and run Uvicorn (fixes the common `No module named uvicorn` environment mismatch). Includes Windows launcher and non-destructive data migration helper.

## Known limitations

- Auto-detected indicator groupings are based on column naming (e.g. `trust_1, trust_2`). Conceptual research roles, construct types and operationalization require human theoretical decisions. Mixed-type, categorical, reverse-coded, second-order and unlabeled data need manual review or preprocessing.
- Live analysis is **recalculation after model/data changes**, not a WebSocket streaming estimator. Runtime depends on N, indicator count, number of paths and bootstrap replications. Errors and insufficient N are shown instead of fabricated estimates.
- Published research should validate the PLS estimates externally; the two-stage moderator implementation, bootstrap uncertainty, discriminant validity and measurement model constraints are not certified.
- Only supported native APIs and **OpenAI-compatible** custom APIs can be used with a secret key. An arbitrary noncompatible vendor protocol cannot work without an adapter.
- Providers differ in limits, models, pricing and regional availability. ChatGPT Plus never covers external API usage. No live provider-key verification is performed during offline automated tests.
- Local prototype only: localhost bind, single local owner account, no cloud sync, no enterprise key vault, no multiuser concurrency guarantees, and no automated dataset version rollback beyond first-edit CSV backup.
