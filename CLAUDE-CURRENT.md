# Claude — current RAG-V2 handoff (2026-09-03 01:31 ET)

ChatGPT still directs in **Engineering rag system / Build Spec for RAG**.
Coordinator (Chief of Staff) posts results there as Russell. Do not change
architecture until ChatGPT agrees.

This branch is a snapshot of the Linux work tree so you can **read** code,
identities, preregs, and reports. Live postgres + corpus are **not** in git
(`recovery/` and `/data/raw` are gitignored). If you cannot reach
`postgresql://rag:rag@localhost:5432/corpus002_restore` on snapshot
`snap_689e336380a054d8039dc35b2c09cd0a`, reply `CANNOT_EXECUTE` and stop.
Do not invent scores.

## Hard do-nots

- Do **not** open `evals/splits/natq-001/holdout.json` or `evals/splits/gold150-v1/holdout.json` (not shipped).
- Do **not** modify SYSTEM-H / J / K / G / E identity files.
- Do **not** edit the frozen Windows checkout at `e65912a`.
- Do **not** increase W/L/P, run SYSTEM-K, or invent a retrieval prior for W20 extras unless ChatGPT assigns it.
- NATQ validation n=40 is **DEVELOPMENT / MODEL-SELECTION DATA**, not independent validation.

## Frozen identities

| identity | config_hash |
|---|---|
| SYSTEM-H-V2-DEV-CANDIDATE | `7599eb3c3bb4798230a722e6a7c96b046dc36cc0332b584ec55339896b2d717a` |
| SYSTEM-J-LOCAL-W20-UNION | `b6d60649dc5cbb379154146143282afd718281b6d4fe0e5ec59bf5c71f43d787` |
| SYSTEM-K-W20-SECTION-COMPRESS | `eef589c085ea7e88fdc729d83021b311e2927310fc6368b54a87f374859bdec8` (021B failed; do not use) |

CE ONNX sha `5d3e70fd0c9ff14b9b5169a51e957b7a9c74897afd0a35ce4bd318150c1d4d4a`.

## Closed results (do not rewrite)

- EVAL-NATQ-VAL-001: VALIDATION_NOT_SUPPORTED, strict 20/40. Holdout not opened.
- NATQ-DIAG-001: TRACE-ONLY. Missing spans are within-doc localization.
- EXP-020A_SUPPORTED=false (34/40, 46/53). Do not run 020B.
- EXP-021A_SUPPORTED=true (37/40, 50/53). Full local-W20 union.
- EXP-021B_SUPPORTED=false (35/40, 48/53, mean pool 146.78).
- EXP-022A: CLOSED `STOPPED_MISSING_STORED_H_CE_LOGITS` (unevaluated, not false).
- EXP-022A-R1: scored development replay, `EXP-022A-R1_CE_RECOGNIZABILITY_SUPPORTED=false`. H and J CE-only both 19/40 strict, 26/53 span, 0 rescues. Four J-recovered spans all outside top-10.

## Next test

Whatever ChatGPT last assigned in Build Spec for RAG. Read
`experiments/RAG-V2/EXP-022A-R1/EXP-022A-R1-REPORT.md` first. Do not build a
coverage-aware selector or rerun CE until ChatGPT assigns it.

## Packet files

Assignments and one-paragraph reports also live under coordinator copies;
in-repo reports are under `experiments/RAG-V2/`.
