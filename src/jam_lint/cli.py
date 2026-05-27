"""jam-lint CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .validator import validate_path


def _format_md(report: dict) -> str:
    lines = [
        "# jam-lint report",
        "",
        f"**Path:** {report['path']}",
        f"**Files:** {', '.join(report['files_checked'])}",
        f"**Errors:** {report['counts']['errors']} · **Warnings:** {report['counts']['warnings']}",
        "",
    ]
    if not report["issues"]:
        lines.append("_No issues found._")
        return "\n".join(lines)
    for issue in report["issues"]:
        loc = f"line {issue['row_number']}" if issue.get("row_number") else "file"
        tid = f" ({issue['test_id']})" if issue.get("test_id") else ""
        lines.append(
            f"- **[{issue['severity']}]** `{issue['file']}` {loc}{tid}: {issue['issue']} — {issue['detail']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate test jam CSV structure.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Validate CSV file or directory")
    check.add_argument("path", type=Path)
    check.add_argument("--format", choices=("md", "json"), default="md")
    check.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = validate_path(args.path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_format_md(report))

    if not report["ok"]:
        return 2
    if args.fail_on_warnings and report["counts"]["warnings"] > 0:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
