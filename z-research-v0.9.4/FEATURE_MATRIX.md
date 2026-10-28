# Feature Coverage and Validation Register (v0.5)

| Domain | Feature | State | Research implications |
|---|---|---|---|
| Data | XLSX/CSV import; preview; missing summaries | Implemented | No claim that rows equal unique participants |
| Basic statistics | Descriptive, multiple OLS, Cronbach alpha | Implemented | Formula-based via scipy/statsmodels |
| Model editor | Construct dragging, indicator mapping, direct paths, SVG/PNG/JSON | Implemented | Visual only; estimations run separately |
| PLS estimation | Iterative centroid inner, Mode A reflective, Mode B formative | Experimental | No SmartPLS-equivalence evidence yet |
| PLS outputs | Path coefficients, outer loadings/weights, latent composite correlations | Experimental | Quantitative values from local Python computation |
| Model quality | Alpha, CR, AVE, HTMT, Fornell–Larcker, cross-loadings | Experimental | Reflective single-item CR/alpha not estimated |
| Collinearity | Inner VIF, formative-indicator VIF | Experimental | Check thresholds and construct theory separately |
| Effect sizes | R² and f² | Experimental | Computed using standardized PLS scores |
| Bootstrap | Percentile 95% confidence intervals, approximate two-sided z p | Experimental | Not yet benchmarked; p is normal approximation |
| Mediation | Indirect effects for two-hop construct paths | Experimental | Only paths actually modeled |
| Q² / blindfolding | Not yet available | Planned | Never present Q² without computation |
| PLSpredict | Not yet available | Planned | Predictive performance not assessed |
| Consistent PLS (PLSc), rho_A | Not yet available | Planned | Must not assert consistent factor estimation |
| HTMT bootstrap inference | Not yet available | Planned | HTMT point estimates only |
| MGA, MICOM | Not yet available | Planned | No cross-group inference |
| Moderation | Latent-interaction modeling not available | Planned | Structural moderation not automatic |
| HCM / repeated indicators | Not yet available | Planned | No higher-order constructs |
| SRMR, d_ULS, d_G | Not yet available | Planned | No global fit claims |
| IPMA / FIMIX | Not yet available | Planned | Advanced segment/importance analysis deferred |
| Chapters | AI-guided Chapter 3 & 4 drafts, one-click pair, local saved drafts | Implemented (API required) | Prompts mandate placeholders for missing facts |
| Word | Edited chapter DOCX export | Implemented | Word writing draft; not publisher typesetting |
| AI | Owner login, OpenAI API connection in server RAM, grounded AI prompt | Implemented (not live-key tested) | OpenAI API billing is separate |
| Reference upload | PDF/DOCX text, RIS/BibTeX parsed records | Implemented | Uploaded references unverified until checked |
| Reference discovery | OpenAlex search | Implemented (not live-network tested) | OpenAlex != Scopus index |
| Reference discovery | Elsevier Scopus search + serial title API | Implemented (requires authorized key; not live-key tested) | Serial title lookup alone does not verify article-year inclusion |
| Quartile | Automated Scopus SJR quartile classification | NOT AVAILABLE | Cannot safely infer quartiles from OpenAlex metadata |
| University deployment | Campus multi-user/SSO, policies, role-based data isolation | NOT AVAILABLE | localhost owner prototype only |
