"""Transporte privado: processos termináveis e recebimento assíncrono."""

import multiprocessing as mp
import queue
import signal
import sys
import threading
import time
from collections.abc import Callable
from multiprocessing.connection import Connection

from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.limits import Limits
from configdiff.workers.protocol import Failure


def _receive[T](
    receiver: Connection,
    inbox: queue.Queue[T | Failure],
    side: Side | None,
    success_type: type[T],
    stopped: threading.Event,
) -> None:
    try:
        # Windows pode reter handles durante o bootstrap interrompido.
        # Espera limitada permite cancelar sem depender de EOF nesse caso.
        while not receiver.poll(0.05):
            if stopped.is_set():
                return
        if stopped.is_set():
            return
        value = receiver.recv()
        if not isinstance(value, (success_type, Failure)):
            value = Failure(ErrorCode.WORKER_FAILED, side)
    except (EOFError, OSError):
        value = Failure(ErrorCode.WORKER_FAILED, side)
    finally:
        receiver.close()
    inbox.put(value)


class ProcessJob[T]:
    def __init__(
        self,
        target: Callable[..., None],
        args: tuple[object, ...],
        success_type: type[T],
        limits: Limits,
        side: Side | None = None,
    ) -> None:
        context = mp.get_context("spawn")
        self._receiver, sender = context.Pipe(duplex=False)
        self._inbox: queue.Queue[T | Failure] = queue.Queue(maxsize=1)
        self._side = side
        self._deadline = time.monotonic() + limits.timeout_seconds
        self.reply: T | Failure | None = None
        self.process = context.Process(target=target, args=(sender, *args))
        try:
            # POSIX: o filho herda SIGINT bloqueado desde o bootstrap Python.
            # O pai restaura a máscara e recebe inclusive um sinal pendente.
            if sys.platform != "win32" and hasattr(signal, "pthread_sigmask"):
                previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
                try:
                    self.process.start()
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            else:
                self.process.start()
        except Exception:  # noqa: BLE001 - fronteira pública não pode expor exceções brutas
            sender.close()
            self._receiver.close()
            raise ConfigError(ErrorCode.WORKER_FAILED, side=side) from None
        sender.close()
        self._reader_stopped = threading.Event()
        self._reader = threading.Thread(
            target=_receive,
            args=(self._receiver, self._inbox, side, success_type, self._reader_stopped),
            daemon=True,
        )
        self._reader.start()

    def poll(self) -> T | Failure | None:
        if self.reply is not None:
            return self.reply
        if self.process.exitcode not in (None, 0):
            return self.cancel(ErrorCode.WORKER_FAILED)
        if time.monotonic() >= self._deadline:
            return self.cancel(ErrorCode.TIMEOUT)
        try:
            self.reply = self._inbox.get_nowait()
        except queue.Empty:
            return None
        self._stop()
        return self.reply

    def _stop(self) -> None:
        self._reader_stopped.set()
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
