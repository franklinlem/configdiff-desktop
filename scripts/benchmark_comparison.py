"""Mede comparação isolada de duas fixtures sintéticas; não mede GUI/exportação."""

import json
import multiprocessing
import platform
import tempfile
import time
from pathlib import Path

from configdiff.domain.results import Category, Format
from configdiff.workers.comparing import Compared, ComparisonJob


def main() -> None:
    multiprocessing.freeze_support()
    data = {f"key_{index:05}": "x" * 80 for index in range(9999)}
    data["key_00000"] += "x" * (1024 * 1024 - len(json.dumps(data).encode()))
    first = json.dumps(data).encode()
    data["key_00001"] = "y" * 80
    second = json.dumps(data).encode()
    assert len(first) == len(second) == 1024 * 1024
    with tempfile.TemporaryDirectory(prefix="configdiff-synthetic-") as temporary:
        a, b = Path(temporary) / "a.json", Path(temporary) / "b.json"
        a.write_bytes(first)
        b.write_bytes(second)
        start = time.monotonic()
        job = ComparisonJob(a, b, Format.JSON, Format.JSON)
        try:
            while (reply := job.poll()) is None:
                time.sleep(0.005)
            assert isinstance(reply, Compared), reply
            assert reply.result.counts[Category.VALUE_CHANGED] == 1
            elapsed = time.monotonic() - start
        finally:
            job.cancel()
    print(f"{platform.system()} {platform.machine()}, Python {platform.python_version()}")
    print(
        f"JSON: 2 x 1048576 bytes / 10000 nós; spawn/leitura/parsing/comparação/IPC/cleanup: {elapsed:.3f} s"
    )
    if platform.system() == "Linux":
        import resource

        print(
            f"Pico RSS de filho (Linux): {resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss} KiB"
        )


if __name__ == "__main__":
    main()
