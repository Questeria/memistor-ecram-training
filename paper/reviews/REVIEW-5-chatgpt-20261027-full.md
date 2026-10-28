**Memistor Paper Version 5 Review**

Reviewed 27 October 2026. Target: the current 41-page [paper](paper/build/main.pdf), version 5. PDF SHA-256: `1d4cfb3c6d8d8fa085e802f0e0596525e8923d98d8bb2afe6786f08d59ad1f3f`.

**Verdict.** The substantive version-4 findings are resolved in the PDF. The new training experiment is actually matched, its arithmetic reproduces, the incorrect cross-machine comparison is explicitly withdrawn, and the release inventory now includes the pulse draws. The diagnostic tables are also substantially easier to read. I found no new major scientific error in the revised PDF.

There is one remaining release problem: **the HTML export is incomplete and contains a table with the wrong body under its caption.** It should not be distributed as an equivalent edition of the paper until repaired. This defect also exists in the preserved version-4 HTML; it was missed by the earlier checks of abstract digits and selected body numbers. It does not invalidate the PDF or the experiment records.

**The matched rerun resolves the methodological finding**

All 15 new records are present: five seeds, each with FP-SGD, aggregate-surrogate and sequential-update arms. Within each seed, the three runs agree on the logical-initialization hash, data-order hash, GPU name, PyTorch version, task, width, learning rate, training budget, scale, sample count and RNG mode. The two analog arms also have identical device specifications and update settings. The sequential arm uses every analog layer. Different seeds have different initialization and data-order hashes.

The independent calculation gives the following results for MNIST MO-ECRAM SGD on the Quadro P2200. Positive gap means lower analog accuracy than FP-SGD; all numbers are percentage points.

| Quantity | Mean | 95% interval |
|---|---:|---:|
| Aggregate surrogate's gap to FP-SGD | 8.710 | [7.015, 10.405] |
| Sequential update's gap to FP-SGD | 8.734 | [6.820, 10.648] |
| Sequential gap minus surrogate gap | 0.024 | [−0.467, 0.515] |

At the paper's two-decimal precision these reproduce **8.71 [7.02, 10.40]**, **8.73 [6.82, 10.65]**, and **0.02 [−0.47, 0.52]**. The paper uses a three-decimal Student-t critical value; using full precision changes the bounds by less than 0.00031 points and changes none of these printed results.

The paired per-seed changes are −0.19, +0.56, −0.47, −0.02 and +0.24 points. Both methods clearly fail the 2-point accuracy-gap criterion. The interval for the mean update-method change lies within ±1 point for this five-seed set. That supports the stated conclusion that switching update methods does not rescue this particular configuration under the tested conditions.

The earlier A4000 result remains visible: three matched seeds, mean change −1.42 points with a wide interval of approximately [−4.84, 2.00]. The new experiment does not erase that result. Version 5 correctly presents the two sets separately and withdraws version 4's mixed, unmatched five-seed calculation. The largest descriptive difference between corresponding A4000/P2200 gaps, 9.97 points, also reproduces.

The new [matching guard](paper/revision4/analyze_rev4.py:63) checks all three roles and rejects missing or unequal initialization hashes, data-order hashes and GPU names before calculating a matched result. Its handling of the previous join is explicit. The saved self-check record reports that the old join and planted mismatches were refused; this review inspected that implementation rather than launching the project tests.

