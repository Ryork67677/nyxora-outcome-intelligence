from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from rag_v1.embeddings import embed_snapshot
from rag_v1.evals.null_eval import run_null_eval
from rag_v1.evals.retrieval_eval import run_retrieval_eval
from rag_v1.evals.validate import validate_golden
from rag_v1.generation import rag_answer
from rag_v1.ingest import ingest_manifest
from rag_v1.reporting import paired_compare
from rag_v1.retrieval import dense_search, interleave_hybrid, lexical_search, rrf_fuse
from rag_v1.snapshot import create_snapshot

app = typer.Typer(no_args_is_help=True, help="Production RAG v1 — evaluation-first baselines")


@app.command("ingest")
def ingest(manifest: Path):
    ids = ingest_manifest(manifest)
    print({"ingested_versions": ids})


@app.command("snapshot-create")
def snapshot_create(name: str = typer.Argument("v1-seed")):
    print({"snapshot_id": create_snapshot(name)})


@app.command("embed")
def embed(snapshot_id: str, batch_size: int = 32):
    model_id, inserted = embed_snapshot(snapshot_id, batch_size)
    print({"model_id": model_id, "new_embeddings": inserted})


@app.command("validate-golden")
def validate_golden_cmd(path: Path):
    print(validate_golden(path))


@app.command("retrieve")
def retrieve(
    query: str,
    snapshot_id: str,
    mode: str = "lexical",
    k: int = 10,
    model_id: str | None = None,
    rrf_k: int = 60,
):
    if mode == "lexical":
        hits = lexical_search(query, snapshot_id, k)
    elif mode == "dense":
        if not model_id:
            raise typer.BadParameter("--model-id required for dense")
        hits = dense_search(query, snapshot_id, model_id, k)
    elif mode in {"hybrid", "rrf"}:
        if not model_id:
            raise typer.BadParameter("--model-id required for hybrid/rrf")
        lex = lexical_search(query, snapshot_id, 30)
        den = dense_search(query, snapshot_id, model_id, 30)
        hits = interleave_hybrid(lex, den, k) if mode == "hybrid" else rrf_fuse([lex, den], rrf_k, k)
    else:
        raise typer.BadParameter("mode must be lexical|dense|hybrid|rrf")
    print(json.dumps([h.model_dump() for h in hits], indent=2, ensure_ascii=False))


@app.command("eval-retrieval")
def eval_retrieval(
    golden: Path,
    snapshot_id: str,
    mode: str,
    output: Path,
    k: int = 10,
    model_id: str | None = None,
    lexical_k: int = 30,
    dense_k: int = 30,
    rrf_k: int = 60,
    include_text: bool = False,
):
    payload = run_retrieval_eval(
        golden, snapshot_id, mode, k, output, model_id, lexical_k, dense_k, rrf_k, include_text
    )
    print({key: value for key, value in payload.items() if key != "cases"})


@app.command("eval-null")
def eval_null(golden: Path, output: Path):
    payload = run_null_eval(golden, output)
    print({k: v for k, v in payload.items() if k != "cases"} | {"output": str(output)})


@app.command("compare")
def compare(old: Path, new: Path):
    print(paired_compare(old, new))


@app.command("answer")
def answer(query: str, snapshot_id: str, model_id: str, k: int = 8, rrf_k: int = 60):
    lex = lexical_search(query, snapshot_id, 30)
    den = dense_search(query, snapshot_id, model_id, 30)
    hits = rrf_fuse([lex, den], rrf_k=rrf_k, top_k=k)
    result = rag_answer(query, hits)
    print(result.text)
