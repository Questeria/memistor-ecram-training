"""Version 16 / archive v1.6: record the fast reproduction run under Python 3.12 (WSL Ubuntu on the desk, Python 3.12.3, torch 2.7.1+cpu,
NumPy 2.5.2, matplotlib 3.9.2; venv /root/me-v15-py312) of the finalized v1.6 (F:/x1000-deposit/py312/v1.6-fast, run by
F:/x1000-deposit/py312/run-fast2.sh with `reproduce_all.py --sums` first, at nice 10).  Writes records/deposit/PY312-FAST.json (v1.5's
is kept in records/deposit/v1.5/).  Derived from revision14/py312_record.py.

    python -I -B revision15/py312_record.py
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


v16 = one(F / "v1.6-fast.logs" / "REPRODUCE-py312.json", F / "v1.6-fast.logs" / "env.txt", F / "v1.6-fast.logs" / "sums.txt",
          lambda r: "REPRODUCE_ALL_OK" if r["all_ok"] else "REPRODUCE_FAILED")
out = {"v1.6": v16,
       "note": "the fast path skips the five slow simulator test groups; the reference-environment clean room runs all steps"}
(P / "records" / "deposit" / "PY312-FAST.json").write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
print("v1.6:", v16["verdict"], v16["file_status_counts"], v16["policy_detail_short"])
