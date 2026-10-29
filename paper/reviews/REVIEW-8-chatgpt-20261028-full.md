**Independent review of the public memistor/ECRAM deposit against paper version 10**

Reviewed 28 October 2026. This review used the fresh public release clone and the supplied 42-page PDF. It did not use private project folders, earlier review conclusions, or unpublished working files. All scientific results discussed here are simulations.

**Result.** The documented CPU reproduction succeeds after correcting one working-directory error in the quick start. All 24 steps pass: 53 regenerated files are byte-identical and 14 figure files match after exactly the documented PDF timestamp / PNG pixel normalization. There are no regenerated numerical-file or table mismatches. I found seven minor findings and two cosmetic findings. None demonstrates that version 10's current main conclusions are wrong. Several defects reproduce perfectly, so successful regeneration is not by itself evidence that every calculation is correct.

The original clone remains unchanged: its Git status is clean and all 3,337 manifest entries pass their SHA-256 checks after the review. Generated outputs and the Python environment are confined to H:/review8. No repository source was edited.

**What was reviewed and run**

The release is tag `v1.0`, commit `076624fbc58b2d50041bf88f2549ff58e37ee52d`, in [the original clone](H:/review8/memistor-ecram-training). Reproduction ran on a separate copy in [reproduction](H:/review8/reproduction), as README recommends because the generators overwrite outputs. The authoritative [version-10 PDF](H:/review8/memistor-paper-v10.pdf) has SHA-256 `8660babf8321459d1f716e2527a72e25da0f1d14a932a54f4e5db75243a717f0`.

The release contains version 9, exactly as version 10's Section 9 says. Comparison with the deposited arXiv PDF found no scientific-result changes: the changes concern availability and revision history, with text reflow. All 42 pages were inspected as rendered contact sheets, with larger renders of the availability page, all three figures, and the sensitivity table.

The fresh environment uses Python 3.13.15, torch 2.7.1+cpu, NumPy 2.5.2, matplotlib 3.9.2 and Pillow 13.0.0 on Windows 11. CUDA was unavailable to the reproduction. Windows did not block package loading; WSL was not needed. The CPU wheel differs from the author's recorded CUDA wheel, as allowed by the CPU reproduction instructions. See [environment and integrity evidence](H:/review8/audit/audit-environment-and-integrity.json).

I executed dataset download, dataset verification, the pre-generation checksum check, the draw-table reconstruction and its corruption checks, and the complete `reproduce_all.py` pipeline from the repository root. The full pipeline covers the fast mode's steps as well as the slow checks; fast mode was not separately repeated after the full run. Its measured step times total 1,356.9 seconds, about 22.6 minutes, excluding installation and download. I additionally ran `paper/sim/test_memsim.py` and regenerated the earlier study's `records/ENERGY.json`, `records/RESULTS.json`, and `VERDICT.md`; all three extra regenerated files are byte-identical.

Evidence: [complete reproduction result](H:/review8/audit/REPRODUCE.json), [console log](H:/review8/audit/reproduce-console.log), [per-step logs](H:/review8/reproduction/_repro), [extra earlier-study regeneration](H:/review8/audit/lane-regeneration.json).

**Every table, figure, and generated number**

The expected values in the following inventories come from the immutable release; the actual values come from fresh regeneration. The PDF's scientific contents were cross-checked against those sources. The inventories retain full expected and actual table text, hashes, and individual macro values, rather than just a pass count.

- [Number inventory, CSV](H:/review8/audit/number-inventory.csv) and [JSON](H:/review8/audit/number-inventory.json): all **2,231 macro definitions** across the five `numbers*.tex` files agree exactly, including historical and unused definitions. Of these, 253 are referenced by current non-number TeX files; their reference locations are [listed separately](H:/review8/audit/number-inventory-current-references.json).
- [Table inventory](H:/review8/audit/table-inventory.json): full expected and actual text for all 26 tables. [Compact CSV](H:/review8/audit/table-inventory.csv).
- [Figure inventory](H:/review8/audit/figure-inventory.json): expected/actual hashes and independent PDF-date or decoded-pixel comparisons for all seven generated figure pairs. Three appear in version 10; four remain repository outputs.
- [Number-bearing PDF lines](H:/review8/audit/paper-number-bearing-lines.json) indexes the 1,128 extracted lines containing digits. This is a coverage aid, not a claim that cited historical facts or proposed experimental settings are measurements regenerated from the run records.

