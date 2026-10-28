**Independent technical review of the memistor training paper**

Reviewed on October 26, 2026. Manuscript: [Can memistor-class electrochemical weights train neural networks?](paper/build/main.pdf), 31 pages, October 2026, by Questeria and Claude (Anthropic).

**Assessment: major revision before submission.** The paper has a worthwhile organizing question, unusually inspectable run records, and a useful attempt to connect historical devices, modern electrochemical memories, training algorithms, and hardware experiments. Its current numerical results should be treated as exploratory results from a particular simulator. They do not yet establish the proposed hardware specifications or the advertised system training advantage.

The most consequential problems are demonstrable in the implementation: the supposedly matched controls have different initializations and training orders; the selected TTv2 and chopped-TTv2 configurations use an effectively instantaneous physical reset that their counted pulses do not implement; and the catalog does not preserve several properties of the published device presets it borrows. These issues affect central comparisons. Editing the abstract alone will not resolve them.

The arithmetic is substantially better than the experimental interpretation. Independent recalculation from 320 main-experiment records reproduced all 60 device/task/algorithm gap means, intervals, and classifications. Recalculation from 90 width-experiment records reproduced all 24 corresponding gap intervals. There were no discrepancies at a tolerance of 1e-10. This verifies the transformation of those records into results, not the validity of the experiments that generated them.

**Scope and evidence**

The review covered the complete extracted manuscript, rendered pages and figures, simulator, task and run code, statistical functions, experiment plan, deviation record, energy model, device catalog, selected supporting hardware files, and primary literature. Small CPU checks exercised constructors and device updates; no training jobs, GPU workloads, cloud rentals, or project test suites were run. The manuscript and repository sources were not edited. Review scripts, outputs, and source hashes are preserved alongside this report.

The reviewed PDF SHA-256 is `f034316344073c67d7ec0b8f3b2a00afc7a91b2efc9b5852e3732579725d646b`. Local source history shows the plan and principal simulator committed at `a07963c9c` on October 25 at 13:33:17 EDT. This supports the documented sequence but is not an independently authenticated public registration timestamp.

**What is valuable and should be retained**

- The distinction between a physical memistor, its modern electrochemical relatives, and the later two-terminal memristor gives the paper a coherent historical motivation.
- The main table exposes unfavorable results and unresolved intervals. The acknowledgment that no single device/algorithm pairing passes all three tasks is particularly useful.
- The paper reports that its initial width-growth hypothesis did not survive a different tuning protocol. Preserving that correction strengthens the work.
- The catalog labels many assumptions, and the limitations section recognizes ideal reads, small models, uncertain device parameters, and inference-chip energy extrapolation.
- The saved configurations and generated tables make independent arithmetic checks possible. Mutation testing is a useful implementation practice, provided it is not presented as validation of the physical model.
- Hardware characterization followed by prediction before a hardware experiment is an appropriate direction for a simulation study.

**Priority of the findings**

| Finding | Severity | Evidence status | Principal consequence |
|---|---|---|---|
| 1. Initialization and data order are not matched | Blocks the claimed controlled comparison | Source inspection and isolated CPU reproduction | Seed-paired controls do not hold the intended conditions fixed |
| 2. Accumulator reset is physically inconsistent with its pulse charge | Blocks device and hardware conclusions for reset-based arms | Source inspection and numerical counterexample | Algorithm dynamics and reset cost are not those of the stated pulse model |
| 3. Borrowed device presets are changed without an equivalence demonstration | Major | Source compared with official AIHWKIT documentation | Device-specific rankings cannot be attributed directly to the published fits |
| 4. Pulse approximation lacks fidelity and clipping checks | Major | Mathematical and source analysis | Claims of exact mean updates and conservative noise are too broad |
| 5. Specification thresholds are conditional and partly confounded | Major | Manuscript, equations, plan, and saved results | The roadmap's pass criteria are not established device qualification criteria |
| 6. Width verdict is not a test of equivalence or a scaling law | Major | Statistical rule and reported numbers | FLAT includes insufficient or non-monotonic evidence |
| 7. Accuracy and algorithm comparisons need stronger baselines | Major | Tables and run definitions | Near-digital needs an explicit optimizer and tolerance qualification |
| 8. Energy is a conditional subsystem projection | Major | Independent arithmetic and primary sources | 32x today is not demonstrated system energy to matched quality |
| 9. Validation and historical claims exceed their evidence | Major wording and scope issue | Manuscript and cited literature | Outcome resemblance does not validate all algorithms or real devices |
| 10. Registration and analysis differ in unlogged details | Reproducibility issue | Plan compared with implementation | Confirmatory and revised analyses need a complete distinction |
| 11. Hardware roadmap needs prediction and endurance revisions | Major before use as a specification | Statistics, pulse accounting, and bench source | Proposed hardware acceptance tests can misclassify devices |
| 12. Related work and release package need completion | Submission issue | Current primary literature and local documents | Novelty and reproducibility are not yet stated adequately |
| 13. Presentation needs focused restructuring | Editorial | Rendered PDF | Important assumptions are harder to find than headline results |

