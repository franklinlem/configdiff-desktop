import math
import pickle
from dataclasses import FrozenInstanceError, asdict

import pytest

from configdiff.domain.errors import ConfigError, ErrorCode, Side
from configdiff.domain.limits import Limits
from configdiff.domain.nodes import Kind, Mapping, Scalar, Sequence, canonicalize
from configdiff.domain.paths import Index, Key, render_path
from configdiff.domain.results import (
    Category,
    ComparisonResult,
    DiffEntry,
    Format,
    SanitizedEntry,
    SanitizedReportDTO,
)


@pytest.mark.parametrize(
    "value,kind",
    [
        (None, Kind.NULL),
        (True, Kind.BOOLEAN),
        (1, Kind.INTEGER),
        (1.0, Kind.FLOAT),
        ("", Kind.STRING),
        ({}, Kind.MAPPING),
        ([], Kind.SEQUENCE),
    ],
)
def test_explicit_kinds(value, kind):
    assert canonicalize(value).kind == kind


def test_python_coercion_does_not_hide_type_change():
    assert canonicalize(True) != canonicalize(1)
    assert canonicalize(1) != canonicalize(1.0)
    assert canonicalize(None) != canonicalize("")
    assert canonicalize({"b": 2, "a": 1}) == canonicalize({"a": 1, "b": 2})
    assert canonicalize([1, 2]) != canonicalize([2, 1])
    assert canonicalize("é") != canonicalize("e\u0301")


def test_detached_immutable_tree_and_private_repr():
    source = {"secret_key": ["sentinel-value"]}
    node = canonicalize(source)
    source["secret_key"].append("new")
    assert node == canonicalize({"secret_key": ["sentinel-value"]})
    assert "sentinel" not in repr(node)
    assert "secret_key" not in repr(node)
    assert "sentinel" not in repr(Scalar("sentinel"))
    with pytest.raises(FrozenInstanceError):
        node.kind = Kind.STRING


@pytest.mark.parametrize(
    "value",
    [math.nan, math.inf, -math.inf, {1: "value"}, {True: 1}, (1, 2), {1, 2}, b"bytes", object()],
)
def test_unsupported_values_are_sanitized(value):
    with pytest.raises(ConfigError) as error:
        canonicalize(value)
    assert error.value.code == ErrorCode.UNSUPPORTED
    assert str(error.value) == "Estrutura ou recurso não suportado"


def test_limits_at_boundaries():
    assert canonicalize({"a": [1]}, Limits(max_nodes=3, max_depth=2))
    with pytest.raises(ConfigError) as error:
        canonicalize({"a": [1]}, Limits(max_nodes=2))
    assert error.value.code == ErrorCode.NODE_LIMIT
    with pytest.raises(ConfigError) as error:
        canonicalize({"a": [1]}, Limits(max_depth=1))
    assert error.value.code == ErrorCode.DEPTH_LIMIT
    assert canonicalize(1, Limits(max_depth=0, max_nodes=1))
    nested = 0
    for _ in range(64):
        nested = [nested]
    assert canonicalize(nested)
    with pytest.raises(ConfigError) as error:
        canonicalize([nested])
    assert error.value.code == ErrorCode.DEPTH_LIMIT


def test_cycle_is_bounded():
    cycle = []
    cycle.append(cycle)
    with pytest.raises(ConfigError) as error:
        canonicalize(cycle)
    assert error.value.code == ErrorCode.DEPTH_LIMIT


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_nodes": 0},
        {"max_depth": -1},
        {"max_depth": 65},
        {"max_bytes": True},
        {"max_tokens": 0},
        {"timeout_seconds": 0},
        {"timeout_seconds": math.nan},
    ],
)
def test_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        Limits(**kwargs)


def test_constructor_invariants():
    with pytest.raises(ConfigError) as error:
        Mapping((("a", Scalar(1)), ("a", Scalar(2))))
    assert error.value.code == ErrorCode.DUPLICATE_KEY
    with pytest.raises(ConfigError):
        Sequence([Scalar(1)])
    with pytest.raises(ConfigError):
        Mapping(((1, Scalar(1)),))
    with pytest.raises(ValueError):
        Index(True)


def test_paths_have_no_ambiguous_segments_or_invisible_controls():
    paths = [
        (),
        (Key("a.b"),),
        (Key("a"), Key("b")),
        (Key("0"),),
        (Index(0),),
        (Key('a"\\\n\u202eç'),),
    ]
    rendered = [render_path(path) for path in paths]
    assert len(set(rendered)) == len(paths)
    assert rendered[:5] == ["$", '$["a.b"]', '$["a"]["b"]', '$["0"]', "$[0]"]
    assert "\n" not in rendered[5] and "\u202e" not in rendered[5]
    assert r"\u202e" in rendered[5] and r"\u00e7" in rendered[5]


def test_results_absent_is_not_null_and_transport_is_controlled():
    entry = DiffEntry((Key("key"),), Category.MISSING_A, None, Scalar(None))
    assert entry.kind_a is None and entry.kind_b == Kind.NULL
    result = ComparisonResult(Format.JSON, (entry,), 0.01)
    assert result.counts[Category.MISSING_A] == 1
    assert result.counts[Category.EQUAL] == 0
    assert pickle.loads(pickle.dumps(result)) == result
    dto = SanitizedReportDTO(
        Format.JSON,
        (SanitizedEntry(render_path(entry.path), entry.category, entry.kind_a, entry.kind_b),),
    )
    assert set(asdict(dto)["entries"][0]) == {"path", "category", "kind_a", "kind_b"}


def test_error_has_only_safe_metadata():
    error = ConfigError(ErrorCode.INVALID_SYNTAX, side=Side.B, line=3, column=8)
    assert str(error) == "Arquivo B: Sintaxe inválida (linha 3, coluna 8)"
    assert error.args == (str(error),)
