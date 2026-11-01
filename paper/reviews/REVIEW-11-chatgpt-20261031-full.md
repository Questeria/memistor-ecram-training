# Review 11 (ChatGPT, of version 13 / main.pdf, 43 pages), pasted by the owner in chat on 2026-10-31 ~19:3x ET

Verbatim copy of the text the owner pasted. The reviewer read the manuscript, checked selected calculations and compared related work; it did
not rerun the experiments or audit the archive. Links with "utm_source" parameters are as pasted.

---

## What the paper is—and my overall assessment

The paper is **“Can memistor-class electrochemical weights train neural networks?”** by **Anthony DeMarco**, with **Claude listed as an AI contributor/coauthor in this copy**. I reviewed the 43-page version dated October 31, 2026.

**It investigates whether neural networks can learn when their adjustable weights are stored in simulated electrochemical memory devices and changed through electrical pulses.** Several device–algorithm combinations perform close to a digital SGD baseline. Performance against the stronger Adam baseline, fidelity to real hardware, and the projected energy savings remain more limited.

**My assessment:** this is a technically serious, transparent simulation study with useful methodological findings. Its strongest contribution is the controlled comparison and examination of simulator assumptions. Its novelty is incremental, and its evidence supports a narrower conclusion than practical competitiveness with GPU training.

Source manuscript: main.pdf

I read the manuscript, inspected its figures and key tables, checked selected calculations, and compared its positioning with primary research papers. I did **not** independently rerun the training experiments or audit the complete code archive. Section, table, and page references below refer to the uploaded paper.

---

## 1. The idea in beginner terms

### Neural networks learn by adjusting numbers

A neural network contains many adjustable numbers called **weights**. Training repeatedly changes those numbers so the network makes better predictions.

On a conventional computer, weights are stored digitally. Computation reads them, calculates changes, and writes updated values.

The alternative explored here is to represent each weight through **how easily electricity flows through a physical device**, called its *conductance*. A programming pulse changes the device’s internal state, changing its conductance and therefore the represented weight.

An array of such devices could potentially perform some neural-network calculations directly where the weights are stored, reducing data movement. The paper connects this idea to Widrow’s **1960 memistor**, an electrochemical device used in early adaptive neural networks, and to modern **electrochemical random-access memory, or ECRAM**. The historical connection is background; the new experiments are simulations. (§§1–3.)

### The difficulty is making reliable adjustments

Imagine trying to tune thousands of knobs when:

- Turning a knob upward changes it more than turning it downward.
- The amount it moves depends on its current position.
- Identical movements produce slightly different results each time.
- Different knobs behave differently.
- Some settings gradually drift.

These are simplified analogies for the device imperfections modeled in the paper.

Ordinary **stochastic gradient descent, or SGD**, can struggle because the requested weight change and the delivered physical change differ. The paper therefore compares SGD with **Tiki-Taka-family algorithms** designed to tolerate such imperfections.

These algorithms use additional arrays and, in some cases, digital buffers or reference estimates to accumulate and transfer updates more reliably. The resulting system is a mixture of analog device operations and digital processing. (§§2.3, 3.3.)

### What was actually tested?

| Task | What the network learns | Scale of the experiment |
|---|---|---|
| **MNIST** | Recognize handwritten digits | A small, fully connected neural network |
| **CIFAR-10 subset** | Classify small images | A convolutional network trained on 10,000 images |
| **Byte-level language modeling** | Predict the next byte of text | A two-layer Transformer trained on a small Wikipedia text sample |

The models have roughly **100,000 to 1 million weights**, depending on the configuration. They are useful research workloads, but this is an early-stage study relative to contemporary large-model training. (§3.5; §6.1.)

The most important modeling choice is that **weight updates are simulated as imperfect device operations, while reading the weights remains ideal, using 32-bit floating-point calculations**. The study principally asks whether the *update mechanism* works under those assumptions. (§3.1.)

---

## 2. What the paper actually found

### A. Four combinations pass its chosen comparison against digital SGD

The paper defines an acceptable performance loss as:

- **2 percentage points of accuracy** for MNIST and CIFAR.
- **5% higher bits per byte** for the language model.

Lower bits per byte means better language prediction.

A result receives **PASS** only when the entire reported confidence interval remains below the permitted loss. **UNRESOLVED** means the experiment does not establish whether the criterion is met. These are practical *non-inferiority* criteria: passing means sufficiently close under the chosen tolerance, rather than identical performance. (§3.6.)

The four combinations passing on all three tasks are:

