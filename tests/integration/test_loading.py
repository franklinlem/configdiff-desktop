import hashlib
import time

import pytest

from configdiff.domain.errors import ErrorCode, Side
from configdiff.domain.limits import Limits
from configdiff.domain.nodes import canonicalize
from configdiff.domain.results import Format
from configdiff.workers.loading import Failure, Loaded, LoadJob


def wait(job):
    deadline = time.monotonic() + 10
    while (reply := job.poll()) is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert reply is not None
    return reply


@pytest.mark.parametrize(
    "format,text,expected",
    [
        (Format.JSON, '{"value":true}', {"value": True}),
        (Format.YAML, "value: true", {"value": True}),
        (Format.ENV, "value=true", {"value": "true"}),
    ],
)
def test_load_real_file(tmp_path, format, text, expected):
    file = tmp_path / "input"
    file.write_text(text, encoding="utf-8")
    before = hashlib.sha256(file.read_bytes()).digest()
    job = LoadJob(file, format, Side.A)
    try:
        reply = wait(job)
        assert isinstance(reply, Loaded)
        assert reply.node == canonicalize(expected)
        assert not job.process.is_alive()
        assert not job._reader.is_alive()
        assert hashlib.sha256(file.read_bytes()).digest() == before
    finally:
        job.cancel()


def test_error_never_crosses_as_raw_exception(tmp_path, capfd):
    file = tmp_path / "input"
    file.write_text('{"secret":"SENTINEL",')
    job = LoadJob(file, Format.JSON, Side.B)
    try:
        reply = wait(job)
        assert isinstance(reply, Failure)
        assert reply.code == ErrorCode.INVALID_SYNTAX and reply.side == Side.B
        assert "SENTINEL" not in str(reply.exception())
        assert "SENTINEL" not in repr(reply)
        output = capfd.readouterr()
        assert not output.out and not output.err
    finally:
        job.cancel()


@pytest.mark.parametrize("action", ["cancel", "timeout", "crash"])
def test_interrupt_load(tmp_path, action):
    file = tmp_path / "input"
    file.write_text("[]")
    job = LoadJob(
        file, Format.JSON, Side.A, Limits(timeout_seconds=0.00001 if action == "timeout" else 10)
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
                "cancel": ErrorCode.CANCELLED,
                "timeout": ErrorCode.TIMEOUT,
                "crash": ErrorCode.WORKER_FAILED,
            }[action]
        )
        assert not job.process.is_alive()
        assert not job._reader.is_alive()
    finally:
        job.cancel()


def test_result_larger_than_pipe_buffer(tmp_path):
    file = tmp_path / "large.json"
    file.write_text("[" + ",".join('"' + "x" * 100 + '"' for _ in range(10_000)) + "]")
    job = LoadJob(file, Format.JSON, Side.A)
    try:
        reply = wait(job)
        assert isinstance(reply, Loaded)
        assert len(reply.node.items) == 10_000
        assert not job._reader.is_alive()
    finally:
        job.cancel()
