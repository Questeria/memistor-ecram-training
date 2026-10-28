**Memistor Paper Version 4 Review**

Reviewed 27 October 2026. Target: *Can memistor-class electrochemical weights train neural networks?*, the current 41-page [main PDF](paper/build/main.pdf). SHA-256: `824bbc1cf8cedc18159cd9ac23431805cda6a2cd9779c94fcf9fa3dcf467feaf`.

**Assessment.** Version 4 is substantially more defensible. It corrects the previous ranking and width claims, discloses the sequential update's noise approximation, and replaces the flawed uncertainty and dependence summaries with calculations that can now be independently reproduced from saved draws. Those are substantive repairs.

One important methodological problem remains in the new training extension: the cross-machine runs do not retain the old initialization and, on MNIST, do not retain the old training-example order. The claimed 7.67-percentage-point change from “GPU rounding alone” is therefore unsupported. The five-seed extension also combines two unmatched pairs with three matched pairs. This affects the interpretation of that extension, rather than invalidating the earlier main experiment or the internally paired update probes. A second, practical issue is that the release instructions omit the external draw files needed to independently reconstruct the new statistics.

I would make a focused revision before submission. A large new experiment is not necessary if the paper limits the new cross-machine results to descriptive observations and retains the earlier matched comparison as its controlled evidence.

**1. High priority: the new training extension loses the matching that its interpretation requires**

The problem appears in Section 4.3, pages 15–16, and in the [response to review 3](paper/RESPONSE-TO-REVIEW-3.md:64). The manuscript describes the seed-0 accuracy change from 82.02% on the RTX A4000 to 89.69% on the Quadro P2000 as arising from GPU rounding alone. The response goes further and says the outcome is more sensitive to rounding than to the update model.

The run records contradict the premise that only numerical rounding changed:

| MO-ECRAM SGD on MNIST | Accuracy | Logical initialization hash prefix | Data-order hash prefix |
|---|---:|---|---|
| Original sequential run, seed 0, RTX A4000 | 82.02% | `19f51772c567e748` | `94e43fb28e9bc937` |
| New sequential run, seed 0, Quadro P2000 | 89.69% | `3d627b7d4bc4d4b` | `b7a073918a1db230` |
| Original surrogate/control, seed 3 | 90.20% / 97.84% | `c26b27308e4b2da4` | `5fff2f216a9091ef` |
| New sequential run, seed 3 | 90.71% | `f90ef4cccfef5a43` | `4e5a6996215b367f` |
| Original surrogate/control, seed 4 | 90.17% / 97.79% | `3a256d89118580dc` | `bd5488fc9fe4d638` |
| New sequential run, seed 4 | 87.74% | `254961cdf56ad54f` | `e3d52ceb38c27497` |

The complete paths, metrics and hashes are preserved in [the independent record audit](paper-review-v4/record-artifact-audit.json). The original seed-0 sequential run, original surrogate, and FP-SGD control agree on both hashes. So do the original triples for seeds 1 and 2. Both hashes disagree for the newly appended seeds 3 and 4.

