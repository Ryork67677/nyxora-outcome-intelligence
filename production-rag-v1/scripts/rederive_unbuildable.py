#!/usr/bin/env python3
"""Re-derive batch 006's NO_BUILDER / UNBUILDABLE span set from a restored corpus.

Batch 006 counted this set and discarded it: ``removed["unbuildable"] += 1`` at
``scripts/export_batch_006.py:733`` increments a counter and returns. The count (2482)
is faithful and unusable — it cannot say *which* spans, so batch 007's calibration pilot
has no input. This script recovers the identities the count threw away.

It re-runs batch 006's own miners and builders, imported unmodified from
``scripts/export_batch_006.py``. That is deliberate and it is the whole method: the
unbuildable set is *defined* by those builders as they were, so re-deriving it with a
changed builder would produce a different set and quietly answer a different question.

Nothing is authored here and no candidate is produced. The output is a manifest of spans.

**It refuses rather than guesses.** Three checks run before any mining, in this order,
and each is fatal:

1. the corpus must be present;
2. it must hash to the frozen snapshot id — a restore labelled ``snap_689e…`` proves
   nothing, since the label is written by whoever did the restore;
3. every closed span must re-read and re-hash correctly at its recorded offsets.

Only then does it mine, and the re-derived count must equal the count batch 006
recorded. A different count means the derivation is not reproducing batch 006's
conditions, and the run stops instead of handing a plausible set to a pilot.

No retrieval is run. SYSTEM-A and SYSTEM-B are not executed. Validation and holdout are
neither read nor written.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from rag_v1.gold.provenance import (  # noqa: E402
    NO_BUILDER,
    UnbuildableLog,
    chunking_config_from_settings,
    verify_fingerprint,
    verify_restored_corpus,
)
from rag_v1.parsing import PARSER_VERSION  # noqa: E402

SNAPSHOT = "snap_689e336380a054d8039dc35b2c09cd0a"
SNAPSHOT_NAME = "v1"
#: What batch 006 recorded. The re-derivation must reproduce it exactly.
EXPECTED_UNBUILDABLE = 2482
GENERATION_REPORT = REPO_ROOT / "experiments/GOLD-001/GOLD-001-batch-006-generation-report.json"
CLOSED_BATCHES = "evals/review/gold_review_batch_00*_final.json"


def closed_records() -> list[dict]:
    """Every closed candidate carrying an anchored, hashed span."""
    records: list[dict] = []
    for path in sorted(glob.glob(str(REPO_ROOT / CLOSED_BATCHES))):
        records.extend(json.loads(Path(path).read_text())["records"])
    return records


def expected_count() -> int:
    """Batch 006's own recorded count, read from its report rather than retyped."""
    if not GENERATION_REPORT.exists():
        return EXPECTED_UNBUILDABLE
    report = json.loads(GENERATION_REPORT.read_text())
    return int(report["removed"]["unbuildable"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",
                        default="experiments/GOLD-001/GOLD-001-batch-006-unbuildable.json")
    parser.add_argument("--snapshot", default=SNAPSHOT)
    args = parser.parse_args()

    # Imported here so the module's own import of rag_v1.db does not fail the script
    # before it can report a missing corpus in its own words.
    try:
        from rag_v1.db import connect
        import export_batch_006 as b006
    except Exception as error:  # noqa: BLE001 - the cause is reported, not swallowed
        raise SystemExit(f"cannot load the batch-006 generator: {error}") from error

    # 1. The corpus must be there at all.
    try:
        with connect() as conn, conn.cursor() as cur:
            docs = b006.load_docs(cur)
            cur.execute(
                """
                SELECT v.version_id, v.content_hash
                FROM document_version v
                JOIN corpus_snapshot_version sv ON sv.version_id = v.version_id
                WHERE sv.snapshot_id = %s
                ORDER BY v.version_id
                """,
                (args.snapshot,))
            versions = [(r[0], r[1]) for r in cur.fetchall()]
    except Exception as error:  # noqa: BLE001
        raise SystemExit(
            f"refusing to re-derive: the corpus is not reachable ({error}). Restore the "
            "frozen snapshot first — do not substitute live URL contents or fixtures.")

    if not docs or not versions:
        raise SystemExit(
            f"refusing to re-derive: no documents found for {args.snapshot}. The database "
            "is reachable but holds no corpus.")

    # 2. It must hash to the snapshot it claims to be.
    print(f"corpus: {len(docs)} documents, {len(versions)} versions in {args.snapshot}")
    check = verify_fingerprint(args.snapshot, versions, name=SNAPSHOT_NAME,
                               parser_version=PARSER_VERSION,
                               chunking_config=chunking_config_from_settings())
    if not check["matches"]:
        raise SystemExit(
            "refusing to re-derive: the restored corpus does not hash to the frozen "
            f"snapshot.\n  expected {check['expected']}\n  computed {check['computed']}\n"
            "This is not the 2026-08-17 corpus. A re-fetch is not a restore.")
    print(f"fingerprint: {check['computed']} — matches the frozen snapshot")

    # 3. Every closed span must re-read and re-hash at its recorded offsets.
    for doc in docs:
        doc["sections"] = b006._sections_from_markdown(doc["text"])
    by_version = {d["version_id"]: d for d in docs}

    def read_span(version_id: str, start: int, end: int) -> str | None:
        doc = by_version.get(version_id)
        return None if doc is None else doc["text"][start:end]

    restore = verify_restored_corpus(closed_records(), read_span)
    if not restore["verified"]:
        raise SystemExit(
            "refusing to re-derive: closed spans do not reproduce from this corpus "
            f"({restore['spans_matched']}/{restore['spans_checked']} matched, "
            f"{len(restore['missing'])} missing). The restore is not byte-identical.")
    print(f"restore: {restore['spans_matched']}/{restore['spans_checked']} closed spans "
          "re-hash correctly")

    # Mining, exactly as batch 006 ran it.
    from rag_v1.gold.factmining import mine_bridge_facts

    conditional_facts: list[dict] = []
    templated: list[dict] = []
    interactions: list[dict] = []
    constraints: list[dict] = []
    lifecycles: list[dict] = []
    for doc in docs:
        conditional_facts += mine_bridge_facts(doc)
        templated += b006.mine_prose(doc, limit=20)
        templated += b006.mine_row_facts(doc, limit=10)
        templated += b006.mine_definition_bullets(doc, limit=10)
        interactions += b006.mine_interactions(doc, limit=60)
        constraints += b006.mine_constraints(doc, limit=60)
        lifecycles += b006.mine_lifecycle(doc, limit=50)

    log = UnbuildableLog()

    def attempt(fact: dict, built: dict | None) -> None:
        if built is None:
            log.record(fact, reason=NO_BUILDER)

    for fact in conditional_facts:
        attempt(fact, b006.build_conditional(fact))
    for fact in interactions:
        attempt(fact, b006.build_interaction(fact))
    for fact in constraints:
        attempt(fact, b006.build_constraint(fact))
    for fact in lifecycles:
        attempt(fact, b006.build_lifecycle(fact))
    claimed = {(f["version_id"], f["char_start"], f["char_end"])
               for f in interactions + constraints + lifecycles}
    for fact in conditional_facts:
        if (fact["version_id"], fact["char_start"], fact["char_end"]) in claimed:
            continue
        if b006.build_conditional(fact) is not None:
            continue
        attempt(fact, b006.build_predicate_fact(fact))

    wanted = expected_count()
    print(f"unbuildable: re-derived {len(log)}, batch 006 recorded {wanted}")
    if len(log) != wanted:
        raise SystemExit(
            f"refusing to write: re-derived {len(log)} unbuildable spans but batch 006 "
            f"recorded {wanted}. The derivation is not reproducing batch 006's "
            "conditions — diagnose before selecting any pilot case from this set.")

    out = REPO_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = log.manifest(corpus_snapshot=args.snapshot, batch=6)
    manifest["reproduced_recorded_count"] = True
    manifest["recorded_count"] = wanted
    manifest["fingerprint_verified"] = check["computed"]
    manifest["closed_spans_verified"] = restore["spans_matched"]
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({len(log)} span identities)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
