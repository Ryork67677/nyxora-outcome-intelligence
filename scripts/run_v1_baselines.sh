#!/usr/bin/env bash
# Reproduce the full V1 experiment sequence end to end.
#
# Prerequisites:
#   * PostgreSQL with pgvector reachable at $DATABASE_URL, schema from sql/001_init.sql
#   * the corpus fetched:  python scripts/fetch_corpus.py
#
# EXP-NULL additionally needs a generation credential. Without one it records
# status "blocked" in its results file and the rest of the sequence continues,
# which is deliberate: a control that did not run must stay visible.
set -euo pipefail

MANIFEST=${MANIFEST:-data/manifests/v1-openai-anthropic.yaml}
GOLDEN=${GOLDEN:-evals/golden/v1.jsonl}
SNAPSHOT_NAME=${SNAPSHOT_NAME:-v1-openai-anthropic}
K=${K:-10}

json_field() { python -c "import json,sys;print(json.loads(sys.stdin.read().replace(chr(39),chr(34)))['$1'])"; }

ragv1 ingest "$MANIFEST"
SNAPSHOT=$(ragv1 snapshot-create "$SNAPSHOT_NAME" | tr -d '\n' | json_field snapshot_id)
echo "Snapshot: $SNAPSHOT"

# The golden set is regenerated against the snapshot so evidence anchors follow a
# re-ingest instead of going stale. The questions themselves are human-authored.
python scripts/build_golden.py --snapshot "$SNAPSHOT" --out "$GOLDEN"
ragv1 validate-golden "$GOLDEN"

# EXP-NULL — closed-book control, no retrieval.
ragv1 eval-null "$GOLDEN" experiments/EXP-NULL/results.json

# EXP-000 — PostgreSQL lexical baseline.
ragv1 eval-retrieval "$GOLDEN" "$SNAPSHOT" lexical experiments/EXP-000/results.json --k "$K"

# The offline LSA embedder must be fitted on the snapshot it will query against.
# With EMBEDDING_PROVIDER=local or openai this export is unnecessary.
export LSA_FIT_SNAPSHOT_ID="$SNAPSHOT"
MODEL_ID=$(ragv1 embed "$SNAPSHOT" | tr -d '\n' | json_field model_id)
echo "Embedding model id: $MODEL_ID"

# EXP-001 dense, EXP-002 hybrid interleave.
ragv1 eval-retrieval "$GOLDEN" "$SNAPSHOT" dense  experiments/EXP-001/results.json --k "$K" --model-id "$MODEL_ID"
ragv1 eval-retrieval "$GOLDEN" "$SNAPSHOT" hybrid experiments/EXP-002/results.json --k "$K" --model-id "$MODEL_ID"

# EXP-003 — pure RRF. rrf_k=60 is tested, not assumed.
for RRF_K in 10 20 60; do
  ragv1 eval-retrieval "$GOLDEN" "$SNAPSHOT" rrf \
    "experiments/EXP-003/results-k${RRF_K}.json" \
    --k "$K" --model-id "$MODEL_ID" --rrf-k "$RRF_K"
done

# Candidate-pool curve. Pool size turned out to matter more than rrf_k, so it is
# swept rather than frozen at the shipped default.
mkdir -p experiments/EXP-003/sweep
for POOL in 10 20 50 100; do
  for RRF_K in 10 20 60; do
    ragv1 eval-retrieval "$GOLDEN" "$SNAPSHOT" rrf \
      "experiments/EXP-003/sweep/pool${POOL}-rrfk${RRF_K}.json" \
      --k "$K" --model-id "$MODEL_ID" --rrf-k "$RRF_K" \
      --lexical-k "$POOL" --dense-k "$POOL"
  done
done

# Paired per-case comparisons and the consolidated table.
python scripts/analyze_experiments.py --out experiments/summary.json
