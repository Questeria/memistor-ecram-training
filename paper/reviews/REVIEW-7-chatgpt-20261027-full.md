**Memistor Paper Version 7 Review**

Reviewed 27 October 2026. Target: version 7 of the [paper](paper/build/main.pdf), the [HTML edition](paper/build/main.html), the submission variant, source archive, and revision evidence. Commit: `c43a544dc`. Main PDF SHA-256: `b1a92aa73403be65e49b44399f776f2d1006f239d8299c2d2ed4b27bbfa463c8`.

**Verdict.** The remaining version-6 finding is fixed. I found no new actionable scientific, numerical, or document-content defect in version 7. The previous substantive findings remain closed. This is a publication repair with unchanged experimental evidence. Mobile HTML rendering remains unverified; that limit does not reopen the repaired Table 9 finding.

**Table 9 is corrected.** The HTML header now contains exactly `Seed`, followed by the intended seven column labels. The stray `(lr)2-6(lr)7-8` text is gone. The five seed rows and the summary row retain their original values. The source change removes the complete table-rule commands before conversion, preserving the table content and leaving the PDF's rules intact. The saved 1280-pixel and 700-pixel browser screenshots visibly show the corrected header.

The new leftover-LaTeX checker scans all 26 tables and the remaining page text, excluding intentional mathematical LaTeX. The saved results show that it rejects the old version-6 artifact and catches six planted faults, including the exact prior header residue. It also preserves the legitimate learning-rate abbreviation `(lr)` and mathematical commands inside math spans. I inspected the checker and the rule-removal implementation; I did not run the project's tests or build.

The existing completeness checker still compares selected table signatures rather than every cell. The new residue check addresses the actual conversion defect without converting that checker into a general cell-equivalence proof. My independent source-to-HTML comparison supplies that additional verification for this release.

**Independent artifact checks.**

| Check | Version 7 result |
|---|---|
| Section/subsection headings | All 34 present in source order |
| Paragraph headings | All 41 present |
| Table captions | All 26 match after resolving macros and references |
| Table rows | All 341 present; every table has the expected row count |
| Table content | No unexpected cell difference; the citation command in Table 2 correctly becomes reference [11] |
| Internal labels | All 56 present; no duplicate IDs or dead internal links |
| Long prose spans | All 238 checked spans present |
| Figures in HTML | Three embedded images retained |
| Submission abstract | Unchanged; 1,918 characters, with its numerical sequence matching the HTML |
| PDFs | Both remain 41 pages; no detected off-page text glyphs or unresolved-reference markers |

The raw HTML diff is especially reassuring here: it contains the header repair and the review-list/history edits, with no unrelated changes elsewhere in the document. The missing-section and wrong-table-content defects from earlier releases have not returned.

I independently extracted and compared both PDFs against their preserved version-6 counterparts. Each comparison produces exactly four changed text spans: `five` becomes `six` in the response inventory, the sixth response filename is added, the version-6 sentence loses `this paper`, and the version-7 history paragraph is added. There is no change to experimental results, equations, methods, conclusions, or limitations. The narrow description of the PDF changes is therefore “review inventory and revision history”; the availability list also changed, even though Appendix F casually describes the update as history-only.

**The scientific evidence is unchanged.** All 1,035 previously audited experiment/probe records and all 12 saved draw archives retain their prior hashes. The draw archives total 81,905,772 bytes. The audited simulator files, all 39 table sources in the prior snapshot, and all five numerical-macro files are unchanged. All seven figure PDFs in the source archive retain the same decoded page-content streams as version 6.

Consequently, the earlier independent statistical analysis still applies. Version 7 neither requires a new training run to validate this formatting fix nor provides new support for broader claims. The paper remains a simulation study with ideal reads, a bounded surrogate-fidelity analysis, task-specific comparisons against FP-SGD and Adam, and a conditional energy projection. The matched P2200 result still concerns agreement between update implementations for one tested cell; it does not establish general equivalence or hardware performance. The energy estimate remains conditional accounting, not measured end-to-end training efficiency.

**Rendering and package integrity.** I rendered all 41 main-PDF pages and inspected the complete contact-sheet set, then inspected the changed history page individually. The added history text moves part of the following list onto page 40 without losing or clipping it. No new PDF layout problem was apparent.

Both installed PDFs, the HTML, and the source archive match the final saved build output. The three saved compilation logs report 41 pages with no undefined references, multiply-defined references, or overfull boxes. All 75 regular archive members match the current source by bytes or, for regenerated figure PDFs, by decoded page content. These checks verify the supplied build evidence and archive contents; no fresh compilation was performed.

I also inspected all six saved browser screenshots. The desktop title/abstract, corrected Table 9, and final references are readable. The 700-pixel Table 9 capture retains all columns. The 420- and 480-pixel captures visibly cut off the right edge, and the supplied rendering method does not establish whether this is a capture limitation or actual narrow-viewport behavior. The table and end captures were made from documents with preceding content removed, so they provide local rendering evidence rather than a complete live-page navigation check. Mobile responsiveness should remain unclaimed. I did not retry or bypass the browser policy that blocked direct local-file browsing in the previous review.

The review remained read-only in the project. The detailed checks are saved in [the independent audit](paper-review-v7/independent-audit.json), [the caption/prose/figure audit](paper-review-v7/content-audit.json), and [the independent PDF comparison](paper-review-v7/pdf-text-comparison.json).
