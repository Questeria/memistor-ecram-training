# Release notes: v1.0

First public release of the code, records and pulse draws behind the paper "Can memistor-class electrochemical weights train neural networks?" (version 9, October 28, 2026).

- Code: the simulators and their checks, the explicit pulse streams and probes, the pod run scripts, the energy model, the analysis
  and figure scripts (MIT).
- Records: every run record, the device catalog, the citation check, the 12 saved pulse-draw archives (`paper/draws/rev3/`)
  (CC BY 4.0).
- History: the plans, deviations, the responses to the seven independent reviews and the reviews themselves, and the paper
  sources with the built PDFs and HTML of the current and the archived versions.
- `fetch_data.py` downloads MNIST, CIFAR-10 and enwik8 and checks them against the digests the paper pins.
- `reproduce_all.py` regenerates every number file, table and figure from the records and compares each byte for byte with the
  paper's; nothing is trained. The result of the author's clean-room run is in `VERIFY.json`.
- 3338 files, 123.5 MB; `SHA256SUMS` covers every file.
- Pod session records (which hold account identifiers) are not included.
