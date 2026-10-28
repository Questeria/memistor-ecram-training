**Independent review of the revised memistor/ECRAM paper — version 2**

Reviewed 26 October 2026. Source: [the 33-page revised paper](<paper/build/main.pdf>), with its arXiv variant, HTML, submission abstract, revised simulator, analysis scripts and saved records. Latest paper commit inspected: `cd5977206`. PDF SHA-256: `d4f9045d7a11150014905d89f27a2bbc93b6d0e7108e211866af52d2d555eb45`.

**Assessment: substantial scientific improvement; a focused further revision is needed before submission.** The repaired main results are supported by the saved records. This is now a considerably more credible comparison under a specified simulator. The strongest previous implementation defects have been addressed, and the Adam comparison substantially improves the interpretation. The remaining problems include an unvalidated update approximation, a width conclusion that is sensitive to the treatment of paired runs, an incorrect control in the fixed-symmetry analysis, and several concrete inconsistencies in the submission artifacts.

My assessment is about the current version. I do not carry forward the old shared-RNG and ideal-reset findings as though they were still the main implementation.

**What I verified**

I read all 33 PDF pages, rendered and inspected every page, inspected the revised code and response to review, and independently recalculated results from the saved run JSON files. I also replayed the local device model on CPU against the saved AIHWKIT response schedules. I did not edit the paper or project, rerun training, launch GPU work, rebuild the manuscript, or publish anything.

