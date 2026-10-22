import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("format", ["json", "yaml", "env"])
def test_cli_fixture_metadata_only(format):
    name = "example.env.txt" if format == "env" else f"example.{format}"
    file = Path(__file__).parents[1] / "fixtures" / name
    result = subprocess.run(
        [sys.executable, "-m", "configdiff.inspect", str(file), "--format", format],
        check=False,
        text=True,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert f"formato={format}" in result.stdout and "nós=5" in result.stdout
    for forbidden in ["synthetic-example-only", "DB_PASSWORD", str(file)]:
        assert forbidden not in result.stdout + result.stderr


def test_cli_invalid_and_ambiguous_format(tmp_path):
    file = tmp_path / "private-name"
    file.write_text('{"SECRET": "SENTINEL",')
    result = subprocess.run(
        [sys.executable, "-m", "configdiff.inspect", str(file)],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 2
    result = subprocess.run(
        [sys.executable, "-m", "configdiff.inspect", str(file), "--format", "json"],
        check=False,
        text=True,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert "Sintaxe inválida" in result.stdout
    for forbidden in ["SENTINEL", "SECRET", os.fspath(file), "Traceback"]:
        assert forbidden not in result.stdout + result.stderr
