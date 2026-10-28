"""ME-REVISE-4: PUBLISHING.md for version 5 (review 4, finding 2 and the v5 build), by named anchors. The draw files' names, sizes
and SHA-256 are read from records/revision4/DRAW-REBUILD.json (written by revision4/rebuild_draw_tables.py, which re-hashed
each file and checked it against its probe record), never typed.

    python -B revision4/edit_publishing_4.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent
dr = json.loads((P / "records" / "revision4" / "DRAW-REBUILD.json").read_bytes())
assert dr["all_identical"]
files = dr["files"]
tot = sum(f["bytes"] for f in files)
rows = "\n".join(f"     | `{f['file']}` | {f['bytes']:,} | `{f['sha256']}` |" for f in files)
draws = (
    f"   - the {len(files)} pulse-draw files of the update probes (NumPy `.npz`, {tot:,} bytes together; kept outside git, on the\n"
    "     desk at `H:/x1000/memistor-paper/rev3/draws/`). Put them in the deposit as `draws/rev3/<name>`. Each holds one probe's\n"
    "     surrogate, per-sample-stream and literal-stream draws, the requested update, the expected pulse update and the initial\n"
    "     state. Their SHA-256 (also recorded in each probe record, `records/revision3/runs/fidprobe3-probes/*.probes.json`):\n\n"
    "     | file | bytes | SHA-256 |\n     |---|---:|---|\n" + rows + "\n\n"
    "     From the paper directory of the deposit, `python -B revision4/rebuild_draw_tables.py --draws draws/rev3` re-hashes\n"
    "     every file, recomputes every statistic of the three probe tables (`tex/tables/rev4_probe_sur.tex`,\n"
    "     `rev4_probe_seq.tex`, `rev4_dep.tex`) from the arrays alone, and prints ALL_OK only if each rebuilt table equals the\n"
    "     paper's byte for byte (`--selftest` also shows it failing on a perturbed draw and on a wrong hash).\n")
SUBS = [
    ("deposit", "   - lane ME's `sim/`, `records/CATALOG.json`, `records/TT-CHOICE.json` and `BENCH.md`, `bench/`.\n",
     "   - lane ME's `sim/`, `records/CATALOG.json`, `records/TT-CHOICE.json` and `BENCH.md`, `bench/`;\n" + draws),
    ("tarlist", "numbers_rev2.tex, numbers_rev3.tex, tables/", "numbers_rev2.tex, numbers_rev3.tex, numbers_rev4.tex, tables/"),
    ("builder", "`pod/build_rev3.sh` for version 4, on the desk in WSL Ubuntu with the same tectonic 0.15.0)",
     "`pod/build_rev3.sh` for version 4 and `pod/build_rev4.sh` for version 5, on the desk in WSL Ubuntu with the same tectonic\n"
     "   0.15.0)"),
    ("check", "`revision3/check_build_v4.py` checks the logs of all three compilations and the HTML.",
     "`revision4/check_build_v5.py` checks the logs of all three compilations, the HTML, the revision numbers in the HTML and the\n"
     "   printed size of every table."),
    ("abstract", "and `revision3/make_abstract_v4.py` (version 4) from",
     "`revision3/make_abstract_v4.py` (version 4) and `revision4/make_abstract_v5.py` (version 5) from"),
]
t = (P / "PUBLISHING.md").read_bytes().decode("utf-8")
for n, a, b in SUBS:
    assert t.count(a) == 1, n
    t = t.replace(a, b)
(P / "PUBLISHING.md").write_bytes(t.encode("utf-8"))
print("PUBLISHING.md:", len(files), "draw files,", tot, "bytes")