| Table | PDF page | Source under paper/tex/tables/ | Regeneration / comparison |
|---|---:|---|---|
| 1 | 7 | rev2_catalog.tex | Exact match |
| 2 | 10 | e1.tex | Exact match |
| 3 | 10 | e1b.tex | Exact match |
| 4 | 14 | rev_main_vs_fp.tex | Exact match |
| 5 | 15 | rev_main_vs_adam.tex | Exact match |
| 6 | 17 | rev4_probe_sur.tex | Exact match, also rebuilt from saved draws |
| 7 | 18 | rev4_probe_seq.tex | Exact match, also rebuilt from saved draws |
| 8 | 19 | rev4_dep.tex | Exact match, also rebuilt from saved draws |
| 9 | 19 | rev4_a2m.tex | Exact match |
| 10 | 20 | rev3_fid.tex | Exact match |
| 11 | 20 | rev_width.tex | Exact match |
| 12 | 21 | rev_spec_p.tex | Final file not regenerated; content matches freshly regenerated rev_spec.tex, apart from a comment and float placement |
| 13 | 23 | rev_energy.tex | Exact match; small underlying accounting error described below does not change its rounded ratios |
| 14 | 33 | rev2_selection.tex | Exact match |
| 15 | 34 | checks.tex | Exact match; corresponding checks also pass on this CPU |
| 16 | 35 | laneme.tex | Exact match; earlier-study result/energy inputs additionally regenerated |
| 17 | 36 | v1s_catalog.tex | Exact match, superseded result |
| 18 | 36 | v1s_e2.tex | Exact match, superseded result |
| 19 | 36 | v1s_main.tex | Exact match, superseded result |
| 20 | 37 | v1s_scale.tex | Exact match, superseded result |
| 21 | 37 | v1s_spec.tex | Exact match, superseded result |
| 22 | 37 | v1s_spec_rel.tex | Exact match, superseded result |
| 23 | 37 | v1s_pairs.tex | Exact match, superseded result |
| 24 | 38 | v1s_energy.tex | Exact match, superseded result |
| 25 | 41 | rev_d1.tex | Exact match, diagnostic comparison |
| 26 | 42 | v3s_rev2_probe.tex | Exact match, explicitly superseded probe analysis |

| Figure | PDF page | Source under paper/tex/figs/ | Result |
|---|---:|---|---|
| 1 | 11 | fig_validation.pdf / .png | Regenerates with identical figure content |
| 2 | 13 | fig_rev_main.pdf / .png | Regenerates with identical figure content |
| 3 | 38 | fig_main.pdf / .png | Regenerates identically, including the plotting error in finding 1 |

The four additional generated figure pairs, `fig_energy`, `fig_oat_cifar`, `fig_oat_lm`, and `fig_scale`, also match under the stated normalization. No allowed normalization changes a plotted pixel or a PDF drawing instruction. Version 10 itself was not rebuilt from LaTeX: the deposit intentionally contains version 9, and the documented pipeline excludes document builds.

**Findings**

1. **Minor — Figure 3 moves negative means and their confidence intervals to the right.** [paper/make_figures.py:81](H:/review8/memistor-ecram-training/paper/make_figures.py:81); version 10, page 38, Appendix E, Figure 3. The call plots `max(mean, 0.05)` but computes the error-bar widths from the original mean. Thus it changes both the center and both endpoints. A symmetric-log axis supports negative values; this clamp is unnecessary.

   | LM cell | Expected mean | Actual plotted mean | Expected 95% interval | Actual plotted interval |
   |---|---:|---:|---|---|
   | Li-ECRAM, c-TTv2 | −1.29345409% | +0.05% | [−4.45998662, 1.87307844]% | [−3.11653253, 3.21653253]% |
   | Protonic, c-TTv2 | −0.84077048% | +0.05% | [−4.30033667, 2.61879571]% | [−3.40956619, 3.50956619]% |

   Confirmed by tracing the plotting arguments from the result JSON and inspecting the rendered figure. See [exact values](H:/review8/audit/figure3-discrepancies.json). This changes two graphical numerical results in the explicitly superseded figure. Table 19 retains the correct numbers; the current Figure 2 and main conclusions are unaffected.