| Simulated device and algorithm | MNIST gap versus digital SGD | CIFAR gap versus digital SGD | Language-model gap versus digital SGD |
|---|---:|---:|---:|
| **Li-ECRAM + chopped TTv2** | 0.62 percentage points worse | 0.21 points better | 1.45% lower bits per byte |
| **Li-ECRAM + AGAD** | 0.57 points worse | 0.84 points better | 1.13% lower bits per byte |
| **Protonic-inspired + chopped TTv2** | 0.30 points worse | 0.37 points better | 1.53% lower bits per byte |
| **Protonic-inspired + AGAD** | 0.75 points worse | 1.34 points better | 0.04% lower bits per byte |

*These are the reported mean gaps. The PASS decisions also use their confidence intervals. Small favorable means generally should not be interpreted as established superiority, particularly after selecting among many configurations.* (Table 4, p. 14.)

That is a useful result: **under this simulator’s assumptions, certain imperfect electrochemical update models can preserve much of the performance of the selected digital SGD baseline.**

However, “protonic-inspired” matters. Several parameters in that model are estimates, and finite retention is replaced with no drift. It represents a plausible scenario rather than a complete characterization of a particular fabricated device. (§3.4.)

### B. The stronger digital baseline changes the interpretation

The authors also compare against **Adam**, a different optimizer with its own selected learning rate.

On the language task:

- Digital SGD achieves **2.965 bits per byte**.
- Digital Adam achieves **2.366 bits per byte**.
- The best analog configuration remains **23.36% worse than Adam in bits per byte**, with a reported confidence interval of **22.15%–24.58%**.
- **No analog configuration passes the language-model criterion against Adam.** (§4.2; Table 5.)

That 23.36% is a difference in the language-model loss metric. It is not a statement that the model is “23% less intelligent” or makes exactly 23% more mistakes.

**The successful analog configurations largely preserve the performance of SGD in these experiments, while leaving a substantial optimizer-performance gap on the language task.**

The paper deserves credit for including Adam and stating this prominently.

### C. Ordinary device-based SGD performs poorly under the tested settings

Plain SGD exceeds the permitted loss in all **12 combinations of the four contemporary device scenarios and three tasks**. (§4.2.)

There is an important qualification: the main experiments reuse the learning rate selected for digital SGD. Each analog SGD configuration does not receive its own comprehensive tuning.

The supported conclusion is therefore:

> Ordinary pulsed SGD performs poorly with these device models and these settings.

It does not establish that every one of those devices must fail under all possible SGD schedules, pulse budgets, or mappings.

### D. Passing the margin can still allow a noticeable degradation

The MNIST digital SGD baseline is **97.77% accurate**. A two-percentage-point loss would reduce this to **95.77%**.

That changes the error rate from **2.23% to 4.23%**—approximately **1.9 times as many errors**.

The authors explicitly acknowledge this. It means readers should interpret PASS as meeting the study’s selected tolerance, not as demonstrating interchangeable accuracy. (§4.2.)

---

## 3. What I think the paper does well

### It makes the comparisons much more controlled

The revised experiments use matched initial weights and data order, with separate random streams for different sources of randomness. The records reportedly include hashes to check the matching.

This matters because otherwise an apparent algorithm improvement can come from a more favorable initialization or training sequence. (§§3.6–3.7.)

### It distinguishes uncertainty from failure

The PASS / FAIL / UNRESOLVED system is a strength. The current manuscript generally avoids treating “we did not detect a difference” as proof that two methods are equivalent.

For example, its width study now uses an explicit equivalence criterion and carefully limits what the result establishes. (§4.4.)

### It documents corrections and measures their consequences

The manuscript describes substantial problems in earlier versions, including:

- Random streams that did not produce properly matched comparisons.
- A reset operation that moved a device instantaneously while merely charging an assumed pulse count.
- An incorrect translation of published device presets into the simulator.

The current version reports repairs, additional checks, and how the changes affected results. Those historical problems should **not** be presented as undisclosed current defects. The transparent correction record improves the paper. (Appendix F.)

### It contains a useful example of finding a misleading physical explanation

One sensitivity experiment initially appeared to show that strong up/down asymmetry destroyed training.

But changing asymmetry also moved the device’s symmetry point toward a boundary, removing much of its usable signed weight range. When the authors controlled for that range shift, the failure became much smaller: one CIFAR gap changed from **42.92 percentage points to 6.20 points**. (§4.5.)

That is an instructive result. It shows why a device parameter cannot always be interpreted independently of how the neural-network weight is mapped onto the device.

### The numerical spot-checks I performed agree with the paper

The reported catalog PASS counts are internally consistent:

