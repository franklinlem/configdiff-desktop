"""Parser por eventos, sem construir objetos/tags do YAML."""

import math
import re

import yaml
from yaml.events import (
    DocumentEndEvent,
    DocumentStartEvent,
    MappingEndEvent,
    MappingStartEvent,
    ScalarEvent,
    SequenceEndEvent,
    SequenceStartEvent,
    StreamEndEvent,
    StreamStartEvent,
)
from yaml.tokens import AliasToken, AnchorToken, TagToken

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import Limits
from configdiff.domain.nodes import Mapping, Node, Scalar, Sequence

_INTEGER = re.compile(r"-?(0|[1-9][0-9]*)")
_FLOAT = re.compile(r"-?(0|[1-9][0-9]*)\.[0-9]+([eE][+-]?[0-9]+)?")


def _scalar(value: str, style: str | None) -> Scalar:
    if style is not None:
        return Scalar(value)
    if value in ("null", "~", ""):
        return Scalar(None)
    if value in ("true", "false"):
        return Scalar(value == "true")
    if _INTEGER.fullmatch(value):
        return Scalar(int(value))
    if _FLOAT.fullmatch(value):
        number = float(value)
        if not math.isfinite(number):
            raise ConfigError(ErrorCode.UNSUPPORTED)
        return Scalar(number)
    if value.lower() in (".nan", ".inf", "+.inf", "-.inf"):
        raise ConfigError(ErrorCode.UNSUPPORTED)
    return Scalar(value)


def parse(text: str, limits: Limits) -> Node:
    try:
        # A varredura não compõe árvores e rejeita recursos antes da construção.
        for count, token in enumerate(yaml.scan(text), 1):
            if count > limits.max_tokens:
                raise ConfigError(ErrorCode.NODE_LIMIT)
            if isinstance(token, (AliasToken, AnchorToken, TagToken)):
                raise ConfigError(
                    ErrorCode.UNSUPPORTED,
                    line=token.start_mark.line + 1,
                    column=token.start_mark.column + 1,
                )
        events = iter(yaml.parse(text, Loader=yaml.BaseLoader))
        nodes = 0

        def expect(event_type: type) -> None:
            if not isinstance(next(events), event_type):
                raise ConfigError(ErrorCode.INVALID_SYNTAX)

        def visit(event: object, depth: int) -> Node:
            nonlocal nodes
            if depth > limits.max_depth:
                raise ConfigError(ErrorCode.DEPTH_LIMIT)
            nodes += 1
            if nodes > limits.max_nodes:
                raise ConfigError(ErrorCode.NODE_LIMIT)
            if isinstance(event, ScalarEvent):
                return _scalar(event.value, event.style)
            if isinstance(event, SequenceStartEvent):
                items: list[Node] = []
                while not isinstance(child := next(events), SequenceEndEvent):
                    items.append(visit(child, depth + 1))
                return Sequence(tuple(items))
            if isinstance(event, MappingStartEvent):
                pairs: list[tuple[str, Node]] = []
                seen: set[str] = set()
                while not isinstance(key := next(events), MappingEndEvent):
                    if not isinstance(key, ScalarEvent) or key.value == "<<":
                        raise ConfigError(ErrorCode.UNSUPPORTED)
                    if key.value in seen:
                        raise ConfigError(
                            ErrorCode.DUPLICATE_KEY,
                            line=key.start_mark.line + 1,
                            column=key.start_mark.column + 1,
                        )
                    seen.add(key.value)
                    pairs.append((key.value, visit(next(events), depth + 1)))
                return Mapping(tuple(sorted(pairs)))
            raise ConfigError(ErrorCode.UNSUPPORTED)

        expect(StreamStartEvent)
        root = next(events)
        if isinstance(root, StreamEndEvent):
            return Scalar(None)
        if not isinstance(root, DocumentStartEvent):
            raise ConfigError(ErrorCode.INVALID_SYNTAX)
        result = visit(next(events), 0)
        expect(DocumentEndEvent)
        # Outro DocumentStartEvent significa múltiplos documentos.
        if not isinstance(next(events), StreamEndEvent):
            raise ConfigError(ErrorCode.UNSUPPORTED)
        return result
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        raise ConfigError(
            ErrorCode.INVALID_SYNTAX,
            line=mark.line + 1 if mark else None,
            column=mark.column + 1 if mark else None,
        ) from None
    except (ValueError, RecursionError, StopIteration):
        raise ConfigError(ErrorCode.INVALID_SYNTAX) from None
