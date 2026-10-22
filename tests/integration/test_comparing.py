import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.limits import Limits
from configdiff.domain.results import Category, Format
from configdiff.services.exporting import export_report
from configdiff.services.reports import sanitized_report
from configdiff.workers.comparing import Compared, ComparisonJob
from configdiff.workers.protocol import Failure


def wait(job):
    deadline = time.monotonic() + 10
    while (reply := job.poll()) is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert reply is not None
    return reply


@pytest.mark.parametrize(
    "format,extension,count",
    [(Format.JSON, "json", 5), (Format.YAML, "yaml", 5), (Format.ENV, "env.txt", 4)],
)
def test_complete_comparison_and_export(tmp_path, format, extension, count):
    fixtures = Path(__file__).parents[1] / "fixtures"
    first, second = fixtures / f"example.{extension}", fixtures / f"example-b.{extension}"
    before = [hashlib.sha256(path.read_bytes()).digest() for path in (first, second)]
    job = ComparisonJob(first, second, format, format)
    try:
        reply = wait(job)
        assert isinstance(reply, Compared)
        dto = sanitized_report(reply.result)
        assert len(dto.entries) == count
        assert reply.result.counts[Category.MISSING_A] == 1
        assert reply.result.counts[Category.MISSING_B] == 1
        assert reply.result.counts[Category.TYPE_CHANGED] == (0 if format == Format.ENV else 1)
        output = tmp_path / "report.md"
        export_report(dto, output, reply.sources)
        text = output.read_text(encoding="utf-8")
        for forbidden in [
            "synthetic-example-only",
            "synthetic-production-only",
            str(first),
            str(second),
        ]:
            assert forbidden not in text
        assert not job.process.is_alive() and not job._reader.is_alive()
        assert before == [hashlib.sha256(path.read_bytes()).digest() for path in (first, second)]
    finally:
        job.cancel()


def test_no_partial_result_if_second_input_fails(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    first.write_text('{"a": "SENTINEL"}')
    second.write_text("{")
    job = ComparisonJob(first, second, Format.JSON, Format.JSON)
    try:
        reply = wait(job)
        assert isinstance(reply, Failure)
        assert reply.side == Side.B and reply.code == ErrorCode.INVALID_SYNTAX
        assert "SENTINEL" not in repr(reply)
    finally:
        job.cancel()


def test_cross_format_requires_explicit_future_rule(tmp_path):
    with pytest.raises(ConfigError) as error:
        ComparisonJob(tmp_path / "a", tmp_path / "b", Format.JSON, Format.YAML)
    assert error.value.code == ErrorCode.FORMAT_MISMATCH


@pytest.mark.parametrize("action", ["timeout", "cancel", "crash"])
def test_comparison_stops_without_result(tmp_path, action):
    first = tmp_path / "input.json"
    first.write_text("{}")
    job = ComparisonJob(
        first,
        first,
        Format.JSON,
        Format.JSON,
        Limits(timeout_seconds=0.00001 if action == "timeout" else 10),
    )
    try:
        if action == "cancel":
            job.cancel()
        elif action == "crash":
            job.process.kill()
        reply = wait(job)
        assert isinstance(reply, Failure)
        assert (
            reply.code
            == {
                "timeout": ErrorCode.TIMEOUT,
                "cancel": ErrorCode.CANCELLED,
                "crash": ErrorCode.WORKER_FAILED,
            }[action]
        )
        assert not job.process.is_alive() and not job._reader.is_alive()
    finally:
        job.cancel()


def test_compare_cli_and_filtered_report(tmp_path):
    fixtures = Path(__file__).parents[1] / "fixtures"
    first, second = fixtures / "example.json", fixtures / "example-b.json"
    output = tmp_path / "report.md"
    command = [
        sys.executable,
        "-m",
        "configdiff.compare_cli",
        str(first),
        str(second),
        "--query",
        "password",
        "--category",
        "value_changed",
        "--output",
        str(output),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert "1 entradas" in result.stdout
    text = output.read_text(encoding="utf-8")
    assert "DB_PASSWORD" in text and "APP_ENV" not in text
    assert "synthetic-" not in text and "synthetic-" not in result.stdout + result.stderr
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=15)
    assert result.returncode == 1
    assert "já existe" in result.stdout
    result = subprocess.run(
        command[:-1] + [os.fspath(first)], check=False, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 1 and "origem" in result.stdout
