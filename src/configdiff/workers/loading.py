"""Carregamento isolado; o consumidor consulta uma fila sem bloquear em IPC."""

import multiprocessing as mp
import queue
import signal
import threading
import time
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from pathlib import Path

from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.limits import DEFAULT_LIMITS, Limits
from configdiff.domain.nodes import Node
from configdiff.domain.results import Format
from configdiff.parsers import parse_bytes
from configdiff.services.files import FileIdentity, read_snapshot


@dataclass(frozen=True, slots=True)
class Loaded:
    node: Node = field(repr=False)
    identity: FileIdentity


@dataclass(frozen=True, slots=True)
class Failure:
    code: ErrorCode
    side: Side
    line: int | None = None
    column: int | None = None

    def exception(self) -> ConfigError:
        return ConfigError(self.code, side=self.side, line=self.line, column=self.column)


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


def _receive(receiver: Connection, inbox: queue.Queue[LoadReply], side: Side) -> None:
    try:
        value = receiver.recv()
        if not isinstance(value, (Loaded, Failure)):
            value = Failure(ErrorCode.WORKER_FAILED, side)
    except (EOFError, OSError):
        value = Failure(ErrorCode.WORKER_FAILED, side)
    finally:
        receiver.close()
    inbox.put(value)


class LoadJob:
    def __init__(
        self, path: Path, format: Format, side: Side, limits: Limits = DEFAULT_LIMITS
    ) -> None:
        context = mp.get_context("spawn")
        self._receiver, sender = context.Pipe(duplex=False)
        self._inbox: queue.Queue[LoadReply] = queue.Queue(maxsize=1)
        self._side = side
        self._deadline = time.monotonic() + limits.timeout_seconds
        self.reply: LoadReply | None = None
        self.process = context.Process(target=_load, args=(sender, path, format, side, limits))
        try:
            self.process.start()
        except Exception:  # noqa: BLE001 - fronteira pública não pode expor exceções brutas
            sender.close()
            self._receiver.close()
            raise ConfigError(ErrorCode.WORKER_FAILED, side=side) from None
        sender.close()
        self._reader = threading.Thread(
            target=_receive, args=(self._receiver, self._inbox, side), daemon=True
        )
        self._reader.start()

    def poll(self) -> LoadReply | None:
        if self.reply is not None:
            return self.reply
        if time.monotonic() >= self._deadline:
            return self.cancel(ErrorCode.TIMEOUT)
        try:
            self.reply = self._inbox.get_nowait()
        except queue.Empty:
            return None
        self._stop()
        return self.reply

    def _stop(self) -> None:
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(0.5)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(0.5)
        self._reader.join(0.5)
        # O leitor já deixou a conexão fechada. Descarta resposta tardia.
        while True:
            try:
                self._inbox.get_nowait()
            except queue.Empty:
                break

    def cancel(self, code: ErrorCode = ErrorCode.CANCELLED) -> Failure:
        self._stop()
        self.reply = Failure(code, self._side)
        return self.reply
