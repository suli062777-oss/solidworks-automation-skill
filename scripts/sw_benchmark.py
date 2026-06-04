"""CLI entrypoints for SolidWorks automation benchmarks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .sw_workflows import BENCHMARK_NAMES, run_benchmark, summarize_results
except ImportError:  # pragma: no cover - direct scripts path compatibility
    from sw_workflows import BENCHMARK_NAMES, run_benchmark, summarize_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SolidWorks automation benchmarks.")
    parser.add_argument(
        "--benchmark",
        choices=BENCHMARK_NAMES,
        default="enterprise_thin_slice",
        help="Benchmark workflow to run.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available benchmarks and exit.",
    )
    parser.add_argument(
        "--output-dir",
        default="output/enterprise_thin_slice",
        help="Directory for generated models, exports, previews, and reports.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        for name in BENCHMARK_NAMES:
            print(name)
        return 0

    output_dir = Path(args.output_dir)
    results = run_benchmark(args.benchmark, output_dir)
    summary = summarize_results(results)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Benchmark: {args.benchmark}")
        print(f"Benchmark ok: {summary['ok']}")
        print(f"Steps: {summary['steps']}")
        for artifact in summary["artifacts"]:
            print(f"- {artifact['kind']}: {artifact['path']}")
        if summary["failed"]:
            print("Failures:")
            for failure in summary["failed"]:
                print(json.dumps(failure, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
