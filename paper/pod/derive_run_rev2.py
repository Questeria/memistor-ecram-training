"""ME-REVISE-2: derive pod/run_rev2.sh and pod/make_payload_rev2.py from run_rev.sh and make_payload_rev.py by named anchors.

    python -B pod/derive_run_rev2.py
run_rev2.sh: the checks are sim/test_rev2.py (then sim/test_rev.py unless ME_SKIP_TESTS=1), the phases run through
sim/sweep_rev2.py. make_payload_rev2.py: the same payload (sim/*.py carries the new files) with run_rev2.sh as run.sh.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = (HERE / "run_rev.sh").read_bytes().decode("utf-8")
SUBS = [
    ("header", "# Lane ME-REVISE pod entry (derived from pod/run.sh)",
     "# Lane ME-REVISE-2 pod entry (derived by pod/derive_run_rev2.py from pod/run_rev.sh)"),
    ("tests",
     'if [ "${ME_SKIP_TESTS:-0}" != "1" ]; then\n',
     '$PY -B "$HERE/sim/test_rev2.py" --out "$OUT/TESTS-REV2-pod.json" > "$OUT/tests-rev2.txt" 2>&1 || { log "REV2 CHECKS FAILED ON THE POD"; tail -3 "$OUT/tests-rev2.txt"; exit 5; }\n'
     'log "checks rev2: $(tail -1 "$OUT/tests-rev2.txt")"\n'
     'if [ "${ME_SKIP_TESTS:-0}" != "1" ]; then\n'),
    ("sweep", 'SW="$PY -B $HERE/sim/sweep_rev.py ', 'SW="$PY -B $HERE/sim/sweep_rev2.py '),
]
for name, a, b in SUBS:
    assert s.count(a) == 1, name
    s = s.replace(a, b)
(HERE / "run_rev2.sh").write_bytes(s.encode("utf-8"))

t = (HERE / "make_payload_rev.py").read_bytes().decode("utf-8")
a = "    files['run.sh'] = (HERE / 'run_rev.sh').read_bytes()\n"
assert t.count(a) == 1, "make_payload run.sh"
t = t.replace(a, "    files['run.sh'] = (HERE / 'run_rev2.sh').read_bytes()\n")
(HERE / "make_payload_rev2.py").write_bytes(t.encode("utf-8"))
print("wrote run_rev2.sh and make_payload_rev2.py")
