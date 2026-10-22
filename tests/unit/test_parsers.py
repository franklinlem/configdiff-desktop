import json

import pytest

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import Limits
from configdiff.domain.nodes import canonicalize
from configdiff.domain.results import Format
from configdiff.parsers import parse_bytes


def parse(text, format=Format.JSON, **kwargs):
    return parse_bytes(text.encode("utf-8"), format, Limits(**kwargs))


@pytest.mark.parametrize(
    "format,text,expected",
    [
        (Format.JSON, '{"a": [true, 1, 1.0, null, "é"]}', {"a": [True, 1, 1.0, None, "é"]}),
        (Format.JSON, '"scalar"', "scalar"),
        (Format.JSON, "42", 42),
        (Format.JSON, "[]", []),
        (Format.JSON, "{}", {}),
        (Format.JSON, "null", None),
        (
            Format.JSON,
            '{"brackets": "[[[[[[[", "escape": "\\""}',
            {"brackets": "[[[[[[[", "escape": '"'},
        ),
        (Format.YAML, "", None),
        (Format.YAML, "# comment\n", None),
        (Format.YAML, 'a: [true, 1, 1.0, null, "é"]', {"a": [True, 1, 1.0, None, "é"]}),
        (
            Format.YAML,
            "a: yes\nb: 2026-10-22\nc: 012\nd: 0x10\ne: 1e3",
            {"a": "yes", "b": "2026-10-22", "c": "012", "d": "0x10", "e": "1e3"},
        ),
        (
            Format.YAML,
            'a: "true"\nb: FALSE\nc: -1.5e+2\ntrue: 3',
            {"a": "true", "b": "FALSE", "c": -150.0, "true": 3},
        ),
        (Format.YAML, "a: |\n  first\n  second\n", {"a": "first\nsecond\n"}),
        (Format.YAML, "a: ~\nb:", {"a": None, "b": None}),
        (Format.ENV, "", {}),
        (Format.ENV, "# comment\n\n", {}),
        (
            Format.ENV,
            "export A = false\nB=\nC=literal#hash\nD=word # comment",
            {"A": "false", "B": "", "C": "literal#hash", "D": "word"},
        ),
        (
            Format.ENV,
            "A= # empty\nB=\"x#y\" # comment\nC='x # y'",
            {"A": "", "B": "x#y", "C": "x # y"},
        ),
        (Format.ENV, 'A="escaped\\"quote\\\\slash"', {"A": 'escaped"quote\\slash'}),
        (
            Format.ENV,
            "A=$HOME\nB=${HOME}\nC=~\nD=$(command)\r\nE=é",
            {"A": "$HOME", "B": "${HOME}", "C": "~", "D": "$(command)", "E": "é"},
        ),
        (Format.ENV, "A='literal\\n'", {"A": "literal\\n"}),
    ],
)
def test_accepted(format, text, expected):
    assert parse(text, format) == canonicalize(expected)


