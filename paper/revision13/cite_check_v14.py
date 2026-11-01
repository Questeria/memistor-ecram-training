"""Version 14 (review 11): verify the references that review 11 raised, with cite/cite_check.py's own functions, and add the new
one to the paper's citation check.

  byun2024   10.1002/aisy.202400543   NEW: Byun et al., "Device Specifications for Neural Network Training with Analog Resistive
                                      Cross-Point Arrays Using Tiki-Taka Algorithms", Advanced Intelligent Systems (Crossref)
  xu2026     10.1021/acsnano.6c09861  ALREADY CITED since version 2; review 11 names it by PubMed id 42915660: the PubMed record
                                      (NCBI E-utilities) must carry this DOI, title and authors, and its abstract the 3 % and 21 %
                                      the paper prints

The Byun entry is written into tex/refs.bib from the fetched Crossref metadata by cite_check.bib_from_meta (after gokmen2021, as in
cite_check.REFS), its row is appended to records/CITE-CHECK.json (n 48 -> 49; the row carries its own check time), and every fetched
field, with the key phrases checked in the abstract, goes to records/revision13/CITE-CHECK-v14.json.  Refuses if byun2024 is already
in refs.bib.  The Wiley landing page answered 403 (a bot challenge) and is not used; the abstract is Crossref's copy (its SHA-256 is
recorded, not its text).

    python -I -B revision13/cite_check_v14.py          (network: api.crossref.org, eutils.ncbi.nlm.nih.gov)
"""
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path

P = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cite_check", P / "cite" / "cite_check.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def crossref_full(doi):
    st, b = C.get("https://api.crossref.org/works/" + doi)
    return json.loads(b.decode("utf-8"))["message"]


def phrases(text, want):
    flat = " ".join(re.sub(r"<[^>]+>", " ", text).replace("‐", "-").split()).lower()
    return {w: (w.lower() in flat) for w in want}


bib = (P / "tex" / "refs.bib").read_bytes().decode("utf-8")
assert "@article{byun2024," not in bib, "byun2024 is already in refs.bib"
row_of = {r[0]: r for r in C.REFS}
assert row_of["byun2024"][2] == "10.1002/aisy.202400543"

# --- Byun et al. (Crossref) ---
m = C.crossref("10.1002/aisy.202400543")
full = crossref_full("10.1002/aisy.202400543")
abs_b = full.get("abstract") or ""
byun = dict(key="byun2024", kind="doi", id="10.1002/aisy.202400543", source="api.crossref.org", checked_at_utc=NOW,
            fetched_title=m["title"], authors=[" ".join(x[::-1]).strip() for x in m["authors"]], year=m["year"], venue=m["venue"],
            volume=m.get("volume"), issue=m.get("issue"), pages=m.get("pages"), crossref_type=m.get("type"),
            published_online=(full.get("published-online") or {}).get("date-parts"),
            published_print=(full.get("published-print") or {}).get("date-parts"))
byun["verified"] = bool(row_of["byun2024"][3] in m["title"].lower() and m["authors"] and m["year"])
byun_detail = dict(abstract_sha256=hashlib.sha256(abs_b.encode("utf-8")).hexdigest(), abstract_chars=len(abs_b),
                   abstract_phrases=phrases(abs_b, ["Tiki-Taka algorithm versions 1 (TTv1) and 2 (TTv2)",
                                                    "asymmetry, retention, number of pulses, and cycle-to-cycle variation",
                                                    "pattern-recognition accuracy", "stochastic gradient descent",
                                                    "TTv2 permits more lenient device specifications than the TTv1"]),
                   not_in_abstract=phrases(abs_b, ["chopped", "AGAD", "ECRAM", "language model", "CIFAR"]),
                   landing_page="https://advanced.onlinelibrary.wiley.com/doi/10.1002/aisy.202400543: HTTP 403 (bot challenge); not used")
assert byun["verified"] and all(byun_detail["abstract_phrases"].values()), (byun, byun_detail)
entry = C.bib_from_meta("byun2024", "doi", m)
assert "‐" not in entry and "Cross-Point" in entry and "Tiki-Taka" in entry, entry

# --- Xu et al. (PubMed and Crossref) ---
st, b = C.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=42915660&retmode=json")
pm = json.loads(b.decode("utf-8"))["result"]["42915660"]
st, ab = C.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=42915660&rettype=abstract&retmode=text")
ab = ab.decode("utf-8", "replace")
mx = C.crossref("10.1021/acsnano.6c09861")
pm_doi = [a["value"] for a in pm.get("articleids", []) if a.get("idtype") == "doi"]
xu = dict(key="xu2026", pubmed_id="42915660", checked_at_utc=NOW, source="eutils.ncbi.nlm.nih.gov (esummary, efetch) and api.crossref.org",
          pubmed_title=pm.get("title"), pubmed_authors=[a["name"] for a in pm.get("authors", [])], pubmed_source=pm.get("source"),
          pubmed_date=pm.get("pubdate"), volume=pm.get("volume"), issue=pm.get("issue"), pages=pm.get("pages"), pubmed_doi=pm_doi,
          crossref_title=mx["title"], crossref_year=mx["year"],
          abstract_sha256=hashlib.sha256(ab.encode("utf-8")).hexdigest(),
          abstract_phrases=phrases(ab, ["cycle-to-cycle (CtoC) variability (3%)", "device-to-device (DtoD) variability (21%)",
                                        "back-end-of-line (BEOL)-compatible", "hardware training simulations"]),
          in_refs_bib="doi = {10.1021/acsnano.6c09861}" in bib)
xu["verified"] = bool(pm_doi == ["10.1021/acsnano.6c09861"] and "protonic electrochemical" in pm.get("title", "").lower()
                      and all(xu["abstract_phrases"].values()) and xu["in_refs_bib"])
assert xu["verified"], xu

# --- write refs.bib (after gokmen2021), CITE-CHECK.json, CITE-CHECK-v14.json ---
anchor = re.search(r"@article\{gokmen2021,.*?\n\}\n", bib, re.S)
bib = bib[:anchor.end()] + "\n" + entry + bib[anchor.end():]
(P / "tex" / "refs.bib").write_bytes(bib.encode("utf-8"))
cc_path = P / "records" / "CITE-CHECK.json"
cc = json.loads(cc_path.read_bytes().decode("utf-8"))
assert not any(r["key"] == "byun2024" for r in cc["refs"])
i = [r["key"] for r in cc["refs"]].index("gokmen2021")
cc["refs"].insert(i + 1, byun)
cc["n"], cc["n_verified"] = len(cc["refs"]), sum(r["verified"] for r in cc["refs"])
cc["added"] = [dict(key="byun2024", at_utc=NOW, by="revision13/cite_check_v14.py (version 14, review 11)")]
cc_path.write_bytes((json.dumps(cc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
rec = dict(schema="altone.x1000.me-paper.cite-check-v14.v1", checked_at_utc=NOW, review="reviews/REVIEW-11-chatgpt-20261031-full.md",
           added=dict(byun, **byun_detail, bib_entry=entry), confirmed_existing=xu,
           cite_check_json=dict(n=cc["n"], n_verified=cc["n_verified"]))
out = P / "records" / "revision13" / "CITE-CHECK-v14.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes((json.dumps(rec, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("byun2024 verified and added (%s %s, vol %s(%s) %s); xu2026 = PubMed 42915660 confirmed; CITE-CHECK.json %d / %d"
      % (m["venue"], m["year"], m.get("volume"), m.get("issue"), m.get("pages"), cc["n_verified"], cc["n"]))