- The preserved `build/v1/main.pdf` has the same SHA-256 as the 31-page version reviewed previously. The new PDF is a different, identifiable artifact.
- I examined 435 E3 records: 390 valid main/reference runs plus 45 retained runs from the incorrectly defined digital-TT control. The latter are excluded from the manuscript tables. All 147 reported comparisons against FP-SGD or Adam reproduce to within `1e-10` under the paper's stated t-quantile convention. I also checked the 18 comparisons for the quarantined digital-TT arms separately.
- All 15 task/seed groups in E3 have one logical-initialization hash and one data-order hash across arms. All 30 task/width/seed groups in E4 also match. Every one of the 360 sensitivity records matches its corresponding E3 FP control on both hashes. These hashes concern the requested logical initialization; device programming error remains an intentional difference.
- The 150 E4 records reproduce the 24 width-specific gap estimates and eight reported Welch verdicts. I additionally calculated paired endpoint contrasts, described below.
- The 360 E5 records reproduce 120 distinct sensitivity cells and all 144 displayed point occurrences, including repeated base anchors. Arithmetic agreement does not validate the choice of those anchors.
- All 60 device/task/algorithm energy rows reproduce in both read-efficiency scenarios. This verifies the stated model's arithmetic, not the completeness of its energy boundary.
- The local model passes all four replayed AIHWKIT response comparisons: Li and MO, each with and without cycle noise. Maximum normalized mean discrepancies were 0.398–0.642 of the allowed tolerance; median spread ratios were 0.939–1.017. I reused the stored AIHWKIT 1.1.0 / torch 2.10.0+cpu reference output; I did not independently rerun AIHWKIT itself. The revised fields also agree with the [official preset documentation](https://aihwkit.readthedocs.io/en/latest/api/aihwkit.simulator.presets.devices.html).

Inspectable audit outputs: [record calculations](<paper-review-v2/record-audit.json>), [record manifest](<paper-review-v2/raw-record-manifest.json>), [model checks](<paper-review-v2/model-details.json>), [artifact checks](<paper-review-v2/artifact-checks.json>), and [telemetry calculations](<paper-review-v2/telemetry-audit.json>). The calculation scripts are saved beside them.

**What the revised results actually establish**

The central result is internally consistent: four pairings—Li-ECRAM and protonic-inspired, each with c-TTv2 or AGAD—pass the preset non-inferiority margins against FP-SGD on all three tasks. None passes all three against Adam. These are conditional simulator results at the selected settings, with ideal reads and the specified pulse approximation.

| Comparator | MNIST passing cells | CIFAR passing cells | LM passing cells | Pairings passing all three |
|---|---:|---:|---:|---:|
| FP-SGD | 14/20 | 6/20 | 4/20 | 4 |
| Adam | 14/20 | 4/20 | 0/20 | 0 |

The denominators include the five catalog scenarios and four algorithms, excluding the additional ideal-device reference. The actual mean digital baselines are MNIST 97.774% / 97.748%, CIFAR 59.690% / 60.758%, and LM 2.96542 / 2.36564 bits per byte, for FP-SGD / Adam respectively. These absolute values should appear alongside the gap tables.

The best analog LM cell, protonic-inspired c-TTv2, averages 2.91832 bits per byte. Its reported paired relative gap to Adam is 23.36%. For additional intuition, converting the mean losses to perplexity gives a ratio of about 1.467; that is a descriptive conversion of means, not a separately estimated paired perplexity effect.

This is useful evidence that the chosen chopped algorithms compensate for some modeled update nonidealities relative to exact-update SGD. It is not evidence of competitiveness with the strongest digital optimizer in the study, nor of a jointly demonstrated accuracy-and-energy operating point. The revision now states much of this clearly.

**1. High priority: pulse fidelity remains the principal scientific uncertainty**

Location: PDF pp. 5, 11 and 17; [pulse-count generation](<paper/sim/memsim_rev.py:257>), [batched device dynamics](<paper/sim/memsim_rev.py:189>).

The revision correctly withdraws “conservative noise,” acknowledges noncommuting pulses, and measures clipping. Those are substantive improvements. It does not yet establish that the aggregate Poisson/continuous-dynamics surrogate preserves the ranking or pass labels produced by physically ordered pulse streams.

This matters in the operating regime actually used. The reported 57.5% CIFAR and 27.8% LM figures are averages over device/algorithm/seed runs for a selected layer. The worst individual layer loses 96.39% of its requested unsigned pulse mass: MO-ECRAM AGAD, CIFAR output layer, seed 3. That is not a small perturbation around the unclipped update.

A simple boundary calculation illustrates the remaining distinction. With one sample, 31 slots, and both line probabilities equal to one, a physical Bernoulli-coincidence train delivers exactly 31 pulses, with variance zero. The simulator instead draws Poisson(31), with variance 31 and a 45.24% probability of exceeding 31 pulses. This is an analytic limiting example, not a claim that 45.24% of all training updates exceed the budget. The saved telemetry does not contain enough information to estimate that training-wide frequency.

Consequently, the sentence on p. 11 calling this “the hardware's pulse budget, not a simulator error” is too categorical. Clipping is an explicitly chosen update-management policy; stochastic counts, ordering, device-state evolution and cross-cell correlations still belong to an approximate model. [AIHWKIT's update documentation](https://aihwkit.readthedocs.io/en/latest/api/aihwkit.simulator.parameters.training.html) also treats pulse length and update management as configurable choices, rather than universal device properties.

The new AIHWKIT comparison checks single-pulse response schedules. It does not validate aggregating a training batch's mixed-sign pulses into one ODE step, evaluating accumulated noise at the initial state, or drawing independent coincidence counts for each cell.

**Required action:** compare the current surrogate with explicit row/column Bernoulli pulse streams and sequential device updates on representative training-derived inputs and states, including clipped and unclipped layers. Report update bias, variance, cross-cell covariance, state error and at least a bounded learning/ranking comparison. A small, well-chosen fidelity study is more useful here than another broad seed sweep. Until then, describe the main result as a comparison within this aggregate-update simulator and retain the fidelity gap prominently. Do not claim that the mismatch has already been shown to overturn the results; it has not.

**2. High priority: width inference ignores a pairing present in the experiment**

Location: PDF pp. 12–14, abstract and conclusion; [Welch contrast and verdict](<paper/revision/analyze_rev.py:126>).

Replacing FLAT with an actual equivalence rule is a major improvement. The implementation follows the registered Welch rule, so this is not an analysis-script arithmetic error. The problem is that Welch treats the endpoint samples as independent although they reuse the same seed and exactly the same data-order hash across widths. Independence is therefore not established. The design supports a paired endpoint contrast, or at minimum a prespecified sensitivity analysis retaining the seed blocks.

For protonic-inspired c-TTv2 on CIFAR, the per-seed differences in gap between widths 64 and 16 are:

`[2.82, 3.82, -0.05, 0.11, 2.11]` percentage points.

| Analysis | Mean change | 90% interval | Verdict under the paper's decision order |
|---|---:|---|---|
| Reported independent Welch | +1.762 pp | [−0.021, +3.545] | INCONCLUSIVE |
| Paired endpoint contrast | +1.762 pp | [+0.146, +3.378] | GROWS |

The paired one-sided p-value against zero is approximately 0.0404, without multiplicity correction. This is a sensitivity result, not a new confirmatory discovery. It does not show growth exceeding the 2 pp practical margin; its interval includes that margin. Both endpoint device cells still pass against their respective FP controls. A gap moving from more negative to less negative can grow while both cells remain acceptable.

The Li-ECRAM c-TTv2 CIFAR equivalence result survives pairing: its paired 90% interval is about [−1.790, +1.106] pp. All four LM endpoint contrasts still shrink. Thus the overall picture remains mixed, but the broad “no growth detected” headline is not robust to the dependence structure.

**Required action:** preserve the registered Welch results as registered results, add and explain the paired analysis, and state the conclusion as unresolved width dependence with one robust CIFAR endpoint-equivalence result. Do not silently replace the planned method. Also distinguish endpoint equivalence from equivalence throughout the width range; the middle width is not covered by an endpoint TOST. The main text correctly notes that the LM's shrinking gap partly reflects a weaker FP-SGD baseline at width 256.

**3. High priority: the hyperparameter appendix describes version 1 settings**

Location: PDF p. 25, Table 9; [appendix source](<paper/tex/app_selection.tex:18>), [old table still included](<paper/tex/tables/e2.tex:4>), [revised selections](<paper/records/revision/CHOICES-REVISION.json>).

The appendix is cited by the revised Methods as the specification of the selected settings, but it still includes the old `tables/e2.tex`.

| Algorithm | Printed in Table 9 | Revised selection and actual E3 records |
|---|---|---|
| TTv2 | period 16; validation 97.86% | period 64; pulse reset; validation 97.60% |
| c-TTv2 | chopper probability 0.2; validation 97.82% | probability 0.05; pulse reset; validation 97.60% |
| AGAD | chopper probability 0.05; validation 97.18% | probability 0.2; no reset; validation 97.30% |

The common transfer gain remains 0.1 and the selected A learning-rate multiplier remains 10. I checked the revised E3 configurations against `CHOICES-REVISION.json`; those records agree. The defect is the paper's experimental description, not a mismatch between selected and executed configurations.

**Required action:** generate a revised selection table directly from the revised choices, explicitly name reset modes and budgets, and move the old selection table into the superseded-results material if retained. Include the selected Adam rates and the width-specific rates; the new width table has lost the old table's learning-rate annotations. A reader should be able to reproduce the revised protocol without discovering that its cited appendix is stale.

**4. Medium priority: the fixed-symmetry sweep uses a base point that was not recentered**

Location: PDF pp. 13–15; [grid definition](<paper/sim/sweep_rev.py:215>), [base substitution](<paper/revision/analyze_rev.py:207>).

The revised recentering intervention is informative: at asymmetry 0.4, CIFAR TTv2's gap changes from 42.92 pp with the symmetry point at the bound to 6.20 pp with recentering. The c-TTv2 contrast is similarly large. This strongly supports a range-loss confound in the original asymmetry sweep, within this model.

However, the fixed-symmetry curve's anchor at asymmetry 0.05 is copied from the ordinary `base` run. Every such record has `recenter_sp=false`. Only 0.1, 0.2 and 0.4 have fixed-symmetry runs. The analysis nevertheless reports the base as having symmetry point zero and a full signed range, and the paper calls 0.05 an established fixed-symmetry threshold.

In a nominal noise-free calculation, the original base has symmetry point 0.125 and normalized weight range [−1.125, +0.875]. The recentered base has symmetry point 0 and range [−1, +1]. They are different interventions. Reusing the first as the second does not establish a passing recentered base.

There is also a plan discrepancy: [the plan](<paper/PLAN-REVISION.md:83>) promises the same asymmetries for both sweeps, which includes zero. The code omits the fixed-symmetry zero point. The [deviation note](<paper/DEVIATIONS-PAPER.md:65>) describes 186 versus 180 runs as a pure arithmetic miscount, but the written 31-point plan and executed 30-point grid differ by that omitted point. This should be logged explicitly. Zero global asymmetry does not automatically make the two population models identical when per-device asymmetry spread remains nonzero.

**Required action:** evaluate a genuinely recentered base, include or explicitly justify omission of the planned zero point, and regenerate the signed-range metadata and threshold. Alternatively remove the unsupported base-threshold claim and describe only the recentered points actually simulated. The moving-symmetry results and the reference-error threshold are not invalidated by this finding.

**5. High priority for submission: the form abstract and packaging instructions are stale**

Location: [submission abstract](<paper/build/arxiv-abstract.txt:1>), [publishing instructions](<paper/PUBLISHING.md:57>), [preamble dependency](<paper/tex/preamble.tex:13>).

The revised PDF abstract is much better, but `build/arxiv-abstract.txt` still contains the version 1 claims: near-digital accuracy, unresolved cells treated as within resolution, no width growth, a few hundred levels sufficing, approximately 32× energy with a 15–234× range, and a release/bench description that no longer matches the revised scope. `PUBLISHING.md` specifically directs the submitter to paste that file into the submission form. This would publish withdrawn claims as the paper's searchable abstract.

The source-file checklist also names `numbers.tex` but omits `numbers_rev.tex`, which the current preamble requires. Uploading the full `tex/` directory would include it; assembling an archive from the explicit checklist would omit a required dependency.

**Required action:** regenerate a suitably concise form abstract from the revised content, update the source manifest, and validate an assembled submission archive rather than the working source tree alone. The main and arXiv PDFs and the HTML should share one revision manifest. This is a publication blocker independent of the scientific issues.

**6. High priority for submission: PDF overflow and literal number placeholders remain**

Location: PDF pp. 5, 14 and 31, both author variants; [Methods source](<paper/tex/sec_methods.tex:52>), [width-table generator](<paper/revision/analyze_rev.py:593>), [diagnostic-table generator](<paper/revision/analyze_rev.py:513>).

- Page 5 prints `RVorderUpDn`, `RVorderDnUp` and `RVorderBatch` as literal text. Their TeX backslashes are missing. The same strings occur in the HTML. The intended values are approximately 0.314, 0.334 and 0.327.
- Table 6 on p. 14 extends to x ≈ 673.91 points on a 612-point-wide page. Much of the verdict column is outside the page, including the labels needed to interpret the width analysis.
- Table 18 on p. 31 extends to x ≈ 634.40 points, cutting off part of the published-style comparison column.

These are visible in the rendered pages, not text-extraction artifacts: [page 5](<paper-review-v2/page-05.png>), [page 14](<paper-review-v2/page-14.png>), [page 31](<paper-review-v2/page-31.png>). The automated macro checker only scans backslash-prefixed macro uses, so it cannot catch bare placeholder names. “No undefined references” therefore did not establish a clean artifact.

**Required action:** repair the placeholders, split or reformat the overwide tables, and check final rendered pages and text bounding boxes. Keep new tables readable rather than shrinking them further. Table 7 is already very dense. Move the revised result figure nearer its discussion; it currently appears on p. 32 after the historical appendices.

**7. Medium priority: reset summaries need their actual aggregation units**

Location: PDF pp. 11 and 17; [summary calculation](<paper/revision/analyze_rev.py:344>).

The stated residual of 67.00 nominal steps is the unweighted mean of per-layer residual means across catalog device runs. The 3.1% pulse share is the unweighted mean of per-run reset-pulse fractions. Both are legitimate macro-averages, but the paper's wording reads as though they are pooled device-event and pulse statistics.

Reaggregating the same E3 catalog records gives:

| Quantity | Macro-average used in paper | Pooled estimate from the records |
|---|---:|---:|
| Residual in nominal steps | 66.996 | about 26.966, weighted by reset device-events |
| Reset share of pulses | 3.074% | 0.492%, total reset pulses / total pulses |

The event-weighted residual was reconstructed from executed row counts, transfer-column counts and layer dimensions. It is not a newly logged direct event-level measurement. The maximum recorded layer-mean residual is 2,081.42 nominal steps, in the MO-ECRAM CIFAR output layer with c-TTv2, seed 4. The spread is much more informative than a single average.

Similarly, 57.5% lost update is a mean across configurations at a layer, while 96.39% is the worst individual recorded layer mean. The logged “lost fraction” measures discarded unsigned expected pulse mass, not the norm of the lost signed gradient after cancellation.

**Required action:** label the averaging unit explicitly, report per-device and per-layer distributions, and distinguish macro-average, pooled fraction and maximum. Do not imply that the new pooled numbers are a universally better scientific estimand; explain which quantity each summary answers. This correction does not invalidate the main accuracy tables.

**8. Medium priority: keep the improved energy analysis at its stated evidentiary level**

Location: PDF pp. 14–16; [energy script](<paper/energy/energy_rev.py>), [Table 8 generator](<paper/revision/analyze_rev.py:545>).

The new energy section is much better. It begins with the incompatible read assumptions, states its matrix-operation boundary, gives two source-efficiency scenarios, and suppresses ratios where the accuracy criterion is not met. Its calculated roughly 18× / 32× ratios reproduce. Those are useful accounting scenarios.

Two labels should still change:

1. “Equal quality” is stronger than the gate establishes. PASS means a confidence bound lies within a practical non-inferiority margin under ideal reads, not that losses are equal. No joint finite-read accuracy/energy point or energy-to-target training trajectory has been demonstrated. Use “conditional energy ratios for cells passing the stated margin under ideal reads.” For UNRESOLVED cells, say “criterion not established,” rather than “quality not reached”; FAIL and UNRESOLVED are different evidence states.
2. The 6.94 TOPS/W source is a projected full-system efficiency including estimated digital processing. It should not be described as an end-to-end measured system efficiency. The primary paper distinguishes chip measurements from the system projection and excludes some external components. See [Ambrogio et al., Nature 2023](https://www.nature.com/articles/s41586-023-06337-5).

The read terms supply at least about 97% of the stated analog total, so the scenarios mostly reflect the borrowed efficiencies. Gating on a PASS cell does not resolve finite precision, tiling/utilization, reference maintenance, digital TT state, update scheduling or full-system costs. These are now mostly acknowledged limitations; they should remain attached to the headline ratio. I do not recommend another broad energy sensitivity band before the accuracy/precision operating point is made coherent.

**Disposition of the previous thirteen findings**

| Earlier finding | Current disposition |
|---|---|
| 1. Shared RNG breaks matching | Resolved for revised logical initialization and data order; verified in records. |
| 2. Reset jumps while charging unused pulses | Repaired in the revised path; physical-model pulses and extra reads are counted. Incomplete reset and surrogate fidelity remain limitations. |
| 3. Changed AIHWKIT presets | Substantially resolved at the parameter/response-curve level; comparison replay passes. |
| 4. Pulse surrogate fidelity | Acknowledged and partly quantified; still open scientifically. |
| 5. Confounded specification sheet | Major improvement: absolute criteria and explicit exploratory scope. Fixed-symmetry anchor still needs repair. |
| 6. FLAT width classifier | Replaced by a meaningful test, but independence/pairing sensitivity remains. |
| 7. Weak optimizer comparator | Adam now makes the limitation explicit. Fair tuning and a true algorithm-only control are not established, but the restricted claim is clear. |
| 8. Energy overclaim | Largely corrected to a conditional scenario; equal-quality and source-projection wording still need correction. |
| 9. Validation and historical overclaim | Substantially narrowed. Selected benchmark agreement remains limited validation, as the revised text acknowledges. |
| 10. Plan deviations | Earlier deviations acknowledged; fixed-symmetry grid omission needs accurate logging. |
| 11. Experimental roadmap | Improved: prediction intervals, physical reset, measured current and unbuilt status. No hardware validation is implied. |
| 12. Related work and release | Wu et al. is now discussed and the lack of public deposit is explicit. Submission materials are not yet synchronized. |
| 13. Presentation | Bibliography improved, but stale settings, overflow and placeholders prevent closure. |

The added [Wu et al. study](https://arxiv.org/abs/2609.36584v1) is characterized appropriately: it scales a hardware-calibrated simulation to approximately 123M parameters while keeping weight-gradient computation digital. The revised paper's contribution is narrower and can stand on that narrower scope. It should emphasize the controlled comparison and limitations rather than suggest that it establishes electrochemical training feasibility for the first time.

**Additional corrections and interpretive points**

- Page 12 says the initial weight scale “grows with width.” The implementation sets alpha proportional to `1/sqrt(fan_in)` for the affected layers, so it decreases as their fan-in grows; layers with fixed fan-in are exceptions. Correct the direction and describe the mapping policy precisely.
- Abstract and conclusion say “without establishing equivalence,” while the body establishes one endpoint-equivalence result. Say “equivalence was established for one CIFAR pairing only.” Combine this with the paired-analysis qualification above.
- Page 9 first says AGAD is unaffected and then correctly says the evidence does not establish that. Keep only the qualified description of the two-seed ordering result.
- Table 1 still presents the original Li/MO field-copy catalog; the preceding paragraph admits this. Give the revised catalog the main-table position, and label the original mapping in the historical appendix. The curve agreement does not make the old table the current configuration.
- Several superseded tables retain standalone captions such as “Main result” or “System energy.” Prefix each with “Version 1—superseded”; float placement currently carries them into the revision appendix. The prose explaining supersession should not be necessary to identify an isolated table.
- The contribution statement still says “released records” despite the availability section saying nothing has been deposited. Use “saved records” until release.
- The statement that remaining questions are experimental is incomplete: surrogate fidelity, dependence-aware statistics and control construction remain computational/methodological work.
- The ideal 1000-level reference is useful but retains stochastic counts, bounds, transfer thresholds and the selected update-management policy. It is not a substitute for an exact-update algorithm-only TT reference. A successful symmetric-device reference on MNIST also does not establish that all other observed failures are unavoidable device limitations.
- The sensitivity table is deliberately stringent: a high-end unresolved point can prevent a monotone threshold even when intermediate points pass. For example, c-TTv2 CIFAR passes at 500, 1000 and 2000 levels but not with sufficient precision at 5000. Explain that “threshold not established” does not mean no grid value passed, and does not establish that more levels harm hardware training in general.

**Recommended next revision, in order**

1. Synchronize the PDF, HTML, submission abstract, revised settings/catalog tables and submission file manifest; fix the two overwide tables and three placeholders. This needs no new training.
2. Add paired width contrasts alongside the registered Welch analysis, revise the headline accordingly, and clarify reset aggregation and energy gating. This needs no new training.
3. Correct the fixed-symmetry control and log the grid discrepancy. A new recentered base requires 12 small-task runs at the existing two algorithms × two tasks × three seeds; adding the omitted zero point would add another 12. These are recommendations, not runs performed during this review.
4. Perform a bounded pulse-fidelity comparison in the actual operating regime before expanding the empirical scope. If it changes ranking or margins materially, rerun the affected comparisons. If it does not, publish the evidence and its bounds.
5. Assemble and test a self-contained reproducibility archive from the intended release manifest. Keep the public-deposit claim in future tense until the deposit exists.

The work worth preserving is the repaired main comparison and its transparent negative result against Adam. With the above corrections, the paper can present a defensible, limited simulation contribution. The current build should not yet be submitted unchanged.
