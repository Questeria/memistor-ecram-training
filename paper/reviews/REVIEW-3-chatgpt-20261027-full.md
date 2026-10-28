# Independent review of the memistor/ECRAM paper, version 3

Reviewed 27 October 2026. Target: [the 37-page main PDF](paper/build/main.pdf), built 26 October at 23:21, and its supporting source and records. Latest paper commit inspected: `bec6f470c`. PDF SHA-256: `916ff34ffa18363a2a95c1b97a9274db07271862e5357db990d8c79b1d5a3bc7`.

**Verdict: substantially improved, but another focused methodological revision is needed before submission.** Six of the eight findings from the previous review are now resolved. The two remaining areas are the interpretation of width and the validation of the aggregate update. The new experiments are useful and their reported arithmetic reproduces, but the fidelity section makes stronger claims than its analysis supports. In particular, its pulse-reference sampling correction ignores pairing, and the assertion that training preserves the classification of cells is contradicted by a PASS-to-UNRESOLVED change in the saved records.

This does not overturn the five-seed main table as a result of the aggregate simulator. It does prevent that table from being treated as validated pulse-stream training. The paper's strongest defensible contribution remains a transparent, conditional comparison within a specified simulator, with a useful account of how corrections and controls affect the conclusions.

**What I checked.** I read the complete manuscript, inspected rendered images of all 37 pages and larger views of the equations, main figure and new tables, compared the two PDF variants, inspected the source archive, read the new simulation and analysis code, recalculated the new experiments independently, and checked primary sources for the pulse scheme, paired statistics and energy attribution. I did not edit the project, rebuild it, run its test suite, or launch training. Independent calculations and this report are outside the project.

All 945 E3/E4/E5 records from the previous review retain identical SHA-256 hashes. I inspected 36 new training-fidelity records, 24 new fixed-symmetry records, three probe-training records and three probe summaries. All 63 new training records match their appropriate FP controls' initialization and data-order hashes. The 36 fidelity runs also retain the corresponding E3 budgets, learning rates, device specifications and algorithm settings. My arithmetic reproduces all 12 A2 comparisons, the eight new fixed-symmetry cells, the eight paired width contrasts, and the A1 pass flags under the implemented formula. See the [independent audit](paper-review-v3/record-audit-v3.json) and [calculation script](paper-review-v3/check_v3.py).

## 1. High priority: the pulse-reference comparison uses the wrong sampling correction

**Location:** pp. 12-16, Section 4.3 and Table 6; [probe implementation](paper/sim/run_rev2.py:100), especially line 121; [fidelity analysis](paper/revision2/analyze_rev2.py:39).

The sequential (`seq`) and literal (`slot`) simulations deliberately share the same Bernoulli line firings. That is a good comparison design. However, the analysis subtracts a sampling floor calculated as if the two outputs were independent:

`floor² = sum(var(seq) + var(slot)) / R / ||mean(slot)||²`.

For paired draws, the numerator should instead use the variance of each draw's difference:

`sum(var(seq - slot)) = sum(var(seq) + var(slot) - 2 cov(seq, slot))`.

