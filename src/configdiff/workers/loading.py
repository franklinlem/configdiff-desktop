"""Carregamento isolado de um documento."""

import signal
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from pathlib import Path

from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.limits import DEFAULT_LIMITS, Limits
from configdiff.domain.nodes import Node
from configdiff.domain.results import Format
from configdiff.parsers import parse_bytes
from configdiff.services.files import FileIdentity, read_snapshot
from configdiff.workers.base import ProcessJob
from configdiff.workers.protocol import Failure

__all__ = ["Failure", "LoadJob", "LoadReply", "Loaded"]


@dataclass(frozen=True, slots=True)
class Loaded:
    node: Node = field(repr=False)
    identity: FileIdentity


type LoadReply = Loaded | Failure


def _load(sender: Connection, path: Path, format: Format, side: Side, limits: Limits) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    reply: LoadReply
    try:
        snapshot = read_snapshot(path, limits)
        node = parse_bytes(snapshot.data, format, limits)
        reply = Loaded(node, snapshot.identity)
    except ConfigError as error:
        reply = Failure(error.code, side, error.line, error.column)
    except Exception:  # noqa: BLE001 - fronteira pública não pode expor exceções brutas
        # Nunca imprimir a exceção ou o conteúdo num traceback do filho.
        reply = Failure(ErrorCode.WORKER_FAILED, side)
    try:
        sender.send(reply)
    except (BrokenPipeError, OSError):
        pass
    finally:
        sender.close()


class LoadJob(ProcessJob[Loaded]):
    def __init__(
        self, path: Path, format: Format, side: Side, limits: Limits = DEFAULT_LIMITS
    ) -> None:
        super().__init__(_load, (path, format, side, limits), Loaded, limits, side)
