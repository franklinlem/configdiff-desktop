import json
import math
import re

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import Limits
from configdiff.domain.nodes import Node, canonicalize

_TOKEN = re.compile(
    r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|true|false|null|NaN|-?Infinity|[{}\[\],:]"
)
_STRING_DECODER = json.JSONDecoder()
_SPACE = re.compile(r"[ \t\r\n]*")


def _preflight(text: str, limits: Limits) -> None:
    """Conta tokens/nós e profundidade antes de alocar a árvore do decoder."""
    position = nodes = tokens = 0
    stack: list[str] = []
    while True:
        position = _SPACE.match(text, position).end()  # type: ignore[union-attr]
        if position == len(text):
            return
        if text[position] == '"':
            # O decoder de strings evita a pilha de backtracking de regex em
            # strings de vários MiB. O conteúdo decodificado é descartado aqui.
            _, position = _STRING_DECODER.raw_decode(text, position)
            token = '"'
        else:
            match = _TOKEN.match(text, position)
            if match is None:
                line = text.count("\n", 0, position) + 1
                column = position - text.rfind("\n", 0, position)
                raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line, column=column)
            token = match.group()
            position = match.end()
        tokens += 1
        if tokens > limits.max_tokens:
            raise ConfigError(ErrorCode.NODE_LIMIT)
        next_position = _SPACE.match(text, position).end()  # type: ignore[union-attr]
        key = token.startswith('"') and text[next_position : next_position + 1] == ":"
        if token not in ("}", "]", ",", ":") and not key:
            nodes += 1
            if nodes > limits.max_nodes:
                raise ConfigError(ErrorCode.NODE_LIMIT)
            if len(stack) > limits.max_depth:
                raise ConfigError(ErrorCode.DEPTH_LIMIT)
        if token in ("{", "["):
            stack.append(token)
        elif token in ("}", "]") and (not stack or stack.pop() != {"}": "{", "]": "["}[token]):
            raise ConfigError(ErrorCode.INVALID_SYNTAX)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(ErrorCode.DUPLICATE_KEY)
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise ConfigError(ErrorCode.UNSUPPORTED)


def _float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ConfigError(ErrorCode.UNSUPPORTED)
    return number


def parse(text: str, limits: Limits) -> Node:
    try:
        _preflight(text, limits)
        data = json.loads(
            text, object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float
        )
        return canonicalize(data, limits)
    except json.JSONDecodeError as error:
        raise ConfigError(ErrorCode.INVALID_SYNTAX, line=error.lineno, column=error.colno) from None
    except (ValueError, RecursionError):
        raise ConfigError(ErrorCode.INVALID_SYNTAX) from None