**1. The control arms do not share the claimed initialization and data order**

The manuscript states on page 6 that the floating-point baseline uses the same initialization and data order. The implementation initializes a single generator and passes it to the model and to training-data sampling. Device construction, initial programming noise, additional A arrays, pulse sampling, reset noise, and chopper decisions all consume that same stream. The exact-update arm skips several of those draws.

The first layer's requested initial matrix can agree. Once device-specific random numbers have been consumed, the second and subsequent matrices do not. The training permutation already differs before training begins; subsequent epochs and language-model window sampling also depend on the random numbers consumed by the different update algorithms. Changing the device or algorithm therefore changes multiple experimental factors simultaneously.

An isolated CPU construction check with seed 0 reproduced this for the actual MNIST MLP. For device SGD, TTv2, c-TTv2, and AGAD versus exact SGD, equality of requested initial matrices was `[true, false, false]`. None of their first-epoch permutations equaled the exact-update permutation. This check did not load data or train a model. The GPU draw sequence was not replayed, but the branch-dependent generator consumption is explicit in the shared source.

Evidence: [generator setup and data sampling](paper/sim/run.py:95), [weight and tile initialization](paper/sim/memsim.py:189), [initial programming noise](paper/sim/memsim.py:108), and [isolated check results](paper-review/implementation-checks.json).

This does not prove that the reported mean improvements reverse, or make every interval mathematically meaningless. Differences between seed-indexed runs can still estimate a difference in expectations. It does mean the experiment is not the matched intervention described in the paper, and its variance reduction and causal interpretation cannot be assumed.

Use independent generators for logical initialization, sample ordering, device variation, write noise, and chopper randomness. Create the logical initial state once per seed and explicitly copy it into every arm, allowing only the intended device programming error. Preserve hashes of logical initialization and data indices. Redo affected comparisons after this correction; existing results can remain as clearly labeled preliminary results.

**2. The selected reset is not implemented by the pulses that are charged for it**

Pages 5 and 30 describe reset-based TTv2 and c-TTv2. In the source, reset assigns `A.u` directly to the analytic symmetry point plus one noise draw. It then adds `2 * BL`, or 62, pulses per reset weight to the pulse counter. It does not apply those pulses through the device dynamics. Both selected TTv2 and c-TTv2 configurations use this reset; the selected AGAD configuration does not.

For the nominal protonic parameters, take 1,000 levels, asymmetry 0.05, gamma 0.2 in each direction, and no noise or spread. The paper's equations give a symmetry point of 0.125. Starting at u = 0.8:

| Operation | Final u |
|---|---:|
| Apply the counted 31 up and 31 down pulses through the simulator's own device equation | 0.783466 |
| Execute the implemented reset | 0.125000 |

The counted pulses leave 97.55% of the displacement from the symmetry point. In the same continuous model, reducing displacement 100-fold takes approximately 11,513 alternating pulses, about 186 times the charged count. This is a single-device counterexample, not a replacement whole-system energy estimate. Increasing pulse energy alone would not repair the change in learning dynamics or timing.

Evidence: [pulse dynamics](paper/sim/memsim.py:116), [direct reset and accounting](paper/sim/memsim.py:282), and [numerical verification](paper-review/implementation-checks.json).

There is also an algorithm identity issue. Published TTv2 accumulates on A, reads it into H, and issues thresholded updates to C; the original description resets the relevant H elements and uses single-pulse C updates. It does not specify the paper's recurring direct reset of A. The manuscript's retained H remainder and up-to-31-pulse transfer are additional variants. These may be legitimate research choices, but should be named and validated as variants. Matching a TTv1 benchmark does not validate them. See [Gokmen 2021, TTv2 Algorithm](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2021.699148/full).

