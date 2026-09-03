#!/usr/bin/env python3
"""EXP-023A: contextualized CE input over the exact stored SYSTEM-J membership.

One scoring change only: the passage handed to the frozen CE becomes
    DOCUMENT TITLE \n SECTION PATH \n\n CANONICAL CHUNK TEXT
Membership, model, tokenizer and decode settings are unchanged. Metric helpers
are imported from the snapshot so definitions match EXP-022A-R1 exactly rather
than being reimplemented.
"""
from __future__ import annotations
import hashlib, json, os, struct, sys, time
from collections import Counter
from datetime import UTC, datetime
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

from cross_encoder import CE_SHA256, CE_TOKENIZER                      # noqa: E402
from run_exp017 import load_control_chunks                             # noqa: E402
from run_exp018_development import first_span_rank, span_in_hits       # noqa: E402
from run_exp019b import mcnemar_exact                                  # noqa: E402
from run_exp021a import hits_from_ids, load_validation                 # noqa: E402
from system_e import TOP_K, covering_chunk_ids                         # noqa: E402
from v2_system_g_ce import make_v2_system_g_d1_reranker                # noqa: E402
from tokenizers import Tokenizer                                       # noqa: E402

POOLS = ROOT / "experiments/RAG-V2/EXP-021A/logs/EXP-021A-pools.jsonl"
BASE_LOGITS = ROOT / "experiments/RAG-V2/EXP-022A-R1/logs/EXP-022A-R1-raw-ce-logits.jsonl"
LOGITS_OUT = OUT / "logs/EXP-023A-raw-ce-logits.jsonl"
PREREG_SHA = (OUT / "EXP-023A-preregistration.json.sha256").read_text().strip()

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def logit_hex(x): return struct.pack("<d", x).hex(), struct.pack(">d", x).hex()
def input_hash(cid, chunk, q, text):
    h = hashlib.sha256()
    for part in (cid, chunk, q, text):
        h.update(part.encode()); h.update(b"\x00")
    return h.hexdigest()

def section_str(sp): return " > ".join(str(x) for x in sp) if sp else ""

def contextualize(title, sp, text):
    """DOCUMENT TITLE \n SECTION PATH \n\n TEXT. Missing parts are omitted, never invented."""
    head = [x for x in (title or "", section_str(sp)) if x]
    return ("\n".join(head) + "\n\n" + text) if head else text

# ---- inputs -----------------------------------------------------------------
if sha_file(BASE_LOGITS) != "abd00619d538a5a497c36cf588b9d4eeed760ca343aaf1925ce466b3619c677c":
    raise SystemExit("STOP: baseline raw-logit sha mismatch")
base = {}
for line in BASE_LOGITS.read_text().splitlines():
    r = json.loads(line); base[(r["case_id"], r["chunk_id"])] = r["raw_ce_logit"]
if len(base) != 7485:
    raise SystemExit(f"STOP: baseline has {len(base)} unique pairs, expected 7485")

raw_rows, cases = load_validation()
pools = {}
for line in POOLS.read_text().splitlines():
    r = json.loads(line); pools[r["case_id"]] = r
chunks = load_control_chunks()

import psycopg                                                          # noqa: E402
with psycopg.connect(os.environ["DATABASE_URL"]) as c, c.cursor() as cur:
    cur.execute("""SELECT dv.version_id, ds.title, ds.provider FROM document_version dv
                   JOIN document_source ds ON ds.source_id = dv.source_id""")
    meta = {v: {"title": t, "provider": pr} for v, t, pr in cur.fetchall()}

j_ids_by_case = {cid: list(p["system_j_union_ids"]) for cid, p in pools.items()}
n_pairs = sum(len(v) for v in j_ids_by_case.values())
membership_equal = (sorted((c, k) for c, ks in j_ids_by_case.items() for k in ks)
                    == sorted(base.keys()))
