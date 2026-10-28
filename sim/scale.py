"""DEV scale check (director's item c; OUTSIDE THE PRE-REGISTRATION): device gap versus width, seed 0 everywhere.
python -B scale.py -> ../records/SCALE-DEV.json. The pre-registered widths (CIFAR 32, LM 128) come from records/runs/<task>;
the others from records/runs/<task>-scale-DEV. The lr is the pre-registered one at every width (not re-tuned)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "records")


def jl(p):
    with open(p, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def metric(r):
    m = r["metric"]
    return m["acc"] * 100 if "acc" in m else m["bpb"]


def main():
    out = dict(schema="altone.x1000.me.scale.v1", results_are="DEV, outside the pre-registration, seed 0, lr not re-tuned per width")
    for t, base, others in (("cifar", 32, (16, 64)), ("lm", 128, (64, 256))):
        rows = {}
        for w in sorted((base,) + others):
            d = os.path.join(REC, "runs", t if w == base else t + "-scale-DEV")
            sfx = "" if w == base else f"_w{w}"
            fpp = os.path.join(d, ("FP__s0" if w == base else f"FP_w{w}__s0") + ".json")
            if not os.path.exists(fpp):
                continue
            fp = metric(jl(fpp))
            row = dict(fp=fp)
            for k in ("protonic_onen2022", "ecram_li_tang2018"):
                p = os.path.join(d, f"CAT_{k}{sfx}__ttv2__s0.json")
                if os.path.exists(p):
                    m = metric(jl(p))
                    row[k] = dict(metric=m, gap=(fp - m) if t == "cifar" else (m / fp - 1) * 100)
            d2 = os.path.join(REC, "runs", t + "-scale-DEV", f"lrsel_w{w}")  # round 2: lr re-chosen on validation
            if w != base and os.path.exists(os.path.join(d2, f"FP_w{w}__s0.json")):
                fp2 = metric(jl(os.path.join(d2, f"FP_w{w}__s0.json")))
                row["retuned"] = dict(lr=jl(os.path.join(d2, "LR-CHOICE.json"))["lr"], fp=fp2)
                for k in ("protonic_onen2022", "ecram_li_tang2018"):
                    p2 = os.path.join(d2, f"CAT_{k}{sfx}__ttv2__s0.json")
                    if os.path.exists(p2):
                        m = metric(jl(p2))
                        row["retuned"][k] = dict(metric=m, gap=(fp2 - m) if t == "cifar" else (m / fp2 - 1) * 100)
            rows[str(w)] = row
        out[t] = rows
    with open(os.path.join(REC, "SCALE-DEV.json"), "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    for t in ("cifar", "lm"):
        for w, r in out[t].items():
            print(t, w, f"fp {r['fp']:.4g}", {k: round(v["gap"], 2) for k, v in r.items() if k not in ("fp", "retuned")})
            if "retuned" in r:
                q = r["retuned"]
                print("   retuned lr", q["lr"], f"fp {q['fp']:.4g}", {k: round(v["gap"], 2) for k, v in q.items() if k not in ("fp", "lr")})


if __name__ == "__main__":
    main()
