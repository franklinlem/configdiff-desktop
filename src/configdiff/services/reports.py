"""Projeção sem valores e Markdown que trata caminhos somente como código literal."""

import re
from collections.abc import Iterable

from configdiff.domain.paths import render_path
from configdiff.domain.results import (
    Category,
    ComparisonResult,
    DiffEntry,
    SanitizedEntry,
    SanitizedReportDTO,
)

LABELS: dict[Category, str] = {
    Category.MISSING_A: "Ausente em A",
    Category.MISSING_B: "Ausente em B",
    Category.TYPE_CHANGED: "Tipo alterado",
    Category.VALUE_CHANGED: "Valor alterado",
    Category.EQUAL: "Igual",
}
DIFFERENCES = frozenset(category for category in Category if category != Category.EQUAL)


def filter_entries(
    entries: Iterable[DiffEntry], *, query: str = "", categories: frozenset[Category] = DIFFERENCES
) -> tuple[DiffEntry, ...]:
    search = query.casefold()
    return tuple(
        entry
        for entry in entries
        if entry.category in categories and search in render_path(entry.path).casefold()
    )


def sanitized_report(
    result: ComparisonResult, *, query: str = "", categories: frozenset[Category] = DIFFERENCES
) -> SanitizedReportDTO:
    entries = filter_entries(result.entries, query=query, categories=categories)
    return SanitizedReportDTO(
        result.format,
        tuple(
            SanitizedEntry(render_path(entry.path), entry.category, entry.kind_a, entry.kind_b)
            for entry in entries
        ),
    )


def _code(text: str) -> str:
    # Renderização pública é ASCII escapado; também protege DTO criado diretamente.
    safe = "".join(
        char
        if 32 <= ord(char) <= 126
        else f"\\u{ord(char):04x}"
        if ord(char) <= 0xFFFF
        else f"\\U{ord(char):08x}"
        for char in text
    )
    longest = max((len(match.group()) for match in re.finditer(r"`+", safe)), default=0)
    delimiter = "`" * (longest + 1)
    return f"{delimiter} {safe} {delimiter}"


def render_markdown(report: SanitizedReportDTO) -> str:
    if type(report) is not SanitizedReportDTO:
        raise TypeError("Relatórios exigem SanitizedReportDTO")
    lines = [
        "# ConfigDiff — relatório sanitizado",
        "",
        "Valores omitidos. Nomes de chaves podem revelar informações; revise antes de compartilhar.",
        "",
        f"Formato: {report.format.value}. Entradas na visão exportada: {len(report.entries)}.",
        "",
    ]
    for entry in report.entries:
        first = entry.kind_a.value if entry.kind_a is not None else "ausente"
        second = entry.kind_b.value if entry.kind_b is not None else "ausente"
        lines.append(
            f"- {_code(entry.path)} — {LABELS[entry.category]}; tipos A/B: {first} / {second}."
        )
    if not report.entries:
        lines.append("Nenhuma entrada nesta visão.")
    return "\n".join(lines) + "\n"