print(f"queries={len(cases)} pairs={n_pairs} membership_identical_to_baseline={membership_equal}")
if not membership_equal or n_pairs != 7485 or len(cases) != 40:
    raise SystemExit("STOP: membership does not match SYSTEM-J exactly")

# ---- score ------------------------------------------------------------------
if LOGITS_OUT.exists():
    raise SystemExit("STOP: contextualized logits already exist; refusing to append")
LOGITS_OUT.parent.mkdir(parents=True, exist_ok=True)
ce = make_v2_system_g_d1_reranker()
if ce.artifact_sha256 != CE_SHA256 or ce.fast or ce.threads != 4 or ce.pad != "batch" or not ce.bucket_by_length:
    raise SystemExit("STOP: CE constructor drift")
tok = Tokenizer.from_file(str(CE_TOKENIZER)); tok.enable_truncation(max_length=512, strategy="longest_first")
tok_full = Tokenizer.from_file(str(CE_TOKENIZER))  # no truncation: measures true lengths
tok_sha = sha_file(CE_TOKENIZER)

lat, rows_written = [], 0
ctx_scores = {}
with LOGITS_OUT.open("w") as fh:
    for case in cases:
        jid = j_ids_by_case[case.case_id]
        texts, titles, secs, blens, clens, lost = [], [], [], [], [], []
        for cid in jid:
            ch = chunks[cid]; m = meta.get(ch["version_id"], {})
            t = m.get("title"); sp = ch["section_path"]
            ctx = contextualize(t, sp, ch["text"])
            texts.append(ctx); titles.append(t or ""); secs.append(section_str(sp))
            b_true = len(tok_full.encode(case.question, ch["text"]).ids)
            c_true = len(tok_full.encode(case.question, ctx).ids)
            blens.append(b_true); clens.append(c_true)
            # chunk-text tokens lost to truncation that the metadata caused
            b_kept = min(b_true, 512); c_kept = min(c_true, 512)
            meta_tokens = c_true - b_true
            lost.append(max(0, (b_true - b_kept) - 0) if False else max(0, min(meta_tokens, c_true - 512) if c_true > 512 else 0))
        t0 = time.perf_counter()
        scores = ce.score_pairs(case.question, texts, batch_size=16)
        lat.append((time.perf_counter() - t0) * 1000.0)
        for i, (cid, s) in enumerate(zip(jid, scores, strict=True)):
            s = float(s); hx, be = logit_hex(s)
            ctx_scores[(case.case_id, cid)] = s
            fh.write(json.dumps({
                "case_id": case.case_id, "chunk_id": cid, "raw_ce_logit": s,
                "raw_ce_logit_hex": hx, "raw_ce_logit_be64_hex": be,
                "document_title_used": titles[i], "section_path_used": secs[i],
                "candidate_input_hash": input_hash(case.case_id, cid, case.question, texts[i]),
                "ce_artifact_sha": ce.artifact_sha256, "tokenizer_sha256": tok_sha,
                "baseline_token_length": blens[i], "contextualized_token_length": clens[i],
                "truncated": clens[i] > 512,
                "baseline_truncated": blens[i] > 512,
                "metadata_caused_new_truncation": (clens[i] > 512) and (blens[i] <= 512),
                "chunk_tokens_lost_to_truncation": lost[i],
                "max_length": 512,
            }, ensure_ascii=True) + "\n")
            rows_written += 1
jsonl_sha = sha_file(LOGITS_OUT)
(OUT / "logs/EXP-023A-raw-ce-logits.jsonl.sha256").write_text(jsonl_sha + "\n")
print(f"wrote {rows_written} contextualized logits, sha {jsonl_sha}")
json.dump({"prereg_sha": PREREG_SHA, "logits_sha": jsonl_sha, "rows": rows_written,
           "latency_ms_per_query": lat, "membership_equal": membership_equal},
          open(OUT / "logs/EXP-023A-run-meta.json", "w"), indent=1)
