"""Unit tests for DriftDetector (CTRL-006)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from controls import DriftDetector


@pytest.fixture
def baseline_file(tmp_path: Path) -> Path:
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {
                "CTRL-002": {"pass_rate": 1.00, "updated": "2026-04-01"},
                "CTRL-003": {"pass_rate": 0.98, "updated": "2026-04-01"},
            }
        )
    )
    return path


def test_no_regression(baseline_file: Path) -> None:
    detector = DriftDetector(baseline_path=baseline_file, regression_delta=-0.02)
    reports = detector.compare({"CTRL-002": 1.00, "CTRL-003": 0.98})
    assert all(not r.regressed for r in reports)


def test_regression_detected(baseline_file: Path) -> None:
    detector = DriftDetector(baseline_path=baseline_file, regression_delta=-0.02)
    reports = detector.compare({"CTRL-002": 0.90, "CTRL-003": 0.98})
    regressed = [r for r in reports if r.regressed]
    assert len(regressed) == 1
    assert regressed[0].control_id == "CTRL-002"
    assert regressed[0].delta < -0.02


def test_missing_baseline_is_noop(tmp_path: Path) -> None:
    detector = DriftDetector(baseline_path=tmp_path / "nope.json")
    reports = detector.compare({"CTRL-002": 1.00})
    assert reports == []


def test_evaluate_is_noop_per_request() -> None:
    detector = DriftDetector()
    result = detector.evaluate(prompt="anything")
    assert result.passed
    assert result.action == "allow"