Implement the published algorithm as a reference. If reset is retained, implement an actual characterized reset primitive, including its residual error, pulse sequence, latency, energy, and endurance cost. Compare published TTv2, the no-reset local variant, and the physically implemented reset variant. Reassess the selected c-TTv2 result and the specification sweeps after that comparison.

**3. The device catalog is an adaptation of published presets, not a demonstrated equivalent fit**

The Li-ECRAM and MO-ECRAM entries copy familiar AIHWKIT step and slope values. However, the official presets have shifted hard bounds: Li-ECRAM uses approximately [-0.8276, 1.1724], and MO-ECRAM [-0.8286, 1.1714]. They also specify nonzero slope variability. The paper's Tile uses nominal bounds [-1, 1], and these catalog entries omit slope spread, leaving `gamma_d2d = 0`. A change of coordinate can preserve a device model, but requires transforming the step functions, reference, and bounds consistently. That equivalence is not demonstrated here. [Official AIHWKIT preset definitions](https://aihwkit.readthedocs.io/en/latest/api/aihwkit.simulator.presets.devices.html).

The difference matters because signed weight range, state-dependent step size, saturation, and distributions of symmetry points determine training behavior. Copying several numerical fields into a different parameterization is insufficient to inherit the original fit's physical interpretation.

The protonic entry is more explicitly hypothetical: asymmetry, saturation, write noise, and several spreads are estimates, and finite published retention is replaced with no drift. That openness is good, but the abstract and conclusions should consistently describe a protonic-inspired scenario. A thousand applied pulses is not by itself a demonstration of a thousand independently distinguishable, reliably programmable states.

Evidence: [catalog definitions and provenance](paper/sim/devices.py:54), [tile bounds and slope variation](paper/sim/memsim.py:79).

Pin the AIHWKIT version, provide the mapping algebra, and overlay mean potentiation/depression curves, their scatter, bounds, and alternating-pulse equilibria against the source model. For estimated parameters, propagate plausible ranges instead of presenting one point as a device property. The unrun AIHWKIT cross-check would now address a substantive uncertainty rather than provide optional reassurance.

**4. The pulse surrogate is useful, but its fidelity is not established**

The simulator samples independent Poisson coincidence counts and solves a continuous differential equation for aggregated positive and negative pulses. That solution is exact for its continuous surrogate. It is not exact for a sequence of discrete state-dependent pulses: order matters, the product of discrete update maps is not an exponential, and hard-bound clipping occurs at different times.

For example, with 20 levels, gamma = 1, zero asymmetry and initial u = 0.4, one up pulse followed by one down pulse gives u = 0.314; reversing their order gives 0.334. The continuous batch expression gives about 0.32749. This alone does not establish unacceptable training error, but it demonstrates a discrepancy in the coarse-device regime used for the reference-offset validation.

The statement that larger Poisson variance is conservative also needs narrowing. A scalar variance inequality does not imply a pessimistic learning outcome. Shared row and column pulse streams create correlations between crosspoints; independent per-cell Poisson draws discard them. Greater independent noise can sometimes regularize rather than worsen optimization. The source's write-noise variance uses local steps at the start of the batch, not the changing steps along the trajectory.

There is a separate clipping problem. `pulse_counts` balances two scaling factors and then clamps both streams to [-1, 1]. It does not guarantee the advertised exact requested pulse mean whenever the pre-clamp probabilities exceed one. Exactness requires `(lr / k_nom) * max|x| * max|d| <= BL`, with `lr` here including the caller's alpha conversion. For a single x = d = 10, lr = 0.1, k = 0.002, the intended mean is 5,000 coincidences but clipping limits it to 31. This synthetic case establishes the missing guarantee; existing records do not establish how often clipping affected the reported training runs.

Evidence: [pulse probability scaling and clipping](paper/sim/memsim.py:158), [aggregated dynamics and noise](paper/sim/memsim.py:116).

Compare the surrogate against a sequential pulse implementation on small matrices and selected training cells. Vary batch size, levels, asymmetry, write noise, and saturation. Record clipping rates and lost update magnitude by layer. Set an explicit acceptable error for this approximation before relying on it for device thresholds.

**5. The specification sheet cannot yet be used as a hardware pass specification**

