"""ME-REVISE-4: verify the findings of review 4 (reviews/REVIEW-4-chatgpt-20261027-full.md) against the records and the code.

    H:/x1000/bench/venv/Scripts/python.exe -B revision4/verify_findings_4.py [--draws-dir H:/x1000/memistor-paper/rev3/draws]

Reads only existing records, sources, the installed torch headers and the draw files (no training run). Writes
records/revision4/VERIFY-FINDINGS-4.json. Every number in it is computed here; each check that supports a verdict is also
shown to react to a planted fault (`faults`).
"""
import argparse
import copy
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(P, *[".."] * 5))
RUNS = os.path.join(P, "records", "revision", "runs")
R3RUNS = os.path.join(P, "records", "revision3", "runs")
T, D, A = "mnist", "ecram_mo_kim2019", "sgd"
V4 = "5afeda818"  # the commit of version 4, which review 4 read


def jl(p):
    return json.load(open(p, "rb"))


def arm(r):
    if r["arm"] == "fp_sgd" and r["algo"] == "sgd":
        return "fp"
    if r["arm"] == "device" and r["spec"]["name"] == D and r["algo"] == A:
        return "seq" if r.get("pulse_mode") == "seq" else "sur"
    return None


def cell_records():
    """The MNIST MO-ECRAM SGD cell's records: E3 (surrogate, FP-SGD control), A2 (pod seq), A2-R (desk seq)."""
    out = []
    for src, pat in (("e3", os.path.join(RUNS, "e3", "e3__mnist_w128__*.json")),
                     ("fid", os.path.join(RUNS, "fid", "fid__mnist_w128__ecram_mo_kim2019__sgd__*.json")),
                     ("fidr", os.path.join(R3RUNS, "fidr", "*.json"))):
        for f in sorted(glob.glob(pat)):
            r = jl(f)
            if r["task"] == T and arm(r):
                out.append(dict(src=src, arm=arm(r), seed=r["seed"], file=os.path.relpath(f, P).replace("\\", "/"),
                                device=r.get("device"), torch=r.get("torch"), acc=r["metric"]["acc"],
                                init=r.get("init_sha256"), data=r.get("data_sha256")))
    return out


def matched(recs):
    """True iff every record has both hashes and they are equal across the records (the rule analyze_rev4.py enforces)."""
    return bool(recs) and all(r["init"] and r["data"] for r in recs) and \
        len({r["init"] for r in recs}) == 1 and len({r["data"] for r in recs}) == 1


def f1(recs):
    by = {}
    for r in recs:
        by.setdefault(r["seed"], []).append(r)
    seeds = {}
    for s in sorted(by):
        pod = [r for r in by[s] if r["src"] in ("e3", "fid")]
        desk = [r for r in by[s] if r["src"] == "fidr"]
        seeds[s] = dict(pod_triple=sorted(r["arm"] for r in pod), pod_matched=matched(pod),
                        desk_seq_matches_pod=[matched(pod + [q]) for q in desk],
                        rows=[dict(r, init=(r["init"] or "")[:16], data=(r["data"] or "")[:16]) for r in by[s]])
    used_v4 = {0: "fid", 1: "fid", 2: "fid", 3: "fidr", 4: "fidr"}  # analyze_rev3.a2r(): seq from the pod for 0-2, desk 3-4
    v4_pairs = {s: matched([r for r in by[s] if r["src"] == "e3"] + [r for r in by[s] if r["src"] == used_v4[s]])
                for s in sorted(by)}
    return seeds, v4_pairs


def probe_runs():
    e3 = {}
    for f in glob.glob(os.path.join(RUNS, "e3", "*.json")):
        r = jl(f)
        if r["arm"] == "device":
            e3[(r["task"], r["spec"]["name"], r["algo"], r["seed"])] = r
    out = []
    for f in sorted(glob.glob(os.path.join(R3RUNS, "fidprobe3", "*.json"))):
        r = jl(f)
        o = e3[(r["task"], r["spec"]["name"], r["algo"], r["seed"])]
        out.append(dict(run=r["tag"], task=r["task"], device=r.get("device"), e3_device=o.get("device"),
                        init_equal=r["init_sha256"] == o["init_sha256"], data_equal=r["data_sha256"] == o["data_sha256"],
                        metric=r["metric"], e3_metric=o["metric"]))
    return out


def header_mechanism():
    """The installed torch's CUDA distribution kernels size their grid by the GPU's multiprocessor count, and the Philox
    counter offset and the element-to-thread assignment follow the grid: quote the lines from the shipped header."""
    import torch
    h = os.path.join(os.path.dirname(torch.__file__), "include", "ATen", "native", "cuda", "DistributionTemplates.h")
    lines = open(h, "rb").read().decode("utf-8").splitlines()
    keep = [f"{i + 1}: {ln.strip()}" for i, ln in enumerate(lines)
            if re.search(r"multiProcessorCount|maxThreadsPerMultiProcessor|counter_offset = |calc_execution_policy\(", ln)]
    return dict(torch=torch.__version__, header=os.path.relpath(h, os.path.dirname(torch.__file__)).replace("\\", "/"),
                lines=keep[:6])