2. **Minor — Classification sample counts include discarded incomplete batches, slightly overstating transfer-read energy.** [paper/sim/run_rev.py:151](H:/review8/memistor-ecram-training/paper/sim/run_rev.py:151) and [line 162](H:/review8/memistor-ecram-training/paper/sim/run_rev.py:162), also [paper/sim/run.py:152](H:/review8/memistor-ecram-training/paper/sim/run.py:152). The loops train only on full batches, but `samples = n * len(hist)` counts the complete dataset each epoch. [paper/energy/energy_system.py:102](H:/review8/memistor-ecram-training/paper/energy/energy_system.py:102) turns that count into an inflated number of optimizer steps. The revised energy analysis uses this function.

   Expected MNIST count at ten epochs: **549,120**, recorded: **550,000**. Expected CIFAR count at thirty epochs: **299,520**, recorded: **300,000**. Across the paper's stored records, 1,457 of the 2,398 records with sample/layer counts have this mismatch; [every affected file and count](H:/review8/audit/targeted-checks.json) is listed.

   I recomputed revised energy using actual layer rows to recover the number of steps. Sixty scenario entries change; [every published/corrected value](H:/review8/audit/energy-correction.json) is listed. The largest relative total-energy change is about **0.000481%**. For MNIST Li-ECRAM/AGAD under the chip scenario, deposited total energy is **0.32511121362649603 pJ**, corrected **0.32510964862248964 pJ**; the corresponding ratio changes from **32.23639876360313** to **32.23655394230493**. None of Table 13's rounded integer ratios changes. This is an accounting defect; correcting the metadata does not change trained accuracy or the energy conclusion. The LM does not have this dropped-classification-batch error.

3. **Minor — The optional ideal reset crashes with AIHWKIT bounds and a partial column selection.** [paper/sim/memsim_rev.py:444](H:/review8/memistor-ecram-training/paper/sim/memsim_rev.py:444), with `Tile.clip` at [line 163](H:/review8/memistor-ecram-training/paper/sim/memsim_rev.py:163). The reset clips selected columns against full-tile bound tensors. A 3×1 selected slice broadcasts to 3×4 and cannot be assigned back. The expected result is a successful reset of the selected columns; actual result is `RuntimeError: shape mismatch: value tensor of shape [3, 4] cannot be broadcast to indexing result of shape [3, 1]`.

   Confirmed by instantiating `AnalogLinear(4, 3, ...)` with `bounds_model='aihwkit'`, `tt_reset='ideal'`, `tt_cols=1`, then calling `_transfer()`. The complete trace is in [targeted checks](H:/review8/audit/targeted-checks.log). A scan found no deposited TT-family training run combining AIHWKIT bounds with this ideal-reset path. It therefore affects a supported simulator configuration, not a published result. The existing green suites do not cover this combination.

4. **Minor — The LM sampler excludes the final valid training window.** [paper/sim/run_rev.py:173](H:/review8/memistor-ecram-training/paper/sim/run_rev.py:173), also [paper/sim/run.py:162](H:/review8/memistor-ecram-training/paper/sim/run.py:162). `torch.randint` has an exclusive upper bound. A window of `ctx + 1` bytes allows the last start `len(tr) - ctx - 1`, but the current call excludes that start. The high argument should be `len(tr) - ctx`.

   With 8,000,000 bytes and context 128, expected last start is **7,999,871**; actual last allowed start is **7,999,870**. The final byte at index 7,999,999 is never used. Confirmed by the slice bounds and an exhaustive toy-sequence enumeration; see [boundary evidence](H:/review8/audit/lm-window-boundary.json). This is a small sampling-coverage error, not train/test leakage. Correcting the random bound can change a training realization, so an exact accuracy delta cannot be inferred without retraining. No conclusion change has been demonstrated.