The manuscript itself identifies the central problem: the specification experiment fixes the device to the FP learning rate even though the width experiment shows that this rate can be inappropriate. Most absolute specification entries are consequently undefined. The added degradation sheet is transparently labeled post hoc, but it answers a different question: how much worse a device can get relative to an already imperfect base.

At CIFAR width 32 the base gap is about 2.39 percentage points. Allowing an additional 2 points can admit a gap near 4.39 points from FP. Stage 1 nevertheless presents the degradation thresholds as pass criteria for TTv2-class training. This changes a conditional sensitivity result into an acceptance specification. The paper should not instruct a fabrication group to treat that region as sufficient for the original near-FP objective.

The parameter sweeps have an additional structural confound. For equal slopes gamma, the paper's symmetry point is `u* = a / (2 gamma)`. At gamma = 0.2, asymmetry values 0.05, 0.2 and 0.4 put the symmetry point at 0.125, 0.5 and 1.0. At a = 0.4 the nominal reference reaches the upper bound, eliminating positive signed weight range. Training collapse then combines update asymmetry with loss of representable weights. It does not isolate a universal 20% asymmetry limit. For very small positive gamma, the same issue can occur, so the roadmap's broad `0 < gamma <= 0.5` interval is not established by the tested grid.

The blanket statement that devices must saturate is also too broad. It concerns the accumulator dynamics of the selected TT-family configuration; it is not a general physical necessity for neural-network training. A sufficiently precise symmetric linear update can implement SGD. A near-zero slope should be assessed with a matched algorithm and adequate weight range.

The joint LM width-64 specification has mean gap 4.74%, but its reported interval is approximately [3.51%, 5.98%]. Its pass flag follows the separately predeclared mean-only joint rule, so this is not an undisclosed calculation error. It would be unresolved under the main table's whole-interval rule. These two meanings of pass must be distinguished. Moreover, the joint interval treats the estimated FP mean as fixed, so it omits baseline uncertainty.

Evidence: manuscript pages 13-14 and 20; [joint specification records](paper/records/E5-JOINT.json); [symmetry-point construction](paper/sim/memsim.py:88).

Rebuild the sheet around a physically validated algorithm and a clearly defined tuning policy. Show the signed representable range alongside each parameter condition. Separate absolute accuracy qualification, conditional degradation, and exploratory interpolation. Validate combined candidate specifications with independent device populations and uncertainty that includes the baseline. The present single-seed and adaptively supplemented sweeps are appropriate for exploration, not precise fabrication tolerances.

**6. The width analysis does not demonstrate a flat gap**

The rule labels growth when the endpoint mean difference exceeds the larger of the endpoint interval half-widths and the middle point satisfies a directional condition. It labels shrinkage by the mirror rule and everything else FLAT. This is a predeclared descriptive classifier, not a conventional confidence interval for a slope or endpoint contrast. Comparing a difference with the maximum marginal half-width does not generally account for uncertainty in both quantities or their covariance.

The distinction is visible in Table 5. Li-ECRAM c-TTv2 on the LM goes from approximately -0.55% at width 64 to -13.73% at width 256, yet is FLAT because its middle-width value is slightly higher than its smallest-width value. FLAT therefore cannot mean approximately unchanged. It includes large non-monotonic changes, noisy differences, and potentially inadequate power.

The paper also correctly notices that FP-SGD gets worse at the largest width: 3.100 bits per byte at 256 versus 2.881 at 128. At a fixed short budget, better analog results can reflect optimizer dynamics or insufficient baseline optimization rather than a favorable hardware scaling law. Increasing width while using a width-dependent weight scale is also a particular mapping policy, not a test of every fixed physical mapping.

Evidence: [growth classifier](paper/sim/stats_paper.py:88), manuscript pages 10-12, and [recomputed width gaps](paper-review/record-checks.json).

The supported wording is: "Our predeclared rule did not detect monotonic gap growth across the three tested widths after per-arm learning-rate selection." To claim practical flatness, define an acceptable slope or endpoint change and test equivalence. To discuss scaling, include converged or quality-matched baselines, training curves, greater depth and width ranges, and the effect of weight mapping. Keep the fixed-budget result as a separate operational question.

**7. The main comparison mixes a device study with an optimizer study**

The main table is a valid way to ask a restricted question: what happens when a fixed FP-SGD learning rate is reused for these device/algorithm configurations? It is not sufficient to conclude that plain SGD cannot work on those devices after fair tuning. The paper's own width results establish why this distinction matters. Every device SGD arm fails the particular main protocol; device SGD did not receive the same per-arm optimization opportunity in the main table.