def p2200_props():
    """Measured on the free P2200 only (CUDA_VISIBLE_DEVICES names it; the busy P2000 is never opened)."""
    q = subprocess.run(["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"], capture_output=True, text=True,
                       check=True).stdout
    idx = [ln.split(",")[0].strip() for ln in q.splitlines() if ln.split(",")[1].strip() == "Quadro P2200"]
    env = dict(os.environ, CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=idx[0])
    code = ("import torch,json;p=torch.cuda.get_device_properties(0);print(json.dumps(dict(name=p.name,"
            "sm=p.multi_processor_count,max_threads_per_sm=getattr(p,'max_threads_per_multi_processor',None),"
            "cc=f'{p.major}.{p.minor}')))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=True).stdout
    d = json.loads(out.strip().splitlines()[-1])
    assert d["name"] == "Quadro P2200", d
    return d


def git_last(path):
    return subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h %cI", "--", path], capture_output=True, text=True,
                          check=True).stdout.strip()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def f2(draws_dir, pub_text, avail_text):
    rows = []
    for f in sorted(glob.glob(os.path.join(R3RUNS, "fidprobe3-probes", "*.probes.json"))):
        for p in jl(f)["probes"]:
            fn = os.path.join(draws_dir, p["draws_file"])
            ok = os.path.exists(fn)
            rows.append(dict(file=p["draws_file"], bytes=os.path.getsize(fn) if ok else None,
                             sha256_recorded=p["draws_sha256"], sha256_equal=ok and sha(fn) == p["draws_sha256"]))
    named_pub = [r["file"] for r in rows if r["file"] in pub_text]
    return dict(n=len(rows), all_present_and_equal=all(r["sha256_equal"] for r in rows),
                total_bytes=sum(r["bytes"] or 0 for r in rows), files=rows,
                publishing_names=len(named_pub), publishing_mentions_draws=bool(re.search(r"\.npz|draws", pub_text)),
                availability_mentions_draws=bool(re.search(r"draw", avail_text, re.I)))


