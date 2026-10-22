"""Comparação estrutural: ausências e mudanças de tipo param na raiz do ramo."""

from configdiff.domain.nodes import Mapping, Node, Scalar, Sequence
from configdiff.domain.paths import Index, Key, Path
from configdiff.domain.results import Category, DiffEntry


def compare(a: Node, b: Node) -> tuple[DiffEntry, ...]:
    entries: list[DiffEntry] = []

    def visit(left: Node | None, right: Node | None, path: Path) -> None:
        if left is None:
            category = Category.MISSING_A
        elif right is None:
            category = Category.MISSING_B
        elif left.kind != right.kind:
            category = Category.TYPE_CHANGED
        elif isinstance(left, Mapping) and isinstance(right, Mapping):
            first, second = dict(left.entries), dict(right.entries)
            keys = sorted(first.keys() | second.keys())
            if keys:
                for key in keys:
                    visit(first.get(key), second.get(key), (*path, Key(key)))
                return
            category = Category.EQUAL
        elif isinstance(left, Sequence) and isinstance(right, Sequence):
            length = max(len(left.items), len(right.items))
            if length:
                for index in range(length):
                    visit(
                        left.items[index] if index < len(left.items) else None,
                        right.items[index] if index < len(right.items) else None,
                        (*path, Index(index)),
                    )
                return
            category = Category.EQUAL
        else:
            assert isinstance(left, Scalar) and isinstance(right, Scalar)
            category = Category.EQUAL if left.value == right.value else Category.VALUE_CHANGED
        entries.append(DiffEntry(path, category, left, right))

    visit(a, b, ())
    return tuple(entries)
