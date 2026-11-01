"""Version 15: the EXPECTED edits of revision14/pdf_text_diff_v15.py, (version 14's text, version 15's text) as extracted from
main-arxiv.pdf (reference numbers as [#]), each checked by hand against revision14/edit_15.py and the regenerated tables: the date,
the Agarwal sentence moved before Byun et al. (finding C), Figure 1's derived labels and key and its caption (finding B), the exact
t quantile (Section 3) and the 16 interval endpoints of Tables 4 and 5 it moves by 0.01 (each with its row's mean and label, which
do not change), the reset-read sentence of Section 5 (finding D1), the availability section and the history.  ARTEFACTS lists
line-break and math-extraction differences of unchanged text (none in version 15)."""
EXPECTED = [
    ('October',
     'November'),
    # finding C: Agarwal et al. and the CNN extension before Byun et al.
    ('',
     'Agarwal et al. [#] reached similar conclusions for conventional (SGD) training, and the requirements were extended to convolutional networks [#].'),
    ('Agarwal et al. [#] reached similar conclusions; the requirements were extended to convolutional networks [#], and reviews',
     'Reviews'),
    # finding B: Figure 1 (labels derived from SETTINGS, the key) and its caption
    ('',
     '(not AGAD)'),
    ('',
     '(c = 1 in TTv2)'),
    ('',
     'Selected settings: TTv2: pulse reset of A; c = 1 (no chopper) c-TTv2: pulse reset of A; chopper signs c AGAD: no reset of A; chopper signs c'),
    ('',
     'In the selected configurations (Table 14) TTv2 and c-TTv2 reset A with pulses and AGAD does not reset it; in the common notation c⊙x, c = 1 for TTv2, and c-TTv2 and AGAD use chopper signs.'),
    # finding D2: the exact t quantile, and the endpoints it moves (Table 4: vs FP-SGD; Table 5: vs Adam)
    ('interval.',
     'interval (the t quantile computed exactly).'),
    ('51.64 [31.64, 71.63] F',                       # Table 4, Li-ECRAM SGD, LM
     '51.64 [31.63, 71.64] F'),
    ('73.84 [7.33, 140.35] F',                       # Table 4, MO-ECRAM SGD, LM
     '73.84 [7.32, 140.36] F'),
    ('19.31 [15.06, 23.57] F',                       # Table 4, MO-ECRAM TTv2, LM
     '19.31 [15.05, 23.57] F'),
    ('22.48 [18.93, 26.04] F',                       # Table 4, W/WOx ECRAM TTv2, LM
     '22.48 [18.92, 26.04] F'),
    ('1.60 [0.87, 2.33] U',                          # Table 4, memistor (optimistic) SGD, MNIST
     '1.60 [0.87, 2.34] U'),
    ('1.39 [0.26, 2.52] U',                          # Table 4, memistor (optimistic) TTv2, CIFAR
     '1.39 [0.26, 2.53] U'),
    ('90.33 [60.59, 120.07] F',                      # Table 5, Li-ECRAM SGD, LM
     '90.33 [60.59, 120.08] F'),
    ('11.48 [4.73, 18.23] F',                        # Table 5, MO-ECRAM SGD, MNIST
     '11.48 [4.73, 18.24] F'),
    ('117.64 [35.42, 199.87] F',                     # Table 5, MO-ECRAM SGD, LM
     '117.64 [35.41, 199.88] F'),
    ('1.40 [0.28, 2.53] U',                          # Table 5, MO-ECRAM c-TTv2, CIFAR
     '1.40 [0.27, 2.53] U'),
    ('35.33 [31.48, 39.19] F',                       # Table 5, MO-ECRAM AGAD, LM
     '35.33 [31.47, 39.19] F'),
    ('5.79 [0.66, 10.91] U',                         # Table 5, ideal 1000-level TTv2, CIFAR
     '5.79 [0.66, 10.92] U'),
    ('19.10 [10.33, 27.87] F',                       # Table 5, ideal 1000-level c-TTv2, CIFAR
     '19.10 [10.33, 27.88] F'),
    # finding D1: the reset's extra reads
    ('',
     'The pulse reset’s extra column reads are priced the same way although they do not update H, a conservative approximation: the buffer allowance stands for the arithmetic that turns each reread into a correction pulse count, and without it the analog energy would be at most 0.15 % lower.'),
    # availability
    ('version 1.4 of the archive holds version 14 of this paper,',
     'version 1.5 of the archive holds version 15 of this paper, version 1.4 holds version 14,'),
    ('(release v1.4).',
     '(release v1.5).'),
    ('the eleven independent reviews',
     'the twelve independent reviews'),
    ('RESPONSE-TO-REVIEW-11.md);',
     'RESPONSE-TO-REVIEW-11.md, RESPONSE-TO-REVIEW-12.md);'),
    ('revision13/make_fig_arch.py',
     'revision14/make_fig_arch.py'),
    ('checked against the simulator by revision13/check_fig_arch.py;',
     'checked against the selected settings, the records and the simulator by revision14/check_fig_arch.py;'),
    # history
    ('Version 14 (October 31, 2026; this paper) answers',
     'Version 14 (October 31, 2026) answers'),
    ('',
     'Version 15 (November 1, 2026; this paper) answers a twelfth review, of version 14 and version 1.4 of the archive (RESPONSE-TO-REVIEW-12.md; no experiment was run and no result changed), which recomputed the statistics and the energy accounting from the records and ran the archive’s fast reproduction. Figure 1 and its caption now show the selected settings (TTv2 and c-TTv2 reset A with pulses, AGAD does not; TTv2 has no chopper), and its check takes them from the main experiment’s settings and records; Section 2 cites Agarwal et al. before the Tiki-Taka studies; the ordinary and paired intervals take the exact t quantile, as the Welch interval already did, which moves 16 endpoints in Tables 4 and 5 by 0.01 and changes no classification; Section 5 states that the reset’s extra reads carry a buffer allowance; and outside its reference environment the archive’s reproduction compares its one CPU resimulation of float32 pulse sequences (the AIHWKIT comparison) under a stated numeric tolerance.'),
]
ARTEFACTS = []
EXPECTED = EXPECTED + ARTEFACTS
