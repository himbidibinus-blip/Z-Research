# New v0.5 API contract

The original v0.2 endpoints remain available. Docs: http://127.0.0.1:8000/docs

All `/api/v05/...` endpoints require the same local owner session established using `/api/auth/setup` or `/api/auth/login`.

## PLS calculation

`POST /api/v05/pls/run`

```json
{
  "dataset_id": "<id from /api/datasets>",
  "nodes": [
    {"id":"a","label":"Social Media Marketing","type":"latent","measurement":"reflective","indicators":["social_media_1","social_media_2","social_media_3"]},
    {"id":"b","label":"Brand Trust","type":"latent","measurement":"reflective","indicators":["trust_1","trust_2","trust_3"]}
  ],
  "edges": [{"source":"a","target":"b","label":"H1"}],
  "bootstraps": 200,
  "seed": 42
}
```

Output includes `analysis_id` and `result`, containing `n`, `excluded_rows`, `paths`, `r_squared`, `f_squared`, `outer_model`, `reliability_validity`, `formative_diagnostics`, `inner_vif`, `cross_loadings`, `htmt`, `fornell_larcker`, `bootstrap`, `indirect_effects`, `limitations`.

Maximum 24 constructs, 2,000 bootstrap runs, noncyclic structural model, one measurement use per indicator, minimum 30 complete observations. Listwise deletion is disclosed. Single-item constructs return no alpha/CR estimate.

## References

- `POST /api/v05/references/upload` multipart form file (`.pdf`, `.docx`, `.bib`, `.ris`, `.txt`)
- `GET /api/v05/references/guides` metadata for uploaded writing guides
- `GET /api/v05/references` listed metadata
- `POST /api/v05/references/manual` bibliographic record
- `DELETE /api/v05/references/{id}` delete a record
- `POST /api/v05/references/search` `{query, from_year, count}` → OpenAlex unverified indexing
- `POST /api/v05/references/search-scopus` `{query, elsevier_api_key, count}` → official Scopus API records if credentials work
- `POST /api/v05/references/verify-scopus` `{issn, elsevier_api_key}` → serial title match, not article-level quartile validation

## Chapters

- `POST /api/v05/chapters/preview` preview final system + researcher prompt without provider cost
- `POST /api/v05/chapters/generate` call OpenAI using connected session API key; saved to SQLite
- `GET /api/v05/chapters` / `GET /api/v05/chapters/{id}` history/read
- `GET /api/v05/chapters/{id}/docx` saved draft Word output
- `POST /api/v05/chapters/export-word` `{chapter:3|4, body:"..."}` → Word export including **edited** text

Generation request example:

```json
{
  "chapter": 4,
  "dataset_id": "<dataset id>",
  "analysis_id": "<completed PLS-SEM analysis id>",
  "style": "ieee",
  "language": "English",
  "research_facts": "Only facts confirmed by researcher...",
  "instructions": "Use explicit tables and precise inferential distinctions...",
  "guide_id": null
}
```

AI requests transmit bounded analysis results and reference metadata, not raw records. An empty `analysis_id` for Chapter 4 produces placeholders rather than real findings.
