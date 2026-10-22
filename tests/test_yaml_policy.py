import pytest

from prototypes.yaml_policy import PolicyError, parse


def test_semantics():
    assert parse('a: true\nb: yes\nc: 2026-10-22\nd: 012\ne: 12\nf: 1.5\ng: "true"') == {
        "a": True,
        "b": "yes",
        "c": "2026-10-22",
        "d": "012",
        "e": 12,
        "f": 1.5,
        "g": "true",
    }


@pytest.mark.parametrize(
    "text",
    [
        "a: 1\na: 2",
        "a: &x 1",
        "a: *x",
        "a: !custom value",
        "a: !!str value",
        "a: 1\n---\nb: 2",
        "? [a, b]\n: value",
        "<<: value",
        "a: .nan",
        "a: [",
        "[" * 66 + "0" + "]" * 66,
    ],
)
def test_rejected_without_content(text):
    with pytest.raises(PolicyError) as error:
        parse(text)
    assert str(error.value) == "YAML rejeitado pela política do protótipo"


def test_size_limit():
    with pytest.raises(PolicyError):
        parse("x" * (5 * 1024 * 1024 + 1))


def test_node_limit():
    with pytest.raises(PolicyError):
        parse("- x\n" * 50_001)