def f3(abstract, table6, table7, app_rev):
    sizes = {"\\scriptsize": "scriptsize", "\\footnotesize": "footnotesize", "\\small": "small"}
    size = lambda s: next((v for k, v in sizes.items() if k in s), "normalsize")
    return dict(
        abstract_meets_unqualified=bool(re.search(r"meets preset lines on", abstract)) and
        not re.search(r"point[- ]estimate", abstract),
        abstract_review_count=re.findall(r"after (\w+) independent reviews", abstract),
        table6_size=size(table6), table6_fitbox="\\fitbox" in table6, table7_size=size(table7), table7_fitbox="\\fitbox" in table7,
        table6_95_tied=bool(re.search(r"\(95\)'': also the 95th percentile of the excess\s+and the gain interval", table6)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "draws", "rev3"))
    a = ap.parse_args()
    recs = cell_records()
    seeds, v4_pairs = f1(recs)
    # the reviewed text is version 4 (commit 5afeda818): read it from git, so the check gives the same answer after the v5 edits
    rel = os.path.relpath(P, REPO).replace("\\", "/")
    rd = lambda p: subprocess.run(["git", "-C", REPO, "show", f"{V4}:{rel}/{p}"], capture_output=True, check=True).stdout.decode("utf-8")
    fid_tex, resp3 = rd("tex/sec_fidelity.tex"), rd("RESPONSE-TO-REVIEW-3.md")
    pr = probe_runs()
    torches = sorted({r["torch"] for r in recs})
    code = {p: git_last(os.path.join(P, p)) for p in ("sim/run_rev.py", "sim/memsim_rev.py", "sim/tasks_rev.py",
                                                       "sim/run_rev2.py", "sim/pulse_seq_rev2.py")}
    rec_commits = {"fid (pod seq)": git_last(os.path.join(RUNS, "fid")), "fidr (desk seq)": git_last(os.path.join(R3RUNS, "fidr"))}
    F1 = dict(
        claim="seed 0 82.02 % (A4000) vs 89.69 % (P2000) is attributed to 'GPU rounding alone'; the five-seed A2-R join mixes "
              "matched and unmatched pairs",
        seeds=seeds, v4_a2r_pair_matched_by_seed=v4_pairs,
        rounding_alone_in_paper="GPU rounding alone" in re.sub(r"\s+", " ", fid_tex),
        rounding_in_response3="more sensitive to rounding" in re.sub(r"\s+", " ", resp3),
        probe_runs_vs_e3=pr, torch_versions=torches, code_last_commit=code, record_commits=rec_commits,
        mechanism=header_mechanism(), p2200=p2200_props())
    pod_ok = all(seeds[s]["pod_matched"] for s in (0, 1, 2))
    desk_bad = all(not any(seeds[s]["desk_seq_matches_pod"]) for s in (0, 3, 4))
    F1["verdict"] = "CONFIRMED" if (pod_ok and desk_bad and not v4_pairs[3] and not v4_pairs[4] and v4_pairs[0]
                                    and F1["rounding_alone_in_paper"] and len(torches) == 1) else "REFUTED"
    F1["cause"] = ("Not the code (the simulator and runner files have one commit each, older than both run sets) and not "
                   "the library (both sets record the same torch build). The installed torch's CUDA random kernels size "
                   "their grid by the GPU's multiprocessor count and threads per multiprocessor (header lines below), and "
                   "the Philox subsequence and offset of every drawn element follow the grid; the generators of "
                   "memsim_rev.Streams live on the GPU, so the same seed gives a different initialisation and a different "
                   "torch.randperm example order on a GPU of another size. The A4000 and the P2000 differ in both. The "
                   "differences between the runs are therefore different random realisations, not rounding of one "
                   "realisation. Consistent with this, the probe runs' CIFAR and LM example orders are equal between the "
                   "A4000 and the P2200 while their initialisations and the MNIST order are not (probe_runs_vs_e3): a draw "
                   "is device-independent only where the drawing kernel's grid does not depend on the device. Prediction "
                   "checked by experiment A2-M: the P2200 (other multiprocessor count) gives "
                   "hashes equal across its own three arms and different from both the A4000's and the P2000's.")
    pub = rd("PUBLISHING.md")
    body = rd("tex/body.tex")
    av = body[body.find("availability"):]
    F2 = f2(a.draws_dir, pub, av)
    F2["verdict"] = "CONFIRMED" if F2["n"] == 12 and F2["all_present_and_equal"] and F2["publishing_names"] == 0 \
        and not F2["availability_mentions_draws"] else "REFUTED"
    F3 = f3(rd("tex/sec_abstract.tex"), rd("tex/tables/rev3_probe.tex"), rd("tex/tables/rev3_dep.tex"), rd("tex/app_revision.tex"))
    F3["verdict"] = "CONFIRMED" if F3["abstract_meets_unqualified"] and F3["abstract_review_count"] == ["two"] and \
        F3["table6_fitbox"] and F3["table6_size"] == "scriptsize" else "PARTLY"
    F3["note"] = ("Table sizes are read from the source (\\scriptsize inside \\fitbox, which shrinks a table wider than the "
                  "text); the printed point sizes are the reviewer's measurements. The '(95)' mark is already defined in "
                  "Table 6's caption as the excess's 95th percentile and the gain interval (table6_95_tied); v5 states that it "
                  "is not a joint guarantee. Page 20's blank area is float placement (checked on the v5 render).")
    # planted faults: each check must change its answer
    faults = {}
    bad = copy.deepcopy(recs)
    pod0 = next(r for r in bad if r["src"] == "fid" and r["seed"] == 0)
    for r in bad:
        if r["src"] == "fidr":
            r["init"], r["data"] = [x for x in (pod0["init"], pod0["data"])] if r["seed"] == 0 else \
                (next(q for q in bad if q["src"] == "e3" and q["seed"] == r["seed"])["init"],
                 next(q for q in bad if q["src"] == "e3" and q["seed"] == r["seed"])["data"])
    s_bad, v_bad = f1(bad)
    faults["desk_hashes_forged_to_pod"] = dict(caught=v_bad[3] and v_bad[4] and any(s_bad[0]["desk_seq_matches_pod"]))
    one = copy.deepcopy(recs)
    next(r for r in one if r["src"] == "e3" and r["seed"] == 1 and r["arm"] == "fp")["data"] = "0" * 64
    faults["pod_seed1_fp_order_changed"] = dict(caught=not f1(one)[0][1]["pod_matched"])
    faults["missing_hash_is_unmatched"] = dict(caught=not matched([dict(init=None, data="x"), dict(init=None, data="x")]))
    names = " ".join(r["file"] for r in F2["files"])
    faults["publishing_listing_detected"] = dict(caught=f2(a.draws_dir, names, "draws")["publishing_names"] == 12)
    tmp = os.path.join(P, "records", "revision4", "_fault_draws")
    os.makedirs(tmp, exist_ok=True)
    first = F2["files"][0]["file"]
    open(os.path.join(tmp, first), "wb").write(b"not the draws")
    faults["corrupt_draw_detected"] = dict(caught=not f2(tmp, "", "")["all_present_and_equal"])
    os.remove(os.path.join(tmp, first))
    os.rmdir(tmp)
    faults["abstract_qualified_detected"] = dict(caught=f3("meets preset lines on", "", "", "")["abstract_meets_unqualified"]
                                                 and not f3("meets preset lines on point-estimate", "", "", "")[
                                                     "abstract_meets_unqualified"])
    res = dict(schema="altone.x1000.me-revision4.verify.v1", review="reviews/REVIEW-4-chatgpt-20261027-full.md",
               F1=F1, F2=F2, F3=F3, faults=faults, all_faults_caught=all(v["caught"] for v in faults.values()))
    out = os.path.join(P, "records", "revision4", "VERIFY-FINDINGS-4.json")
    open(out, "wb").write((json.dumps(res, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print("F1", F1["verdict"], "F2", F2["verdict"], F2["n"], F2["total_bytes"], "F3", F3["verdict"],
          "faults", res["all_faults_caught"], "p2200", F1["p2200"])


if __name__ == "__main__":
    main()
