from pathlib import Path

import pytest

from jam_lint.validator import validate_csv_file, validate_path

ROOT = Path(__file__).parent.parent
VALID = ROOT / "examples" / "valid.csv"
BROKEN = ROOT / "examples" / "broken.csv"


def test_valid_csv_passes():
    issues = validate_csv_file(VALID)
    assert not [i for i in issues if i.severity == "error"]


def test_broken_csv_fails():
    issues = validate_csv_file(BROKEN)
    assert any(i.severity == "error" for i in issues)


def test_validate_directory():
    report = validate_path(ROOT / "examples")
    assert "valid.csv" in report["files_checked"]
    assert report["counts"]["errors"] >= 1


def test_missing_path():
    with pytest.raises(FileNotFoundError):
        validate_path(ROOT / "nope")
