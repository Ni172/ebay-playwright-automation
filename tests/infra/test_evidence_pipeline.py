"""Exercise real pytest failures in a child run; the outer verification passes."""

import json
import os
import subprocess
import sys

import pytest

from config.settings import ROOT

pytestmark = pytest.mark.infra


def test_failed_run_keeps_screenshot_and_trace(tmp_path):
    (tmp_path / "conftest.py").write_text(
        (ROOT / "conftest.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "pytest.ini").write_text(
        f"[pytest]\npythonpath = {ROOT.as_posix()}\n", encoding="utf-8"
    )
    (tmp_path / "test_failure.py").write_text(
        "def test_deliberate_failure(page):\n"
        "    page.set_content('<h1>Controlled failure</h1>')\n"
        "    assert False, 'Intentional infrastructure verification'\n",
        encoding="utf-8",
    )
    results = tmp_path / "results"
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", f"--alluredir={results}"],
        cwd=tmp_path,
        env={**os.environ, "EBAY_TRACE": "retain-on-failure"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 1, run.stdout + run.stderr
    reports = [json.loads(path.read_text()) for path in results.glob("*-result.json")]
    assert len(reports) == 1
    assert reports[0]["status"] == "failed"
    pngs = list(results.glob("*.png"))
    traces = list(results.glob("*.zip"))
    assert pngs and all(path.stat().st_size > 0 for path in pngs)
    assert traces and all(path.stat().st_size > 0 for path in traces)
    all_metadata = "".join(path.read_text() for path in results.glob("*.json"))
    assert pngs[0].name in all_metadata
    assert traces[0].name in all_metadata