- Against SGD: **14, 6, and 4** for MNIST, CIFAR, and the language model.
- Against Adam: **14, 4, and 0**.

I also recalculated the comparison in Table 9 from its five displayed seed-level results. The stream-minus-surrogate difference is approximately **0.024 percentage points**, with a 95% interval of **−0.467 to +0.515 points**, agreeing with the printed rounded result.

These checks support the accuracy of those summaries. They do not constitute an independent reproduction of the whole study.

---

## 4. The most consequential remaining weaknesses

### 4.1 The main simulator remains only partially validated against more faithful pulse behavior

The fast simulator replaces individual programming pulses with an aggregate approximation. In particular, it uses independent pulse counts for individual cells.

A physical array shares row and column signals. Cells therefore receive **correlated updates**, and the order of pulses can matter when device behavior depends on its current state.

The authors test this approximation, but the evidence is incomplete:

- **10 of 12 probes** satisfy the chosen criteria using point estimates.
- Only **one probe** satisfies the additional reported bootstrap-bound checks.
- Even that flag is not a joint confidence guarantee across every diagnostic.
- Full training comparisons cover MNIST.
- CIFAR comparisons replace the approximation only in the fully connected layers.
- The language model receives update-level probes, but **no full training comparison using the more faithful stream**. (§4.3; Tables 6–10.)

One CIFAR configuration changes from **PASS to UNRESOLVED** when the update method changes. Its mean performance moves only modestly, but the uncertainty becomes too large to preserve the original conclusion.

My interpretation is that **the findings are established most directly as comparisons inside this particular aggregate simulator**. Their transfer to a more faithful physical simulation remains an open question.

**The highest-value next computational experiment would be to validate the successful configurations over complete CIFAR and language-model training trajectories.**

### 4.2 The chosen pulse budget substantially alters some requested updates

The Tiki-Taka accumulator arrays use a learning rate ten times the SGD rate, while each sample is allocated 31 pulse slots.

When the requested update exceeds that budget, probabilities are clipped and part of the requested update is discarded. The paper reports:

- Layer-average losses reaching **57.5%** of requested update mass.
- A worst individual layer record losing **96.4%**. (§4.2.)

This is not a minor perturbation.

It means results can reflect the interaction of **device behavior, learning rate, pulse budget, and update-management policy**. A poor result cannot automatically be attributed to the material. A successful result may also depend on how clipping modifies the effective learning dynamics.

The paper acknowledges this, but a targeted comparison of pulse lengths and update-management policies would make the device comparisons more informative.

### 4.3 Algorithm behavior and device behavior are not fully separated

An interesting control uses an “ideal” symmetric, noise-free, 1,000-level device. Yet some Tiki-Taka configurations perform much worse on it than on imperfect saturating devices.

The explanation is that the chosen algorithm settings use device saturation to provide decay in the accumulator. Removing saturation changes an important part of the effective optimizer. (§4.2.)

The result is useful, but the control does not isolate all sources of error.

I would want a clearer sequence of controls:

1. Exact digital SGD.
2. A digital implementation of the intended Tiki-Taka dynamics, with accumulator decay explicitly specified.
3. Finite pulses and finite levels with otherwise ideal devices.
4. The target device imperfections.
5. Shared-line pulse streams.

That would separate losses caused by the optimizer, pulse discretization, material properties, and simulator approximation.

### 4.4 The “device specification sheet” is exploratory

The title promises a device specification sheet, but the revised evidence establishes relatively few limits:

- The original TTv2 sensitivity analysis establishes no thresholds.
- Chopped TTv2 establishes a few one-variable ranges for CIFAR.
- No language-model threshold is established under the stated rule.
- Most sweeps use only three seeds.
- Joint deviations from the assumed device properties are not established by those one-variable results. (§4.5; Table 12.)

These are useful sensitivity experiments. They are insufficient as manufacturing tolerances.

For example, passing when asymmetry changes alone and passing when reference error changes alone does not demonstrate passing when both change together.

I would call this an **exploratory device sensitivity analysis** and reserve stronger specification language for validated, combined parameter ranges.

### 4.5 The study does not establish favorable scaling

The width experiments are interpreted much more carefully in the current version:

- Only one CIFAR pairing establishes endpoint equivalence within the selected margin.
- Another pairing’s gap grows by **1.76 percentage points**, with a paired 90% interval of **0.15–3.38 points**.
- The language model’s apparently improving relative performance partly reflects the digital SGD baseline getting worse at greater width under the fixed training budget. (§4.4; Table 11.)

