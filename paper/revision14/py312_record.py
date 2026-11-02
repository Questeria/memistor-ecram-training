"""Version 15 / archive v1.5 (review 12, finding A): record the fast reproduction run under Python 3.12 (WSL Ubuntu on the desk,
Python 3.12.3, torch 2.7.1+cpu, NumPy 2.5.2, matplotlib 3.9.2; venv /root/me-v15-py312) of release v1.4 (git archive of 39c6ed7fe,
F:/x1000-deposit/py312/v1.4-fast) and of the finalized v1.5 (F:/x1000-deposit/py312/v1.5-fast), both run by
F:/x1000-deposit/py312/run-fast*.sh with `reproduce_all.py --sums` first, at nice 10.  Writes records/deposit/PY312-FAST.json.

    python -I -B revision14/py312_record.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent
F = Path("F:/x1000-deposit/py312")


def one(rep_path, env_path, sums_path, verdict):
    r = json.loads(Path(rep_path).read_bytes().decode("utf-8"))
    steps = r["steps"]
    pol = {k: v["detail"] for k, v in r["files"].items() if v["status"] == "within_policy"}
    return dict(python=r["python"].split()[0], environment=Path(env_path).read_text(encoding="utf-8").strip().splitlines(),
                sums=Path(sums_path).read_text(encoding="utf-8").strip().splitlines()[-1],
                steps=len(steps), steps_ok=sum(1 for s in steps if s["ok"]), all_ok=r["all_ok"],
                file_status_counts=r["file_status_counts"],
                differs=[k for k, v in r["files"].items() if v["status"] == "DIFFERS"],
                within_policy=pol,
                policy_detail_short=(next(iter(pol.values())).split(" (largest")[0] if pol else "none"),
                verdict=verdict(r))


v14 = one(F / "v1.4-fast" / "_repro" / "REPRODUCE-py312.json", F / "v1.4-fast" / "_env.txt", F / "v1.4-fast" / "_sums.txt",
          lambda r: "REPRODUCE_ALL_OK" if r["all_ok"] else "REPRODUCE_FAILED, as review 12 found")
v14["sums_note"] = ("the two unlisted files are this run's own _env.txt and _sums.txt, written into the copy before the sums check; "
                    "0 mismatches")
v15 = one(F / "v1.5-fast.logs" / "REPRODUCE-py312.json", F / "v1.5-fast.logs" / "env.txt", F / "v1.5-fast.logs" / "sums.txt",
          lambda r: "REPRODUCE_ALL_OK" if r["all_ok"] else "REPRODUCE_FAILED")
out = {"v1.4": v14, "v1.5": v15,
       "note": "the fast path skips the five slow simulator test groups; the reference-environment clean room runs all 31 steps"}
(P / "records" / "deposit" / "PY312-FAST.json").write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
print("v1.4:", v14["verdict"], v14["file_status_counts"], "| v1.5:", v15["verdict"], v15["file_status_counts"], v15["policy_detail_short"])
