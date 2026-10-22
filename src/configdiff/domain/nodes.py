"""Árvore imutável, com tipo escalar explícito e repr sem valores."""

import math
from dataclasses import dataclass, field
from enum import StrEnum

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import DEFAULT_LIMITS, Limits


class Kind(StrEnum):
    NULL = "null"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    MAPPING = "mapping"
    SEQUENCE = "sequence"


type ScalarValue = None | bool | int | float | str


def scalar_kind(value: ScalarValue) -> Kind:
    # Igualdade Python não distingue True de 1; tipos exatos distinguem.
    kinds = {
        type(None): Kind.NULL,
        bool: Kind.BOOLEAN,
        int: Kind.INTEGER,
        float: Kind.FLOAT,
        str: Kind.STRING,
    }
    kind = kinds.get(type(value))
    if kind is None or (type(value) is float and not math.isfinite(value)):
        raise ConfigError(ErrorCode.UNSUPPORTED)
    return kind


@dataclass(frozen=True, slots=True)
class Scalar:
    value: ScalarValue = field(repr=False)
    kind: Kind = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", scalar_kind(self.value))


@dataclass(frozen=True, slots=True)
class Mapping:
    entries: tuple[tuple[str, "Node"], ...] = field(repr=False)
    kind: Kind = field(default=Kind.MAPPING, init=False)

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise ConfigError(ErrorCode.UNSUPPORTED)
        seen: set[str] = set()
        for pair in self.entries:
            if type(pair) is not tuple or len(pair) != 2:
                raise ConfigError(ErrorCode.UNSUPPORTED)
            key, value = pair
            if type(key) is not str or not isinstance(value, (Scalar, Mapping, Sequence)):
                raise ConfigError(ErrorCode.UNSUPPORTED)
            if key in seen:
                raise ConfigError(ErrorCode.DUPLICATE_KEY)
            seen.add(key)


@dataclass(frozen=True, slots=True)
class Sequence:
    items: tuple["Node", ...] = field(repr=False)
    kind: Kind = field(default=Kind.SEQUENCE, init=False)

    def __post_init__(self) -> None:
        if type(self.items) is not tuple or any(
            not isinstance(child, (Scalar, Mapping, Sequence)) for child in self.items
        ):
            raise ConfigError(ErrorCode.UNSUPPORTED)


type Node = Scalar | Mapping | Sequence


def canonicalize(value: object, limits: Limits = DEFAULT_LIMITS) -> Node:
    """Raiz na profundidade 0; conta raiz + cada entrada/elemento recursivamente.

    Aceita somente tipos built-in vindos dos parsers, sem coerção de objetos.
    Ciclos falham no limite de profundidade; não se expande alias ilimitadamente.
    """
    count = 0

    def visit(item: object, depth: int) -> Node:
        nonlocal count
        if depth > limits.max_depth:
            raise ConfigError(ErrorCode.DEPTH_LIMIT)
        count += 1
        if count > limits.max_nodes:
            raise ConfigError(ErrorCode.NODE_LIMIT)
        if type(item) is dict:
            pairs: list[tuple[str, Node]] = []
            for key, child in item.items():
                if type(key) is not str:
                    raise ConfigError(ErrorCode.UNSUPPORTED)
                pairs.append((key, visit(child, depth + 1)))
            # Ordem de mapeamentos não afeta a igualdade canônica.
            return Mapping(tuple(sorted(pairs)))
        if type(item) is list:
            return Sequence(tuple(visit(child, depth + 1) for child in item))
        if item is None or type(item) in (bool, int, float, str):
            return Scalar(item)  # type: ignore[arg-type]
        raise ConfigError(ErrorCode.UNSUPPORTED)

    return visit(value, 0)