The paper appropriately concludes that width dependence remains unresolved.

A stronger scaling study would need training curves, well-tuned controls, larger models, and comparisons at a common achieved quality or convergence criterion.

### 4.6 More seeds would help, but would not solve every uncertainty

Five seeds for the main comparisons and three for sensitivities produce some wide intervals. Selecting attractive configurations from many comparisons also makes the best results look more favorable; the paper explicitly makes no multiplicity correction.

More repetitions would help resolve borderline results. However, narrow confidence intervals over training seeds would still leave uncertainty about:

- Whether the device parameters are correct.
- Whether omitted physical effects matter.
- Whether the update approximation is faithful.
- Whether another dataset or optimizer changes the conclusions.

The paper’s hardware roadmap correctly asks for prediction intervals incorporating these broader uncertainties. (§§6–7.)

---

## 5. How seriously should you take the 18–32× energy claim?

**Treat it as a conditional engineering calculation for selected weight-matrix operations.**

The paper has not demonstrated an operating point that simultaneously delivers its reported accuracy and its assumed energy efficiency.

### Accuracy and energy use different read assumptions

The accuracy experiments use ideal floating-point reads.

The energy estimate assumes efficient finite-precision analog reads, borrowing performance from a **phase-change-memory inference chip**, a different technology and workload. The cited source does support up to **12.4 TOPS/W** chip performance and a **6.94 TOPS/W** projected aggregate figure, with stated system limitations. [Nature](https://www.nature.com/articles/s41586-023-06337-5?utm_source=chatgpt.com)

The missing link is whether an ECRAM training system can achieve the reported accuracy with a realizable read path delivering those efficiencies.

### Most of the projected advantage comes from that borrowed read efficiency

The manuscript says reads account for at least **97% of its modeled analog energy**. (§5.)

I checked the arithmetic. Two matrix-read multiply-accumulates correspond to four conventionally counted operations per weight and training row:

| Assumed read efficiency | Calculated energy for those reads | Ratio to the paper’s 10.48 pJ GPU reference, before write overhead |
|---|---:|---:|
| 12.4 TOPS/W | 0.323 pJ | 32.5× |
| 6.94 TOPS/W | 0.576 pJ | 18.2× |

These are already very close to the reported **17.9–32.4×** range.

Consequently, the new training experiments mainly determine **which simulated configurations qualify for displaying the conditional ratio**. They do not independently establish the ratio’s magnitude.

### Energy per operation is different from energy to reach a useful model

A practical comparison would measure:

> Total energy required to reach the same specified model quality.

That includes the number of training steps, realistic reads, transfers, buffers, reference maintenance, control, and other system costs.

This distinction is particularly important for the language model, where no analog configuration passes the chosen margin against Adam. The manuscript correctly withholds an Adam-relative qualifying energy ratio there. (§5; Table 13.)

### One specific reporting issue needs correction or clarification

Page 23 gives a GPU energy range of **7.05–11.17 pJ** “over” 38–43% utilization.

Using the apparent assumptions behind its central value—approximately 989 TFLOP/s dense BF16 and 700 W—the corresponding range is approximately **9.88–11.18 pJ**. A lower endpoint of **7.05 pJ** is consistent with **500 W at 43% utilization**. NVIDIA’s H100 specifications support the approximate dense throughput and configurable power ceiling used in this reconstruction. [NVIDIA](https://www.nvidia.com/en-us/data-center/h100/?utm_source=chatgpt.com)

This looks like an **omitted power-range assumption in the prose**, rather than a proven error in the underlying calculation. The paper should print the equation and all input ranges.

It should also clarify its digital-cost boundary: page 23 includes a “digital buffer,” while page 24 says “digital TT state” remains outside the ratio. Those statements can be consistent if they refer to different costs, but the distinction needs to be explicit.

---

## 6. How original is it?

**Its contribution is a particular comparative study and a set of methodological lessons within an established research area.**

The closest prior work substantially limits any broader novelty claim:

| Prior work | What was already established |
|---|---|
| **Chen et al., 2023** | Actual ECRAM-array training of a small bilayer neural network, including reported 99.4% mushroom-classification accuracy. |
| **Rasch et al., 2024** | Chopped TTv2 and AGAD, along with analysis of device noise, symmetry, retention, and endurance. |
| **Wu et al., 2026** | ECRAM-calibrated simulations of Transformers up to approximately 123 million parameters, with finite converters and a digital weight-gradient path. |

These precedents are real, and the manuscript generally describes them fairly. Its fully pulsed update focus differs from Wu et al.’s mixed-precision approach. [Nature Communications](https://www.nature.com/articles/s41467-023-41958-4?utm_source=chatgpt.com)

### A particularly relevant paper is missing

I found a close predecessor absent from the bibliography:

**Byun et al., “Device Specifications for Neural Network Training with Analog Resistive Cross-Point Arrays Using Tiki-Taka Algorithms.”**

It appeared online in 2024 and in a 2025 issue. It already examines device specifications for SGD, TTv1, and TTv2 through simulations of asymmetry, retention, state counts, and noise, including a device-requirements table. [Wiley Online Library](https://advanced.onlinelibrary.wiley.com/doi/10.1002/aisy.202400543?utm_source=chatgpt.com)

That is a substantive but repairable related-work omission. The manuscript should explain its additions relative to this study: the selected electrochemical catalog, chopped algorithms, multiple tasks, paired uncertainty estimates, and analysis of simulator repairs.

The specification-sheet concept itself is established prior art.

### Where this manuscript adds value

Its most useful contributions are likely:

- A common comparison across the selected electrochemical device models.
- Quantification of how simulator repairs change conclusions.
- Demonstration that signed weight range can confound an asymmetry sweep.
- Evidence that an approximation can change a performance label.
- A reproducibility-oriented record of assumptions, limitations, and proposed hardware tests.

Those are legitimate research contributions. They are more defensible than a claim of having newly discovered that electrochemical devices can train neural networks.

---

## 7. What I would prioritize next

I would separate improvements to this manuscript from experiments needed for a stronger follow-up.

### Focused manuscript revisions

1. **Add the closest device-specification literature**, especially Byun et al., and sharpen the incremental contribution.
2. **Make the GPU energy assumptions and digital-cost boundary explicit.**
3. **Use sensitivity-analysis language consistently** where device thresholds remain unestablished.
4. **Shorten the main narrative.** The correction history is valuable, but it competes with the scientific story. Keep the final model, decisive comparisons, and remaining uncertainties central; place more historical detail in supplementary material.
5. **Add a clear analog/digital architecture diagram.** Readers should immediately see which arrays, buffers, reads, and calculations are simulated as analog and which remain digital.

The title could also more directly emphasize the distinctive contribution: comparing pulsed electrochemical update models and testing simulator assumptions under ideal reads.

### Highest-value follow-up experiments

| Priority | Experiment | What it would resolve |
|---|---|---|
| **1** | Run the successful configurations with validated, correlated pulse updates over full CIFAR and language-model trajectories | Whether the central results survive a more faithful update model |
| **2** | Introduce realistic read precision, noise, and array effects while tracking energy | Whether useful accuracy and projected efficiency can coexist |
| **3** | Tune algorithms and update management with comparable search budgets | Whether rankings reflect device capabilities or restrictive settings |
| **4** | Refit devices from measured data and propagate parameter uncertainty | How much depends on favorable assumed parameters |
| **5** | Test a small hardware array against predictions made beforehand | Whether the simulator predicts real device training behavior |

Recent protonic-device measurements provide a potential basis for a better-grounded model. For example, Xu et al. report quantified cycle-to-cycle and device-to-device variability, although their measurement definitions would need to be reconciled with the simulator before using those numbers directly. [PubMed](https://pubmed.ncbi.nlm.nih.gov/42915660/?utm_source=chatgpt.com)

The manuscript’s own staged hardware roadmap is sensible, especially its emphasis on characterizing devices and resets before attempting a complete accelerator.

---

## Final review verdict

| Aspect | My judgment |
|---|---|
| **Clarity of the scientific question** | Good, although the title is broader than the distinctive contribution |
| **Experimental discipline** | Strong in matched comparisons, explicit criteria, and correction tracking |
| **Numerical reporting** | Selected checks agree; one energy-assumption clarification is needed |
| **Novelty** | Incremental, with useful simulator and benchmarking lessons |
| **Physical validation** | Limited; major assumptions remain untested in complete training trajectories |
| **Evidence for scaling** | Inconclusive |
| **Evidence for practical energy savings** | Conditional projection |
| **Overall value** | A worthwhile simulation and reproducibility contribution with clear follow-up work |

**I would recommend developing this as a focused simulation and methodology paper.** Its central, qualified finding is supported by the presented results: selected electrochemical update models, combined with chopped Tiki-Taka algorithms, can remain close to the chosen SGD comparator on three small tasks.

The most important next advance is to establish that those successful configurations retain their performance with realistic pulse streams and reads. Demonstrating that—and measuring energy at the same achieved quality—would move the work from a useful simulator comparison toward evidence for a practical training technology.
