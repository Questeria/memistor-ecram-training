# Can memistor-class electrochemical weights train neural networks?

Code, records and pulse draws for the paper "Can memistor-class electrochemical weights train neural networks?" (Anthony DeMarco, independent researcher; version 14, October 31, 2026).
The study asks, in simulation, how close memistor-class electrochemical weights (Li-ion, metal-oxide and protonic ECRAM) come to
digital training when every weight update is made of device pulses. **All results are simulations**; nothing here is a
measurement of a physical device (the `bench/` folder is a measurement protocol for a future one).

This repository mirrors the author's study folder, so the paths the paper prints resolve as stated, for example, from the
paper directory of the deposit (`paper/`): `python -B revision4/rebuild_draw_tables.py --draws draws/rev3`.

## Layout

| Path | Contents |
|---|---|
| `paper/` | the paper: `tex/` (sources, generated number macros, tables, figures; `tex/v1..v13` are the archived versions), `build/` (built PDFs and HTML, current and `v1..v13`), the plans, deviations and responses, `analyze.py`, `make_figures.py`, `revision*/` (analysis and verification scripts per revision), `sim/` (the repaired simulator, pulse streams, probes and their checks), `pod/` (pod run and build scripts), `energy/`, `cite/` (citation check), `records/` (every run record and result file), `reviews/` (the eleven independent reviews), `draws/rev3/` (the 12 saved pulse-draw archives) |
| `sim/`, `records/` | the first study (lane ME): the original simulator and its checks, the device catalog (`records/CATALOG.json`), the tuned Tiki-Taka choice (`records/TT-CHOICE.json`) and its run records |
| `bench/`, `BENCH.md` | the bench protocol (parts list, Arduino sketch, analysis) |
| `energy/`, `pod/` | lane ME's energy model and pod payload scripts |
| `PLAN.md`, `DEVIATIONS.md`, `VERDICT.md`, `LITERATURE.md`, `README-lane-ME.md` | lane ME's plan, deviations, verdict, literature notes and readme |
| `fetch_data.py` | downloads MNIST, CIFAR-10 and enwik8 into `data/` and checks the digests the paper pins |
| `reproduce_all.py` | regenerates the paper's numbers, tables and figures from the records and compares them byte for byte |
| `ENVIRONMENT.md`, `SHA256SUMS`, `VERIFY.json`, `DEPOSIT-PATCHES.json`, `RELEASE-NOTES.md` | environment, digests of every file, the clean-room verification, the path edits made for this deposit, release notes |
| `REDACTIONS.md` | exactly what was shortened or redacted for privacy in the reviews and the review-3 support files, in which files; the unredacted originals are kept by the author |

Left out on purpose: the pod session records (they hold account identifiers), scratch folders, caches, and the datasets.

## Licensing

- Code (`*.py`, `*.sh`, `*.ino`, build scripts): **MIT** (`LICENSE`).
- Records, the saved pulse draws, the device catalog, text (paper, plans, deviations, responses, reviews) and figures:
  **CC BY 4.0** (`LICENSE-DATA`).
- MNIST, CIFAR-10 and enwik8 are not distributed here; they keep their own terms.
- The independent reviews in `paper/reviews/` are written by ChatGPT (OpenAI) and included as part of the record.

## Environment

