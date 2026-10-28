# Z-Research v0.5.4 — Writer Workspace Update

## Changes
- Reference search: saved ✓ indicator, disabled second click; database-level duplicate guard (DOI or normalized title + year).
- Chapter 1–4: responsive two-column academic writer + citation library rail. Use **Cite +** to insert an author-year citation at the editor cursor, or drag a reference into editor. Tick a source to include its metadata in the AI prompt. Sources are selected per chapter, not silently all passed to AI.
- Chapter 1: collapsible, bounded news search results, maximum 12 visible news leads, with saved evidence scroll area.
- Ollama server generation timeout 3,600 seconds (1h) with 12 sec connection timeout. Browser or a reverse proxy may time out earlier. 1h is a maximum wait, not promised completion; running a local model can be slow.
- Branding: **Settings → Z-Research brand logo** upload the original PNG/JPG/WebP from the other chat. Exact old logo was not packaged/available in this archive, so no invented replacement. Once uploaded the original will be displayed; logo saved in local_data/branding.
- No change to experimental SEM engine or research model builder.

## Mac startup
1. Stop old Z-Research server with Control+C.
2. Extract ZIP as `z-research-v0.5.4` to Downloads; do **not** overwrite old folder.
3. If migrating data, from the new folder run `bash UPGRADE_EXISTING_MAC.command` **before** starting. Source is your previous Z-Research directory. Verify it copied only the `local_data` directory.
4. Run `bash START_MAC.command` in the new folder.
5. Visit http://127.0.0.1:8000/api/health and check version `0.5.4`, then open dashboard.
6. Ollama should be running at http://127.0.0.1:11434 and `qwen3:8b` installed.

## Reference integrity
Cite buttons insert formatted **citation placeholders** from saved bibliographic metadata; researchers must inspect the source and check author spelling, year, relevance, DOI, APA/IEEE numbering, and the reference list before using in a thesis/publication. Numeric IEEE citation ordering in the lightweight editor follows library order and is not yet automatically synchronized with a Word bibliography. Drag and drop inserts using the current cursor, not an exact page layout coordinate.
