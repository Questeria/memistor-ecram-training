r"""ME-DEPOSIT-2: every committed tex/numbers*.tex must equal what its generator writes now (so a count that is computed from another
file, like \RVnDev from DEVIATIONS-PAPER.md, cannot go stale).  Version 8's numbers_rev.tex said \RVnDev = 6 while the generator, run
after R7 and R8 had been added, writes 8; the code-and-data deposit's clean-room regeneration found it.

The check copies what the generators read (analyze.py, sim, energy, revision*, records, tex without its archives) to a temporary
folder, runs the paper's number generators there in the deposit's order (reproduce_all.py), and compares every tex/numbers*.tex byte
for byte with the committed ones: a differing file, a file only one side has, and a generator that fails are all errors.  Nothing in
the paper folder is written.

    python -B revision8/check_numbers_fresh.py [--against DIR] [--json out.json]
    python -B revision8/check_numbers_fresh.py --selftest [--json out.json]    (clean passes; v8's numbers_rev.tex, a changed digit,
                                                                               a missing file and a stray file each fail)
"""
import difflib
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
BS = b"\\"
# (argv after python) in the order of deposit-src/reproduce_all.py; figures are not number generators
GENERATORS = [
    ["-B", "energy/energy_system.py", "--runs", "records/runs/e3", "--out", "records/ENERGY-SYSTEM.json"],
    ["-I", "analyze.py"],
    ["-B", "revision/compare_curves.py", "records/revision/AIHWKIT-CURVES.json", "records/revision/AIHWKIT-COMPARE.json"],
    ["-B", "revision/analyze_d1.py"],
    ["-B", "energy/energy_rev.py", "--runs", "records/revision/runs/e3", "--out", "records/revision/ENERGY-REVISION.json"],
    ["-B", "revision/analyze_rev.py"],
    ["-B", "revision2/analyze_rev2.py"],
    ["-B", "revision3/analyze_rev3.py"],
    ["-B", "revision4/analyze_rev4.py"],
    ["-B", "revision4/make_abstract_v5.py"],
]
COPY = ["analyze.py", "sim", "energy", "revision", "revision2", "revision3", "revision4", "records", "tex", "DEVIATIONS-PAPER.md"]


def numbers_in(d):
    return {os.path.basename(p): p for p in glob.glob(os.path.join(d, "numbers*.tex"))}