TT-family methods also change temporal filtering and effective optimization. Digital SGD alone cannot isolate the value or cost of the device nonideality from that of the algorithm. Add digital ideal-device versions of the relevant TT algorithms, and a well-tuned digital momentum/Adam baseline. Distinguish accuracy relative to the same optimizer from accuracy relative to an appropriate digital training baseline.

The existing Adam context is informative and deserves more visibility. At base LM width, the saved means are approximately 2.8725 bpb for Li-ECRAM c-TTv2 and 2.3611 for digital Adam. The reported paired relative bpb disadvantage is about 21.66%. Converting the difference of those mean bpb values to perplexity gives a ratio of approximately 1.425, or 42.5% higher perplexity. The analog result is near the selected FP-SGD comparator, not near the stronger digital result in the same study. The Adam arm also needs matched initialization after finding 1 is corrected.

The tolerances are practical noninferiority margins, not exact equivalence. For MNIST, a 2-point accuracy loss from 97.85% permits roughly 4.15% error instead of 2.15%, nearly doubling the error rate. The paper may reasonably choose that margin, but should motivate it rather than equate it with near-identical accuracy.

Finally, the best LM cell is selected after comparing multiple devices and algorithms. Its interval [-4.46%, 1.87%] includes zero; it does not establish superiority to FP. Finding a different winning algorithm for each task also uses test results to construct the all-task device narrative. The manuscript admits there is no common all-task passing pairing, which should remain prominent. Unresolved means insufficient evidence against the margin, not evidence of adequate performance. Use validation to select any proposed deployable pairing, then test it on fresh seeds; keep the full exploratory table available.

Evidence: manuscript pages 6, 9-12 and 19; [main result records](paper/records/RESULTS-PAPER.json); [independent arithmetic checks](paper-review/record-checks.json).

**8. The energy calculation is internally consistent but does not establish a 32x training system**

The central arithmetic checks out. Using the code's inputs gives:

`E_GPU = 6 * 700 / (989.5e12 * 0.405) = 10.4804 pJ per weight-row`.

`E_analog_reads = 4 / (12.4e12) = 0.32258 pJ per weight-row`.

For protonic c-TTv2 on the LM, the modeled remaining terms total about 0.003923 pJ, yielding a ratio of 32.10. The large ratio is therefore largely set by two external efficiency assumptions; changes in simulated pulse counts barely move it. The result is an accounting scenario, not an independent energy measurement of the simulated learning system.

There are five material boundaries:

