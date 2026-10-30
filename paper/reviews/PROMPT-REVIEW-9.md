# The prompt for review 9 (2026-10-29)

Review 9 checks release v1.1 and paper version 11 before the arXiv submission.

The owner runs it in a new Codex conversation, opened on `F:\review9`. That folder was made for this review and holds only
`memistor-paper-v11.pdf`, a copy of `build/main-arxiv.pdf` (sha256 67530090a653ced3...).

The review goes on F: because the drive-G backup needs the room left on H:.

The prompt differs from review 8's in four ways:
- the fresh audit reads the v1.0 -> v1.1 diff first;
- it adds a referee read of the paper;
- it adds an arXiv-style pdfLaTeX compile of the source, which the author built with Tectonic;
- it reads review 8 and its response only at the end, so they do not steer the fresh audit.

```text
Review a research paper and its public code-and-data release independently, from scratch, before the paper goes to arXiv. Work only in F:\review9, an empty folder made for this review, and do not read anything else on this computer, including anything under C:\Projects. Do not edit, push or publish anything; to test a change, change a copy.

Repository: https://github.com/Questeria/memistor-ecram-training, release v1.1 (archived at https://doi.org/10.5281/zenodo.23773334; all versions: https://doi.org/10.5281/zenodo.23748861)
Paper: F:\review9\memistor-paper-v11.pdf, version 11 of "Can memistor-class electrochemical weights train neural networks?" by Anthony DeMarco. All results are simulations.

Setup: git clone --branch v1.1 https://github.com/Questeria/memistor-ecram-training F:\review9\memistor-ecram-training
Create the Python environment inside F:\review9, following the repository's own instructions. If Windows blocks a package from loading (Smart App Control), use WSL Ubuntu with a fresh virtual environment under /mnt/f/review9 and say so. Install nothing on C: (it is nearly full).

1. Reproduce. Follow README.md exactly as written, in a fresh shell, including the install section and the quick start, then run reproduce_all.py on CPU. Report every instruction that is wrong, missing or fails. For every number, table and figure in the paper, report whether it regenerates and matches; for each mismatch give the file, the expected value and the actual value.

2. Audit the code. First read every change from v1.0 to v1.1 (git diff v1.0 v1.1) line by line. Then audit the computational code as a first reviewer would: the device models and pulse updates in paper/sim/, the training loops and data sampling, the energy model in paper/energy/, the analysis that turns run records into the paper's statistics (paper/analyze.py and paper/revision*/), and the scripts that regenerate the tables and figures. Look for anything that would change a number or a conclusion: wrong formulas, sign or unit errors, off-by-one errors, seeds or data splits mixed between compared arms, leakage between training and evaluation data, and statistics that are not what the paper says they are. Run the repository's own tests and checks, and confirm that at least one of them fails when you plant a fault in a copy.

3. Read the paper as a referee. Check that every claim is supported by the results shown, that each statistic is described correctly, that the limitations are stated, and that the text, tables, figures and appendices agree with each other and with the records. Check Section 9 (Code and data availability), README.md, CITATION.cff and .zenodo.json: every path must exist, and every statement about contents, versions, DOIs and licences must be true. Report any secret, credential, personal path or private name in the repository.

4. Check the arXiv source. arXiv compiles paper/build/arxiv-source.tar.gz with TeX Live and pdfLaTeX, using the bundled .bbl; the author built it with Tectonic. If you can install TeX Live inside F:\review9 (not on C:), compile the archive in an empty folder the way arXiv does, and report any error, any undefined reference or citation, the page count, and any visible difference from the PDF. If you cannot, say so.

5. Only after steps 1 to 4, read the previous review (paper/reviews/REVIEW-8-chatgpt-20261028-full.md) and the authors' response (paper/RESPONSE-TO-REVIEW-8.md), and check that each of its nine findings is fixed or disclosed as the response says.

Write the full report to F:\review9\audit\REVIEW.md, with logs and evidence beside it. For each finding give: the file and line (or the paper's page and section), what is wrong, whether it changes a number or a conclusion, how you confirmed it, and a severity (critical, major, minor or cosmetic). Then list what you checked and found correct, and what you could not check and why.
```
