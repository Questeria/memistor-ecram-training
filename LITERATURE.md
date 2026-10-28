# Lane ME literature check (1960-2026): electrochemical three-terminal weights for training

Read 2026-10-24 20:05-20:30 ET. Quotes are from the fetched texts (pypdf text layers in this lane's scratch); where only a
secondary source or a search abstract was reached, it says so. Nothing here is a lane result.

## 1. Widrow and Hoff's memistor (1960-1963)

- Built: copper plated from a copper sulphate / sulphuric acid bath onto pencil lead; three terminals ("The conductance
  between two of the terminals is controlled by the time integral of the current in the third"). Widrow 1960, Stanford TR
  1553-2 ("An adaptive 'adaline' neuron using chemical 'memistors'", Oct. 17, 1960); the scan has no text layer.
- Widrow's own figures (via Wikipedia 'Memistor', quoting Widrow, Pierce and Angell 1961, TR 1552-2/1851-1): "Reproducible
  elements have been made which are continuously variable (thousands of possible analog storage levels), and which typically
  vary in resistance from 100 ohms to 1 ohm, and cover this range in about 10 seconds with several milliamperes of plating
  current." Sensing by AC, adaptation by DC.
- Hayes 2011 (bit-player, via the research notes): bare lead ~5 ohm, plated ~0.5 ohm; reversible, near linear over a range.
- Mouttet, arXiv:1012.5124 (text read): Widrow's ideal memistor: "the conductance would vary linearly with total plating
  charge ... the plating process be reversible, ... the memistor resistance stay put indefinitely when plating current is
  zero, ... no hysteresis"; Widrow came "very near to this ideal" with "brightener additives to eliminate unwanted hysteresis";
  a linear-region model g = c q_g from Widrow's Fig. 6b (the constant is garbled in the text layer).
- Widrow and Lehr 1990, Proc. IEEE 78(9) (text read): "Madaline I was built out of hardware [78] and used in pattern
  recognition research. The weights in this machine were memistors, electrically variable resistors developed by Widrow and Hoff
  which are adjusted by electroplating a resistive link [79]"; "In the early 1960s, a 1000-weight" Madaline was built
  (the sentence continues on the next column of the scan).
- Why it died (research notes): no multilayer rule (Widrow and Lehr 1990); not integrable (wet cells); Gaines 1967:
  "electro-chemical stores and transfluxors are unreliable or require sophisticated external circuitry".
- NOT found anywhere readable: write noise, up/down asymmetry, retention, endurance. Those are ESTIMATES in this lane.

## 2. What device training needs (the algorithm side)

- Gokmen and Vlasov 2016 (Front. Neurosci. 10:333, text read): the RPU spec for plain SGD at an "acceptable 0.3% error
  penalty" on MNIST: 1,000 levels (600 as a lower estimate), up/down asymmetry tolerance 2 % in the table (5 % global in the
  text), cycle-to-cycle variation of the step up to ~150 %, device-to-device step variation ~110 %, bounds ~80 %, 1 ns pulses,
  projected ~30,000x over a CPU at 84,000 GOPS/W for ~1B weights.
- Gokmen and Haensch 2020, Tiki-Taka (Front. Neurosci. 14:103, text read): W = gamma A + C; A takes the gradient pulses, columns
  of A are transferred into C; it needs A's symmetry point at zero (symmetry-point shifting, sigma <= 0.01); on asymmetric
  devices FCN-MNIST: FP 2.0 % error, SGD ~15 %, Tiki-Taka ~2 %; CNN-MNIST: FP 0.8 %, SGD ~8 %, TT 1.0 %; an LSTM did not reach FP.
  The device model had ~1,000 steps and 30 % cycle-to-cycle noise.
- TTv2 (Gokmen 2021) adds a digital buffer H between A and C; c-TTv2 and AGAD (Rasch, Carta, Fagbohungbe, Gokmen, Nat. Commun.
  2024; abstract only) add choppers to remove the remaining offset (reference) sensitivity and "greatly relax the device
  requirements". Wu et al. 2025 (arXiv 2502.06309, abstract) prove Tiki-Taka as a residual-learning scheme converges exactly to
  a critical point.

## 3. Modern electrochemical devices (published specs)

| device | levels | symmetry / linearity | noise | retention | speed | energy per update | source (how read) |
|---|---|---|---|---|---|---|---|
| Li-WO3 ECRAM (IBM) | up to 1,000 | "symmetric and linear" | fit: 30 % of a step | "good" | 5 ns pulses | ~1 fJ projected at 100x100 nm | Tang et al. IEDM 2018 (abstract) + aihwkit EcRamPresetDevice fit (gamma 0.115 / 0.509) |
| metal-oxide ECRAM (IBM) | ~7,000 small steps (fit) | gamma 0.415 / 0.734 | 200 % of a step | - | - | - | Kim et al. IEDM 2019 via aihwkit EcRamMOPresetDevice |
| protonic PSG/WO3 (MIT) | 1,000 up + 1,000 down pulses | "nearly linear and symmetric" | not given | ~100 s shown | 5 ns at 10 V / -8.5 V | ~2.5 fJ per pulse (gate charging), ~15 aJ proton transfer | Onen et al. Science 2022 (text read) |
| W/YSZ/WOx ECRAM 10x10 | 256 | ANL 0.21 +- 0.05 | c2c 0.8 % (sim. input), d2d 2.3 %, open-loop write error 1.07 % | 20 states shown | 100 ms pulses | - | Chen et al. Nat. Commun. 2023 (PMC text) |
| protonic WO3 ECRAM (2025) | > 1,000 | - | c2c < 3 %, d2d ~15 % | - | - | - | MRS Fall 2025 abstract (search only) |
| organic ECRAM | - | - | "low noise" | - | 20 ns | ~80 fJ per write | Sci. Adv. 2020 (search summary only) |
| Li-ion synaptic transistor LISTA (Sandia) | hundreds | "write linearity" | - | - | - | < 10 aJ simulated at 200 nm | Fuller et al. Adv. Mater. 2017 (Sandia abstract) |

Arrays that trained in situ: 10x10 W/YSZ/WOx (mushroom task, 99.4 %, Chen 2023); 21x21 selector-free ECRAM, 441 devices
(Kwak et al., 2025 slides, unpublished); a 64x64 ECRAM chip with peripheral circuits (Neuronics 2026 abstract). No
electrochemical array has trained a network beyond these toy sizes in hardware; everything at MNIST/CIFAR scale is simulation
on fitted device models (the gap this lane measures).

## 4. How far the device-to-algorithm gap is from closing (before this lane's sims)

Plain SGD wants ~1,000 symmetric levels (Gokmen-Vlasov); Tiki-Taka family algorithms remove the symmetry demand but need a
calibrated symmetry point; published ECRAM/protonic devices report ~1,000 levels at ns pulses and fJ, but write noise and
asymmetry figures are sparse and come mostly from fits; the largest hardware in-situ training is 441 devices.