@pytest.mark.parametrize(
    "format,text,code",
    [
        (Format.JSON, '{"a": 1, "a": 2}', ErrorCode.DUPLICATE_KEY),
        (Format.JSON, '{"a": 1, "\\u0061": 2}', ErrorCode.DUPLICATE_KEY),
        (Format.JSON, '{"a": {"x": 1, "x": 2}}', ErrorCode.DUPLICATE_KEY),
        *[
            (Format.JSON, text, ErrorCode.UNSUPPORTED)
            for text in ["NaN", "Infinity", "-Infinity", "1e999"]
        ],
        *[
            (Format.JSON, text, ErrorCode.INVALID_SYNTAX)
            for text in [
                "",
                " ",
                "[1,]",
                "{}{}",
                "01",
                "[}",
                '{"a":}',
                '{"a": "SENTINEL"',
                '"bad\\x"',
                '"bad\nline"',
            ]
        ],
        (Format.YAML, "a: 1\na: 2", ErrorCode.DUPLICATE_KEY),
        (Format.YAML, 'a: 1\n"a": 2', ErrorCode.DUPLICATE_KEY),
        *[
            (Format.YAML, text, ErrorCode.UNSUPPORTED)
            for text in [
                "a: &x 1",
                "a: *x",
                "a: !custom SENTINEL",
                "a: !!str value",
                "<<: value",
                "? [a, b]\n: value",
                "---\na: 1\n---\nb: 2",
                "a: .nan",
                "a: -.Inf",
                "a: 1.0e999",
            ]
        ],
        (Format.YAML, "a: [SENTINEL", ErrorCode.INVALID_SYNTAX),
        (Format.ENV, "A=1\nA=2", ErrorCode.DUPLICATE_KEY),
        *[
            (Format.ENV, text, ErrorCode.INVALID_SYNTAX)
            for text in [
                "NO_EQUALS",
                "1KEY=x",
                'A="SENTINEL',
                'A="unknown\\n"',
                'A="unknown\\$"',
                'A="x"suffix',
                'A="x"#comment',
                "A=multi\\\nline",
                "A='first\nsecond'",
                "A=\x00",
                "A=x\ry",
                'A=x"y',
            ]
        ],
    ],
)
def test_rejected_without_raw_content(format, text, code):
    with pytest.raises(ConfigError) as error:
        parse(text, format)
    assert error.value.code == code
    assert "SENTINEL" not in str(error.value)
    assert error.value.__cause__ is None
    if error.value.__context__ is not None:
        assert error.value.__suppress_context__


@pytest.mark.parametrize(
    "format,text", [(Format.JSON, "{}"), (Format.YAML, "{}"), (Format.ENV, "A=1")]
)
def test_bytes_bom_utf8_and_size(format, text):
    data = b"\xef\xbb\xbf" + text.encode()
    assert parse_bytes(data, format) == parse(text, format)
    assert parse_bytes(data, format, Limits(max_bytes=len(data)))
    with pytest.raises(ConfigError) as error:
        parse_bytes(data, format, Limits(max_bytes=len(data) - 1))
    assert error.value.code == ErrorCode.SIZE_LIMIT
    with pytest.raises(ConfigError) as error:
        parse_bytes(b"\xff\xfe", format)
    assert error.value.code == ErrorCode.INVALID_ENCODING


@pytest.mark.parametrize("format", [Format.JSON, Format.YAML])
def test_nested_limits_before_building_deep_tree(format):
    assert parse("[[0]]", format, max_depth=2, max_nodes=3)
    with pytest.raises(ConfigError) as error:
        parse("[[0]]", format, max_depth=1)
    assert error.value.code == ErrorCode.DEPTH_LIMIT
    with pytest.raises(ConfigError) as error:
        parse("[" * 2000 + "0" + "]" * 2000, format)
    assert error.value.code == ErrorCode.DEPTH_LIMIT


@pytest.mark.parametrize(
    "format,text", [(Format.JSON, "[0,1]"), (Format.YAML, "[0,1]"), (Format.ENV, "A=x\nB=y")]
)
def test_node_limits(format, text):
    assert parse(text, format, max_nodes=3)
    with pytest.raises(ConfigError) as error:
        parse(text, format, max_nodes=2)
    assert error.value.code == ErrorCode.NODE_LIMIT


@pytest.mark.parametrize("format", [Format.JSON, Format.YAML])
def test_token_limit(format):
    with pytest.raises(ConfigError) as error:
        parse("[1,2,3]", format, max_tokens=3)
    assert error.value.code == ErrorCode.NODE_LIMIT


def test_json_string_tokens_do_not_look_like_structure():
    text = json.dumps({"a": "[{", "b": '\\"', "c": {":": True}})
    assert parse(text, max_depth=2, max_nodes=5) == canonicalize(json.loads(text))


def test_error_position():
    with pytest.raises(ConfigError) as error:
        parse('{\n "a": invalid\n}')
    assert error.value.line == 2
    assert error.value.column is not None
