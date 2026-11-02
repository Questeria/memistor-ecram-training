"""Version 16: the EXPECTED edits of revision15/pdf_text_diff_v16.py, (version 15's text, version 16's text) as extracted from
main-arxiv.pdf (reference numbers as [#]), each checked by hand against revision15/edit_16.py: the contribution statement's
review count, the availability section and the history."""
EXPECTED = [
    # the contribution statement (both variants): the review count
    ('reviewed versions 1 to 7 of this paper in turn:',
     'reviewed versions 1 to 7 and 10 to 15 of this paper in turn, thirteen reviews in all:'),
    # the abstract's last sentence
    ('This version repairs the simulator after independent reviews and reports how far each repair moved the original results.',
     'The simulator was repaired after independent reviews, and the paper reports how far each repair moved the original results.'),
    # availability
    ('version 1.5 of the archive holds version 15 of this paper,',
     'version 1.6 of the archive holds version 16 of this paper, version 1.5 holds version 15,'),
    ('(release v1.5).',
     '(release v1.6).'),
    ('the twelve independent reviews',
     'the thirteen independent reviews'),
    ('RESPONSE-TO-REVIEW-12.md);',
     'RESPONSE-TO-REVIEW-12.md, RESPONSE-TO-REVIEW-13.md);'),
    # history
    ('Version 15 (November 1, 2026; this paper) answers',
     'Version 15 (November 1, 2026) answers'),
    ('',
     'Version 16 (November 1, 2026; this paper) answers a thirteenth review, of version 15 and version 1.5 of the archive (RESPONSE-TO-REVIEW-13.md; no experiment was run and no result changed), which found the version-15 changes right and no defect in the paper. The contribution statement now counts all thirteen reviews (versions 1 to 7 and 10 to 15) instead of versions 1 to 7, and the abstract no longer says that this version repairs the simulator. The review’s one optional finding concerned the archive’s reproduce_all.py: the negative control of its numeric-policy self-test shifted a printed value by a fixed amount, which for another starting value the policy permits would not change the printed number; the control now computes the shift from the starting value, as the review suggested, to just across the nearest rounding boundary of the printed number and within the stated tolerance.'),
]
ARTEFACTS = []
EXPECTED = EXPECTED + ARTEFACTS
