# Z-Research v0.5.3 release notes

- Added Ollama local provider (`http://127.0.0.1:11434/api/chat`) with `qwen3:8b` model check and no API secret.
- Preserved API providers (OpenAI, Gemini, Anthropic, OpenRouter, Groq, DeepSeek, Mistral, Together, custom HTTPS compatible provider).
- Reordered research flow: Dashboard → Research Model Builder → SEM-PLS Analysis → Chapter 1 Phenomena → Reference Library → Chapter 2 Literature → Chapter 3 Methodology → Chapter 4 Findings.
- Moved statistical tools to a unified collapsible panel under SEM-PLS; Python computation routes remain for backward compatibility.
- Added PLS output explanation, path coefficients and R² interpretations, and explanatory glossary for reliability/validity/OLS/descriptives.
- Added dataset-variable-driven exploratory phenomena suggestions, news RSS discovery, evidence URL library, article PDF/DOCX/TXT upload.
- Added Literature Review generator and bibliographic evidence matrix from shared Reference Library; warns that metadata does not establish article findings.
- Added complete editable Chapter 1–4 writers, prompt preview, shared refs and guide upload, Word/Markdown export, saved history and explicit save-edited operations.
- Added optional current edited research model as contextual theoretical specification in chapter prompts.
- Preserved local dataset snapshots, model builder, live PLS, and all earlier endpoints.
- Added 3 new automated test functions; 15 total tests passing. Browser UI tests could not run due to environment network/navigation restrictions.