The pairing principle is to analyze the differences within pairs, including their variability. [NIST's treatment of paired observations](https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm) states this explicitly. Sharing the line firings makes independence inappropriate even though the write-noise samples differ. With positive covariance, the present expression subtracts too much sampling noise and can erase a real mean discrepancy.

This matters in the actual saved summaries. For the LM output layer at update 2250, the raw relative mean difference is **0.1280**, while the independent floor is **0.4392**. The reported excess is consequently zero. Every one of the 12 sequential comparisons has an excess of zero. That is not proof that its true mean discrepancy is zero or below 0.05.

I also constructed an exact illustrative counterexample, separate from the paper's data. Take 16 reference draws alternating between 0 and 2 and paired comparison draws equal to the reference plus 0.2. The mean bias is 20%, and every paired difference is exactly 0.2. The implemented independent floor is 0.3651 and reports zero excess; the paired floor is zero and retains the 20% discrepancy. The calculation is saved in the audit.

**What this establishes:** the estimator used to certify the sequential reference is inappropriate for its sampling design. **What it does not establish:** that any particular real probe fails after correction. The JSON files discard the per-cell means, variances and paired cross-moments, as well as the individual draws, so the corrected 12 decisions cannot be recovered from these summaries alone.

There is also an important modeling distinction to state in the paper. The sequential method is exact for the noise-free same-sign recurrence in its intended parameter regime. Its stochastic update is still an approximation: it adds `c2c * sqrt(n) * local_step(u_pre)` noise once per sample and clips after each sample. The literal method applies noise and clipping after each pulse. This is documented in [the implementation](paper/sim/pulse_seq_rev2.py:12), but the manuscript's description of a closed-form version of “the same stream” does not explain it. The new training experiments are comparisons against this intermediate approximation, rather than literal pulse-by-pulse training.

**Required correction:** preserve paired draws or sufficient paired moments; calculate the sampling floor from paired differences; quantify uncertainty in the mean-discrepancy and gain estimates; and report the noise approximation explicitly. Resample whole draws rather than treating correlated cells as independent observations. Keep “meets our registered diagnostic thresholds” distinct from a statistical demonstration of equivalence. If a corrected probe analysis is deferred, remove the unconditional “valid reference for training” claim and retain A1/A2 as bounded diagnostics.

The original [Gokmen-Vlasov pulse scheme](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2016.00333/full) does use Bernoulli row/column streams and coincidence updates. The new literal comparator therefore addresses the right structural issue. The problem is the strength of the validation inferred from its summaries.

## 2. High priority: training does not preserve all labels or the full ranking

**Location:** pp. 14-15, Section 4.3; Table 7 on p. 17; abstract; [fidelity prose](paper/tex/sec_fidelity.tex:38); [ranking filter](paper/revision2/analyze_rev2.py:91).

The paper says that the aggregate surrogate preserves the ranking and pass/fail reading of the tested Tiki-Taka cells. Applying the paper's own 95% paired-gap rule to exactly the same three seeds gives:

| CIFAR Li-ECRAM c-TTv2, seeds 0-2 | Mean gap to FP-SGD | 95% interval | Label against 2 pp |
|---|---:|---:|---|
| Aggregate surrogate | -1.1367 pp | [-3.8931, 1.6198] | PASS |
| Sequential FC-layer update | -0.6200 pp | [-6.4423, 5.2023] | UNRESOLVED |

The difference in mean gaps is only +0.5167 pp, but the uncertainty increases enough to lose PASS. This is not evidence that the sequential method FAILS. It is evidence that “the label is preserved” is false. This comparison uses three seeds on both sides, so the difference cannot be dismissed as simply comparing the five-seed main table with a smaller sample.

The registered materiality rule only checks the point estimate of the change against 1 pp. It is implemented correctly, but a small mean change does not establish equivalent performance or preservation of the confidence-interval decision. The CIFAR Li-ECRAM difference interval, [-3.26, 4.29] pp, also does not establish that the change is bounded within ±1 pp.

Likewise, the code counts ranking reversals only when the original separation exceeds 1 pp. It correctly finds **zero reversals meeting that condition**, but the text says no pair reverses at all. Two do:

| Pair | Surrogate gaps | Sequential gaps |
|---|---:|---:|
| CIFAR Li c-TTv2 / protonic c-TTv2 | -1.1367 / -0.8467 pp | -0.6200 / -1.4600 pp |
| MNIST MO AGAD / protonic AGAD | 0.7733 / 0.7900 pp | 0.8867 / 0.7700 pp |

Neither reversal meets the registered 1 pp separation rule, and neither demonstrates a statistically reliable ranking change. The correct statement is therefore **“no material ranking reversal under the registered rule,”** not preservation of the whole ranking.

The MO-SGD discussion also mixes a five-seed main-table FAIL with the three-seed diagnostic. On the latter, the surrogate gap is 14.10 pp with interval [0.04, 28.15], and the sequential gap is 12.68 pp with interval [1.27, 24.09]. Both diagnostic cells are UNRESOLVED under the paper's rule, despite their poor point estimates. Calling them a failing cell “under either update” needs qualification.

**Required correction:** add the surrogate and sequential P/F/U labels and their intervals to the A2 analysis; report the one label transition and the two sub-threshold rank reversals; replace the broad preservation claim in the abstract, results and limitations. Preserve the actual registered result: one material mean change, no material rank reversals, and no TT-family mean shift above 0.61 pp. Those useful observations do not require an equivalence claim.

## 3. Medium priority: “sub-margin growth” reverses the interpretation of the width interval

**Location:** pp. 1, 16, 22 and 24; Table 8; [width interpretation](paper/tex/sec_scale.tex:23).

The paired analysis itself is now included and numerically correct. The protonic c-TTv2 CIFAR endpoint contrast is:

**D = 1.762 pp; 90% paired interval [0.146, 3.378] pp.**

The text calls this growth below or at the margin “since the interval includes 2 pp.” Including 2 pp means that the magnitude is unresolved relative to 2 pp. Values above the margin remain compatible with the data. The lower bound above zero supplies the paper's directional growth finding; it supplies no upper bound below 2 pp.

There are therefore **two** CIFAR arms for which growth exceeding 2 pp is not excluded: protonic c-TTv2, and Li-ECRAM TTv2, whose paired interval is [-1.529, 5.349] pp. The current summary names only the latter. The broader statement that no arm shows statistically detected growth *beyond* 2 pp can remain if accompanied by this distinction.

Suggested replacement:

> One CIFAR pairing met endpoint equivalence. A paired analysis detected positive growth for protonic c-TTv2, but its magnitude relative to the 2 pp margin remains unresolved. Growth exceeding 2 pp cannot be excluded for that pairing or for Li-ECRAM TTv2.

No new runs are needed for this correction. Keep the separate caution that LM gaps shrink partly because FP-SGD worsens at the largest width; the revision handles that limitation well.

## 4. Medium priority: the correlation summary cannot establish weak shared-line dependence

**Location:** pp. 13-14; [correlation calculation](paper/sim/run_rev2.py:52).

The numerical bound of approximately 0.011 describes the saved statistic, but that statistic is not generally the mean pairwise Pearson correlation. `_offcorr` averages off-diagonal covariances and divides by one pooled residual variance. It does not normalize each pair by its two standard deviations. Heterogeneous variances can make it small even with highly correlated pairs.

It is also a signed average. Opposite update signs can cancel positive and negative dependence. For an exact illustrative shared-line model with firing probabilities 0.5, two same-sign cells sharing a line have correlation 1/3. With 128 cells and balanced signs, the signed mean off-diagonal correlation is only -1/(3 × 127), or **-0.002625**, although every pair's absolute correlation is 1/3. This lies well inside the paper's quoted 0.011 bound.

This does not show that the paper's actual cells have correlation 1/3. It shows that the reported statistic cannot justify the opening assertion that the introduced cross-cell correlation is small. Chopping and mixed gradient signs make cancellation especially relevant here.

**Correction:** rename the current quantity as a pooled, signed normalized covariance and limit the conclusion accordingly. To support a statement about weak dependence, add properly normalized, sign-aware or absolute/RMS correlation summaries and useful distributions over row/column pairs, with uncertainty. Correlation was descriptive rather than an acceptance criterion, so fixing this wording alone does not change the registered A1 pass count.

## 5. Low priority: update the revision history and reproducibility directions to version 3

**Location:** pp. 24 and 36; [availability inventory](paper/tex/body.tex:15), [revision history](paper/tex/app_revision.tex:3), [publishing directions](paper/PUBLISHING.md).

Appendix F still identifies version 2 as “this paper” and describes only the first review. The availability inventory omits `PLAN-REVISION-2.md`, `RESPONSE-TO-REVIEW-2.md`, the `*_rev2.py` simulator files and `revision2/analyze_rev2.py`, even though the new results depend on them.

The publishing guide names `revision2/make_arxiv_source.py`, which is absent. The archive is actually assembled by `pod/build_rev2.sh`. It also attributes abstract generation to `revision2/analyze_rev2.py`; the separate script is `revision2/make_abstract.py`. These are documentation corrections, not evidence that the delivered archive is broken.

The archive contains 64 regular files, including all three number-macro files; 65 tar entries include the directory entry. I found no missing `input`/`include` targets. Its active figure PDF content streams match the local figures even though the binary hashes differ. The archived bibliography is newer than the stale loose `tex/main-arxiv.bbl`, so the ready archive is preferable to manually copying that loose file. I did not independently recompile the archive.

## What is resolved from the preceding review

| Previous finding | Version 3 assessment |
|---|---|
| Aggregate pulse update had no operating-regime validation | Meaningfully addressed with A1/A2; not closed because of Findings 1, 2 and 4 above. |
| Width analysis ignored seed pairing | Paired computation added correctly; interpretation still needs Finding 3. |
| Appendix settings described the old runs | Resolved. Table 11 now gives the revised selections, resets and learning rates. |
| Fixed-symmetry axis borrowed the wrong base and omitted zero | Resolved by 24 actual recentred runs and corrected control selection. |
| Stale submission abstract and missing macro dependencies | Resolved for the delivered artifacts. Abstract is current, 1,867 characters; archive includes `numbers_rev.tex` and `numbers_rev2.tex`. New scientific wording issues still propagate into the abstract. |
| Unexpanded macros and overflowing tables | Resolved in the current PDFs. No off-page text characters in either 37-page PDF; the former placeholders render numerically. |
| Reset averages conflated different weighting conventions | Resolved. Macro versus pooled residuals and pulse shares are distinguished. |
| Energy attribution and equal-quality wording | Resolved. The measured chip result, projected system result, non-inferiority margin and ideal-read limitation are explicitly separated. |

For the fixed-symmetry experiment, the new CIFAR c-TTv2 base at asymmetry 0.05 has gap **-0.4067 pp**, interval **[-2.6728, 1.8594]**, PASS. The zero point is **-1.4267 pp**, interval **[-2.8552, 0.0018]**, PASS. Thus the narrow 0.05 threshold now follows from the actual intervention and the registered rule. The recentred-minus-unrecentred difference is +0.44 pp, interval [-2.66, 3.54]; that does not establish the two interventions are equivalent. Larger asymmetries and the LM still lack established thresholds, as the manuscript correctly says.

The reset reporting now distinguishes the approximately **67.00-step macro-average from the 26.97-step pooled residual**, and approximately **3.1% mean per-run reset share from 0.49% pooled share**. That is the needed distinction. The short limitations bullet could repeat which mean it uses, but the main explanation is clear.

The revised energy attribution also matches [Ambrogio et al.](https://www.nature.com/articles/s41586-023-06337-5): the 6.94 TOPS/W figure incorporates modeled digital processing in a projected system, while 12.4 TOPS/W is a measured chip figure. The paper now explains the excluded external costs and the lack of a joint finite-read accuracy/energy operating point. I would retain the 17.9-32.4× numbers only as the clearly labeled accounting scenario used here.

## Assessment of the paper's contribution and presentation

The core comparison remains informative. Four Li-ECRAM/protonic-inspired and chopped-algorithm pairings meet the chosen margins against FP-SGD across the three tasks. None meets them across all tasks against the tuned Adam comparator, and the best analog LM result remains 23.36% worse in bits per byte. These are useful, bounded findings about the chosen update model, budgets and tuning policy. The paper now makes the weakness of the FP-SGD LM comparator and the estimated protonic parameters much clearer.

The new fidelity work is the right direction: an explicit literal comparator, a cheaper sequential approximation, matched training comparisons, worst-clipped examples, and honest reporting of the registered material change. The remaining concern is inference from these experiments, not evidence that the experiments should be discarded. Fixing their statistics and wording would make this section substantially more credible.

The fixed-symmetry result is a particularly useful methodological contribution. It separates a dynamic asymmetry question from a loss of usable signed range and tests the missing control rather than treating a nominal parameter value as an equivalent intervention. The narrow scope and exploratory status of the sensitivity sheet should remain prominent.

The rendered document is now readable and consistent in its main tables. Table 9 and the historical appendix tables are dense; a machine-readable companion is more useful than shrinking them further. Figure 2 is legible at full-page size but its many rotated labels make cross-device comparison slow. A future presentation revision could separate the three task panels or add a compact overview of which cells pass. That is optional and does not block the scientific corrections.

The paper is 37 pages because it contains extensive superseded results and response history. Preserve that evidence, but consider moving most of it to a supplement while keeping a short revision summary in the main paper. The scientific narrative should lead with the current model, current main comparison, fidelity limits and controlled sensitivity result. This is an editorial recommendation, not a request to remove unfavorable results.

## Concrete revision order

1. Correct the A1 paired sampling calculation and save sufficient evidence to reproduce it. Until then, weaken the claim that `seq` is a validated reference and describe its noise approximation.
2. Generate A2 labels and intervals from both three-seed arms. Report the PASS-to-UNRESOLVED transition and distinguish all rank changes from registered material rank changes.
3. Replace “sub-margin growth” throughout the abstract, scale section, discussion, conclusion and submission abstract with the correct interval interpretation.
4. Correct the correlation metric's name and inference; add stronger dependence diagnostics only if retaining a claim of small correlations.
5. Update the version-3 history and release instructions, then regenerate and inspect the artifacts.

Items 2-5 can be addressed from current records and source. Item 1 needs paired probe statistics that are not retained in the JSON summaries, or a narrower validation claim. Neither the current evidence nor this review justifies advertising physical training equivalence, general scaling behavior or measured end-to-end energy savings.

Evidence retained beside this report: [snapshot](paper-review-v3/review-snapshot.json), [record manifest](paper-review-v3/new-record-manifest.json), [independent calculations](paper-review-v3/record-audit-v3.json), [PDF/archive checks](paper-review-v3/artifact-checks-v3.json), the full extracted text and rendered pages. All substantive numerical findings above were checked against the current files; earlier review records were used to verify continuity, not to assume the updated results.