5. **Minor — The quick-start commands do not work sequentially.** [README.md:47](H:/review8/memistor-ecram-training/README.md:47) changes into `paper`, after which lines 48–49 try to run the root-level `reproduce_all.py` without returning to the root. Expected: the reproduction starts. Actual: Python cannot open `paper/reproduce_all.py`, with exit code 1. I executed that sequence and saved [the failure](H:/review8/audit/readme-cwd-failure.log). Returning to the repository root resolves it; the full run then passes. This affects instructions only, not results. A subshell for the draw command or an explicit `cd ..` would make the sequence work. The `&&` form also presumes a shell that supports it; the shell used here did.

6. **Minor — The headline claim that the command regenerates every table exceeds its automated coverage.** [README.md:48](H:/review8/memistor-ecram-training/README.md:48), contrasted with its accurate exception at [line 106](H:/review8/memistor-ecram-training/README.md:106). `rev_spec_p.tex`, the actual Table 12 file, is retained rather than regenerated. The pipeline's final comparison at [reproduce_all.py:208](H:/review8/memistor-ecram-training/reproduce_all.py:208) compares files that steps rewrote; it is not an independent assertion that every manuscript artifact was rebuilt.

   Expected under the headline wording: the final Table 12 file is regenerated and compared. Actual: `rev_spec.tex` is regenerated, while `rev_spec_p.tex` is unchanged and absent from the rewritten-file comparison. I separately normalized only the added comment and `[p]` versus `[t]` placement and verified identical content. There is **no stale value in Table 12**. This is a coverage/documentation issue, not a numerical mismatch. Section 9's broader claim that derivation scripts are included remains substantially supported; it should not be read as a claim that this one command rebuilds the entire PDF.

7. **Minor — A fresh environment has no copyable dependency-installation recipe.** [README.md:35](H:/review8/memistor-ecram-training/README.md:35)–40 and [ENVIRONMENT.md](H:/review8/memistor-ecram-training/ENVIRONMENT.md). Dependencies and several version sets are described, but there is no installation command or requirements file and no explicit CPU-wheel selection command. The user must choose how to reconcile training-environment versions with clean-room versions. This did not prevent reproduction: I supplied the environment described above and all steps passed. No stated compatible version was shown to fail. The finding is a missing setup instruction, not evidence that the declared dependencies are wrong.

8. **Cosmetic — The README's size total is stale.** [README.md:147](H:/review8/memistor-ecram-training/README.md:147) says **122.9 MB** for 3,337 files excluding `SHA256SUMS`. Summing those exact manifest-listed files gives **123,008,145 bytes**, or **123.0 MB** at the displayed decimal precision. The file count is correct. Including the 456,474-byte manifest gives 123,464,619 bytes, which agrees with the release notes' **123.5 MB**. Confirmed by both Git's tracked-file list and the manifest list; see [size evidence](H:/review8/audit/deposit-size.json). No scientific effect.

9. **Cosmetic — Figure 3's legend overlaps its x-axis label.** Version 10, page 38, Appendix E; [paper/make_figures.py:90](H:/review8/memistor-ecram-training/paper/make_figures.py:90). The bottom figure-level legend and the center panel's x-axis label occupy overlapping space. Confirmed in the supplied PDF's [larger page render](H:/review8/audit/v10-page38.png), and the regenerated output preserves it. Expected: separately legible legend and axis labels. Actual: text and legend marks overlap. It does not change a statistic or conclusion, but it should be corrected when fixing finding 1.

**What the code audit found correct**

I read the computational source line by line: the original and repaired device models and catalogs; pulse-stream implementation; original and revised tasks, runners and probes; all five analysis scripts under `paper/revision*/analyze*.py`; `paper/analyze.py`; both `paper/energy` scripts; the draw-table reconstruction; statistical helpers; the original and revised sweep/selection drivers; and the figure generators. Additional reads covered the earlier study's energy/verdict derivations. The historical code-editing utilities, build wrappers, all archived review scripts, and all unrelated repository files were not given the same line-by-line audit.

