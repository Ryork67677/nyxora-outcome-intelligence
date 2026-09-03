# Code Tool Handoff — Build/Run Production RAG v1

You are taking over a deliberately small, evaluation-first RAG repository. **Do not add a reranker, LangChain/LlamaIndex, agent loop, UI, or automatic crawler until EXP-NULL through EXP-003 produce actual measurements.**

## Mission

Get this exact V1 running against a small OpenAI + Anthropic technical-documentation corpus, then produce honest experiment results.

## Required sequence

1. Inspect the repository and run `pytest -q` before modifying architecture.
2. Start PostgreSQL/pgvector with `docker compose up -d`.
3. Verify current OpenAI and Anthropic terms/robots rules before fetching documentation. Keep raw snapshots under `data/raw/` (gitignored).
4. Create a local manifest in `data/manifests/` with about 200 focused documents total. Prefer official API/reference docs. Preserve provider, URL, captured time, authority class, and raw file path.
5. Ingest and create an immutable corpus snapshot.
6. Build **20 human-verified golden cases first**. Anchor expected evidence to `version_id + section_path + char_span`, never only `chunk_id`.
7. Run `EXP-NULL` with zero retrieval.
8. Run `EXP-000` lexical.
9. Create embeddings and run `EXP-001` dense.
10. Run `EXP-002` hybrid interleave.
11. Run `EXP-003` pure RRF for `rrf_k` in `{10,20,60}` and retrieval K in `{10,20,50,100}` where practical.
12. Compare configurations per question: rescued, regressed, unchanged-good, unchanged-bad.
13. Write one failure report that identifies the exact stage that failed.

## Do not hide ugly results

If closed-book beats retrieval on a question, record it. If lexical beats dense, record it. If RRF regresses a case, record it. The portfolio value is the diagnosis and measurable improvement, not a perfect score.

## Technical rules

- Keep plain Python orchestration.
- Preserve historical document versions.
- Never overwrite an old source version.
- Keep raw provider docs out of the public repository.
- Prefer deterministic checks over LLM judges when the claim can be checked directly.
- Do not use a scalar exact-identifier boost. If tested later, add exact matches as a third ranked list in RRF.
- Do not promote a new crawler/parser snapshot to current if corpus-health checks fail.
- Do not introduce a universal similarity confidence threshold.

## Expected outputs

At minimum, create:

- `evals/golden/v1.jsonl`
- `experiments/EXP-NULL/results.json`
- `experiments/EXP-000/results.json`
- `experiments/EXP-001/results.json`
- `experiments/EXP-002/results.json`
- `experiments/EXP-003/results-k10.json`, `results-k20.json`, `results-k60.json`
- `docs/failure-reports/FAIL-0001.md`
- README Results section containing actual numbers and limitations.

Do not redesign the project unless a failing experiment demonstrates why the redesign is needed.
