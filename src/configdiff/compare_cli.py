"""Comparação local pelo terminal; nunca imprime valores ou documentos brutos."""

import argparse
import multiprocessing
import time
from pathlib import Path

from configdiff.domain.errors import ConfigError
from configdiff.domain.results import Category, Format
from configdiff.services.exporting import export_report
from configdiff.services.files import detect_format
from configdiff.services.reports import DIFFERENCES, render_markdown, sanitized_report
from configdiff.workers.comparing import ComparisonJob
from configdiff.workers.protocol import Failure


def main() -> int:
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="Compara configurações sem exibir valores")
    parser.add_argument("arquivo_a", type=Path)
    parser.add_argument("arquivo_b", type=Path)
    parser.add_argument("--format", choices=[format.value for format in Format])
    parser.add_argument("--query", default="", help="Busca no caminho exibido; nunca nos valores")
    parser.add_argument(
        "--category",
        action="append",
        choices=[category.value for category in Category],
        help="Repita para combinar categorias; padrão: somente diferenças",
    )
    parser.add_argument(
        "--output", type=Path, help="Novo arquivo Markdown; recusa destino existente"
    )
    args = parser.parse_args()
    first = Format(args.format) if args.format else detect_format(args.arquivo_a)
    second = Format(args.format) if args.format else detect_format(args.arquivo_b)
    if first is None or second is None:
        print("Formato não identificado; escolha --format json, yaml ou env")
        return 2
    job = None
    try:
        job = ComparisonJob(args.arquivo_a, args.arquivo_b, first, second)
        while (reply := job.poll()) is None:
            time.sleep(0.01)
        if isinstance(reply, Failure):
            print(reply.exception().message)
            return 1
        categories = (
            frozenset(Category(category) for category in args.category)
            if args.category
            else DIFFERENCES
        )
        report = sanitized_report(reply.result, query=args.query, categories=categories)
        if args.output is not None:
            export_report(report, args.output, reply.sources)
            print(
                f"Relatório sanitizado gravado: {len(report.entries)} entradas; valores omitidos."
            )
        else:
            print(render_markdown(report), end="")
        return 0
    except ConfigError as error:
        print(error.message)
        return 1
    except KeyboardInterrupt:
        return 130
    finally:
        if job is not None:
            job.cancel()


if __name__ == "__main__":
    raise SystemExit(main())
