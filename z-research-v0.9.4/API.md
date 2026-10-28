# API reference — Z-Research v0.2

Local API: `http://127.0.0.1:8000`. Interactive FastAPI documentation: `http://127.0.0.1:8000/docs`.

## Existing statistical endpoints (unchanged)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Version and local status |
| POST | `/api/datasets` | Multipart CSV/XLSX upload (`file` field) |
| GET | `/api/datasets` | Dataset list |
| GET | `/api/datasets/{dataset_id}` | Preview and missing counts |
| POST | `/api/analyze/descriptive` | Descriptive statistics |
| POST | `/api/analyze/regression` | Multiple OLS regression |
| POST | `/api/analyze/reliability` | Cronbach Alpha |
| POST | `/api/reports/methodology` | Deterministic v0.1 methodology template |
| GET | `/api/analyses/{analysis_id}` | Exact analysis output |
| GET | `/api/analyses/{analysis_id}/export` | Download reproducible JSON |

Example statistical requests:

```json
{"dataset_id":"YOUR_DATASET_ID","columns":["age","trust_1"]}
```

```json
{"dataset_id":"YOUR_DATASET_ID","outcome":"purchase_intention","predictors":["trust_1","social_media_1"]}
```

```json
{"dataset_id":"YOUR_DATASET_ID","indicators":["trust_1","trust_2","trust_3"]}
```

## New v0.2 authenticated AI and modeling endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/auth/status` | Owner setup, login and provider status (never returns a secret) |
| POST | `/api/auth/setup` | First and only owner account (`username`,`password` >=10 chars) |
| POST | `/api/auth/login` | Local owner login; Strict SameSite, HTTP-only session cookie |
| POST | `/api/auth/logout` | End session and forget provider key |
| POST | `/api/ai/connect` | Verify API key with GET `/v1/models`, store key in RAM only |
| POST | `/api/ai/disconnect` | Remove provider key from session |
| GET | `/api/ai/templates` | Sections and default prompt guidance |
| POST | `/api/ai/prompt-preview` | Full system + user prompt WITHOUT external AI call |
| POST | `/api/ai/generate` | OpenAI Responses API generation, saved as draft |
| GET | `/api/ai/analyses` | Available saved statistical results for AI writing |
| GET | `/api/ai/drafts` | Recent AI text history |
| GET | `/api/ai/drafts/{draft_id}` | One saved AI draft |
| POST | `/api/models` | Save model JSON with constructs and directed paths |
| GET | `/api/models` | List saved model metadata |
| GET | `/api/models/{model_id}` | Restore model |

### Connection request

```json
{"api_key":"YOUR_REAL_API_KEY","model":"gpt-5-mini"}
```

The connection call verifies key access without generating text. Permission for the specific chosen model is validated by the first generation attempt. Users supply their own valid API key and funded/authorized API project.

### Methodology generation request

```json
{
  "kind":"methodology",
  "section":"ethical_process",
  "dataset_id":"YOUR_DATASET_ID",
  "research_facts":{
    "design":"cross-sectional survey; researcher verified",
    "population":"Adults purchasing beauty products in Indonesia; eligibility criteria documented",
    "sampling":"recruitment process not yet documented",
    "collection_period":"Actual date needs verification",
    "instrument":"three trust items; exact wording and scale anchors to verify",
    "ethical_process":"consent and ethics details not yet documented",
    "analysis_plan":"Descriptive, internal consistency, OLS regression"
  },
  "style":"ieee",
  "custom_style":"Concise tone. Target journal requires separate methodology subheadings.",
  "user_prompt":"Use objective third-person prose. Highlight unknown approval status.",
  "language":"English"
}
```

Available `section` values: `design`, `population`, `sampling`, `collection_period`, `instrument`, `ethical_process`, `analysis_plan`.

### Results generation request

```json
{
 "kind":"results",
 "section":"regression",
 "analysis_id":"REAL_COMPUTED_ANALYSIS_ID",
 "dataset_id":"DATASET_USED_FOR_ANALYSIS",
 "research_facts":{},
 "style":"ieee",
 "user_prompt":"Use exact β/b/t/p values available; no unsupported causal claims.",
 "language":"English"
}
```

Allowed results sections: `descriptive`, `regression`, `reliability`, `methodology`, with a matching existing stored analysis. User cannot submit their own purported coefficients to masquerade as a computed result through this endpoint.

### Research model save request

```json
{
  "name":"SMM, trust, purchase intention",
  "dataset_id":"YOUR_DATASET_ID",
  "nodes":[
    {"id":"smm","label":"Social Media Marketing","type":"latent","indicators":["smm_1","smm_2","smm_3"],"x":220,"y":210},
    {"id":"trust","label":"Brand Trust","type":"latent","indicators":["trust_1","trust_2","trust_3"],"x":540,"y":210}
  ],
  "edges":[{"source":"smm","target":"trust","label":"H1"}]
}
```

Geometry and indicator labels drive diagram rendering only. The model is **not fit** by the statistical engine. To compare structures statistically, future SEM analysis endpoints will be needed.