def regenerate(paper):
    """Run the generators in a temporary copy of `paper`; return (tmp_root, list of failed commands)."""
    root = tempfile.mkdtemp(prefix="numbers_fresh_")
    dst = os.path.join(root, "paper")
    os.makedirs(os.path.join(dst, "build"))
    for n in ('records', 'sim', 'energy', 'bench'):      # the study folder's own (the generators read ../records)
        s = os.path.join(os.path.dirname(paper), n)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(root, n), ignore=shutil.ignore_patterns('__pycache__'))
    for n in COPY:
        s = os.path.join(paper, n)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(dst, n), ignore=shutil.ignore_patterns("__pycache__", "v[0-9]*"))
        elif os.path.exists(s):
            shutil.copy2(s, os.path.join(dst, n))
    env = {k: v for k, v in os.environ.items() if k not in ("ME_PAPER_RECORDS", "ME_PAPER_TEX", "ME_RECORDS", "PYTHONPATH")}
    env["PYTHONHASHSEED"] = "0"
    failed = []
    for g in GENERATORS:
        r = subprocess.run([sys.executable] + g, cwd=dst, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            failed.append(dict(cmd=" ".join(g), rc=r.returncode, tail=(r.stdout + r.stderr).strip()[-300:]))
    return root, os.path.join(dst, "tex"), failed


def compare(fresh_tex, committed_dir):
    """Problems between regenerated and committed numbers*.tex."""
    f, c = numbers_in(fresh_tex), numbers_in(committed_dir)
    problems = []
    for n in sorted(set(f) | set(c)):
        if n not in f:
            problems.append(dict(file=n, problem="committed but no generator writes it"))
        elif n not in c:
            problems.append(dict(file=n, problem="a generator writes it but it is not committed"))
        else:
            a, b = open(c[n], "rb").read(), open(f[n], "rb").read()
            if a != b:
                d = [l for l in difflib.unified_diff(a.decode("utf-8").splitlines(), b.decode("utf-8").splitlines(), "committed",
                                                    "regenerated", n=0, lineterm="") if l[:1] in "+-" and l[:3] not in ("+++", "---")]
                problems.append(dict(file=n, problem="differs from its regeneration", diff=d[:6], diff_lines=len(d)))
    return problems


def selftest(fresh_tex, paper):
    res = dict(cases={})
    tmp = tempfile.mkdtemp(prefix="numbers_planted_")
    live = os.path.join(paper, "tex")

    def plant(name, mutate):
        d = os.path.join(tmp, name)
        os.makedirs(d)
        for n, p in numbers_in(live).items():
            shutil.copy2(p, os.path.join(d, n))
        mutate(d)
        return d

    def edit_digit(d):
        p = os.path.join(d, "numbers.tex")
        t = open(p, "rb").read().decode("utf-8")
        i = next(k for k, ch in enumerate(t) if ch.isdigit() and t[k - 1] == "{")
        open(p, "wb").write((t[:i] + str((int(t[i]) + 1) % 10) + t[i + 1:]).encode("utf-8"))

    cases = [("clean", plant("clean", lambda d: None), True),
             ("one digit of numbers.tex changed", plant("digit", edit_digit), False),
             ("numbers_rev3.tex missing", plant("missing", lambda d: os.remove(os.path.join(d, "numbers_rev3.tex"))), False),
             ("stray numbers_zz.tex", plant("stray", lambda d: open(os.path.join(d, "numbers_zz.tex"), "wb").write(BS + b"newcommand{" + BS + b"ZZ}{1}\n")), False)]
    v8 = os.path.join(paper, "tex", "v8")
    if os.path.isdir(v8):
        cases.append(("version 8's own numbers_rev.tex (RVnDev = 6)", v8, False))
    for name, d, want_ok in cases:
        pr = compare(fresh_tex, d)
        res["cases"][name] = dict(ok=(not pr), expected_ok=want_ok, as_expected=((not pr) == want_ok), problems=[p["file"] for p in pr])
    res["ok"] = all(c["as_expected"] for c in res["cases"].values())
    return res


def main():
    a = sys.argv[1:]
    committed = os.path.join(P, "tex")
    if "--against" in a:
        committed = os.path.abspath(a[a.index("--against") + 1])
    root, fresh_tex, failed = regenerate(P)
    out = dict(committed_dir=os.path.relpath(committed, P).replace(os.sep, "/") if committed.startswith(P) else os.path.basename(committed), numbers_files=sorted(numbers_in(committed)), generator_failures=failed)
    out["problems"] = compare(fresh_tex, committed)
    out["ok"] = not failed and not out["problems"]
    if "--selftest" in a:
        out["selftest"] = selftest(fresh_tex, P)
        out["ok"] = out["ok"] and out["selftest"]["ok"]
    shutil.rmtree(root, ignore_errors=True)
    if "--json" in a:
        jp = a[a.index("--json") + 1]
        jp = jp if os.path.isabs(jp) else os.path.join(P, jp)
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        open(jp, "wb").write((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    for p in out["problems"]:
        print("STALE", p["file"], "-", p["problem"], *p.get("diff", [])[:4])
    for f in failed:
        print("GENERATOR FAILED", f["cmd"], f["tail"])
    if "selftest" in out:
        for k, v in out["selftest"]["cases"].items():
            print("selftest", "OK  " if v["as_expected"] else "BAD ", k, "->", "passes" if v["ok"] else "fails", v["problems"])
    print(len(out["numbers_files"]), "numbers files |", "FRESH" if not out["problems"] and not failed else "STALE", "|", "ALL_OK" if out["ok"] else "NOT_OK")
    sys.exit(0 if out["ok"] else 1)


if __name__ == "__main__":
    main()