The following checks support the current results:

- **Mean gaps and confidence intervals:** independently recalculated 165 revised comparison statistics from run records without using the repository's analysis functions; maximum numerical discrepancy was 2.84×10⁻¹⁴. The signs and units agree: classification uses FP-minus-device percentage points; LM uses relative bits-per-byte excess. See [independent comparison results](H:/review8/audit/independent-main.json).
- **Pairing:** checked 825 compared seed-arm pairs for initialization hashes, example-order hashes and hardware. No mismatch was found. The current matched-triple analysis enforces the same checks. The old mixed-hardware analysis remains explicitly withdrawn, not silently reused as current evidence.
- **Selection and splits:** all 34 recorded learning-rate selections choose the best validation score, and none ends at a selected grid edge. The three TT-family setting selections also match their grid maxima: AGAD 0.973, c-TTv2 0.976, TTv2 0.976. The 1,410 revised training records checked use the stated validation/test split by phase. See [algorithm selections](H:/review8/audit/algorithm-selection.json) and [record audit](H:/review8/audit/record-and-figure-audit.log).
- **No current split leakage found:** source slicing keeps MNIST's 55k/5k/10k sets separate; CIFAR uses the specified training subset, validation subset from a different training batch, and official test data; CIFAR normalization is derived from training data. LM validation selection holds out the last 0.5 MB of the training slice, while final evaluation uses the separate stated slice. The LM boundary defect above does not cross a split boundary. The original single-RNG design and other superseded flaws are acknowledged in the paper.
- **Pulse/device equations:** checked update signs, conductance/normalized-state conversion, stable exponential step accumulation, asymmetric symmetry points, bound-scaled slopes, device-to-device variation, square-root scaling of independent write noise, drift target, probability clipping, chopper modulation/demodulation, transfer direction, residual buffer updates, and actual pulse-reset accounting. The optional ideal-reset slice bug is the specific failure found. Ideal reads and digital attention/auxiliary operations are disclosed rather than represented as physical device measurements.
- **Probe statistics:** independently recomputed mean error, gain ratio, independent/paired sampling floors and excess from all 12 draw archives. Maximum absolute disagreement was 4.44×10⁻¹⁶. Source review and the repository's checks support paired whole-draw bootstrap and per-pair dependence calculations rather than a signed correlation average that can cancel. The draw rebuild verifies the archived hashes and reproduces Tables 6–8 exactly; its self-test rejects a changed draw and an incorrect hash. See [independent draw calculations](H:/review8/audit/independent-draws.json).
- **Inference labels:** inspected paired intervals, absolute sensitivity thresholds, width contrasts and 90% endpoint-equivalence intervals. The code distinguishes failure to establish growth from established equivalence; the manuscript reports the narrow equivalence finding and the unresolved comparisons. The added c-TTv2 sensitivity sheet is identified as post hoc. Multiple-comparison limitations are disclosed.
- **Energy:** verified the row-weighted pulse and line activity, conversion between joules/fJ/pJ, MAC/FLOP factors, the GPU power/throughput/utilization expression, reset overhead, and quality filtering. The comparison remains a conditional projection borrowing hardware efficiency assumptions and excluding stated operations. Finding 2 makes a tiny accounting correction; it does not justify treating the ratios as measured end-to-end ECRAM training efficiency.

The deposited records support the paper's main distinctions: four device/algorithm pairings pass all three task margins against same-rate FP-SGD; none passes all three against tuned Adam; the best analog LM result remains 23.36% worse than Adam. Probe point-estimate agreement does not imply agreement at bootstrap confidence, and the paper explicitly reports where the surrogate and literal streams differ. The audit did not establish that these outcomes generalize to larger models, more seeds, nonideal reads, or physical devices.

**Simulator checks**

| Suite | Checks passed | Planted faults detected |
|---|---:|---:|
| sim/test_memsim.py | 9 | 10 |
| paper/sim/test_paper.py | 5 | 7 |
| paper/sim/test_rev.py | 8 | 8 |
| paper/sim/test_rev2.py | 5 | 5 |
| paper/sim/test_rev3.py | 4 | 4 |
| Additional paper/sim/test_memsim.py | 9 | 10 |
| Total suite executions | **40** | **44** |