See `ENVIRONMENT.md`. In short: runs used torch 2.7.1+cu126 and NumPy 2.2.6 on Python 3.10.12 (pods, RTX A4000) and on the author's
desk (Quadro P2000 / P2200). The same seed draws a different initialisation and example order on a different GPU model
(review-4 finding), so training runs are not re-run here; reproduction starts from the saved records and draws. The analysis and
checks run on CPU with torch, NumPy and matplotlib 3.9.2 (the figures' version).

## Install (CPU)

The clean-room runs (the author's, in `VERIFY.json`, and reviews 8 to 10) used Python 3.13.15, torch 2.7.1, NumPy 2.5.2 and
matplotlib 3.9.2 (the reviews with the CPU build of torch, as below). Python 3.12 or newer is needed (NumPy 2.5.2 requires it).
From the repository root (`reproduce_all.py --sums` skips the `.venv` folder):

    python -m venv .venv
    .venv\Scripts\activate               # Windows (PowerShell: .venv\Scripts\Activate.ps1); Linux and macOS: source .venv/bin/activate
    python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
    python -m pip install -r requirements.txt     # numpy 2.5.2, matplotlib 3.9.2

## Quick start

Run each line from the repository root, in order; the generators overwrite files in place, so run them in a copy.

    python fetch_data.py                 # MNIST, CIFAR-10, enwik8 into data/ (about 0.2 GB), digests checked
    python fetch_data.py --verify-only   # check existing copies
    python -B reproduce_all.py --sums    # checks every file against SHA256SUMS (run it before the generators)
    cd paper
    python -B revision4/rebuild_draw_tables.py --draws draws/rev3      # prints ALL_OK
    cd ..
    python -B reproduce_all.py --fast    # regenerate every number file, table and figure of the paper, byte-compared
    python -B reproduce_all.py           # also the simulators' CPU checks (about 40 minutes)

## What rebuilds what

Derived by `reproduce_all.py` in the author's clean-room run (`VERIFY.json`): 30 of 30 steps passed
(a step passes when its command exits 0 and prints its token if one is required; the files the generators rewrote are then compared
with the deposit's copies: 55 byte-identical, 15 identical after one stated normalisation (figure PDFs: only the creation-date stamp; figure PNGs: same decoded pixels, different compressed bytes across platforms), and 0 with a documented difference (none: version 9 of the paper corrected the one count that differed in version 8, `\RVnDev`, and `paper/revision8/check_numbers_fresh.py` fails on any stale `numbers*.tex`). Docstrings of the older scripts show the author's desk interpreter (`H:/x1000/bench/venv/Scripts/python.exe`):
read it as `python`.

| Paper item | File | Command that rebuilds it |
|---|---|---|
| Figure `fig_arch` | `paper/tex/figs/fig_arch.pdf, .png` | (from `paper`) `python -B revision13/make_fig_arch.py --out tex/figs` |
| Figure `fig_energy` | `paper/tex/figs/fig_energy.pdf, .png` | (from `paper`) `python -B make_figures.py --records records --out tex/figs` |
| Figure `fig:main` | `paper/tex/figs/fig_main.pdf, .png` | (from `paper`) `python -B make_figures.py --records records --out tex/figs` |
| Figure `fig_oat_cifar` | `paper/tex/figs/fig_oat_cifar.pdf, .png` | (from `paper`) `python -B make_figures.py --records records --out tex/figs` |
| Figure `fig_oat_lm` | `paper/tex/figs/fig_oat_lm.pdf, .png` | (from `paper`) `python -B make_figures.py --records records --out tex/figs` |
| Figure `fig:rev_main` | `paper/tex/figs/fig_rev_main.pdf, .png` | (from `paper`) `python -B revision/make_figures_rev.py --results records/revision/RESULTS-REVISION.json --out tex/figs` |
| Figure `fig_scale` | `paper/tex/figs/fig_scale.pdf, .png` | (from `paper`) `python -B make_figures.py --records records --out tex/figs` |
| Figure `fig:validation` | `paper/tex/figs/fig_validation.pdf, .png` | (from `paper`) `python -B make_figures.py --records records --out tex/figs` |
| Number macros | `paper/tex/numbers.tex` | (from `paper`) `python -I analyze.py` |
| Number macros | `paper/tex/numbers_rev.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Number macros | `paper/tex/numbers_rev2.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Number macros | `paper/tex/numbers_rev3.tex` | (from `paper`) `python -B revision3/analyze_rev3.py` |
| Number macros | `paper/tex/numbers_rev4.tex` | (from `paper`) `python -B revision4/analyze_rev4.py` |
| Results record | `paper/records/ENERGY-SYSTEM.json` | (from `paper`) `python -B energy/energy_system.py --runs records/runs/e3 --out records/ENERGY-SYSTEM.json` |
| Results record | `paper/records/RESULTS-PAPER.json` | (from `paper`) `python -I analyze.py` |
| Results record | `paper/records/revision/AIHWKIT-COMPARE.json` | (from `paper`) `python -B revision/compare_curves.py records/revision/AIHWKIT-CURVES.json records/revision/AIHWKIT-COMPARE.json` |
| Results record | `paper/records/revision/D1-ANALYSIS.json` | (from `paper`) `python -B revision/analyze_d1.py` |
| Results record | `paper/records/revision/ENERGY-REVISION.json` | (from `paper`) `python -B energy/energy_rev.py --runs records/revision/runs/e3 --out records/revision/ENERGY-REVISION.json` |
| Results record | `paper/records/revision/RESULTS-REVISION.json` | (from `paper`) `python -B revision/analyze_rev.py` |
| Results record | `paper/records/revision2/RESULTS-REV2.json` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Results record | `paper/records/revision3/RESULTS-REV3.json` | (from `paper`) `python -B revision3/analyze_rev3.py` |
| Results record | `paper/records/revision4/RESULTS-REV4.json` | (from `paper`) `python -B revision4/analyze_rev4.py` |
| Table `tab:catalog` (archived snapshot) | `paper/tex/tables/catalog.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:checks` (in the paper) | `paper/tex/tables/checks.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:e1` (in the paper) | `paper/tex/tables/e1.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:e1b` (in the paper) | `paper/tex/tables/e1b.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:e2` (archived snapshot) | `paper/tex/tables/e2.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:energy` (archived snapshot) | `paper/tex/tables/energy.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:laneme` (in the paper) | `paper/tex/tables/laneme.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:main` (archived snapshot) | `paper/tex/tables/main.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:pairs` (archived snapshot) | `paper/tex/tables/pairs.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:rev_catalog` (in the paper) | `paper/tex/tables/rev2_catalog.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:rev2_fid` (archived snapshot) | `paper/tex/tables/rev2_fid.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:rev2_probe` (archived snapshot) | `paper/tex/tables/rev2_probe.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:rev_selection` (in the paper) | `paper/tex/tables/rev2_selection.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:rev3_dep` (archived snapshot) | `paper/tex/tables/rev3_dep.tex` | (from `paper`) `python -B revision3/analyze_rev3.py` |
| Table `tab:rev3_fid` (in the paper) | `paper/tex/tables/rev3_fid.tex` | (from `paper`) `python -B revision3/analyze_rev3.py` |
| Table `tab:rev3_probe` (archived snapshot) | `paper/tex/tables/rev3_probe.tex` | (from `paper`) `python -B revision3/analyze_rev3.py` |
| Table `tab:rev4_a2m` (in the paper) | `paper/tex/tables/rev4_a2m.tex` | (from `paper`) `python -B revision4/analyze_rev4.py` |
| Table `tab:rev3_dep` (in the paper) | `paper/tex/tables/rev4_dep.tex` | (from `paper`) `python -B revision4/analyze_rev4.py` |
| Table `tab:rev3_probe` (in the paper) | `paper/tex/tables/rev4_probe_seq.tex` | (from `paper`) `python -B revision4/analyze_rev4.py` |
| Table `tab:rev4_probe_sur` (in the paper) | `paper/tex/tables/rev4_probe_sur.tex` | (from `paper`) `python -B revision4/analyze_rev4.py` |
| Table `tab:rev_d1` (in the paper) | `paper/tex/tables/rev_d1.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:rev_energy` (in the paper) | `paper/tex/tables/rev_energy.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:rev_vs_adam` (in the paper) | `paper/tex/tables/rev_main_vs_adam.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:rev_vs_fp` (in the paper) | `paper/tex/tables/rev_main_vs_fp.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:rev_spec` (archived snapshot) | `paper/tex/tables/rev_spec.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:rev_spec` (in the paper) | `paper/tex/tables/rev_spec_p.tex` | (from `paper`) `python -B revision10/derive_rev_spec_p.py` |
| Table `tab:rev_width` (in the paper) | `paper/tex/tables/rev_width.tex` | (from `paper`) `python -B revision/analyze_rev.py` |
| Table `tab:scale` (archived snapshot) | `paper/tex/tables/scale.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:spec` (archived snapshot) | `paper/tex/tables/spec.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:specrel` (archived snapshot) | `paper/tex/tables/spec_rel.tex` | (from `paper`) `python -I analyze.py` |
| Table `tab:catalog` (in the paper) | `paper/tex/tables/v1s_catalog.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:e2` (in the paper) | `paper/tex/tables/v1s_e2.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:energy` (in the paper) | `paper/tex/tables/v1s_energy.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:main` (in the paper) | `paper/tex/tables/v1s_main.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:pairs` (in the paper) | `paper/tex/tables/v1s_pairs.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:scale` (in the paper) | `paper/tex/tables/v1s_scale.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:spec` (in the paper) | `paper/tex/tables/v1s_spec.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:specrel` (in the paper) | `paper/tex/tables/v1s_spec_rel.tex` | (from `paper`) `python -B revision2/analyze_rev2.py` |
| Table `tab:v3s_rev2_probe` (in the paper) | `paper/tex/tables/v3s_rev2_probe.tex` | (from `paper`) `python -B revision3/analyze_rev3.py` |
| Tables `rev4_probe_sur`, `rev4_probe_seq`, `rev4_dep` (probe statistics from the saved draws) | `paper/tex/tables/rev4_*.tex` | (from `paper`) `python -B revision4/rebuild_draw_tables.py --draws draws/rev3`  (prints `ALL_OK`) |

## How to verify

1. `SHA256SUMS` lists every file; the 12 draw files' digests also appear in `paper/PUBLISHING.md` and in each probe record.
2. `python -B reproduce_all.py --fast` (above) and, from `paper/`, `python -B revision4/rebuild_draw_tables.py --draws draws/rev3`
   (which also has `--selftest`: it shows the check failing on a perturbed draw and on a wrong hash).
3. `python fetch_data.py --selftest` shows the data check failing on corrupted copies.
4. `VERIFY.json` holds the author's clean-room result, the secret and privacy scan, and the size check.

## Not re-run by `reproduce_all.py` (and why)

- Every training run: re-training is out of scope, and a rerun on another GPU model is a different realisation (`ENVIRONMENT.md`).
- `paper/cite/cite_check.py`: it re-verifies every reference against Crossref, the arXiv API and live URLs, so it needs the network; its
  result is the deposited `paper/records/CITE-CHECK.json`.
- The LaTeX/pandoc builds (`paper/pod/build_rev*.sh`, `paper/pod/build_payload_rev*.py`): they need tectonic and pandoc; the built PDFs
  and HTML are in `paper/build/`.
- `paper/revision*/verify_findings*.py` and `check_build_v*.py`: the review-time verification scripts as they ran on the author's desk
  (several read the author's git history or desk build trees); kept as record. The pod launch wrappers that need the author's cloud
  account and funds ledger are left out of the deposit.
- `paper/reviews/review-3-support/*` are the reviewer's own check scripts and outputs for review 3; local paths in them are shortened (`REDACTIONS.md`).

## Known defects, kept as run

- The LM runners (`paper/sim/run.py`, `paper/sim/run_rev.py`) draw each window's start with `torch.randint(0, len(tr) - ctx - 1)`, whose
  upper bound is exclusive: the last window of the training slice is never drawn, so the slice's final byte is never a target (review 8,
  finding 4). No held-out byte is involved. The code is kept as it ran: a corrected bound draws other windows from the same seed, and
  the records could no longer be traced to this code. Version 11 of the paper discloses it (Section 3).
- The runners' `samples` field counts every example of an epoch, the incomplete last batch that training skips included (review 8,
  finding 2). Nothing reads it any more: `paper/energy/energy_system.py` counts a run's steps from its layers' row counts.

## Changes since v1.3

v1.4 answers the eleventh review (`paper/reviews/REVIEW-11-chatgpt-20261031-full.md`, a review of version 13; the response, with every
finding verified, is `paper/RESPONSE-TO-REVIEW-11.md`) and holds version 14 of the paper. No experiment was run and no result changed;
the changes are to the text and one new figure. Version 14 cites Byun et al. (Advanced Intelligent Systems, doi 10.1002/aisy.202400543;
`paper/records/CITE-CHECK.json` now verifies 49 references), prints the GPU energy equation with every input range, states the
energy ratio's digital-cost boundary, calls the sensitivity sheet an exploratory device sensitivity analysis (in the subtitle too),
adds Figure 1 (`paper/revision13/make_fig_arch.py`, checked against the simulator by `paper/revision13/check_fig_arch.py`; both are
steps of `reproduce_all.py`), adds a control ladder and computational follow-ups, and moves correction history from the main text
into Appendix F. `RELEASE-NOTES.md` lists every change.

## Changes since v1.2

v1.3 answers the tenth review (`paper/reviews/REVIEW-10-chatgpt-20261029-full.md`; the response, with every finding verified, is
`paper/RESPONSE-TO-REVIEW-10.md`) and holds version 13 of the paper. No experiment was run and no number changed. It corrects this
README's account of v1.2 (below) and its count of the reviews, the start version in Table 11's caption (versions 2 to 11 rounded the
Welch degrees of freedom; version 1 used another width test), and the name check's self-test, which left a PDF open so that its
clean-up failed on Windows (`paper/revision9/name_check_v10.py`). `RELEASE-NOTES.md` lists every change.

## Changes since v1.1

v1.2 answers the ninth review (`paper/reviews/REVIEW-9-chatgpt-20261029-full.md`; the response, with every finding verified, is
`paper/RESPONSE-TO-REVIEW-9.md`) and holds version 12 of the paper. The width study's Welch interval now uses the
Welch-Satterthwaite degrees of freedom themselves (they were rounded down). This corrects all eight Welch intervals (each moves by at
most 0.18 in its units) and turns one verdict (CIFAR, protonic-inspired c-TTv2) from inconclusive to grows, so the count of
inconclusive CIFAR arms falls from 2 to 1; the deviation count becomes 9 (R1 to R9). The paired comparisons are unchanged, and so is
every experimental result outside the width analysis. (The v1.2 README said that no other printed number changed; review 10 found
that wrong, finding 1.) `RELEASE-NOTES.md` of v1.2 listed every change.

## Changes since v1.0

v1.1 answers the eighth review (`paper/reviews/REVIEW-8-chatgpt-20261028-full.md`; the response, with every finding verified, is
`paper/RESPONSE-TO-REVIEW-8.md`) and holds version 11 of the paper. `RELEASE-NOTES.md` lists the changes; no number the paper prints changed.

## Citation

Cite the concept DOI [10.5281/zenodo.23748861](https://doi.org/10.5281/zenodo.23748861), which covers every release (v1.0 holds version 9 of the
paper, v1.1 version 11, v1.2 version 12, v1.3 version 13, v1.4 version 14); `CITATION.cff` has the metadata.

3608 files, 138.3 MB (excluding `SHA256SUMS`).
