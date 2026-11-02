# Publishing the memistor/ECRAM paper: the owner's steps

The code and data archive is published (release v1.0 on 2026-10-28 and v1.1 on 2026-10-29; section 4). Release v1.2, which holds
version 12 (the answer to review 9), was published on 2026-10-29 at 21:38 ET. Release v1.3, which holds version 13 (the
answer to review 10), was published on 2026-10-31 at 19:12 ET (tag v1.3 = 03474b26b; Zenodo version DOI 10.5281/zenodo.23848730,
record 23848730, zip 106,146,105 bytes). Release v1.4, which holds version 14 (the answer to review 11), was
published on 2026-10-31 at 22:18 ET (tag v1.4 = 39c6ed7fe; Zenodo version DOI 10.5281/zenodo.23851109, record 23851109, zip
107,820,671 bytes). Release v1.5, which holds version 15 (the answer to review 12), was published on
2026-11-01 at 01:01 EST (after the 02:00 EDT fall-back) (tag v1.5 = b5f86bed2; Zenodo version DOI 10.5281/zenodo.23852922, record 23852922, zip 109,418,606 bytes). Release v1.6, which holds
version 16 (the answer to review 13), is built and verified and waits for publishing. The
paper is not yet on arXiv: submit version 16 (not 15), after release v1.6 is published.
Submitting it needs your arXiv account, an endorsement if asked, and your acceptance of arXiv's terms, so it is your act: sections 2, 3 and 5.
Everything to upload and paste is in the Desktop folder "memistor paper - arXiv submission (v16)" (SUBMIT-TO-ARXIV.txt there).
Review 13 (ChatGPT, of release v1.5) recommends submission: the round is closed; its one optional self-test fix is in release v1.6, which holds version 16 (the contribution statement counts all thirteen reviews).

## 1. Which file to submit, and why there are two author variants

- **`tex/main.tex`** lists the authors as you asked: "Anthony DeMarco" and "Claude (Anthropic)". Use it for the copy you keep, share
  or post on your own site.
- **`tex/main-arxiv.tex`** lists "Anthony DeMarco" alone. Claude's role is stated in the contribution statement at the end of the
  paper.

Why two variants? arXiv's current moderation policy (fetched 2026-10-25 from
https://info.arxiv.org/help/moderation/index.html, section "Policy for authors' use of generative AI language tools") says:

- "generative AI language tools should not be listed as an author";
- by signing as an author each person takes "full responsibility for all its contents";
- authors must report "any significant use of sophisticated tools", which includes "text-to-text generative AI".

The fetch and the check of this text are recorded in `records/CITE-CHECK.json` (key `arxiv_policy`). Most journals take the
same position (for example Nature's and Science's editorial policies). If you submit to a journal later, check its current
policy page.

Version 8 prints your official name, "Anthony DeMarco", with the affiliation "Independent researcher", in both files (your word of
2026-10-27); there is nothing left to replace. The contribution statement of both variants also credits ChatGPT (OpenAI), an AI
system and not an author, for its thirteen reviews (versions 1 to 7 and 10 to 15). Neither variant prints an email address. arXiv shows the submitter's name, and lets you add an affiliation or leave "Independent researcher".

## 2. arXiv account and endorsement

1. Create an account at https://arxiv.org/user/register (your legal or chosen name, email, and an affiliation, which may be
   "Independent researcher").
2. Choose the category. The primary is **cs.ET** (Emerging Technologies); cross-list to **cs.LG** (Machine Learning) and,
   optionally, **physics.app-ph** (Applied Physics) or **cs.NE** (Neural and Evolutionary Computing).
3. **Endorsement.** A first-time submitter to a category usually needs an endorsement from an established author in it. arXiv
   tells you when you start the submission. It gives you an endorsement code to send to a person who has published in cs.ET
   or cs.LG (for example an author of one of the cited analog-training papers, or a university researcher you know). Ask
   politely and attach the PDF. arXiv explains the process at https://info.arxiv.org/help/endorsement.html.

## 3. Licence

**CC BY 4.0** (Creative Commons Attribution) is recommended. It lets anyone reuse the paper with credit, and it is accepted by
arXiv and by open-access journals. arXiv offers it in the submission form. The code is released under a permissive licence
(MIT, see the repository) and the records under CC BY 4.0.

