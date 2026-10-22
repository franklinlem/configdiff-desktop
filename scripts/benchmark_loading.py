"""Mede o carregamento isolado de fixture sintética; não mede comparação/GUI."""

import json
import multiprocessing
import platform
import tempfile
import time
from pathlib import Path

from configdiff.domain.errors import Side
from configdiff.domain.results import Format
from configdiff.workers.loading import Loaded, LoadJob


def main() -> None:
    multiprocessing.freeze_support()
    data = {f"key_{index:05}": "x" * 80 for index in range(9999)}
    payload = json.dumps(data).encode()
    data["key_00000"] += "x" * (1024 * 1024 - len(payload))
    payload = json.dumps(data).encode()
    assert len(payload) == 1024 * 1024
    with tempfile.TemporaryDirectory(prefix="configdiff-synthetic-") as temporary:
        path = Path(temporary) / "fixture.json"
        path.write_bytes(payload)
        start = time.monotonic()
        job = LoadJob(path, Format.JSON, Side.A)
        try:
            while (reply := job.poll()) is None:
                time.sleep(0.005)
            assert isinstance(reply, Loaded), reply
            elapsed = time.monotonic() - start
        finally:
            job.cancel()
    print(f"{platform.system()} {platform.machine()}, Python {platform.python_version()}")
    print(f"JSON: 1048576 bytes, 10000 nós, spawn/leitura/parsing/IPC/cleanup: {elapsed:.3f} s")
    if platform.system() == "Linux":
        import resource

        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        print(f"Pico RSS de filho (medição Linux): {usage.ru_maxrss} KiB")


if __name__ == "__main__":
    main()