Counts include overlapping checks in the original and paper simulator suites; they are not 40 independent scientific validations. In the stream suites, planted-fault records report `ok: false` as intended and `all_faults_caught: true`. The complete [test inventory](H:/review8/audit/test-inventory.json) preserves those results. Dataset corruption checks, revision-4 analysis self-tests, draw corruption checks and bench-analysis self-tests also pass. Green tests do not cover every configuration, as finding 3 demonstrates.

**Section 9, README, contents and licensing**

Every concrete path and glob named in Section 9 resolves within `paper/`, with root-relative archive documents handled separately. The README's layout entries, archived `tex/v1`–`v8` and `build/v1`–`v8`, and every listed generated figure/table path exist. See [Section 9 / README path inventory](H:/review8/audit/path-inventory.json) and [layout inventory](H:/review8/audit/layout-inventory.json).

There are exactly 12 saved NumPy draw archives totaling **81,905,772 bytes**, matching Section 9. Dataset files are absent from the tracked release and are fetched separately; all three downloaded datasets pass the pinned digest checks. There are seven numbered full review documents, plus a summary for review 2 and support files. Their existence and deposited hashes were checked without adopting their findings as evidence for this review.

The code/data license distinction agrees across Section 9, README, `LICENSE`, `LICENSE-DATA`, and citation metadata: MIT for code and CC BY 4.0 for the stated records, draws, text and figures. Both license texts are present. This verifies the declaration and contents; it cannot establish ownership of every incorporated element or the legal authority of every upstream contributor to grant those rights.

All 11 current-file hashes in `REDACTIONS.md` match. Claims about what changed relative to private unredacted originals cannot be independently established from this release. The old support manifest's two nonmatching redacted-file hashes are explicitly disclosed by `REDACTIONS.md`; they are not failures of the release's root checksum manifest.

The environment's run-record counts are correct: **2,691** records report torch 2.7.1+cu126; **2,421** name RTX A4000, **252** Quadro P2000 and **18** Quadro P2200. NumPy, Python and driver facts said to come from excluded pod logs cannot be independently verified from those logs here. No additional wrong or failing README/ENVIRONMENT execution instruction was found beyond findings 5–7; the small size error is finding 8.

**What could not be established from the allowed evidence**

- Full GPU training trajectories were not rerun. The documented reproduction explicitly starts from saved records/draws and does not retrain. This audit checks those records' internal consistency and their analysis, not independent recreation of all training outcomes from raw data.
- AIHWKIT itself was not independently installed and rerun. The deposited curve-comparison calculation was rerun, and the mapped device formulas were audited; the upstream reference curves remain deposited evidence.
- The Zenodo archive was not downloaded and compared with GitHub. Section 9 names a DOI, but archive accessibility, concept-versus-version metadata, and byte identity across hosting services were not established using only the clone and PDF.
- External cited papers, historical numerical claims, physical device parameters and quoted efficiency assumptions were not revalidated against outside publications. The included citation-check record is evidence of an author's check, not a fresh external verification. Proposed bench settings and literature inputs are not outputs that `reproduce_all.py` can regenerate.
- Public history contains one release commit. Internal plans and timestamps are present, but the claim that every plan was committed before its experiments cannot be independently reconstructed from the public Git history. Private histories, pod logs and unredacted originals were outside scope.
- The version-10 PDF was read and visually checked, but could not be rebuilt from version-10 sources because those sources are not in v1.0. README explicitly excludes LaTeX/pandoc builds and desk-specific historical verification scripts from reproduction. No missing v10 source is being treated as an undisclosed version mismatch.
- A line-by-line audit and finite tests cannot prove absence of all bugs. No new physical measurement, hardware validation, independent replication on another training seed ensemble, or assessment of real-world energy advantage was performed.

The numerical reproduction is successful and the main conclusions survive the specific defects found. Correct the minor computational and plotting errors, tighten the setup and coverage wording, and preserve the explicit limits on simulation fidelity and conditional energy claims.
