"""Resultados ricos são transitórios; exportadores recebem somente o DTO sanitizado."""

from dataclasses import dataclass, field
from enum import StrEnum

from configdiff.domain.nodes import Kind, Node
from configdiff.domain.paths import Path


class Format(StrEnum):
    JSON = "json"
    YAML = "yaml"
    ENV = "env"


class Category(StrEnum):
    MISSING_A = "missing_a"
    MISSING_B = "missing_b"
    TYPE_CHANGED = "type_changed"
    VALUE_CHANGED = "value_changed"
    EQUAL = "equal"


@dataclass(frozen=True, slots=True)
class DiffEntry:
    path: Path
    category: Category
    a: Node | None = field(repr=False)
    b: Node | None = field(repr=False)

    @property
    def kind_a(self) -> Kind | None:
        return self.a.kind if self.a is not None else None

    @property
    def kind_b(self) -> Kind | None:
        return self.b.kind if self.b is not None else None


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    format: Format
    entries: tuple[DiffEntry, ...] = field(repr=False)
    duration_seconds: float

    @property
    def counts(self) -> dict[Category, int]:
        counts = dict.fromkeys(Category, 0)
        for entry in self.entries:
            counts[entry.category] += 1
        return counts


@dataclass(frozen=True, slots=True)
class SanitizedEntry:
    path: str
    category: Category
    kind_a: Kind | None
    kind_b: Kind | None


@dataclass(frozen=True, slots=True)
class SanitizedReportDTO:
    format: Format
    entries: tuple[SanitizedEntry, ...]
