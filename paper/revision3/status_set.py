"""Set fields of STATUS.json's revision_3 block: status_set.py key=json_value ... (LF bytes)."""
import json, sys, pathlib, datetime, subprocess
p = pathlib.Path(__file__).resolve().parent.parent / "STATUS.json"
s = json.loads(p.read_bytes())
r = s.setdefault("revision_3", {})
for a in sys.argv[1:]:
    k, v = a.split("=", 1)
    if k.startswith("+"):
        r.setdefault(k[1:], []).append(json.loads(v))
    else:
        r[k] = json.loads(v)
et = datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET")  # desk clock is ET
r["updated_et"] = et
s["lane"] = "x1000-ME-REVISE-3 (version 4 of the memistor paper, answering review 3); earlier: ME-REVISE, ME-REVISE-2"
s["state"] = r.get("state", "working")
p.write_bytes((json.dumps(s, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("ok", et)