## 4. Code and data DOI (Zenodo)
<!-- deposit-built -->
**Release v1.6 (2026-11-01 22:44 EST): BUILT and verified, committed LOCALLY as 24be25ce2 in `C:/Projects/memistor-ecram-training` on top of
the published b5f86bed2, NOT pushed. It holds version 16 of the paper, the answer to review 13 (the contribution statement counts
all thirteen reviews; the policy self-test's negative control no longer depends on the starting value; no result changed).**

- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.6`).
- Clean room (reference environment): REPRODUCE_ALL_OK, 31 of 31 steps (57 files identical, 13 after the stated normalisation); 6 of 6 mutation tests caught.
- Python 3.12.3 / torch 2.7.1+cpu (WSL) on the finalized v1.6: REPRODUCE_ALL_OK, 26 of 26 fast steps (58 identical, 11 normalised, 1 within the numeric policy: AIHWKIT-COMPARE.json, 26 float fields differ within the numeric policy)
  (`records/deposit/PY312-FAST.json`; v1.5's records are in `records/deposit/v1.5/`).
- Scan: 0 unjustified. The archived version 15 joins the mirror-address entry, and version 16's record script joins those of
  versions 10, 13, 14 and 15.
- FINAL_CHECK_OK; 3,731 files, 145.3 MB (`records/deposit/`).
- Publishing is one push and one release, as for v1.5 (the same two commands with v1.6 and the new commit):
  `git -C C:/Projects/memistor-ecram-training push origin main`, then
  `gh release create v1.6 --repo Questeria/memistor-ecram-training --target 24be25ce2 --title "v1.6: code, records and pulse
  draws for the memistor paper (version 16)" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.
  The new version DOI comes from Zenodo; the concept DOI stays.

**Release v1.5 (2026-11-01 01:43 EDT): BUILT and verified, committed as b5f86bed2 in `C:/Projects/memistor-ecram-training` on top of
the published 39c6ed7fe; PUBLISHED 2026-11-01 at 01:01 EST (after the 02:00 EDT fall-back), Zenodo version DOI 10.5281/zenodo.23852922. It holds version 15 of the paper, the answer to review 12 (Figure 1's settings, the
reproduction's numeric policy, the Agarwal order, the exact t quantile: 16 interval endpoints move by 0.01; no result changed).**

- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.5`).
- Clean room (reference environment): REPRODUCE_ALL_OK, 31 of 31 steps (57 files identical, 13 after the stated normalisation); 6 of 6 mutation tests caught (M5 and M6 are new: a flipped
  acceptance boolean and a discrepancy past its line in AIHWKIT-COMPARE.json must fail). `reproduce_all.py` gains one step,
  the numeric policy's self-test; Figure 1's two steps now run `revision14/`.
- Python 3.12.3 / torch 2.7.1+cpu (WSL) on the finalized v1.5: REPRODUCE_ALL_OK, 26 of 26 fast steps (58 identical, 11 normalised, 1 within the numeric policy: AIHWKIT-COMPARE.json, 26 float fields differ within the numeric policy). For comparison, release v1.4 itself under the same Python 3.12 setting: 25 of 25 fast steps passed and 69 files matched, 1 differed (paper/records/revision/AIHWKIT-COMPARE.json): REPRODUCE_FAILED, as review 12 found
  (`records/deposit/PY312-FAST.json`).
- Scan: 0 unjustified. The archived version 14 joins the mirror-address entry, and version 15's record script joins those of
  versions 10, 13 and 14; one long keyword identifier in `revision14/verify_findings_12.py`, read by the scan as a
  high-entropy token, is justified as an identifier.
- FINAL_CHECK_OK; 3,671 files, 142.1 MB (`records/deposit/`; v1.4's records are in `records/deposit/v1.4/`).
- Publishing is one push and one release, as for v1.4 (the same two commands with v1.5 and the new commit):
  `git -C C:/Projects/memistor-ecram-training push origin main`, then
  `gh release create v1.5 --repo Questeria/memistor-ecram-training --target b5f86bed2 --title "v1.5: code, records and pulse
  draws for the memistor paper (version 15)" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.
  The new version DOI comes from Zenodo; the concept DOI stays.

**Release v1.4 (2026-10-31 22:13 ET): BUILT and verified, committed LOCALLY as 39c6ed7fe in `C:/Projects/memistor-ecram-training` on top of
the published 03474b26b, NOT pushed. It holds version 14 of the paper, the answer to review 11 (text and one new figure; no
result changed).**

- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.4`).
- Clean room: REPRODUCE_ALL_OK, 30 of 30 steps (55 files identical, 15 after the stated normalisation); 4 of 4 mutation tests caught. `reproduce_all.py` gains two steps: Figure 1
  (`revision13/make_fig_arch.py`) and its check against the simulator (`revision13/check_fig_arch.py`).
- Scan: 0 unjustified. The archived version 13 joins the mirror-address entry, and the record scripts of versions 13 and 14
  join version 10's.
- FINAL_CHECK_OK; 3,609 files, 138.8 MB (`records/deposit/`; v1.3's records are in `records/deposit/v1.3/`).
- Publishing is one push and one release, as for v1.3 (the same two commands with v1.4 and the new commit):
  `git -C C:/Projects/memistor-ecram-training push origin main`, then
  `gh release create v1.4 --repo Questeria/memistor-ecram-training --target 39c6ed7fe --title "v1.4: code, records and pulse
  draws for the memistor paper (version 14)" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.
  The new version DOI comes from Zenodo; the concept DOI stays.

**Release v1.3 (2026-10-31 19:10 ET): BUILT and verified, committed LOCALLY as 03474b26b in `C:/Projects/memistor-ecram-training` on top of
the published 47da42036, NOT pushed. It holds version 13 of the paper, the answer to review 10 (no number changed).**

- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.3`).
- Clean room: REPRODUCE_ALL_OK, 28 of 28 steps (55 files identical, 13 after the stated normalisation); 4 of 4 mutation tests caught.
- Scan: 0 unjustified. Path rule P5 (`REDACTIONS.md`) masks the records' namespace prefix that review 10 quotes in its prose,
  and the archived version 12 joins the mirror-address entry.
- FINAL_CHECK_OK; 3,544 files, 135.4 MB (`records/deposit/`; v1.2's records are in `records/deposit/v1.2/`).
- Publishing is one push and one release, as for v1.2 (the same two commands with v1.3 and the new commit):
  `git -C C:/Projects/memistor-ecram-training push origin main`, then
  `gh release create v1.3 --repo Questeria/memistor-ecram-training --target 03474b26b --title "v1.3: code, records and pulse
  draws for the memistor paper (version 13)" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.
  The new version DOI comes from Zenodo; the concept DOI stays.

**Release v1.2 (2026-10-29, 21:38 ET): PUBLISHED. It holds version 12 of the paper, the answer to review 9.**

- Version DOI **10.5281/zenodo.23788075** (https://zenodo.org/records/23788075; version 1.2, Software, CC BY 4.0; Zenodo dates it
  2026-10-30 in UTC). It has one file, `Questeria/memistor-ecram-training-v1.2.zip`: 104,736,531 bytes, md5
  60185c563156ab2b2f6a60a14546329e (GitHub's archive of tag v1.2). The ZIP was not downloaded for a read-back; the metadata was read
  through Zenodo's API.
- GitHub: https://github.com/Questeria/memistor-ecram-training/releases/tag/v1.2. Branch `main` and tag `v1.2` both point at
  47da4203630b179779a3433861ca5ecc937e05c4 (`git ls-remote`, 2026-10-29).
- Claude published it at the owner's word (2026-10-29: "Yes, publish archive v1.2 now"), by the same two steps as v1.1, with the tag
  pinned to the verified commit. Just before publishing: a clean tree, all 3,490 files equal to SHA256SUMS, and the build files
  byte-identical to `build/`.
- As built (below):

- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.2`; H: is kept for the drive-G backup).
- Clean room: REPRODUCE_ALL_OK, 28 of 28 steps (55 files identical, 13 after the stated normalisation); 4 of 4 mutation tests
  caught.
- Scan: 0 unjustified, after two additions. The archived version 11 joins the mirror-address entry, and an email hit is now masked
  to its domain, because review 9 quotes the account's no-reply address.
- FINAL_CHECK_OK; 3,491 files, 132.4 MB (`records/deposit/`; v1.1's records are in `records/deposit/v1.1/`).
- The concept DOI that the paper cites now resolves to v1.2.

**Release v1.1 (2026-10-29, 13:53 ET): PUBLISHED. It holds version 11 of the paper, which answers review 8.**

- Version DOI **10.5281/zenodo.23773334** (https://zenodo.org/records/23773334; version 1.1, Software, CC BY 4.0, dated 2026-10-29). It has
  one file, `Questeria/memistor-ecram-training-v1.1.zip`: 103,313,523 bytes, md5 02289e95b2e2fe8bbf358ddc0d748f4d (GitHub's archive of tag
  v1.1). The ZIP was not downloaded for a read-back; the record's metadata was read through Zenodo's API.
- GitHub: https://github.com/Questeria/memistor-ecram-training/releases/tag/v1.1. Branch `main` and tag `v1.1` both point at
  aaee0bed81a95bc909a8df34ba3c9a5e8f26c16e (`git ls-remote`, 2026-10-29).
- Claude published it at the owner's word (2026-10-29: "Finish the paper and attachments to be released"), running the steps of
  `Publish the memistor deposit v1.1.cmd` (a copy is in this folder):
  - `git push origin main`, with gh's stored sign-in passed for that one command;
  - `gh release create v1.1`, with the tag pinned to the verified commit.
- Just before publishing:
  - the deposit tree was clean at aaee0be;
  - all 3,437 files matched SHA256SUMS;
  - its four build files were byte-identical to this folder's checked version-11 build.
- Before that, as built: clean room REPRODUCE_ALL_OK (27 of 27 steps; 55 files identical, 13 after the stated normalisation); 4 of 4 mutation
  tests caught; scan 0 unjustified; FINAL_CHECK_OK; 3,438 files, 129.4 MB. The records are in `records/deposit/`; v1.0's are in
  `records/deposit/v1.0/`.
- The paper cites the concept DOI, which resolves to the newest version, so version 11 needs no rebuild.

**Release v1.0 (2026-10-28, evening ET): PUBLISHED by the owner's command; version 10 of the paper carries the DOI.**

- Cite the concept DOI **10.5281/zenodo.23748861** (all versions; https://doi.org/10.5281/zenodo.23748861). Version 1.0 is 10.5281/zenodo.23748862
  (https://zenodo.org/records/23748862; Zenodo dates it 2026-10-29; resource type Software; CC BY 4.0 on the record, MIT for the code as its
  description states; one file `Questeria/memistor-ecram-training-v1.0.zip`, 100,543,489 bytes, md5 8813e49b550ec91f3b7ee1dca166b074,
  which is GitHub's archive of tag v1.0). Version 1.0 holds version 9 of the paper, as version 10's availability section says.
- GitHub, under the author's account: https://github.com/Questeria/memistor-ecram-training; branch `main` and tag `v1.0` are both at
  076624fbc58b2d50041bf88f2549ff58e37ee52d, the commit verified before publishing (`git ls-remote`, 2026-10-28).
- Zenodo's Files panel says "Too many files inside the ZIP file.": its previewer does not list an archive this large (3,338 files).
  It is a display limit; the ZIP downloads whole.

- Where: `C:/Projects/memistor-ecram-training` (repository name `memistor-ecram-training`), a fresh git history of 1 commit ("Release v1.0",
  branch `main`, author Anthony DeMarco with the GitHub no-reply address), pushed by the owner's command (2026-10-28). Built by `make_deposit.py` from an explicit allowlist (this folder);
  the commit hash, file count and sizes are in `records/deposit/FINAL-CHECK.json`. Version 9 of the paper (October 28, 2026) is the one deposited.
- Layout: the deposit mirrors lane ME's folder, so the paper directory is `paper/` and the 12 draws are in `paper/draws/rev3/`; from `paper/`,
  `python -B revision4/rebuild_draw_tables.py --draws draws/rev3` resolves as printed below. The text below is the version-8 plan of the list;
  the deposit holds its own `README.md`, `ENVIRONMENT.md`, `SHA256SUMS`, `VERIFY.json`, `REDACTIONS.md`, `fetch_data.py` and `reproduce_all.py`.
- Published with (2026-10-28, by the owner): double-click `Publish the memistor paper deposit.cmd` (on the Desktop; a copy is in this folder). If `gh` is missing it runs
  `winget install --id GitHub.cli -e` (winget shows its own prompts), if `gh` is not signed in it runs `gh auth login --web --git-protocol https`,
  then it creates the public repository `Questeria/memistor-ecram-training` with `gh repo create`,
  opens https://zenodo.org/account/settings/github/ (sign in with GitHub, accept Zenodo's terms, switch the repository ON), waits for one
  keypress, then runs `gh release create v1.0`. Zenodo mints the DOI within minutes; tell Claude the DOI (cite the CONCEPT DOI).
- Privacy defaults (the owner can reverse them): in the deposit's copies of the reviews and the review-3 support files, local paths are shortened to
  study-relative paths and private project and folder names are removed; `REDACTIONS.md` in the deposit lists every file; the unredacted originals stay with the author.
- Verification (a clean room outside the author's repository with CUDA hidden, the secret and privacy scan, sizes): `records/deposit/VERIFY.json` (also inside the deposit).
  Steps 2 and 3 below are therefore done by the command, except putting the DOI into the paper.

The planned list as written for version 8:


1. Make a public GitHub repository, or a release archive, holding:
   - `ops/x1000-20261023/phase2/memistor/paper/` (sim, pod, records, energy, cite, tex, analyze.py, make_figures.py);
   - lane ME's `sim/`, `records/CATALOG.json`, `records/TT-CHOICE.json` and `BENCH.md`, `bench/`;
   - the 12 pulse-draw files of the update probes (NumPy `.npz`, 81,905,772 bytes together; kept outside git, on the
     desk at `H:/x1000/memistor-paper/rev3/draws/`). Put them in the deposit as `draws/rev3/<name>`. Each holds one probe's
     surrogate, per-sample-stream and literal-stream draws, the requested update, the expected pulse update and the initial
     state. Their SHA-256 (also recorded in each probe record, `records/revision3/runs/fidprobe3-probes/*.probes.json`):

     | file | bytes | SHA-256 |
     |---|---:|---|
     | `fidprobe3__cifar_w32__ecram_mo_kim2019__agad__lr0.001__s0__probe__L3__U600.npz` | 14,738,834 | `9318854e01c1bd3a159735eb0a8036d92fa4c11094a3df3ec56d95acd3ca9310` |
     | `fidprobe3__cifar_w32__ecram_mo_kim2019__agad__lr0.001__s0__probe__L4__U600.npz` | 159,073 | `055713cff7a594af1171c08cb6db03aece29e085a24e22f30e4c6a04a911cec2` |
     | `fidprobe3__cifar_w32__ecram_mo_kim2019__agad__lr0.001__s0__probe__L3__U2000.npz` | 14,756,559 | `367f471bbf363928c428f4345c33343d7be0085bb6ab18632fa2d4eded9844d1` |
     | `fidprobe3__cifar_w32__ecram_mo_kim2019__agad__lr0.001__s0__probe__L4__U2000.npz` | 169,714 | `ecc7d4d3b445ca1781bb92d65f1147f791c2ec6d02a55c03a16882f72b0ad6eb` |
     | `fidprobe3__lm_w128__protonic_onen2022__cttv2__lr0.0001__s0__probe__L0__U750.npz` | 2,436,035 | `a040a0863ae4509f6a5107597bc04c2b98d210b553b4ff808404ed2cb3df1757` |
     | `fidprobe3__lm_w128__protonic_onen2022__cttv2__lr0.0001__s0__probe__L9__U750.npz` | 3,073,036 | `10c519823e3ca7055bae6a7b391b01aca837ec6d7b3a5c5a99414f4a38949097` |
     | `fidprobe3__lm_w128__protonic_onen2022__cttv2__lr0.0001__s0__probe__L0__U2250.npz` | 2,139,293 | `ffb3180f9313e0c45b48b38320996bd26e853cf406d75d105f8eeb2bc6e02149` |
     | `fidprobe3__lm_w128__protonic_onen2022__cttv2__lr0.0001__s0__probe__L9__U2250.npz` | 2,585,400 | `bdab3ba2741f645bad7d07bb70341ea4b8ecfc9e72a7986b46f8c53569390b64` |
     | `fidprobe3__mnist_w128__ecram_li_tang2018__cttv2__lr0.003__s0__probe__L0__U1000.npz` | 21,971,077 | `f34d09ea763c2e3d4fe6ffc77f408d3d6f9237bfdd7813b548c872d5f12aead3` |
     | `fidprobe3__mnist_w128__ecram_li_tang2018__cttv2__lr0.003__s0__probe__L2__U1000.npz` | 244,518 | `1b81cf51ff0df0c41086bac3b0be902dcabe7dc79da9097de3a4fb1594831e38` |
     | `fidprobe3__mnist_w128__ecram_li_tang2018__cttv2__lr0.003__s0__probe__L0__U3500.npz` | 19,388,651 | `266c46c10f2c0d8f93517469118f29f6da32ce9e82227f17f91e030035d723a8` |
     | `fidprobe3__mnist_w128__ecram_li_tang2018__cttv2__lr0.003__s0__probe__L2__U3500.npz` | 243,582 | `1ddeceb98029d63ac80eb6382ba4509ce596ff49a3987232ca6d49dd740e7efd` |

     From the paper directory of the deposit, `python -B revision4/rebuild_draw_tables.py --draws draws/rev3` re-hashes
     every file, recomputes every statistic of the three probe tables (`tex/tables/rev4_probe_sur.tex`,
     `rev4_probe_seq.tex`, `rev4_dep.tex`) from the saved arrays and the probe records' metadata (layer, clipping figures, bootstrap
     counts), and prints ALL_OK only if each rebuilt table equals the
     paper's byte for byte (`--selftest` also shows it failing on a perturbed draw and on a wrong hash).

   It must not hold the `sessions/` folders, which contain pod records.
2. Sign in to https://zenodo.org with GitHub, enable the repository, and create a release. Zenodo mints a DOI.
3. Put that DOI in the paper's "Code and data availability" paragraph (`tex/body.tex`, the `\availability` text) and rebuild.
   Done in version 10 (`revision9/edit_10.py`), with the GitHub mirror under the author's account.

## 5. Submit

1. On arXiv choose "Start new submission", the licence, and the categories.
2. Upload the LaTeX source as a .zip or .tar.gz of `tex/`:
   - main-arxiv.tex, preamble.tex, body.tex, sec_*.tex, app_*.tex, numbers.tex, numbers_rev.tex, numbers_rev2.tex, numbers_rev3.tex, numbers_rev4.tex, tables/,
     figs/*.pdf, refs.bib;
   - the generated `main-arxiv.bbl`, which arXiv prefers to running BibTeX itself.

   The ready archive is `build/arxiv-source.tar.gz`. The build script assembles it from exactly this list (`pod/build_rev2.sh`
   for version 3, on a pod; `pod/build_rev3.sh` for version 4, `pod/build_rev4.sh` for version 5, `pod/build_rev5.sh` for version 6 and `pod/build_rev6.sh` for version 7 and `pod/build_rev7.sh` for version 8 and `pod/build_rev8.sh` for versions 9 to 13 and `pod/build_rev9.sh` for version 14 and `pod/build_rev10.sh` for versions 15 and 16, on the desk in WSL Ubuntu with the same tectonic
   0.15.0) and
   compiles main-arxiv.tex from that archive in an empty directory, so a missing file fails the build. Use the archive, not
   loose copies of the files; `revision15/check_build_v16.py` (version 16) runs `revision6/check_build_v7.py` and reads the version-16
   proofs: the word-count text diff `revision15/pdf_text_diff_v16.py` (v15 -> v16, reference numbers as [#], the same 44 pages),
   the name check in WSL and in Windows, numbers freshness, Figures 1 and 4, the reset and the Welch test;
   `revision14/check_build_v15.py` (version 15) runs `revision6/check_build_v7.py` and reads the version-15
   proofs: the word-count text diff `revision14/pdf_text_diff_v15.py` (v14 -> v15, reference numbers as [#], the same 44 pages),
   the name check in WSL and in Windows, numbers freshness, Figure 1 against the selected settings, the records and the
   simulator, Figure 4, the reset and the Welch test; `revision13/check_build_v14.py` (version 14) runs `revision6/check_build_v7.py` and reads the version-14
   proofs: the word-count text diff `revision13/pdf_text_diff_v14.py` (v13 -> v14, reference numbers as [#], one page more), the
   name check in WSL and in Windows, numbers freshness, Figure 1 against the simulator, Figure 4, the reset and the Welch test;
   `revision12/check_build_v13.py` (version 13) runs `revision6/check_build_v7.py` and reads the version-13
   proofs: the word-count text diff `revision12/pdf_text_diff_v13.py` (v12 -> v13, pages equal), the name check in WSL and in
   Windows, numbers freshness, Figure 3, the reset and the Welch test; `revision11/check_build_v12.py` (version 12) runs `revision6/check_build_v7.py` and reads the version-12
   proofs: the word-count text diff `revision11/pdf_text_diff_v12.py` (v11 -> v12; the extra page reflows floats), the name check,
   numbers freshness, Figure 3 (its self-test on bundled version-10 code), the reset and `revision11/test_welch_df.py`;
   `revision10/check_build_v11.py` (version 11) runs `revision6/check_build_v7.py` and reads the version-11 proofs:
   the name check (`revision9/name_check_v10.py`, the same rule), `revision10/pdf_text_diff_v11.py` (v10 -> v11: the expected edits only),
   `revision10/check_fig_main.py` (Figure 3 draws every mean and interval of its results; its legend overlaps no label),
   `sim/test_ideal_reset_cols.py` and the numbers-freshness record; `revision9/check_build_v10.py` (version 10) runs `revision6/check_build_v7.py` and reads the version-10 proofs:
   `revision9/name_check_v10.py` (the old name appears only inside the GitHub mirror's address, which the owner allowed on 2026-10-28),
   `revision9/pdf_text_diff_v10.py` (v9 -> v10: the expected edits only) and the numbers-freshness record; `revision8/check_build_v9.py` runs `revision7/check_build_v8.py` and adds the numbers-freshness proof
   (`revision8/check_numbers_fresh.py`: every committed `tex/numbers*.tex` equals what its generator writes now; shown to fail on version 8's
   `numbers_rev.tex`); `revision7/check_build_v8.py` runs `revision6/check_build_v7.py` and adds the name proof (`revision7/name_check.py`: the old name
   appears nowhere in the sources, either PDF's text and metadata, the HTML or the archive); `revision6/check_build_v7.py` runs
   `revision5/check_build_v6.py` and adds `revision6/html_leftover.py` (no `cmidrule`, no `(lr)2-6`-style
   rule argument and no raw `\command` outside the math spans in the HTML text; `pod/html_prep_rev6.py` removes `\cmidrule` and `\cline`
   before pandoc). `revision5/check_build_v6.py` runs `revision4/check_build_v5.py` (the logs of all three compilations, the HTML, the revision numbers in
   the HTML, the printed size of every table) and adds `revision5/html_complete.py`: every section and subsection heading of the LaTeX
   source is in the HTML in order, every table caption is followed by its own table's header and rows, and no `??`, `[?]`, raw
   `[label]` or dead internal link remains. The HTML is made by pandoc 2.19.2 (pypandoc_binary 1.13) from `main-html.tex`, which
   `pod/html_prep_rev5.py` writes: it also rewrites every `p{..}` tabular column to `l`, because that pandoc fuses a table with a
   `p{..cm}` column and a later table with a `p{..\linewidth}` column and drops what lies between them (`revision5/pandoc_repro.py`
   reproduces it). The pandoc log stays empty in that failure: read the check, not the log.

   arXiv compiles the source. Check the preview PDF page by page.
3. Fill in the title. The abstract for the form is ready in `build/arxiv-abstract.txt`: it is generated by `revision2/make_abstract.py` (version 3) `revision3/make_abstract_v4.py` (version 4) and `revision4/make_abstract_v5.py` (versions 5 and 6) from
   `tex/sec_abstract.tex` with every number macro expanded from the generated `tex/numbers*.tex` (the same numbers as the PDF abstract) and fits arXiv's 1,920-character limit. Add the comments field; for version 16: "44 pages, 4 figures; code and data: https://doi.org/10.5281/zenodo.23748861".
4. Submit. It appears after moderation, usually the next working day.

## 6. Later: a journal

Candidate venues for a simulation-plus-roadmap paper:

- *Frontiers in Neuroscience* (Neuromorphic Engineering), where the RPU and Tiki-Taka papers appeared;
- *Neuromorphic Computing and Engineering* (IOP);
- *APL Machine Learning*.

All accept arXiv preprints. Check each journal's authorship and AI-use policy and use the arXiv variant there.
