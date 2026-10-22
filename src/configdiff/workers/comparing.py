"""Lê, interpreta e compara as duas capturas no mesmo processo isolado."""

import signal
import time
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from pathlib import Path

from configdiff.domain.comparison import compare
from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.limits import DEFAULT_LIMITS, Limits
from configdiff.domain.results import ComparisonResult, Format
from configdiff.parsers import parse_bytes
from configdiff.services.exporting import SourceRef
from configdiff.services.files import read_snapshot
from configdiff.workers.base import ProcessJob
from configdiff.workers.protocol import Failure


@dataclass(frozen=True, slots=True)
class Compared:
    result: ComparisonResult = field(repr=False)
    sources: tuple[SourceRef, ...] = field(repr=False)


def _compare(sender: Connection, first: Path, second: Path, format: Format, limits: Limits) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    reply: Compared | Failure
    side: Side | None = Side.A
    try:
        start = time.monotonic()
        snapshot_a = read_snapshot(first, limits)
        a = parse_bytes(snapshot_a.data, format, limits)
        source_a = SourceRef.capture(first, snapshot_a.identity)
        side = Side.B
        snapshot_b = read_snapshot(second, limits)
        b = parse_bytes(snapshot_b.data, format, limits)
        source_b = SourceRef.capture(second, snapshot_b.identity)
        side = None
        entries = compare(a, b)
        reply = Compared(
            ComparisonResult(format, entries, time.monotonic() - start), (source_a, source_b)
        )
    except ConfigError as error:
        reply = Failure(error.code, side, error.line, error.column)
    except Exception:  # noqa: BLE001 - não transportar exceções brutas para a interface
        reply = Failure(ErrorCode.WORKER_FAILED, side)
    try:
        sender.send(reply)
    except (BrokenPipeError, OSError):
        pass
    finally:
        sender.close()


class ComparisonJob(ProcessJob[Compared]):
    def __init__(
        self,
        first: Path,
        second: Path,
        format_a: Format,
        format_b: Format,
        limits: Limits = DEFAULT_LIMITS,
    ) -> None:
        if format_a != format_b:
            raise ConfigError(ErrorCode.FORMAT_MISMATCH)
        super().__init__(_compare, (first, second, format_a, limits), Compared, limits)