These are meaningful hashes. [run_rev.py](paper/sim/run_rev.py:148) hashes the actual integer permutations consumed during classification training. It separately hashes the saved logical initial weights at lines 203–204. The data hash is not a floating-point training-output hash: different integer permutations cannot be explained as rounding of otherwise identical matrix arithmetic. [memsim_rev.py](paper/sim/memsim_rev.py:313) constructs generators on the execution device, and generates the initial weights there. A shared seed value is consequently insufficient evidence that the realized inputs matched across these runs. PyTorch itself limits reproducibility guarantees across platforms and describes repeatable random sequences in the context of the same environment. [Official PyTorch reproducibility documentation](https://docs.pytorch.org/docs/2.14/notes/randomness.html).

The exact reason the random realizations changed has not been isolated. The hashes establish that they changed; they do not reveal how large the initial-weight differences were or identify a particular CUDA implementation as the cause. That distinction is enough to reject the exclusive rounding attribution.

The arithmetic in the five-seed extension is correct. Independently recomputing it gives:

| Reported comparison | Mean gap/change, percentage points | Nominal 95% interval |
|---|---:|---:|
| Sequential minus FP-SGD performance gap | 11.042 | [5.979, 16.105] |
| Surrogate minus FP-SGD performance gap | 11.510 | [4.875, 18.145] |
| Sequential gap minus surrogate gap | −0.468 | [−2.864, 1.928] |
| Same change after substituting the new seed-0 run | −2.002 | [−7.285, 3.281] |

Here a positive performance gap means lower analog accuracy. The first row combines old sequential seeds 0–2 with new sequential seeds 3–4. The implementation in [analyze_rev3.py](paper/revision3/analyze_rev3.py:128) joins by seed and does not enforce initialization or data-order equality. The last two nominal intervals therefore cannot be interpreted as isolating the effect of changing the update method under the advertised matching. They also combine execution environments without a matched control on the new hardware.

The large observed deficits still make poor performance of this SGD configuration a reasonable descriptive conclusion. But “FAIL under either update at five matched seeds” and the change from “material” to “not material” need narrower wording until the controls are repaired. Changing the interval formula alone would not isolate the update effect.

The three new probe-training runs also all have different initialization hashes from their earlier E3 counterparts. The MNIST probe additionally has a different data-order hash; CIFAR and LM retain that hash. Their final metrics are 96.98% versus 97.22%, 61.77% versus 61.59%, and 2.88772 versus 2.93779 bits per byte, respectively. The manuscript should describe these as fresh training realizations. Final metrics alone do not establish that their intermediate array states differed only “slightly” because of rounding.

This does **not** break the within-probe comparison: all three update methods start from the same saved state within each new probe, and sequential/literal draws share the intended firings. Nor does it undo the original three-seed training comparison, whose matching still checks out.

**Correction.** Remove the rounding-only explanation from the paper and response. Mark the new five-seed calculation as an unmatched, mixed-environment diagnostic, and avoid using it to resolve the controlled update-effect question. If that question must be resolved experimentally, run FP-SGD, surrogate and sequential arms with verified identical logical initialization and example order within each seed, with each comparison on the same hardware. Persist portable initial tensors and ordering arrays if cross-machine replay is required; also audit device-population matching where relevant. Make the analysis reject mismatched hashes before producing a result labelled matched. The earlier matched three-seed result can remain as it is, with its broad intervals and stated limits.

**2. Medium priority: the release recipe omits the raw draws that make the new analysis auditable**

All 12 new `.npz` files are present and accessible under [the external draw directory](paper/draws/rev3). Their hashes match the corresponding probe summaries. Together they occupy 81,905,772 bytes, approximately 78.1 MiB. Each contains the surrogate, sequential and literal update draws plus the requested update, expected pulse update and initial state.

However, [PUBLISHING.md](paper/PUBLISHING.md:43) tells the owner to release the paper directory and selected lane files. None of those instructions includes this external directory, and there are no `.npz` files under the paper directory. The [availability paragraph](paper/tex/body.tex:12) lists the run JSON records and scripts but does not explicitly include the draws.

Following that recipe would preserve reported answers and their file hashes, while omitting the data needed to independently recalculate the paired uncertainty or replace the dependence statistic. A hash identifies a missing file; it cannot reconstruct it. This is a release-preparation issue: the paper correctly says nothing has yet been deposited publicly.

**Correction.** Explicitly include the 12 draw files in the research-data deposit, give them portable relative paths, retain the current hashes, and include a short command that reconstructs Tables 6–7 from the deposited arrays. Check the release inventory against the filenames referenced by the probe summaries. They can remain outside the Git repository if the data deposit carries them. Their absence from the separate arXiv LaTeX archive is not itself a problem; that archive has a different purpose.

**What now checks out**

The new pulse analysis is reproducible. An independent CPU calculation from the saved arrays agrees with the recorded mean errors, independent and paired sampling floors, excess errors, gain ratios, variance-ratio medians, bootstrap quantiles, and per-pair dependence summaries, within the audit's numerical tolerance. All 12 array hashes match. The audit used a separate NumPy formulation and the recorded bootstrap seeds, without importing the project's analysis functions. [Calculation and results](paper-review-v4/draw-audit.json).

| Update comparison | Probes meeting registered point criteria | Also meeting the reported bootstrap criteria |
|---|---:|---:|
| Aggregate surrogate versus literal stream | 10/12 | 1/12 |
| Sequential approximation versus literal stream | 12/12 | 6/12 |

The sequential paired floor is now correctly based on the variance of the draw-by-draw difference. Its point excess reaches about 0.015, but the largest bootstrap upper value is about 0.286. The paper appropriately separates passing its registered diagnostic from establishing equivalence. The bootstrap criteria cover the reported excess and gain bounds; the variance-ratio condition still uses a point estimate.

The revised dependence analysis also resolves the substantive objection. Its largest empirical null-adjusted RMS is about 0.345, and its largest sign-aligned mean correlation is about 0.208. Six probes exceed the stated 0.05 excess criterion. The earlier pooled signed statistic stays small because it allows cancellation; version 4 now acknowledges that it cannot establish uniformly small dependence. These are update-level empirical diagnostics, not a calibrated prediction of training loss.

The earlier training-label finding is correctly incorporated: CIFAR Li-ECRAM c-TTv2 changes from PASS to UNRESOLVED when both arms use the same three seeds. The two close mean-order reversals are now reported. Neither crosses the preregistered separation requirement for a material rank reversal. There is no longer an unconditional ranking-preservation claim.

The width interpretation is repaired. The paired analysis detects growth for protonic-inspired c-TTv2, while its interval crosses the 2-point margin. Growth beyond that margin remains unexcluded for this arm and Li-ECRAM TTv2. The paper now distinguishes detection of positive growth from establishing its size relative to the margin. It also keeps the LM warning that a shrinking gap can reflect a worsening digital baseline.

The five issues from the preceding review are therefore addressed in their original scope: paired pulse uncertainty, labels and rankings, width interpretation, dependence measurement, and revision documentation. The new matching problem belongs to the additional cross-machine extension. The draw-deposit omission is a narrower remaining availability task.

**Scientific interpretation**

The paper's strongest supported result remains a comparison within a specified simulator: four device/algorithm pairings stay within the chosen margins against FP-SGD across all three tasks, while none does so against separately tuned Adam across all tasks. The best analog language-model result remains about 23.36% worse in bits per byte than Adam. Those statements have a clear baseline, task scope, and decision rule.

All 1,011 previously audited experiment/probe records are byte-for-byte unchanged. The ten previously reviewed simulator, runner, sweep and check files included in the source comparison are also unchanged. The new findings give no reason to discard the earlier table arithmetic. They do require retaining the simulator boundary around the scientific conclusion.

The fidelity experiments strengthen understanding of that boundary, but do not yet validate the entire aggregate training procedure against literal pulse hardware. The two most clipped output probes fail the surrogate's point criteria. Most probes do not meet its bootstrap criteria. Convolutional updates and the LM training trajectory still lack the corresponding full training comparison. The sequential stream itself approximates write noise and bound application. Version 4 largely states these limitations correctly; further experiments would support stronger claims rather than being necessary to publish the present bounded result.

The energy section remains a conditional estimate for weight-matrix operations, combining ideal-read accuracy with borrowed analog-inference efficiency. The reported 17.9–32.4× range should retain those conditions wherever it appears. It does not establish measured system training energy or energy to reach an equal final quality. The current section makes these distinctions substantially clearer than the original version.

The historical memistor connection, device catalog, controlled algorithm comparison and explicit separation of measured, fitted and assumed quantities give the paper useful substance. Its most convincing presentation is as a reproducible simulation study that identifies where device and update assumptions matter, with a roadmap to hardware validation.

**Presentation and artifact checks**

Both current PDF variants contain 41 pages. All pages of the main PDF were rendered and inspected; text-bound checks found no off-page characters or unresolved `??` markers in either PDF. The preserved build diagnostics report no undefined citations/references, multiply defined labels, or overfull boxes. This review did not rerun the compiler.

The arXiv source archive contains 69 regular files. The text sources match the current corresponding files. Seven regenerated figure PDFs have different file hashes, but their decoded page-content streams and extracted text match the corresponding source figures. The differences do not indicate changed plotted content. The submission abstract is 1,893 characters. Its digit sequence matches the HTML abstract, the revised body numbers checked are present, and no raw revision-number macros remain in the HTML. The earlier HTML macro omission has been repaired.

Three small presentation changes would help:

- Table 6 on page 17 uses approximately 6.82-point text, and Table 7 about 7.18 points. Split Table 6 by method or move secondary columns into a companion table so the central evidence can be read comfortably in print. Page 20 has only a short text continuation before a large blank area; float placement could be improved at the same time.
- In the abstract, qualify “meets preset lines on 10 of 12 probes” as meeting **point-estimate** criteria. The body is careful, but the abstract currently omits the much weaker bootstrap result. Keep “(95)” in Table 6 explicitly tied to excess/gain bounds; it is not a joint 95% guarantee for every criterion.
- The abstract still says “after two independent reviews,” while the revision history and availability section describe three. Use the current count or remove the count.

**Recommended disposition.** Correct the cross-machine attribution and pairing claim, add the draw files to the deposit recipe, and make the small presentation changes. The earlier repairs should remain closed. The manuscript then has a credible, appropriately limited simulation contribution without requiring a new claim of physical equivalence.

Review evidence and independent scripts are saved in [this review folder](paper-review-v4). Project sources and artifacts were left unchanged; no training, GPU workload, project test suite, or build was launched.