1. **The measured chip is an inference chip.** The borrowed 12.4 TOPS/W value concerns a PCM speech-inference chip, whereas the proposed system uses ECRAM, backward computations, repeated writes, references, and TT state. The source reports up to 12.4 TOPS/W, not that efficiency for every workload or mapping. [Ambrogio et al., author publication page](https://research.ibm.com/publications/an-analog-ai-chip-for-energy-efficient-speech-recognition-and-transcription).
2. **Chip efficiency is not complete training-system efficiency.** The source's broader system discussion includes mapping utilization, communication and auxiliary digital work. Its reported 6.94 TOPS/W system estimate is a useful alternative sensitivity anchor. Substituting that number while holding this manuscript's other LM assumptions fixed gives about 18.1x, not 32.1x. This is another scenario, not a corrected hardware prediction. [Ambrogio et al., full article, Power and system performance](https://pmc.ncbi.nlm.nih.gov/articles/PMC10447234/).
3. **Accuracy and energy use different read assumptions.** Training quality is obtained with ideal fp32 reads; energy is priced using finite-precision analog hardware. The paper has not shown that the same operating point supplies both the reported accuracy and the assumed efficiency. Quantization, clipping, read noise, tiling, and signal range must be modeled jointly with conversion energy.
4. **The compared workloads and system boundaries are different.** H100 board power and utilization from a very large training run are applied to tiny models and normalized linear work. On the analog side, attention products, nonlinearities, normalization, activation storage, data movement, control, reference maintenance, and static power are not modeled as a complete system. Digital host/network exclusions do not cancel analog exclusions automatically.
5. **There is no energy-to-target comparison.** Failed SGD/device cells still receive essentially the same favorable energy ratio. A system that consumes little energy per operation but does not reach the target quality has not demonstrated cheaper training. The Adam gap and corrected reset costs are central here.

Evidence: [energy inputs and equations](paper/energy/energy_system.py:24), [energy output](paper/records/ENERGY-SYSTEM.json), and manuscript pages 14-19 and 21.

The 15-234x range sets uncertain inputs jointly to favorable or unfavorable extremes, and its high end uses a projected 84 TOPS/W system. It is a scenario envelope, not a confidence interval or measured range. Some device pulse energies are reused estimates across different materials and pulse durations. The "97% reads" result is conditional on those assignments and cannot by itself prove that the ADC/DAC components, specifically, dominate a realized ECRAM system; the borrowed chip number bundles more than conversion.

Keep the model, but rename it a conditional matrix-training energy projection. Replace "32x today" with explicit assumptions. Show an operations and storage ledger, actual array occupancy, a feasible bidirectional read architecture, reset/reference maintenance, digital TT state traffic and leakage, and energy to a stated quality target. The H buffer alone has one digital entry per weight; AGAD adds P and Pref. Capacity and access costs should remain visible when projecting to large models.

**9. The validation is an outcome-level sanity check, and the historical claim remains hypothetical**

The Gokmen-Haensch comparison is useful: the published MNIST experiment reports approximately 2% FP error, 15% analog SGD error, and 2% Tiki-Taka error. The local implementation yields broadly similar numbers. But the original experiment uses batch 1 and explicit read noise, finite input/output resolution, and signal bounds. The local version uses batch 16 and ideal reads. The source itself shows that read-path constraints can contribute to performance gaps. [Gokmen and Haensch 2020](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2020.00103/full).

Matching an endpoint under different sources of error cannot rule out compensating mistakes. The local batch-64 SGD result of 24.32%, versus 14.47% at batch 16, demonstrates substantial protocol sensitivity. Broad predeclared acceptance bands are transparent but do not turn this into comprehensive quantitative validation. A more accurate description is "agreement with selected published outcomes under a simplified read model."

The Rasch check has two seeds per condition and tests an ordering under offsets. It does not establish equivalence of local c-TTv2 or AGAD to the published implementations. Nor does lack of a statistically detected change establish that AGAD is unaffected. The primary paper already studies reference correction, retention, endurance and device requirements, so those conceptual findings are prior art, with this paper potentially contributing a new comparison or interpretation. [Rasch et al. 2024](https://www.nature.com/articles/s41467-024-51221-z).

The statement that accuracy was not an obstacle for Widrow's actual memistor is not supported by a model whose noise, asymmetry, drift and variability are largely unknown or estimated. A hypothetical device consistent with selected optimistic descriptions can be useful, but it cannot settle the historical hardware's accuracy. The pessimistic modeled twin fails, which demonstrates dependence on the assumptions. Replace the categorical historical conclusion with a conditional one and keep the macroscopic energy estimate explicitly assumption-based.

**10. Several analysis changes are missing from the deviation record**

The existing D1 disclosure is helpful. However, comparing the plan with the implementation identifies other departures:

| Item | Plan | Implemented analysis | Treatment needed |
|---|---|---|---|
| Pairwise interaction | `gap(a,b) - [gap(a) + gap(b)]` | Adds the base gap back | The implemented difference-in-differences form is the sensible correction; record it explicitly |
| c2c and reference-error interpolation | Linear interpolation | Log interpolation when both endpoints are positive | Correct the code or document the changed method and recompute affected crossings |
| GPU utilization sensitivity | 30-55% | 38-43% | Explain the narrower range and show the planned range if retaining the registration claim |

Evidence: [plan, sensitivity and energy sections](paper/PLAN-PAPER.md:215), [interpolation function](paper/sim/stats_paper.py:118), [interaction calculation](paper/analyze.py:502), [energy range](paper/energy/energy_system.py:30), and [deviation record](paper/DEVIATIONS-PAPER.md).

These are reporting and reproducibility problems, not evidence of fabricated results or deliberate misconduct. Correcting a mistaken formula is appropriate; a registered study should preserve the original formula and explain the correction. A committed internal plan is still useful. Publish an immutable copy and timestamp, and distinguish it from registration in an external registry.

**11. The roadmap needs a prediction interval and physical operating conditions**

The best feature of Stage 3 is fitting and predicting before measuring hardware training. However, a hardware outcome should not generally be required to fall inside a confidence interval for the simulator's mean. That interval can become arbitrarily narrow with additional simulation seeds even when real hardware variability remains. Use a prediction interval that includes device-population variation, fit uncertainty, training randomness, and measurement noise, and specify the number of independent chips or device populations.

Reference calibration must be characterized as a physical process: pulse count to convergence, remaining bias, variability, duration, and drift. The physical requirement is a stable operating point with enough positive and negative weight range, not only a small scalar reference-error statistic. At gamma = 0.2 and asymmetry = 0.05, the reset example above already demonstrates why a specified pulse budget matters.

The endurance calculation extrapolates an average across weights and the two arrays to 10^10 rows. Average pulse demand does not bound the most stressed cell or array; A and C loads can differ sharply. The recorded totals do not provide per-cell maxima or lifetime distributions. Correct reset physics could also change the exposure substantially. The cited endurance evidence concerns a particular device and pulse regime, not every protonic descendant. Report per-array and per-layer distributions, hot-cell tails, and the required pulse waveform and temperature before declaring a measured endurance figure sufficient.

A retention requirement in training steps is incomplete without a schedule. Convert it using the complete step duration, including reads, transfers, reset/calibration, tiling, stalls and idle time. Declaring 100 seconds effectively infinite based only on nanosecond pulse widths is insufficient for an unspecified architecture or training duration.

For the hobby bench appendix, the proposal is clearly labeled unbuilt in the appendix and source, but the abstract's "a bench replication" can suggest that it was performed. Change that to "a proposed bench replication protocol." The firmware estimates read current from a nominal total chain resistance while the four leads change resistance. The fitter also analyzes increments without checking measured charge equality or rejecting timeout-shortened pulses. Before treating its fitted noise, asymmetry, or energy as metrology, measure the actual read current, retain per-pulse charge, separate read noise from write noise, and reject incomplete pulses. Evidence: [read-current assumption](bench/memistor_bench.ino:36) and [fit logic](bench/analyze_bench.py:39).

**12. The novelty and release claims need to be made current and concrete**

The broad proposition that electrochemical weights can train small networks is already supported by prior hardware and simulation work. Chen et al. report in-situ training on an ECRAM array and larger-network simulations. The introduction should position the contribution as a specific reproducible comparison, carefully calibrated requirements analysis, or historically informed synthesis, rather than as the first answer to the title question. [Chen et al. 2023](https://www.nature.com/articles/s41467-023-41958-4).

A directly relevant preprint appeared on September 29, 2026: **Making Analog Training Scale: Co-Designing Mapping, Optimizer, and Converters**. It reports ECRAM-calibrated simulations up to roughly 123 million Transformer parameters, with finite conversion and device nonidealities. Its weight-gradient path remains digital, so it does not establish the same fully in-memory update objective. That distinction gives this paper a useful comparison to discuss: what computational cost is saved by analog updates, and what accuracy and calibration cost accompanies that saving? It should be addressed in the related work and scaling discussion. [Wu et al., arXiv:2609.36584v1](https://arxiv.org/abs/2609.36584v1).

For the 2026 ACS Nano citation, the publisher's issue page confirms the article metadata. Full text was not accessible during this review, so its specific variability and endurance values were not independently checked here. Those claims should be verified against the article or supplement and mapped to the same normalization used in this simulator. A percentage of absolute conductance, range, or step is not interchangeable. [ACS Nano issue 20(39)](https://pubs.acs.org/ancac3/issue/20/39).

Page 22 says everything is released, while the archive DOI is still to be added; the publishing instructions say nothing has been posted. Use future tense until there is an accessible immutable release. The paper subtree also depends on material in its parent lane, so test the documented reproduction path from the actual release archive on a clean machine. Include versions, source hashes, dataset identities, split offsets, run manifests, configuration defaults, and the software/data licenses. A DOI lookup or successful URL fetch verifies bibliographic existence, not whether the cited passage supports the assigned number.

**13. Presentation and wording**

The PDF is visually coherent. Body text and equations render cleanly; the apparent missing spaces in some text extraction are mostly extraction artifacts, not pervasive visible typography defects. The tables and figures are present, and their broad ordering follows the argument.

The largest presentation problems are information density and the balance between claims and caveats. Table 5 on page 12 and Tables 6-7 on page 14 are small after fitting to page width. Table 9 on page 18 contains enough precision and rows to become difficult to inspect. The Llama 3 author list occupies much of pages 26-28. Use a conventional abbreviated bibliography style, and split or move the densest tables into supplementary material while retaining readable principal results.

The abstract is too crowded and contains too many distinct claims. Its final sentence is especially prone to being read as a completed hardware replication. State ideal reads, the exact-update SGD comparator, and the projected nature of energy early. Reduce the history to the motivation and give the paper one main scientific contribution after the experiments are repaired.

Several specific wording changes would make the current evidence clearer:

| Current wording or implication | More defensible wording |
|---|---|
| Plain SGD fails on every published device and task | Every analog-SGD arm tested at the FP-selected learning rate exceeded the chosen margin |
| The gap does not grow with width | The prespecified classifier did not detect monotonic growth across the three tested widths |
| Two device properties decide | Reference error and accumulator response were influential in this conditional sweep |
| A few hundred levels suffice | Several relative-degradation sweeps tolerated hundreds of nominal levels; absolute thresholds varied and were often undefined |
| The memistor lacked density, speed and energy, not accuracy | An optimistic historical-device scenario attained useful accuracy in this simulator |
| 32x today with the periphery counted | A conditional matrix-operation energy model yields about 32x under borrowed PCM read efficiency and assumed ECRAM update costs |
| A bench replication | A proposed, unbuilt bench replication protocol |
| Every matrix is analog | Learned weight matrices use the analog device model; activation-dependent attention products and other operations remain digital |

The sentence on page 5 claiming every TT-family A learning rate is multiplied by 1/lambda has an exception in the validation TTv1 configuration: eta is 0.01, lambda is 0.02, and `tt_lr_ratio` is 1. State the main-table rule separately from the published-benchmark configuration. Table 3's "mean and range ... as a t-interval" should simply say mean and 95% t interval, with n = 2.

**What the paper can presently claim**

It can report that the saved experiments, under the stated simulator and tuning rules, produced the listed results; that the generated main and width tables agree with those records; that reference error is influential within this particular reset-based model; that learning-rate selection changes the observed width trend; and that borrowing particular chip efficiencies gives a favorable conditional energy scenario. It can provide a valuable proposed experiment program.

It cannot yet claim that the exact published ECRAM devices have been shown to satisfy the proposed qualification sheet, that the implemented TT variants reproduce the published algorithms, that the same physical system achieves both ideal-read accuracy and the projected energy, that a real memistor's historical accuracy was sufficient, or that width scaling is resolved.

**Recommended revision sequence**

1. Preserve this version and its records. Document the initialization, reset, and mapping findings as a new audit record; do not silently replace the old experiments.
2. Correct the random-stream separation and verify matching logical initialization and sample order. Add a physically justified reset or use the published no-reset algorithm. Explicitly label local algorithm variants.
3. Validate device mappings and pulse approximations against an independent reference. This is the highest-value use of additional compute before another large sweep.
4. Run a small matched diagnostic matrix first: exact SGD, analog SGD, ideal-device TT, published TT, and the local variant, on one well-characterized device and one vision/LM case. Choose learning rates on validation with equal selection budgets. Inspect trajectories, clipping, range occupancy and pulse counts.
5. Rerun the primary comparison only after the diagnostics pass. Rebuild specifications using absolute objectives, joint uncertainty, and candidate combined settings. Replace FLAT with a meaningful statistical interpretation.
6. Couple finite read precision and noise to the energy model, and compare energy to a target quality. Keep unsupported architectural parameters as explicit scenarios.
7. Rewrite the abstract and conclusion around the corrected evidence, update related work, complete the deviation ledger, and verify the standalone release.

This sequence preserves the useful work while testing the assumptions most likely to change the conclusions. More seeds alone would make the current simulator's answers more precise without repairing those assumptions.

**Preserved review materials**

- [Independent record recalculation](paper-review/record-checks.json): 60 main cells, 24 width cells, energy arithmetic, and source hashes.
- [Implementation check results](paper-review/implementation-checks.json): matched-control construction and reset counterexample.
- [Implementation check script](paper-review/check_implementation.py): CPU only, no training or source writes.
- [Record check script](paper-review/check_records.py): independent standard-library arithmetic from saved runs.

Unresolved technical questions are the quantitative impact of each implementation correction on final accuracy, the magnitude of pulse clipping in completed runs, fidelity under real read-path nonidealities, and attainable energy on a specified ECRAM training architecture. They require new targeted evidence and are not settled by this review.
