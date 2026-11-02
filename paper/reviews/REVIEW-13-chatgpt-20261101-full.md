# Review 13 (ChatGPT, of release v1.5 / version 15, commit b5f86bed2), pasted by the owner in chat on 2026-11-01

Verbatim copy of the text the owner pasted. The reviewer reran the fast reproduction (Python 3.12.14, PyTorch 2.7.1+cpu, NumPy 2.5.2,
Matplotlib 3.9.2), recomputed the statistics and checked the figure and energy changes. It did not repeat the training campaign or the five
slow simulator test groups. Links and the content-reference marker are as pasted.

---

## Verdict: v1.5 resolves the required findings from my previous review

**I would close the previous revision requests.** The fixes are implemented correctly, the fast reproduction procedure now passes in the environment that exposed the v1.4 failure, and I found **no new substantive numerical or scientific defect in the changes reviewed**.

My recommendation has moved from **“minor revision” to “ready to submit for scientific review as a clearly scoped simulation and methodology paper.”** There is one optional improvement to a test, explained below, but I would not hold the release for it.

I reviewed [release v1.5](https://github.com/Questeria/memistor-ecram-training/releases/tag/v1.5), verified that its tag points to commit `b5f86bed24dfef605646fb4f4ac1e5a29f933470`, and confirmed that the attached manuscript matches the release PDF exactly.

:chatgpt-content-reference{index="0"}

## 1. The previous findings are addressed

| Previous finding | What v1.5 does | My assessment |
|---|---|---|
| **The reproduction command failed because one CPU-generated diagnostic differed slightly across environments** | Introduces a numerical comparison policy for that specific file, preserves exact structural and decision checks, protects the manuscript’s printed values, and documents the reference environment | **Resolved in the tested environment.** The full fast procedure now passes. |
| **Figure 1 implied that AGAD uses a pulse reset and left TTv2’s chopper notation ambiguous** | The diagram, settings key, and caption explicitly distinguish the algorithms | **Resolved.** The figure agrees with the selected configurations and recorded runs. |
| **The architecture checker used a synthetic reset configuration for every algorithm** | The checker reads the selected settings and main-experiment records, then checks actual reset activity and chopper presence | **Resolved.** It passes and catches all eight planted faults. |
| **The Agarwal sentence became ambiguous after the Byun insertion** | Places Agarwal before the Tiki-Taka comparison and explicitly associates it with conventional SGD training | **Resolved.** The chronology and attribution are clear. |
| **Rounded Student-\(t\) constants introduced small interval discrepancies** | Uses the full-precision numerical quantile for ordinary and paired intervals | **Resolved.** Independent calculations agree; classifications remain unchanged. |
| **Reset rereads received an \(H\)-buffer allowance despite not updating \(H\)** | Explicitly describes the allowance and quantifies its effect | **Adequately addressed as a disclosed approximation.** The stated maximum effect of 0.15% is correct. |

I checked the implementations in the [reproduction driver](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/reproduce_all.py), [architecture checker](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/revision14/check_fig_arch.py), [statistical analysis](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/revision/analyze_rev.py), and the revised manuscript passages. These conclusions are based on those checks, not solely on the response-to-review document.

## 2. The reproduction fix works—and remains appropriately strict

### Result of the actual run

I reran:

```text
python -B reproduce_all.py --fast
```

using the same Python **3.12.14**, PyTorch **2.7.1+cpu**, NumPy **2.5.2**, and Matplotlib **3.9.2** environment that revealed the previous portability issue.

The result was:

| Check | Result |
|---|---:|
| Archive files verified against the checksum manifest | **3,670 / 3,670** |
| Fast reproduction steps passed | **26 / 26** |
| Regenerated files byte-identical | **58** |
| Files matching under the documented figure normalization | **11** |
| Files accepted under the new numerical policy | **1** |
| Unmatched files | **0** |
| Final command result | **`REPRODUCE_ALL_OK`** |

The three diagnostic tables rebuilt from saved pulse draws also matched exactly. Their self-test detected both the deliberately perturbed draw and the incorrect hash.

**This closes the concrete failure observed in v1.4.** It is a reproduction of the deposited analyses, figures, and CPU diagnostics. I did not repeat the full training campaign or the five slow simulator test groups.

### Why I accept the numerical policy

The policy applies to one named artifact: the AIHWKIT pulse-response comparison. That calculation re-simulates long floating-point pulse sequences, and the previous review showed small numerical differences without changed validation decisions.

V1.5 constrains the permitted differences in several ways:

- JSON structure, keys, list lengths, and value types must agree.
- Strings, integers, and every acceptance boolean must agree exactly.
- Only four specified numeric field types receive tolerances.
- Other floating-point fields remain subject to exact comparison.
- A change is rejected if it alters a value printed in the manuscript, even when it lies within the numerical tolerance.

The [policy and its self-test](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/reproduce_all.py) implement these restrictions, and the [README](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/README.md) now explains the reference environment and the exception.

I applied the policy directly to the saved output that failed the previous review. It accepts precisely the expected **26 differing floating-point fields**, while confirming identical metadata, decisions, and printed values. In the fresh run, the largest differences were again approximately:

| Quantity | Largest observed difference |
|---|---:|
| Maximum absolute mean discrepancy | \(5.69\times10^{-6}\) |
| Spread ratio | \(7.82\times10^{-6}\) |
| Discrepancy expressed in acceptance-tolerance units | \(4.70\times10^{-4}\) |

The policy’s built-in **14-case self-test passed**. An additional independent set of **18 mutation cases** also behaved as intended, including rejection of non-finite values, altered types, changed keys, modified exact fields, and changes to printed results.

That is a reasonable resolution of this problem: it accommodates the observed numerical variation while retaining checks on the scientific conclusions.

## 3. The statistical cleanup is correct

The changes to the confidence intervals are as small and as limited as the release says.

I independently verified that:

- All **2,404 raw run-record JSON files** are byte-identical between v1.4 and v1.5.
- The updated quantile calculation agrees with SciPy across the relevant integer and fractional degrees of freedom.
- All **165 stored main arm–baseline comparisons** and all **eight paired width intervals** agree with independent calculations.
- Exactly **16 displayed interval endpoints** change across Tables 4 and 5, each by **0.01**.
- No means, PASS/FAIL/UNRESOLVED labels, width verdicts, or sensitivity thresholds change.

The changes arise from replacing the rounded critical values with the more precise calculation in the [analysis code](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/revision/analyze_rev.py).

Representative changes are:

| Comparison | v1.4 interval | v1.5 interval | Classification |
|---|---|---|---|
| Li-ECRAM, SGD, LM versus FP-SGD | [31.64, 71.63] | **[31.63, 71.64]** | FAIL, unchanged |
| MO-ECRAM, SGD, LM versus FP-SGD | [7.33, 140.35] | **[7.32, 140.36]** | FAIL, unchanged |
| MO-ECRAM, SGD, LM versus Adam | [35.42, 199.87] | **[35.41, 199.88]** | FAIL, unchanged |
| Optimistic memistor, TTv2, CIFAR versus FP-SGD | [0.26, 2.52] | **[0.26, 2.53]** | UNRESOLVED, unchanged |

The LM intervals above are in percentage differences in bits per byte; the CIFAR interval is in accuracy percentage points. The current values appear in the [FP-SGD comparison table](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/tex/tables/rev_main_vs_fp.tex) and [Adam comparison table](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/tex/tables/rev_main_vs_adam.tex).

This is a precision improvement to the analysis. It does not change the evidence for which configurations meet the stated margins.

## 4. The architecture and energy clarifications are sufficient

### Figure 1 now matches the experiments

The figure on page 7 clearly states:

| Algorithm | Reset of \(A\) | Chopper |
|---|---|---|
| TTv2 | Pulse reset | None; \(c=\mathbf{1}\) in the common notation |
| c-TTv2 | Pulse reset | Present |
| AGAD | No reset | Present |

Those settings agree with all **90 main-experiment device records per algorithm**, as well as the selected-settings record. The revised checker now verifies that relationship instead of imposing the same synthetic pulse-reset setting on every algorithm.

Its execution reported:

```text
settings problems 0
sim problems 0
layout problems 0
faults caught 8 of 8
FIG_ARCH_OK
```

I also inspected the rendered page. The added key and qualifications are legible, and they resolve the earlier ambiguity without making the diagram difficult to follow. See the [figure generator](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/revision14/make_fig_arch.py) and [checker](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/revision14/check_fig_arch.py).

### The small energy allowance is now disclosed accurately

Section 5 now explains that reset rereads receive the same buffer allowance even though they do not update \(H\), treating that allowance as a stand-in for the arithmetic that determines correction pulses.

I recalculated the sensitivity from the deposited energy records. Removing that allowance reduces modeled analog energy by at most **0.1497328%**, consistent with the manuscript’s **“at most 0.15%”** statement. The energy scripts and deposited energy output are unchanged from v1.4. See the [revised energy section](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/tex/sec_energy.tex).

For a conditional accounting model with substantially larger uncertainty in its hardware assumptions, this is an adequate treatment. I do not think separating the two read categories is necessary to close the review.

## 5. One optional improvement: make a negative-control test independent of the starting value

**Severity: low; this does not block the release.**

One numerical-policy self-test adds a hardcoded **\(4\times10^{-5}\)** to a value and expects the change to alter the manuscript’s four-decimal printed number. That works for the deposited reference and the actual environments tested.

It is slightly fragile over the full range the policy permits:

1. Subtracting \(4\times10^{-5}\) from the deposited Li-ECRAM noisy maximum discrepancy produces another policy-permitted value that still prints as **0.0111**.
2. Adding the test’s hardcoded \(4\times10^{-5}\) back still prints as **0.0111**.
3. The self-test would expect rejection even though its mutation no longer changes the printed value.

I verified that sequence. It could produce a **false failure of the test** on a different permitted starting value. It does not cause the policy to accept a changed printed result, and it did not affect the successful reproduction run.

A future cleanup would derive the mutation from a nearby rounding boundary, or run this particular negative control against an immutable fixture. The relevant function is `policy_selftest()` in the [reproduction driver](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/reproduce_all.py).

**I would fix this when next maintaining the test, but I would not request another manuscript revision for it.**

## 6. What this means for the paper scientifically

The release strengthens confidence in the **analysis and reproducibility of the existing evidence**. It does not add a new experimental campaign.

The central findings remain:

- **Four device/algorithm pairings**—Li-ECRAM and the protonic-inspired scenario, each with c-TTv2 or AGAD—meet the specified margins on all three tasks against the exact-update SGD comparator.
- **No analog configuration meets the language-model margin against Adam.** The best remains **23.36% worse in bits per byte**.
- Width dependence remains only partly resolved.
- The sensitivity analysis establishes a limited set of one-property-at-a-time results.
- The **17.9–32.4×** energy figure remains a conditional projection per weight-row under the stated assumptions.

Those conclusions remain appropriately bounded in the [discussion](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/tex/sec_discussion.tex) and [energy section](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/tex/sec_energy.tex).

### My assessment of its contribution

The paper’s strongest contribution is an **inspectable comparison of device models, update algorithms, and failure modes**, supported by records, explicit margins, diagnostics, and documented corrections.

Its novelty remains incremental. Its credibility as a comparative simulation study has improved because the paper now makes it much easier to determine which conclusions follow from the calculations and which depend on assumptions.

The largest remaining scientific uncertainty is still the fidelity of the aggregate-update approximation over complete training trajectories. The paper’s diagnostics do not establish that the strongest CIFAR and language-model results survive a correlated shared-line pulse process across every analog layer. That limitation is disclosed in the [fidelity section](https://github.com/Questeria/memistor-ecram-training/blob/b5f86bed24dfef605646fb4f4ac1e5a29f933470/paper/tex/sec_fidelity.tex).

Similarly, ideal-read accuracy and the borrowed finite-read energy efficiency have not been demonstrated together at one operating point. This continues to limit the interpretation of the energy projection, even though the accounting itself reproduces.

These are **boundaries of the current study**, and the manuscript now handles them sufficiently clearly. They should guide the next research stage.

## Recommendation

**I would close this review round and proceed with v1.5 for submission or circulation within its stated simulation scope.** All three required findings from the previous review are resolved, both optional numerical cleanups are addressed, and the full fast reproduction command now succeeds.

The next scientific milestone should be the one the paper already prioritizes: **full correlated-stream training of the passing configurations through complete CIFAR and language-model trajectories**. That experiment can materially strengthen—or revise—the central finding. The remaining optional test cleanup can be handled as routine maintenance.
