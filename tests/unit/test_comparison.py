import random

import pytest

from configdiff.domain.comparison import compare
from configdiff.domain.nodes import canonicalize
from configdiff.domain.paths import Index, Key, render_path
from configdiff.domain.results import Category, ComparisonResult, Format
from configdiff.domain.sensitivity import potentially_sensitive
from configdiff.services.reports import filter_entries, sanitized_report


def diff(a, b):
    return compare(canonicalize(a), canonicalize(b))


@pytest.mark.parametrize(
    "a,b,path,category",
    [
        ({}, {"x": None}, '$["x"]', Category.MISSING_A),
        ({"x": ""}, {}, '$["x"]', Category.MISSING_B),
        (None, "", "$", Category.TYPE_CHANGED),
        (True, 1, "$", Category.TYPE_CHANGED),
        (1, 1.0, "$", Category.TYPE_CHANGED),
        (1.0, 1.0000000001, "$", Category.VALUE_CHANGED),
        ({"x": {"a": 1}}, {"x": []}, '$["x"]', Category.TYPE_CHANGED),
        ({"x": {"a": 1}}, {}, '$["x"]', Category.MISSING_B),
        ([None], [], "$[0]", Category.MISSING_B),
        ([], [None], "$[0]", Category.MISSING_A),
        ("é", "e\u0301", "$", Category.VALUE_CHANGED),
        ("a ", "a", "$", Category.VALUE_CHANGED),
        ({}, {}, "$", Category.EQUAL),
        ([], [], "$", Category.EQUAL),
    ],
)
def test_categories_and_single_root_for_subtrees(a, b, path, category):
    entries = diff(a, b)
    assert len(entries) == 1
    assert render_path(entries[0].path) == path
    assert entries[0].category == category


def test_paths_and_list_positions():
    entries = diff(
        {"a.b": 1, "a": {"b": 1}, "0": [1, 2]}, {"a.b": 2, "a": {"b": 2}, "0": [2, 1, 3]}
    )
    assert [entry.path for entry in entries] == [
        (Key("0"), Index(0)),
        (Key("0"), Index(1)),
        (Key("0"), Index(2)),
        (Key("a"), Key("b")),
        (Key("a.b"),),
    ]
    assert entries[2].category == Category.MISSING_A
    assert all(
        entry.category == Category.VALUE_CHANGED for i, entry in enumerate(entries) if i != 2
    )


def test_order_independence_and_counts():
    entries = diff({"b": 2, "a": 1}, {"a": 1, "b": 2})
    assert all(entry.category == Category.EQUAL for entry in entries)
    result = ComparisonResult(Format.JSON, entries, 0)
    assert result.counts[Category.EQUAL] == 2
    assert sum(result.counts.values()) == 2
    assert not filter_entries(entries)


def test_symmetry_and_identity_on_generated_synthetic_trees():
    rng = random.Random(13)

    def tree(depth):
        if not depth:
            return rng.choice([None, True, False, 0, 1, 1.5, "", "value"])
        return rng.choice(
            [
                {str(i): tree(depth - 1) for i in range(rng.randrange(4))},
                [tree(depth - 1) for _ in range(rng.randrange(4))],
                None,
            ]
        )

    reverse = {Category.MISSING_A: Category.MISSING_B, Category.MISSING_B: Category.MISSING_A}
    for _ in range(60):
        first, second = tree(2), tree(2)
        assert all(entry.category == Category.EQUAL for entry in diff(first, first))
        forward, backward = diff(first, second), diff(second, first)
        assert len(forward) == len(backward)
        for a, b in zip(forward, backward, strict=True):
            assert a.path == b.path
            assert reverse.get(a.category, a.category) == b.category
            assert a.a == b.b and a.b == b.a


def test_filters_search_only_paths_and_project_exact_view():
    entries = diff(
        {"password": "SENTINEL", "equal": 1, "new": 2}, {"password": "OTHER", "equal": 1}
    )
    result = ComparisonResult(Format.JSON, entries, 0)
    assert not filter_entries(entries, query="SENTINEL")
    selected = filter_entries(entries, query="PASS", categories=frozenset({Category.VALUE_CHANGED}))
    assert len(selected) == 1
    dto = sanitized_report(result, query="PASS", categories=frozenset({Category.VALUE_CHANGED}))
    assert len(dto.entries) == 1 and dto.entries[0].path == '$["password"]'
    assert not filter_entries(entries, categories=frozenset())
    assert len(filter_entries(entries, categories=frozenset(Category))) == 3
    assert "SENTINEL" not in repr(dto) and "OTHER" not in repr(dto)


@pytest.mark.parametrize(
    "key", ["DB_PASSWORD", "api-key", "accessToken", "PRIVATE_KEY", "nested.secret"]
)
def test_sensitivity_hint(key):
    assert potentially_sensitive((Key(key), Index(0)))
    assert not potentially_sensitive((Key("hostname"),))
