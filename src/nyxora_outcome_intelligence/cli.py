from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import uvicorn

from .config import DEFAULT_AS_OF_DATE, DEFAULT_LEAD_COUNT, DEFAULT_SEED, ProjectPaths, default_root
from .dashboard import build_dashboard_artifact
from .modeling import train_models
from .monitoring import build_monitoring_report
from .scoring import score_recent_candidates
from .synthetic import generate_dataset, write_dataset
from .warehouse import build_warehouse, validate_warehouse


def _find_portable_builder() -> Path | None:
    configured = os.environ.get("NYXORA_PORTABLE_BUILDER")
    if configured:
        candidate = Path(configured).expanduser()
        return candidate if candidate.exists() else None
    pattern = (
        ".codex/plugins/cache/openai-curated-remote/data-analytics/*/skills/"
        "build-report/scripts/deliver_portable_artifact.mjs"
    )
    candidates = sorted(Path.home().glob(pattern), reverse=True)
    return candidates[0] if candidates else None


def package_dashboard(paths: ProjectPaths, builder: Path | None = None) -> bool:
    builder = builder or _find_portable_builder()
    if builder is None:
        return False
    node = shutil.which("node")
    if node is None:
        embedded_nodes = sorted(
            (Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "runtimes").glob(
                "cua_node/*/bin/node.exe"
            ),
            reverse=True,
        )
        node = str(embedded_nodes[0]) if embedded_nodes else None
    if node is None:
        return False
    subprocess.run(
        [
            node,
            str(builder),
            "--input",
            str(paths.artifacts_dir / "artifact.json"),
            "--output",
            str(paths.artifacts_dir / "dashboard.html"),
        ],
        cwd=paths.root,
        check=True,
    )
    return True


def build_all(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    paths = ProjectPaths(root)
    paths.ensure()
    as_of_date = date.fromisoformat(args.as_of)
    print(f"[1/7] Generating {args.leads:,} synthetic leads with seed {args.seed}...")
    dataset = generate_dataset(
        lead_count=args.leads,
        seed=args.seed,
        as_of_date=as_of_date,
        lookback_days=args.lookback_days,
    )
    write_dataset(dataset, paths.raw_dir)
    print(f"      wrote {len(dataset.leads):,} leads and {len(dataset.events):,} events")

    print("[2/7] Building DuckDB source, fact, and mart tables...")
    build_warehouse(paths, as_of_date=as_of_date)
    print("[3/7] Enforcing blocking data contracts...")
    quality = validate_warehouse(paths)
    print(f"      {len(quality['checks'])} checks passed")

    print("[4/7] Training and evaluating chronological model candidates...")
    metrics = train_models(paths, seed=args.seed, as_of_date=as_of_date.isoformat())
    selected = metrics["selected_test_metrics"]
    print(
        f"      selected {metrics['selected_model']} | "
        f"ROC AUC {selected['roc_auc']:.3f} | Brier {selected['brier_score']:.3f}"
    )

    print("[5/7] Scoring open leads and producing counterfactual guidance...")
    scored = score_recent_candidates(paths)
    print(f"      scored {len(scored):,} open candidates")
    print("[6/7] Building drift, calibration, and slice monitoring...")
    monitoring = build_monitoring_report(paths)
    print(f"      maximum PSI {monitoring['maximum_psi']:.3f}")

    print("[7/7] Generating the bounded dashboard snapshot...")
    build_dashboard_artifact(paths, as_of_date=as_of_date.isoformat())
    if args.skip_dashboard_package:
        print("      dashboard packaging skipped")
    elif package_dashboard(paths, Path(args.portable_builder) if args.portable_builder else None):
        print(f"      packaged {paths.artifacts_dir / 'dashboard.html'}")
    else:
        print(
            "      portable builder unavailable; artifact.json was generated and the checked-in "
            "dashboard snapshot, if present, was preserved"
        )
    print("Build complete. Start the API with: nyxora-intel serve")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Nyxora Outcome Intelligence")
    subcommands = result.add_subparsers(dest="command", required=True)
    build = subcommands.add_parser("build", help="Run the complete reproducible pipeline")
    build.add_argument("--root", default=str(default_root()))
    build.add_argument("--leads", type=int, default=DEFAULT_LEAD_COUNT)
    build.add_argument("--seed", type=int, default=DEFAULT_SEED)
    build.add_argument("--as-of", default=DEFAULT_AS_OF_DATE.isoformat())
    build.add_argument("--lookback-days", type=int, default=365)
    build.add_argument("--portable-builder")
    build.add_argument("--skip-dashboard-package", action="store_true")
    build.set_defaults(func=build_all)

    serve = subcommands.add_parser("serve", help="Serve the dashboard and scoring API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")

    def serve_app(args: argparse.Namespace) -> None:
        uvicorn.run(
            "nyxora_outcome_intelligence.api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )

    serve.set_defaults(func=serve_app)
    return result


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
