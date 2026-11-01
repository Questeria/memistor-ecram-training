# Review 12 (ChatGPT, of release v1.4 / version 14, commit 39c6ed7fe), pasted by the owner in chat on 2026-10-31 ~23:xx ET

Verbatim copy of the text the owner pasted. The reviewer checked the release's checksums, recomputed the statistics from the records and
ran the fast reproduction path (Python 3.12.14, PyTorch 2.7.1+cpu, NumPy 2.5.2, Matplotlib 3.9.2). It did not repeat the training campaign,
run the five slow simulator test groups or perform physical validation. Links are as pasted.

---

## My assessment: v1.4 is substantially improved, with a few minor corrections remaining

I reviewed **[release v1.4](https://github.com/Questeria/memistor-ecram-training/releases/tag/v1.4)** at commit `39c6ed7feba42302cd4e9da3eaa9d0d56c34812c`, containing version 14 of *“Can memistor-class electrochemical weights train neural networks?”*

**For the paper’s current scope as a simulation and methodology study, my recommendation is minor revision.** The specific reporting and framing problems from my previous review are largely addressed. This time, I also examined the deposited records and ran the reproduction procedure. I found **no result-changing error in the main statistical comparisons or energy calculation**.

There are three actionable issues:

1. The reproduction command fails its exact-file check for one numerically sensitive diagnostic on this environment.
2. The new architecture diagram needs to distinguish the reset and chopper settings of the three algorithms.
3. The new related-work passage introduces a small attribution ambiguity.

These are limited corrections. The larger scientific uncertainties remain consequential, but the revised paper now describes them more accurately.

## 1. What I verified

This review went beyond reading the revised prose.

| Check | What I examined | Result |
|---|---|---|
| Release integrity | The PDF and the archive’s checksum manifest | The attached PDF matches the release PDF exactly; all **3,608 listed files** pass their checksums. |
| Main experiment records | **435 records**, including controls and auxiliary arms | Complete seed groups; the recorded initialization and data-order metadata support the claimed pairing. |
| Main statistical analysis | **165 stored arm–baseline comparisons** | Recomputed means and PASS/FAIL/UNRESOLVED decisions agree. |
| Width study | **150 records**, eight Welch contrasts and eight paired contrasts | Results agree, apart from immaterial last-digit differences in paired intervals caused by rounded critical values. |
| Sensitivity analysis | **384 records**, supporting 148 displayed grid-point comparisons, including reused base points | Means, classifications, and reported thresholds agree. |
| Energy accounting | The complete **60-row revised energy output** | Reproduces **byte for byte**. |
| Fast reproduction procedure | All **25 steps** in the documented fast path | Every step completes successfully, but the final file comparison flags one diagnostic JSON, discussed below. |

The statistical checks included independent calculations from the records, rather than only running the authors’ analysis functions. The reproduction run also rebuilt the three pulse-draw diagnostic tables exactly and passed the checks that deliberately perturb draws or supply incorrect hashes. The relevant inputs and procedure are in the [deposited records](https://github.com/Questeria/memistor-ecram-training/tree/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/records/revision) and [reproduction driver](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/reproduce_all.py).

This supports the internal consistency of the reported simulation results. **I did not repeat the full training campaign, run the five slow simulator test groups, or perform physical validation.**

## 2. Findings that should be corrected

### A. The strict reproduction procedure has a small portability problem

**Severity: minor, but worth fixing because it affects someone following the documented reproduction command.**

I ran the fast procedure with Python **3.12.14**, PyTorch **2.7.1+cpu**, NumPy **2.5.2**, and Matplotlib **3.9.2**. The project documents Python 3.12+ compatibility; the authors’ reference environment used Python 3.13.15.

The result was:

| Reproduction result | Count |
|---|---:|
| Steps completed successfully | **25 / 25** |
| Regenerated files byte-identical | **60** |
| Files matching after the permitted figure normalization | **9** |
| Files differing beyond those rules | **1** |

Consequently, the command finishes with **`REPRODUCE_FAILED`**, despite all individual steps passing. The differing artifact is the [AIHWKIT comparison JSON](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/records/revision/AIHWKIT-COMPARE.json).

I investigated the differences:

- **26 floating-point fields differ.**
- **Every acceptance boolean is unchanged.**
- The largest change in a reported maximum absolute mean discrepancy is approximately **\(5.69\times10^{-6}\)** weight units.
- The largest change in a discrepancy expressed in units of its acceptance tolerance is approximately **0.000470**.
- The largest corrected-model discrepancy remains about **0.642**, against an acceptance limit of **1.0**.
- The old, rejected device mapping still fails by a large margin.
- The corresponding manuscript values still round to the same displayed numbers.

This diagnostic actually **re-simulates long float32 pulse sequences on the CPU**, making it more sensitive to runtime arithmetic than an aggregation of saved observations. An isolated rerun with AVX2 selected produced the same output as this environment’s default dispatch, so that change alone did not resolve the discrepancy. **I have not isolated the particular runtime or library cause.** See the [comparison implementation](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/revision/compare_curves.py).

**Recommended correction:** make the reproduction guarantee explicit and enforceable. Either provide a sufficiently specified reference environment for exact reproduction, or introduce a narrowly defined numerical comparison policy for this particular diagnostic. Such a policy should preserve exact schema, metadata, acceptance decisions, and manuscript-facing values, with justified numerical tolerances and a check that meaningful perturbations still fail.

The current evidence supports the scientific device-comparison conclusion. It also shows that the advertised strict reproduction procedure needs a small portability repair.

### B. Figure 1 overgeneralizes the reset and chopper configuration

**Severity: minor presentation error with an associated checker-coverage gap.**

The new architecture diagram is useful: it makes the device state, digital state, and ideal reads much easier to understand. However, its shared Tiki-Taka panel covers TTv2, c-TTv2, and AGAD while labeling the \(A\) array with a pulse reset and expressing the update input as \(c\odot x\).

The selected main-experiment configurations are:

| Algorithm | Reset of \(A\) | Chopper |
|---|---|---|
| TTv2 | Pulse reset | Absent |
| c-TTv2 | Pulse reset | Present |
| AGAD | **No reset** | Present |

I checked the revised main records: all 90 device records for each algorithm use the corresponding reset setting above. The existing settings table already reports this correctly. The ambiguity is in the common figure, which is described as showing the algorithms “as run here.” See the [selected settings](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/tables/rev2_selection.tex) and [figure generator](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/revision13/make_fig_arch.py).

A sufficient caption addition would be:

> In the selected configurations, TTv2 and c-TTv2 use the pulse reset, while AGAD uses no reset. In the common input notation, take \(c=\mathbf{1}\) for TTv2; c-TTv2 and AGAD use chopper signs.

The new figure checker does not catch this because it constructs **all three algorithms with `tt_reset="pulse"`**, including AGAD. It checks state types, ideal reads, and pulse destinations on that synthetic configuration, but does not verify the reset configurations selected for the reported experiments. See the [architecture checker](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/revision13/check_fig_arch.py).

**Recommended correction:** qualify the caption or boxes, and have the checker verify the selected configurations. No new training is required; the stored AGAD runs and the settings table already agree.

### C. The Byun insertion makes one related-work sentence ambiguous

**Severity: minor wording issue.**

Section 2.2 now moves from:

1. Gokmen and Vlasov’s device requirements for plain SGD;
2. Byun’s comparison of TTv1 and TTv2;
3. “Agarwal et al. reached similar conclusions.”

The immediate antecedent of “similar conclusions” is now the TTv1/TTv2 comparison. Agarwal is a **2016** reference, preceding the Tiki-Taka papers discussed here. A reader could therefore interpret the sentence as attributing that later algorithm comparison to the earlier work. See the [revised background](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_background.tex) and [bibliography](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/refs.bib).

**Recommended correction:** move the Agarwal sentence before the Byun passage, or explicitly say that Agarwal also studied device requirements for conventional neural-network training.

The addition of Byun itself addresses the earlier missing-prior-art concern.

## 3. What v1.4 resolves from the previous review

The revision makes several substantive improvements to how the evidence is presented.

| Previous concern | Assessment of v1.4 |
|---|---|
| **Missing close prior art** | Byun is now cited in the introduction and background, and the paper describes its own incremental contribution more precisely. |
| **Unexplained GPU energy range** | Resolved. The text now includes the **500–700 W** power range as well as the **38–43%** utilization range, the equation, and the endpoints. |
| **Unclear digital-buffer cost boundary** | Substantially resolved. The included ADC and \(H\)-buffer operations are distinguished from excluded storage, reference arithmetic, chopping, thresholds, and scheduling. |
| **Energy ratio could be read as demonstrated training efficiency** | The revised wording clearly identifies a conditional, read-dominated estimate per weight-matrix operation and explains the missing joint accuracy–energy operating point. |
| **“Device specification sheet” sounded too strong** | Resolved at the level of claims. The subtitle and body now describe an exploratory sensitivity analysis, including the lack of a joint guarantee across device properties. |
| **Algorithm and device effects were not adequately separated** | The missing control ladder is now explicitly described, together with which stages were actually run. This improves disclosure; the missing controls remain future experiments. |
| **Next steps moved too quickly toward fabrication** | The roadmap now prioritizes full correlated-stream training, update management, controls, and fair tuning. These address the present uncertainties directly. |
| **Correction history obscured the scientific story** | Improved. Moving detailed historical repairs to the appendix makes the current method and evidence easier to follow. |

These changes are visible in the [introduction](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_intro.tex), [energy section](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_energy.tex), [limitations](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_discussion.tex), and [roadmap](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_roadmap.tex).

### The earlier energy-range concern should be closed

The updated explanation matches the implementation:

\[
E_{\mathrm{GPU}}=\frac{6P}{Fu},
\qquad F=989.5\ \mathrm{TFLOP/s}.
\]

Using the paper’s stated inputs gives:

| Scenario | Recomputed energy per weight per row |
|---|---:|
| 700 W, 40.5% utilization | **10.4804 pJ** |
| 500–700 W, 38–43% utilization | **7.0508–11.1699 pJ** |
| 500–700 W, 30–55% utilization | **5.5124–14.1486 pJ** |

The previous discrepancy was an omitted description of the power sweep. The calculation was already using that sweep. The revised prose now makes it reproducible from the stated assumptions. The [energy implementation](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/energy/energy_rev.py) reproduces the deposited output exactly.

## 4. The central numerical conclusions hold up

Across the five catalog specifications and four algorithms, excluding the separate ideal-device controls, the main-table PASS counts reproduce:

| Comparator | MNIST | CIFAR | Language model |
|---|---:|---:|---:|
| Exact-update FP-SGD | **14 / 20** | **6 / 20** | **4 / 20** |
| Tuned Adam | **14 / 20** | **4 / 20** | **0 / 20** |

The underlying tables are [the FP-SGD comparison](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/tables/rev_main_vs_fp.tex) and [the Adam comparison](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/tables/rev_main_vs_adam.tex).

The defensible interpretation remains:

- **Li-ECRAM and the protonic-inspired scenario each pass all three tasks with c-TTv2 or AGAD** against the specified FP-SGD comparator.
- **No analog configuration passes the language-model margin against Adam.**
- The best language-model result against Adam is still **23.36% worse in bits per byte**, with a reported 95% interval of **[22.15%, 24.58%]**.
- PASS establishes the stated non-inferiority criterion under this protocol. It does not establish equal performance.

The delicate width result also checks out. For protonic-inspired c-TTv2 on CIFAR, the gap grows by about **1.762 percentage points**, with a paired 90% interval of approximately **[0.146, 3.378]**. This detects growth, while leaving its magnitude relative to the **2-point margin** unresolved. The revised paper correctly preserves that distinction. Endpoint equivalence is established for one CIFAR arm, Li-ECRAM c-TTv2. See the [width results](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/tables/rev_width.tex).

That is a useful outcome of this audit: the nuanced conclusions survive independent reanalysis, including the inconvenient and unresolved results.

## 5. Scientific assessment of the revised paper

### Its contribution is now positioned more convincingly

My assessment is that the paper’s strongest contribution is the **auditable comparison of device models, update algorithms, and failure modes under an explicitly restricted simulator**.

The value comes from connecting several things that are often difficult to inspect together: device-parameter provenance, algorithm settings, paired comparisons, pulse accounting, surrogate-versus-stream diagnostics, and the consequences of corrections. The newly acknowledged prior art makes the incremental nature of this contribution clearer. The [revised introduction](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_intro.tex) now supports that positioning.

### The update approximation remains the largest uncertainty

The most consequential limitation is still the gap between the aggregate-update surrogate and a physical shared-line pulse process.

The paper reports that the surrogate meets its diagnostic lines on **10 of 12 probes using point estimates**, with much weaker coverage when bootstrap uncertainty is required to stay inside all the lines. Training-level comparisons cover MNIST and CIFAR’s dense layers; they do not establish the full language-model trajectory or the convolutional layers. One CIFAR configuration loses its PASS classification under the stream comparison at the same three seeds. These limits are now stated clearly in the [fidelity section](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_fidelity.tex).

**Reproducing the surrogate’s results strengthens confidence in the computation. It does not settle whether the surrogate preserves the strongest training conclusions under the more faithful update process.**

The revised roadmap therefore chooses the right next scientific milestone: train the passing configurations through full CIFAR and language-model trajectories with correlated streams on every analog layer.

### The energy result is now appropriately qualified

The accounting is reproducible, and the missing assumptions are now visible. Its applicability still depends on assumptions that the accuracy experiments do not jointly test:

- Accuracy uses ideal reads.
- Read energy comes from a different hardware platform and operating regime.
- Several costs of a complete training system remain outside the accounting boundary.
- The comparison does not measure energy required to reach a common target quality.

The paper explicitly acknowledges these conditions. I would retain the conditional projection as a scenario analysis within that scope. It does not support a demonstrated **18–32× reduction in the energy needed to train a model to a given quality**. See the [revised energy discussion](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_energy.tex).

### The uncertainty intervals have a specific meaning

The paired intervals quantify variation across the saved training seeds under the chosen models and settings. They do not propagate uncertainty in estimated device parameters or establish robustness to combinations of nonidealities.

The change to “exploratory device sensitivity analysis” is consequently more than cosmetic: it brings the headline description into line with what three-seed, one-property-at-a-time sweeps can establish. The paper now explains that boundary in its [sensitivity section](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/tex/sec_spec.tex).

## 6. Two optional numerical cleanups

These have no material effect on my recommendation.

**Reset reread accounting.** The energy code adds reset rereads to the read count and then charges each counted read for both an ADC conversion and an \(H\)-buffer update. Reset rereads do not actually update \(H\). Removing that extra buffer allowance would reduce modeled analog energy by **at most about 0.15%** among the modern-device rows. It is a small conservative approximation that could be labeled explicitly or separated into two read categories. See the [read-count calculation](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/energy/energy_rev.py) and [energy pricing function](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/energy/energy_system.py).

**Critical-value consistency.** Some ordinary and paired intervals still use three-decimal Student-\(t\) constants, while the Welch calculation uses a more accurate quantile routine. Using that routine consistently would remove small endpoint differences across independent implementations. **No classification changes in the comparisons I checked.** See the [statistical analysis code](https://github.com/Questeria/memistor-ecram-training/blob/39c6ed7feba42302cd4e9da3eaa9d0d56c34812c/paper/revision/analyze_rev.py).

## Recommendation

**I would close the previous substantive reporting concerns and request three limited corrections:**

1. Resolve or explicitly accommodate the small numerical portability failure in the reproduction procedure.
2. Qualify Figure 1’s reset/chopper notation and check it against the selected settings.
3. Clarify the Agarwal sentence after the Byun insertion.

I would **not require a hardware demonstration to accept the paper’s present, explicitly conditional simulation claims**. The remaining hardware and algorithm-validation questions should continue to constrain its conclusions.

My confidence in the reported calculations is higher after this review. The next advance in the scientific evidence will come from the full correlated-stream training validation that v1.4 now prioritizes.
