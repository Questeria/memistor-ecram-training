**Memistor Paper Version 6 Review**

Reviewed 27 October 2026. Target: the current 41-page [paper](paper/build/main.pdf), its [HTML edition](paper/build/main.html), submission variant, source archive, and supporting revision records. Current commit: `0b632060a`. Main PDF SHA-256: `2e42b090f9b3b8dd6a9474cb660c492f601b5d48d5a9fc0c6e52afef69fe4632`.

**Verdict.** Version 6 resolves the substantive findings from the version-5 review. The HTML now includes the missing sections, the previously mispaired tables have their correct contents, and the two availability/reproducibility wording corrections are accurate. I found no new major scientific or numerical error. One minor HTML conversion defect remains in Table 9's header. It does not affect the results or the PDF.

**Remaining finding — P3: remove LaTeX rule arguments from Table 9's HTML header.**

The first cell of the second header row contains `(lr)2-6(lr)7-8 Seed`, where the intended content is simply `Seed`. The literal text is present in [main.html, line 1990](paper/build/main.html:1990). It comes from the `\cmidrule(lr){2-6}\cmidrule(lr){7-8}` commands in [rev4_a2m.tex, line 3](paper/tex/tables/rev4_a2m.tex:3). The HTML contains ordinary text and spans for these arguments, so they are content rather than an invisible style instruction. The same residue was already present in version 5; this review's complete row comparison exposed it.

The PDF renders the header correctly on page 19. All five seeds' values and the summary row agree between the source and HTML. This is a cosmetic defect, not a reason to reopen the matched-run analysis. Strip or correctly handle the complete `\cmidrule` command, including its optional trimming argument and column range, in the HTML preparation stage. Check that the exported cell contains only `Seed`.

The new completeness checker is useful but does not catch this detail: [html_complete.py, line 175](paper/revision5/html_complete.py:175) checks selected signatures from a table's header, first row, and last row. It records row counts without enforcing their equality and does not compare every cell. That is a limit of the checker, not evidence of additional corruption: my independent comparison covered all 341 rows and found no other unexpected content difference. The other raw comparison difference was the correct conversion of a citation command to reference [11].

**The previous release defect is closed.**

The independent HTML audit found:

- All 34 section/subsection headings, in source order, plus all 41 paragraph headings.
- All 26 table captions matching the source after resolving references and number macros; all 341 table rows present, with matching row counts for every table.
- The sensitivity sheet under its own caption, and separate energy, hyperparameter-selection, and simulator-check tables with their correct contents.
- All 56 source labels present as HTML IDs, no duplicate IDs, no dead internal links, and none of the previous raw labels or unresolved-reference markers.
- Correct lettered appendices, three embedded figure images, and agreement between the numerical sequence in the HTML abstract and the 1,918-character submission abstract.
- All 236 checked long, uninterrupted prose spans present after resolving the owner's author-statement variant. This complements the heading checks; it does not treat headings alone as proof that a section's body survived.

Sections 5–9, the author-contribution and acknowledgment statements, and Appendices A and B are restored. The conversion repair is appropriately confined to HTML preparation. Its recorded small reproduction isolates the mixed paragraph-column-width case, and the source now rewrites those column specifications before conversion. I inspected the reproduction code and its saved outputs; I did not rerun the project's build or tests.

The saved completeness-check record rejects the old version-4 and version-5 HTML and reports detection of eight deliberately planted faults. My conclusion about the current artifact rests additionally on the independent comparisons above.

**The two wording corrections are closed.**

Section 4.3 now places the saved draws in the *deposit inventory*, consistent with Section 9's explicit statement that nothing has yet been deposited publicly. It no longer implies that a public archive already exists. Section 4.3 and Section 9 now say that rebuilding Tables 6–8 requires both the draw arrays and the probe-record metadata. That matches the reconstruction dependency on layer information, clipping statistics, and bootstrap counts. Appendix F's history uses the same corrected inventory language.

**The scientific conclusions retain their previous scope.**

I rehashed all 1,035 previously audited experiment/probe records and all 12 saved draw archives, totaling 81,905,772 bytes. None changed. The prior review snapshot also confirms unchanged contents for 14 simulator files, 39 table sources, and all five numerical-macro files. All seven figure PDFs in the source archive have unchanged decoded page-content streams relative to version 5. The manuscript changes are confined to availability language, the fidelity paragraph's reproducibility wording, and revision history.

The earlier independent calculations therefore remain applicable; this revision does not supply new experimental evidence. In particular, the five matched P2200 triples still yield surrogate and sequential gaps of 8.71 and 8.73 percentage points, with a paired difference of approximately 0.02 pp and a 95% interval of [-0.47, 0.52] pp. Both analog arms remain outside the 2 pp task margin. This supports the narrow agreement of those two update implementations in that experiment, without establishing their general equivalence or good task performance.

The paper still distinguishes success against the selected FP-SGD comparator from success against Adam. It retains the surrogate's clipping and shared-line-dependence limitations, the limited scope of the sequential-training comparisons, and the conditional nature of the 17.9–32.4× energy projection. Those are essential boundaries of the evidence. Version 6 does not turn a simulation study into a physical-device demonstration or a measured end-to-end training-efficiency result. No new literature review or training rerun was necessary for the publication-only changes examined here.

**PDF and submission-artifact checks.**

I rendered all 41 main-PDF pages, inspected the complete contact-sheet set, and inspected pages 19, 27, and 39 individually for the Table 9 header, availability wording, and revision history. Both current PDFs contain 41 pages, with no detected off-page text glyphs or unresolved `??` references. No new layout defect was apparent in the inspected PDF renders.

All four installed release artifacts—both PDFs, HTML, and source archive—match the final saved build output. The three corresponding TeX logs report 41 pages, with no undefined references, multiply-defined references, or overfull boxes. The archive contains 75 regular files plus its directory entry; every non-PDF member matches the current source, and archived figures match the current figures' decoded page streams. This checks the saved compilation evidence and archive contents; I did not perform a fresh compilation.

The review remained read-only in the project. Independent scripts, extracts, rendered pages, and results are saved in this review directory: [content/record audit](paper-review-v6/independent-audit.json) and [caption/prose/figure audit](paper-review-v6/content-audit.json).

**Verification limit.** Browser security policy rejected opening the local HTML file because `file:` URLs are not permitted. I did not bypass that restriction. HTML findings are based on its parsed document, source comparisons, and embedded content; browser layout, MathJax execution, and narrow-window behavior remain visually unverified. The PDF was visually inspected as described above.
