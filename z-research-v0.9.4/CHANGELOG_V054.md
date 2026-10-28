# Changelog v0.5.4 — Citation & UX update

- Academic reference discovery search buttons remember saved items and display **✓ Added to library**, disabling repeat clicks.
- Backend prevents duplicate bibliographic records for a user by DOI or normalized title + year; imports benefit as well.
- Chapter 1–4 drafting split into spacious manuscript editor and adjacent citation assistant. Selecting references controls which citations' bibliographic records are passed to the AI generator. Click **Cite +** to insert an inline citation at caret; drag-and-drop is supported. Included sources can be selected individually or all at once. Insert a draft bibliography on demand.
- Source selection persists in this browser for the four chapter editors; a refresh does not reset the selected reference IDs.
- Chapter 1 news search results constrained to scrollable height (up to 12 leads shown). Evidence link/upload form is collapsed by default and expands when user chooses a news lead.
- Common page spacing, button alignment, responsive editor/sidebar, and accessibility tweaks.
- Ollama local generation receives **3600 seconds** response timeout; 12 seconds connect timeout. Other AI providers unchanged.
- Original logo asset upload available through AI Settings; displays exact user-provided PNG/JPG/WebP in sidebar. The previous logo from a different chat is not contained in the supplied source ZIP.
- All existing Research Model Builder, SEM-PLS, statistics interpretation, and Chapter 1–4 document saves/exports preserved.

Caution: citations are metadata-derived draft references; read the articles and verify APA/IEEE formatting and citations before submission. Experimental SEM-PLS remains subject to external benchmark verification.
