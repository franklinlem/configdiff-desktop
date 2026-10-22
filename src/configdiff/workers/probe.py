"""Prova de processo spawn terminável. Não processa arquivos de usuários."""

import multiprocessing as mp
import time
from multiprocessing.connection import Connection


def _work(connection: Connection, delay: float) -> None:
    try:
        time.sleep(delay)
        connection.send("ok")
    finally:
        connection.close()


class ProbeJob:
    def __init__(self, delay: float = 30, timeout: float = 10) -> None:
        context = mp.get_context("spawn")
        self.receiver, sender = context.Pipe(duplex=False)
        self.process = context.Process(target=_work, args=(sender, delay))
        self.deadline = time.monotonic() + timeout
        self.state = "running"
        self.process.start()
        sender.close()

    def poll(self) -> str:
        if self.state != "running":
            return self.state
        if self.receiver.poll():
            try:
                message = self.receiver.recv()
            except (EOFError, OSError):
                message = None
            self.state = "done" if message == "ok" else "error"
            self.close()
        elif time.monotonic() >= self.deadline:
            self.cancel("timeout")
        elif not self.process.is_alive():
            self.cancel("error")
        return self.state

    def cancel(self, state: str = "cancelled") -> None:
        if self.state == "running":
            self.state = state
        self.close()

    def close(self) -> None:
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(0.5)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(0.5)
        self.receiver.close()
