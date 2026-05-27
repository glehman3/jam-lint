"""Validate test jam CSV structure."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

FORMULA_PREFIX_CHARS = ("=", "+", "-", "@", "\t", "\r")

EXECUTION_TRACKING_COLUMNS = [
    "Status",
    "Tester",
    "Date Tested",
    "Actual Results",
    "Notes",
    "Bug ID",
]

REQUIRED_CORE_COLUMNS = [
    "Test ID",
    "Category",
    "Test Name",
    "Priority",
    "Type",
    "Component",
    "Objective",
    "Pre-conditions",
    "Test Steps",
    "Expected Results",
]

REQUIRED_NUMBERED_LIST_COLUMNS = [
    "Pre-conditions",
    "Test Steps",
    "Expected Results",
]


@dataclass
class CsvIssue:
    severity: str
    file: str
    row_number: int | None
    test_id: str | None
    issue: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "file": self.file,
            "row_number": self.row_number,
            "test_id": self.test_id,
            "issue": self.issue,
            "detail": self.detail,
        }


def load_csv_rows(path: Path) -> dict:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return {"header": rows[0] if rows else [], "rows": rows[1:] if len(rows) > 1 else []}


def get_test_id(header: list[str], row: list[str]) -> str | None:
    for key in ("Test ID", "Test Case ID", "Test Id"):
        if key in header:
            idx = header.index(key)
            if idx < len(row):
                v = (row[idx] or "").strip()
                return v or None
    return None


def validate_csv_file(path: Path) -> list[CsvIssue]:
    issues: list[CsvIssue] = []
    blob = load_csv_rows(path)
    header: list[str] = blob["header"]
    rows: list[list[str]] = blob["rows"]

    if not header:
        issues.append(
            CsvIssue("error", path.name, None, None, "Missing header row", "CSV is empty.")
        )
        return issues

    expected_len = len(header)
    if len(set(header)) != len(header):
        issues.append(
            CsvIssue(
                "error",
                path.name,
                1,
                None,
                "Duplicate header columns",
                "Header contains duplicate column names.",
            )
        )

    missing = [c for c in REQUIRED_CORE_COLUMNS if c not in header]
    if missing:
        issues.append(
            CsvIssue(
                "error",
                path.name,
                1,
                None,
                "Missing required columns",
                f"Missing: {', '.join(missing)}",
            )
        )

    if len(header) >= 5 and header[4] != "Type":
        issues.append(
            CsvIssue(
                "error",
                path.name,
                1,
                None,
                'Column 5 header is not "Type"',
                f"Found {header[4]!r}.",
            )
        )

    for i, row in enumerate(rows, start=2):
        if len(row) != expected_len:
            issues.append(
                CsvIssue(
                    "error",
                    path.name,
                    i,
                    get_test_id(header, row),
                    "Row column-count mismatch",
                    f"Expected {expected_len} columns, found {len(row)}.",
                )
            )

    col_index = {name: idx for idx, name in enumerate(header)}
    tracking_indices = {c: col_index[c] for c in EXECUTION_TRACKING_COLUMNS if c in col_index}
    for i, row in enumerate(rows, start=2):
        tid = get_test_id(header, row)
        for col, idx in tracking_indices.items():
            if idx < len(row) and (row[idx] or "").strip():
                issues.append(
                    CsvIssue(
                        "warning",
                        path.name,
                        i,
                        tid,
                        "Execution tracking field is non-empty",
                        f"Column '{col}' should be blank in generated CSVs.",
                    )
                )
                break

    for i, row in enumerate(rows, start=2):
        tid = get_test_id(header, row)
        for j, cell in enumerate(row):
            s = str(cell or "")
            if s and s[0] in FORMULA_PREFIX_CHARS and not s.startswith("'"):
                col_name = header[j] if j < len(header) else f"col {j + 1}"
                issues.append(
                    CsvIssue(
                        "error",
                        path.name,
                        i,
                        tid,
                        "Potential CSV formula injection",
                        f"Column {col_name!r} starts with {s[0]!r}; prefix with '.",
                    )
                )
                break

    bullet_re = re.compile(r"^\s*[-*•+]\s+", re.MULTILINE)
    numbered_re = re.compile(r"^\s*\d+[\.\)]\s+")
    for i, row in enumerate(rows, start=2):
        tid = get_test_id(header, row)
        for col in REQUIRED_NUMBERED_LIST_COLUMNS:
            idx = col_index.get(col)
            if idx is None or idx >= len(row):
                continue
            text = (row[idx] or "").strip()
            if not text:
                continue
            if bullet_re.search(text):
                issues.append(
                    CsvIssue(
                        "error",
                        path.name,
                        i,
                        tid,
                        "Bullet points detected",
                        f"Column {col!r} must use numbered lists (1., 2., 3.).",
                    )
                )
                break
            bad = [ln.strip() for ln in text.splitlines() if ln.strip() and not numbered_re.match(ln.strip())]
            if bad:
                issues.append(
                    CsvIssue(
                        "error",
                        path.name,
                        i,
                        tid,
                        "Non-numbered list formatting",
                        f"Column {col!r}: example {bad[0]!r}",
                    )
                )
                break

    return issues


def discover_csv_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        files = sorted(target.glob("testjam_*.csv"))
        if not files:
            files = sorted(target.glob("*.csv"))
        return files
    return []


def validate_path(target: Path) -> dict:
    files = discover_csv_files(target)
    if not files:
        raise FileNotFoundError(f"No CSV files found at {target}")

    all_issues: list[CsvIssue] = []
    for p in files:
        all_issues.extend(validate_csv_file(p))

    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]
    return {
        "path": str(target),
        "files_checked": [p.name for p in files],
        "counts": {"errors": len(errors), "warnings": len(warnings), "total": len(all_issues)},
        "issues": [i.to_dict() for i in all_issues],
        "ok": len(errors) == 0,
    }
