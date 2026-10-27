# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Command-line inspection tools for sphinx-llm build artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPORT_FILENAME = "sphinx-llm-summaries.json"


def _read_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(
            f"cannot read report {str(path)!r}: {error.strerror}"
        ) from error
    except UnicodeError as error:
        raise ValueError(f"report {str(path)!r} is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON in {str(path)!r} at line {error.lineno}, "
            f"column {error.colno}"
        ) from error

    if not isinstance(report, dict) or report.get("version") != 1:
        raise ValueError(f"{str(path)!r} is not a supported summaries report")
    summaries = report.get("summaries")
    if not isinstance(summaries, list):
        raise ValueError(f"{str(path)!r} has no summaries list")
    for index, summary in enumerate(summaries):
        if not isinstance(summary, dict) or any(
            not isinstance(summary.get(key), str)
            for key in ("target", "origin", "summary")
        ):
            raise ValueError(
                f"{str(path)!r} contains an invalid summary at index {index}"
            )
        # Reports created before cache status was added remain readable.
        summary.setdefault("cache_status", "unknown")
    return report


def _format_text(report: dict[str, Any]) -> str:
    summaries = report["summaries"]
    if not summaries:
        return "No summaries found."

    entries = []
    for summary in summaries:
        model = summary.get("model") or "—"
        provider = summary.get("provider") or "—"
        entries.append(
            "\n".join(
                (
                    f"{summary['target']} ({summary['origin']})",
                    f"  provider: {provider}",
                    f"  model: {model}",
                    f"  cache: {summary['cache_status']}",
                    f"  summary: {summary['summary']}",
                )
            )
        )
    return "\n\n".join(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sphinx-llm")
    commands = parser.add_subparsers(dest="command", required=True)
    summaries = commands.add_parser(
        "summaries", help="inspect summaries from a Sphinx build report"
    )
    summaries.add_argument(
        "--report",
        type=Path,
        default=Path(REPORT_FILENAME),
        help=f"report path (default: ./{REPORT_FILENAME})",
    )
    summaries.add_argument(
        "--format", choices=("text", "json"), default="text", dest="output_format"
    )
    args = parser.parse_args(argv)

    try:
        report = _read_report(args.report)
    except ValueError as error:
        print(f"sphinx-llm: {error}", file=sys.stderr)
        return 2

    if args.output_format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
