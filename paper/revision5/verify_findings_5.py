"""ME-REVISE-5: verify each finding of review 5 (reviews/REVIEW-5-chatgpt-20261027-full.md) against the files themselves, before any
repair.  Writes records/revision5/VERIFY-FINDINGS-5.json.  Run on the unrepaired state: build/v5/ (the archived version-5 build),
build/v4/, the exact LaTeX trees those HTMLs were built from (desk: H:/x1000/memistor-paper/rev4/build-v5b/tex, .../rev3/build-v4b/tex)
and tex/v5/ (the archived version-5 sources).

    python -B revision5/verify_findings_5.py
"""
import hashlib
import html as H
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import html_complete as HC  # noqa: E402

V5 = os.path.join(P, "build", "v5", "main.html")
V4 = os.path.join(P, "build", "v4", "main.html")
TEX5 = "H:/x1000/memistor-paper/rev4/build-v5b/tex"
TEX4 = "H:/x1000/memistor-paper/rev3/build-v4b/tex"
PANDOC_LOG = "H:/x1000/memistor-paper/rev4/build-v5b/out/pandoc.txt"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def visible(path):
    t = HC.html_text_blocks(open(path, encoding="utf-8").read())
    return " ".join(H.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def read(p):
    return open(p, "rb").read().decode("utf-8")


def main():
    r5, r4 = HC.check(TEX5, V5), HC.check(TEX4, V4)
    t5, t4 = visible(V5), visible(V4)
    out = dict(reviewed_html_sha256=sha(V5), review_cites_html_sha256="e8718e33f935a298d40b24697a79d2084f84cb578020ffc9973411ac03839fd9",
               review_cites_pdf_sha256="1d4cfb3c6d8d8fa085e802f0e0596525e8923d98d8bb2afe6786f08d59ad1f3f",
               pdf_sha256=sha(os.path.join(P, "build", "v5", "main.pdf")))
    out["same_files_as_reviewed"] = out["reviewed_html_sha256"] == out["review_cites_html_sha256"] and out["pdf_sha256"] == out["review_cites_pdf_sha256"]

    sentinels = {"Section 5 energy analysis (first sentence)": "This section is an accounting scenario, not an energy measurement", "Section 6 discussion": "Limitations",
                 "Section 7 roadmap": "A proposed roadmap for groups", "Section 8 conclusion": "Conclusion",
                 "Section 9 availability": "Code and data availability", "Author contributions and use of AI": "Author contributions and use of AI",
                 "Acknowledgments": "Acknowledgments", "Appendix A bench": "Bench replication of the 1960 memistor",
                 "Appendix B hyperparameter selection": "Hyperparameter selection", "Appendix C simulator checks (heading)": "Simulator checks and the planted faults",
                 "Section 4.5 explanatory text": "Around the protonic-inspired base we move one device property"}
    f1 = dict(finding="HTML export is incomplete (drops energy, discussion, roadmap, conclusion, availability, statements, two appendices)",
              headings_missing_v5=r5["headings"]["missing"], n_headings_source=r5["headings"]["n_source"], n_headings_html=r5["headings"]["n_html"],
              sentinels_absent_in_v5_html={k: (v not in t5) for k, v in sentinels.items()},
              pandoc_log_bytes=os.path.getsize(PANDOC_LOG) if os.path.exists(PANDOC_LOG) else None)
    f1["verdict"] = "CONFIRMED" if r5["headings"]["missing"] and all(f1["sentinels_absent_in_v5_html"].values()) else "PARTLY"
    out["F1"] = f1

    # F2: the caption of tab:rev_spec with the rows of the simulator-checks table
    m = re.search(r'<div id="tab:rev_spec">\s*<table.*?</table>', HC.html_text_blocks(open(V5, encoding="utf-8").read()), flags=re.S)
    tb = m.group(0) if m else ""
    heads = [" ".join(H.unescape(re.sub(r"<[^>]+>", "", x)).split()) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb, flags=re.S)]
    rows = [" ".join(H.unescape(re.sub(r"<[^>]+>", "", x)).split()) for x in re.findall(r"<td[^>]*>(.*?)</td>", tb, flags=re.S)]
    cap = re.search(r"<caption>(.*?)</caption>", tb, flags=re.S)
    src_tables = HC.source_tables(HC.flatten(TEX5))
    spec = next(s for s in src_tables if s["caption"].startswith("Revised sensitivity sheet"))
    f2 = dict(finding="rows of the simulator-checks table sit under the sensitivity table's caption",
              caption_starts=" ".join(H.unescape(re.sub(r"<[^>]+>", "", cap.group(1))).split())[:70] if cap else None,
              html_header_cells=[h for h in heads if h], html_first_cells=[c for c in rows if c][:3],
              source_header_row=spec["rows"][0][:60], source_first_data_row=spec["rows"][1][:50],
              n_sensitivity_rows_in_source=len(spec["rows"]) - 1, tables_check_problems_v5=r5["tables"]["problems"])
    f2["verdict"] = "CONFIRMED" if heads and "Check" in heads and any(c.startswith("c_asym_drift") for c in rows) else "REFUTED"
    out["F2"] = f2

    # F3 and F4: unresolved references
    def refs(t):
        return sorted(set(re.findall(r"\[((?:sec|tab|fig|app|eq):[^\]\s]+)\]", t)))
    hc = lambda p: subprocess.run([sys.executable, "-B", os.path.join(P, "pod", "html_check.py"), p], capture_output=True, text=True).returncode
    f3 = dict(finding="nine reference labels are unresolved in the HTML", unresolved_v5=refs(t5), n=len(refs(t5)),
              old_html_check_rc_v5=hc(V5), note="pod/html_check.py (rc 0) greps raw \\ref, \\cite, '[@' and '???' only; pandoc prints an unresolved \\ref as [label]")
    f3["verdict"] = "CONFIRMED" if f3["n"] == 9 else ("PARTLY" if f3["n"] else "REFUTED")
    out["F3"] = f3
    f4 = dict(finding="v4 HTML has the same defect and earlier checks missed it", unresolved_v4=refs(t4), n=len(refs(t4)),
              headings_missing_v4=r4["headings"]["missing"], tables_problems_v4=r4["tables"]["problems"][:3],
              old_html_check_rc_v4=hc(V4), same_as_v5=refs(t4) == refs(t5) and r4["headings"]["missing"] == r5["headings"]["missing"])
    f4["verdict"] = "CONFIRMED" if f4["n"] and f4["headings_missing_v4"] and f4["old_html_check_rc_v4"] == 0 else "PARTLY"
    out["F4"] = f4

    # F5: the two wording corrections
    rev = read(os.path.join(P, "tex", "v5", "app_revision.tex"))
    fid = read(os.path.join(P, "tex", "v5", "sec_fidelity.tex"))
    body = read(os.path.join(P, "tex", "v5", "body.tex"))
    # PUBLISHING.md as committed for version 5 (HEAD before the version-6 commit), not the edited working copy
    pub = subprocess.run(["git", "show", "0c2073426:ops/x1000-20261023/phase2/memistor/paper/PUBLISHING.md"], capture_output=True, cwd=P).stdout.decode("utf-8")
    reb = read(os.path.join(P, "revision4", "rebuild_draw_tables.py"))
    a = re.sub(r"\s+", " ", rev)
    f5a = dict(finding="Appendix F says the saved draws 'joined the deposit' while Section 9 says nothing has been deposited",
               appendix_f_phrase="joined the deposit" in a, section9_nothing_deposited="Nothing has been deposited publicly yet" in re.sub(r"\s+", " ", body))
    f5a["verdict"] = "CONFIRMED" if f5a["appendix_f_phrase"] and f5a["section9_nothing_deposited"] else "REFUTED"
    out["F5a"] = f5a
    f = re.sub(r"\s+", " ", fid)
    f5b = dict(finding="'rebuilt from the arrays alone' is too broad: the script also uses the probe records",
               phrase_in_sec_fidelity="can be rebuilt from them alone" in f, phrase_in_PUBLISHING="from the arrays alone" in re.sub(r"\s+", " ", pub),
               script_deepcopies_probe_record="out = copy.deepcopy(p)" in reb,
               script_reads_draws_sha_boot_layer_from_record=all(k in reb for k in ('p["draws_sha256"]', 'p["draws"]', 'p["layer"]', 'p[nm]["paired"]["boot"]')),
               lost_frac_copied_not_recomputed=("lost_frac" in read(os.path.join(P, "sim", "run_rev3.py")) and "lost_frac" not in reb))
    f5b["verdict"] = "CONFIRMED" if (f5b["phrase_in_sec_fidelity"] and f5b["phrase_in_PUBLISHING"] and f5b["script_deepcopies_probe_record"]
                                     and f5b["lost_frac_copied_not_recomputed"]) else "PARTLY"
    out["F5b"] = f5b
    out["verdicts"] = {k: out[k]["verdict"] for k in ("F1", "F2", "F3", "F4", "F5a", "F5b")}
    dest = os.path.join(P, "records", "revision5", "VERIFY-FINDINGS-5.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print(out["verdicts"], "same_files_as_reviewed", out["same_files_as_reviewed"])


if __name__ == "__main__":
    main()