The revised explanation for changed random realizations has a concrete source basis. The installed PyTorch header and the version-pinned upstream source use device properties to determine random-kernel grid size and Philox counter progression. This can change which draws reach which tensor elements across GPU configurations. The checked records establish that the realized initialization and, for MNIST, example order actually differed. [PyTorch 2.7.1 CUDA distribution implementation](https://github.com/pytorch/pytorch/blob/v2.7.1/aten/src/ATen/native/cuda/DistributionTemplates.h#L48-L88).

Keep that explanation scoped to the observed configurations. Different GPU model names do not universally imply different random arrays for every tensor shape, and these records do not separately quantify the contribution of floating-point execution differences. The key scientific repair is the verified matching within each comparison.

**The draw-release omission and presentation findings are closed**

[PUBLISHING.md](paper/PUBLISHING.md:43) now lists all 12 `.npz` files, sizes, SHA-256 hashes, the intended portable deposit path, and a reconstruction command. Every listed hash and size agrees with the actual file. The total is **81,905,772 bytes**. The PDF availability section includes these files and the reconstruction script.

The saved arrays and all 1,020 previously audited run/probe records are unchanged. The previously reviewed simulator files are unchanged too. The new surrogate and sequential table rows agree with the prior independent calculations after fresh verification of the source-array hashes; the dependence table preserves its previously checked numeric rows. The author's saved reconstruction record reports byte-identical regeneration of all three tables. I source-reviewed that reconstruction command; I did not rerun it or a project test suite.

The established diagnostic results therefore remain:

| Update comparison | Meets point criteria | Also meets the reported bootstrap criteria |
|---|---:|---:|
| Aggregate surrogate against literal pulses | 10/12 | 1/12 |
| Sequential approximation against literal pulses | 12/12 | 6/12 |

The abstract now calls the first count a point-estimate result and includes the bootstrap count. The captions explicitly state that the additional bootstrap check covers excess and gain bounds, while the variance ratio remains a point estimate; it is not a joint 95% guarantee for all criteria.

Tables 6 and 7 now print at approximately **8.97 points**, compared with 6.82 points for the old combined table. The dependence table prints at approximately **8.36 points**, also an improvement. The large blank area formerly on page 20 is gone. The two smaller historical appendix tables are disclosed in the recorded layout deviation rather than silently exempted.

**Remaining finding — medium priority: the HTML is not a complete or faithful edition**

The current [HTML export](paper/build/main.html), SHA-256 `e8718e33f935a298d40b24697a79d2084f84cb578020ffc9973411ac03839fd9`, omits substantial material present in the PDF:

- Section 5, the conditional energy analysis and its detailed assumptions.
- Section 6, discussion and limitations.
- Sections 7–9, the experimental roadmap, conclusion, and code/data availability.
- The author-contribution/AI-use statement and acknowledgments.
- The bench protocol and hyperparameter-selection appendix text. The simulator-checks appendix is also structurally misplaced.

The error is visible directly in the HTML source. Under `id="tab:rev_spec"`, the caption describes the revised device-sensitivity sheet, but the table headers are **Check / Result / Planted faults caught**, followed by rows such as `c_asym_drift`, `c_c2c_noise`, and `c_fp_equivalence`. Those are the simulator-check rows from another table. They are not the sensitivity results. The document then continues into “Earlier development results.” The explanatory text of Section 4.5 is missing in the current HTML as well.

Nine distinct unresolved reference tokens remain, including `[sec:energy]`, `[sec:limits]`, `[sec:availability]`, `[app:bench]` and `[tab:rev_selection]`. A reader following the HTML encounters both missing qualifications and mislabeled evidence.

This is a conversion defect rather than missing source material. The saved flattened LaTeX input for the exact matching build contains the energy section, discussion, availability statement and appendix sections. The generated HTML does not. The recorded Pandoc log is empty, and the build was marked successful despite the loss. The same broad omission is present in the preserved version-4 export, so this should not be attributed to the new matched experiment.

The checker explains why it escaped detection: [html_check.py](paper/pod/html_check.py:17) checks for raw macros and citation syntax, but does not reject the emitted `[sec:...]` reference form or require the expected sections. Version 5's additional checks validate abstract digits and table sizes; those checks cannot establish that the body survived conversion.

**Required repair for the HTML release:** trace the conversion around the sensitivity-table block, restore the omitted sections, and verify that each table's caption, headers and rows belong together. Add checks against an expected section/appendix inventory, unresolved reference tokens, and representative content from every main section. Compare the resulting HTML with the PDF after rebuilding. The PDF can be reviewed and shared independently in the meantime; the current HTML should not be presented as its complete counterpart.

Evidence is preserved in [the HTML completeness audit](paper-review-v5/html-completeness-audit.json) and [the literal mismatched-table excerpt](paper-review-v5/html-sensitivity-table-excerpt.txt).

**Two small wording corrections**

Appendix F says the saved draws “joined the deposit,” while Section 9 correctly says nothing has been publicly deposited. “Were added to the deposit inventory” would express the current state accurately.

The claim that Tables 6–8 are rebuilt “from the arrays alone” is slightly too broad. The reconstruction script also uses the probe records, including the clipping figure. It recomputes the update-comparison statistics, but copies `lost_frac` metadata used in Table 6. “From the saved arrays and probe metadata” is precise and does not weaken the reproducibility contribution.

**Artifact checks and scientific scope**

Both PDF variants contain 41 pages. All main-PDF pages were rendered and inspected. Neither PDF has off-page text characters or unresolved `??` markers in the text-bound checks. The current arXiv source archive contains 75 regular files: its text sources match the corresponding current files, and regenerated figure PDFs have matching decoded page-content streams. The submission abstract is 1,918 characters. Its digits match the HTML abstract, demonstrating why that narrow check passes despite the body loss.

The paper remains a bounded simulation study. The corrected five-seed result concerns one MNIST SGD configuration and the approximate sequential stream. It does not validate convolutional or LM training against literal pulse dynamics, establish general update equivalence, or turn the conditional energy projection into a hardware measurement. Those limits are now clearly visible in the PDF and are essential to a faithful HTML edition.

The scientific revision can proceed without another experiment to answer the version-4 findings. Before releasing the full artifact set, repair the HTML and make the two small wording changes. Detailed independent calculations and source hashes are in [independent-audit.json](paper-review-v5/independent-audit.json). No project files were changed, and no training, GPU workload, project tests, or builds were launched during this review.
