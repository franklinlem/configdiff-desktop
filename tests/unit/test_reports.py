import re
from dataclasses import fields

import pytest

from configdiff.domain.comparison import compare
from configdiff.domain.nodes import canonicalize
from configdiff.domain.results import (
    Category,
    ComparisonResult,
    Format,
    SanitizedEntry,
    SanitizedReportDTO,
)
from configdiff.services.reports import render_markdown, sanitized_report


def test_export_has_no_values_including_equal_null_or_containers():
    a = {
        "changed": "SENTINEL_A",
        "equal": "SENTINEL_SAME",
        "branch": {"v": "SENTINEL_NEST"},
        "null": None,
    }
    b = {"changed": "SENTINEL_B", "equal": "SENTINEL_SAME", "branch": []}
    result = ComparisonResult(Format.JSON, compare(canonicalize(a), canonicalize(b)), 0)
    report = sanitized_report(result, categories=frozenset(Category))
    markdown = render_markdown(report)
    assert "SENTINEL" not in markdown
    assert "Valores omitidos" in markdown
    assert "Tipo alterado" in markdown and "Igual" in markdown and "Ausente em B" in markdown
    assert {field.name for field in fields(SanitizedEntry)} == {
        "path",
        "category",
        "kind_a",
        "kind_b",
    }
    with pytest.raises(TypeError, match="SanitizedReportDTO"):
        render_markdown(result)


@pytest.mark.parametrize(
    "key",
    [
        "`",
        "`````",
        "[click](https://example.invalid)",
        "<img src=x onerror=alert(1)>",
        "![image](https://example.invalid)",
        "https://example.invalid",
        "| table |\n# heading",
        "bidi\u202e\x00\n\r",
    ],
)
def test_hostile_paths_stay_in_single_literal_code_span(key):
    result = ComparisonResult(
        Format.JSON, compare(canonicalize({key: 1}), canonicalize({key: 2})), 0
    )
    report = sanitized_report(result)
    markdown = render_markdown(report)
    row = next(line for line in markdown.splitlines() if line.startswith("- "))
    delimiter = re.match(r"- (`+) ", row).group(1)
    assert row.count(delimiter) == 2
    literal = row.split(delimiter)[1].strip(" ")
    assert literal == report.entries[0].path
    assert "\u202e" not in markdown and "\x00" not in markdown
    assert len(markdown.splitlines()) == 7


def test_empty_view_and_no_names_or_source_paths():
    markdown = render_markdown(SanitizedReportDTO(Format.ENV, ()))
    assert "Nenhuma entrada" in markdown
    assert "0" in markdown
