# Chapter 3 and Chapter 4 Writing Prompt Design

The actual versioned system instructions are stored in `app/v05.py` as `GUARD`, `CHAPTER3`, and `CHAPTER4`; the original seven methodology and three results templates remain in `app/prompts.py`.

## Universal academic system guard

- Base statistical statements exclusively on calculations from the selected analysis ID.
- Treat uploaded dataset dimensions as dataset shape, never as verified eligible unique participants.
- Separate researcher-confirmed procedures from recommended steps and missing documentation.
- No invented informed consent, research approval, sampling strategy, recruitment window, validated questionnaire provenance, coefficients, p-values, or sample descriptors.
- Never generate bibliography entries not present in the actual user reference library; insert `[REFERENCE NEEDED]` for unsupported assertions.
- Format according to IEEE / APA / target journal *without reproducing copyrighted passages* from uploaded writing examples.
- For PLS-SEM, prominently disclose the experimental estimation engine and its unvalidated equivalence to established software.

## Chapter 3: numbered outline

3.1 Research Approach and Design
3.2 Conceptual Framework and Hypotheses
3.3 Target Population and Eligibility
3.4 Sampling Frame, Method and Sample Size
3.5 Instrument Development and Operationalization
3.6 Data Collection
3.7 Research Ethics
3.8 Data Screening and Missingness
3.9 Data Analysis Plan (measurement/structural model, bootstraps, missingness, assumptions, cutoffs)
3.10 Reproducibility and Chapter Summary

**Specific controls**: Every unknown field receives `[RESEARCHER TO CONFIRM: ...]` rather than a plausible-sounding invention. State whether analysis is planned or completed according to verified user facts and available results.

## Chapter 4: numbered outline

4.1 Introduction
4.2 Data Screening and Analytical Sample
4.3 Descriptive Findings
4.4 Measurement Model Assessment
4.5 Structural Model Assessment
4.6 Hypotheses Summary Table
4.7 Indirect Effects
4.8 Results Interpretation and Limitations
4.9 Chapter Summary

**Specific controls**: Use numerical results from the selected completed analysis. Copy tables and statistics only where provided. Show estimated path coefficients and exact reported uncertainty. When a result is absent, use `[RUN ANALYSIS]` instead of inferring a missing value. Do not present normal approximate p-values as exact permutation tests.

## Custom journal styling

The user can select IEEE, APA, general academic, or custom. The user can enter a prompt in AI Settings and optionally upload journal writing guidance (PDF/DOCX/TXT). The guide is used for stylistic cues with bounded excerpts, never as authority to copy an article or invent a reference.

## Reference discovery

OpenAlex is for discovery only. Elsevier Scopus API access offers direct serial title or article metadata when authorized. Q1/Q2/Q3/Q4 and article-level Scopus coverage require independent, year-appropriate verification. Each library record defaults to `NOT_VERIFIED`.
