"""Ferramenta da fase 2: valida um arquivo e imprime apenas metadados."""

import argparse
import multiprocessing
import time
from pathlib import Path

from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.nodes import Mapping, Node, Sequence
from configdiff.domain.results import Format
from configdiff.services.files import detect_format
from configdiff.workers.loading import Failure, Loaded, LoadJob


def _count(root: Node) -> int:
    stack = [root]
    total = 0
    while stack:
        node = stack.pop()
        total += 1
        if isinstance(node, Mapping):
            stack.extend(child for _, child in node.entries)
        elif isinstance(node, Sequence):
            stack.extend(node.items)
    return total


def main() -> int:
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="Valida configuração sem exibir chaves ou valores")
    parser.add_argument("arquivo", type=Path)
    parser.add_argument("--format", choices=[format.value for format in Format])
    args = parser.parse_args()
    format = Format(args.format) if args.format else detect_format(args.arquivo)
    if format is None:
        print("Formato não identificado; escolha --format json, yaml ou env")
        return 2
    job: LoadJob | None = None
    try:
        job = LoadJob(args.arquivo, format, Side.A)
        while (reply := job.poll()) is None:
            time.sleep(0.01)
        if isinstance(reply, Failure):
            print(reply.exception().message)
            return 1
        assert isinstance(reply, Loaded)
        print(
            f"Válido: formato={format.value}; tipo={reply.node.kind.value}; "
            f"nós={_count(reply.node)}; bytes={reply.identity.size}"
        )
        return 0
    except ConfigError as error:
        print(error.message)
        return 1
    except KeyboardInterrupt:
        return 130
    finally:
        if job is not None:
            job.cancel(ErrorCode.CANCELLED)


if __name__ == "__main__":
    raise SystemExit(main())
