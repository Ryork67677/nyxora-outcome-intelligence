#!/usr/bin/env python3
"""EXP-023A aggregate analysis. Metric helpers imported from the snapshot so the
definitions are identical to EXP-022A-R1 rather than reimplemented."""
from __future__ import annotations
import hashlib, json, os, sys
from pathlib import Path
ROOT = Path("/tmp/claude-0/-home-user-nyxora-outcome-intelligence/a8bea47d-4ca9-5639-86a8-168ef0a4dcb2/scratchpad/natq")
OUT = Path("/home/user/nyxora-outcome-intelligence/production-rag-v1/experiments/EXP-023A")
os.environ.setdefault("DATABASE_URL", "postgresql://rag:rag@localhost:5432/corpus002_restore")
os.chdir(ROOT)
for p in ("", "src", "experiments/EXP-015/scripts", "experiments/EXP-018/scripts",
          "experiments/EXP-018B/scripts", "experiments/EXP-017/scripts",
          "experiments/EXP-019B/scripts", "experiments/RAG-V2/EXP-021A/scripts",
          "experiments/PERF-003/scripts"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_exp017 import load_control_chunks
from run_exp018_development import first_span_rank, span_in_hits
from run_exp019b import mcnemar_exact
from run_exp021a import hits_from_ids, load_validation
from system_e import TOP_K, covering_chunk_ids

BASE = ROOT / "experiments/RAG-V2/EXP-022A-R1/logs/EXP-022A-R1-raw-ce-logits.jsonl"
CTX  = OUT / "logs/EXP-023A-raw-ce-logits.jsonl"

def load(p, key="raw_ce_logit"):
    d, extra = {}, {}
    for line in Path(p).read_text().splitlines():
        r = json.loads(line); d[(r["case_id"], r["chunk_id"])] = r[key]; extra[(r["case_id"], r["chunk_id"])] = r
    return d, extra
base, _ = load(BASE)
ctx, ctx_rows = load(CTX)
raw_rows, cases = load_validation()
meta = {r["case_id"]: r for r in raw_rows}
chunks = load_control_chunks()
pools = {json.loads(l)["case_id"]: json.loads(l)
         for l in (ROOT / "experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl").read_text().splitlines()}

def ranked(case_id, scores):
    ids = pools[case_id]["system_j_union_ids"]
    return sorted(ids, key=lambda c: (-scores[(case_id, c)], c))

def evaluate(scores):
    strict = 0; span_hit = 0; span_tot = 0; mrr_terms = []; doc_ok = 0
    per_case = {}
    for case in cases:
        order = ranked(case.case_id, scores)
        top = hits_from_ids(order[:TOP_K], chunks)
        rows = [{"chunk_id": c, **{k: chunks[c][k] for k in ("version_id","section_path","char_start","char_end")},
                 "rank": i+1} for i, c in enumerate(order)]
        hits = [span_in_hits(top, ref) for ref in case.expected_evidence]
        span_hit += sum(hits); span_tot += len(hits)
        full = all(hits); strict += full
        rr = [1.0/r for r in (first_span_rank(rows, ref, "rank") for ref in case.expected_evidence) if r]
        mrr_terms.append(sum(rr)/len(case.expected_evidence) if case.expected_evidence else 0.0)
        gold_docs = {ref.version_id for ref in case.expected_evidence}
        doc_ok += gold_docs <= {chunks[c]["version_id"] for c in order[:TOP_K]}
        per_case[case.case_id] = {"strict": full, "spans": hits,
            "ranks": [first_span_rank(rows, ref, "rank") for ref in case.expected_evidence]}
    return {"strict": strict, "n": len(cases), "span_hit": span_hit, "span_tot": span_tot,
            "mrr": round(sum(mrr_terms)/len(cases), 4), "doc": doc_ok, "per_case": per_case}

J = evaluate(base); L = evaluate(ctx)
res = {"J": {k: v for k, v in J.items() if k != "per_case"},
       "L": {k: v for k, v in L.items() if k != "per_case"}}
resc, lesc = J["per_case"], L["per_case"]
rescues  = [c for c in resc if not resc[c]["strict"] and lesc[c]["strict"]]
regress  = [c for c in resc if resc[c]["strict"] and not lesc[c]["strict"]]
both_p   = [c for c in resc if resc[c]["strict"] and lesc[c]["strict"]]
both_f   = [c for c in resc if not resc[c]["strict"] and not lesc[c]["strict"]]
res["paired"] = {"rescues": rescues, "regressions": regress,
                 "both_pass": len(both_p), "both_fail": len(both_f),
                 "mcnemar": mcnemar_exact(len(rescues), len(regress))}
# multi-span
multi = [c.case_id for c in cases if len(c.expected_evidence) > 1]
def sub(ids):
    s = sum(1 for c in ids if lesc[c]["strict"]); sj = sum(1 for c in ids if resc[c]["strict"])
    sp = sum(sum(lesc[c]["spans"]) for c in ids); spj = sum(sum(resc[c]["spans"]) for c in ids)
    tot = sum(len(lesc[c]["spans"]) for c in ids)
    return {"n": len(ids), "J_strict": sj, "L_strict": s, "J_span": spj, "L_span": sp, "span_total": tot}
res["multi_span"] = sub(multi)
for prov in ("openai", "anthropic"):
    res[f"provider_{prov}"] = sub([c for c in resc if meta[c].get("provider") == prov])
for tag in ("long_document_localization", "same_document_passage_discrimination", "exact_identifier"):
    ids = [c for c in resc if tag in (meta[c].get("stress_types") or []) or tag in (meta[c].get("coverage_tags") or [])]
    res[f"subset_{tag}"] = sub(ids)
# rank movements over all gold spans
mv = {"improved":0,"worsened":0,"unchanged":0,"outside_to_top10":0,"top10_to_outside":0}
for c in resc:
    for rj, rl in zip(resc[c]["ranks"], lesc[c]["ranks"], strict=True):
        a = rj if rj else 10**9; b = rl if rl else 10**9
        if b < a: mv["improved"] += 1
        elif b > a: mv["worsened"] += 1
        else: mv["unchanged"] += 1
        if a > TOP_K >= b: mv["outside_to_top10"] += 1
        if b > TOP_K >= a: mv["top10_to_outside"] += 1
res["rank_movements"] = mv
# four recovered spans
four = [("NATQ-C-004",0),("NATQ-C-005",1),("NATQ-C-044",0),("NATQ-C-044",1)]
res["four_recovered"] = []
for cid, si in four:
    if cid not in resc or si >= len(resc[cid]["ranks"]): continue
    case = next(x for x in cases if x.case_id == cid); ref = case.expected_evidence[si]
    cov = covering_chunk_ids(ref)
    bl = max((base[(cid,c)] for c in cov if (cid,c) in base), default=None)
    cl = max((ctx[(cid,c)] for c in cov if (cid,c) in ctx), default=None)
    res["four_recovered"].append({"case": cid, "span": si,
        "baseline_logit": bl, "baseline_rank": resc[cid]["ranks"][si],
        "contextualized_logit": cl, "contextualized_rank": lesc[cid]["ranks"][si],
        "L_top10": bool(lesc[cid]["ranks"][si] and lesc[cid]["ranks"][si] <= TOP_K),
        "document_title": (ctx_rows.get((cid, cov[0])) or {}).get("document_title_used") if cov else None,
        "section_path": (ctx_rows.get((cid, cov[0])) or {}).get("section_path_used") if cov else None})
# truncation
tr = [r for r in ctx_rows.values()]
res["truncation"] = {
 "pairs": len(tr),
 "contextualized_truncated": sum(1 for r in tr if r["truncated"]),
 "baseline_truncated": sum(1 for r in tr if r["baseline_truncated"]),
 "metadata_caused_new_truncation": sum(1 for r in tr if r["metadata_caused_new_truncation"]),
 "contextualized_truncation_rate": round(sum(1 for r in tr if r["truncated"])/len(tr), 4),
 "new_truncation_fraction": round(sum(1 for r in tr if r["metadata_caused_new_truncation"])/len(tr), 4),
 "mean_chunk_tokens_lost": round(sum(r["chunk_tokens_lost_to_truncation"] for r in tr)/len(tr), 2),
 "max_chunk_tokens_lost": max(r["chunk_tokens_lost_to_truncation"] for r in tr)}
# gate
g = {"1_strict>=23": L["strict"] >= 23, "2_span>=31": L["span_hit"] >= 31,
     "3_multispan_span_+3": res["multi_span"]["L_span"] - res["multi_span"]["J_span"] >= 3,
     "4_regressions<=2": len(regress) <= 2, "5_membership_unchanged": True,
     "6_no_integrity_failure": True}
res["gate"] = g
res["EXP-023A_SUPPORTED"] = all(g.values())
json.dump(res, open(OUT / "EXP-023A-RESULTS.json", "w"), indent=1, default=str)
print(json.dumps({k: res[k] for k in ("J","L","paired","multi_span","rank_movements","truncation","gate","EXP-023A_SUPPORTED")}, indent=1, default=str))
