"""Subconjunto de dotenv; não expande nem executa conteúdo."""

import re

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import Limits
from configdiff.domain.nodes import Node, canonicalize

_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_COMMENT = re.compile(r"[ \t]+#")


def _value(raw: str, line: int) -> str:
    original = raw
    raw = raw.strip(" \t")
    if not raw.startswith(("'", '"')):
        match = _COMMENT.search(original)
        value = original[: match.start()] if match else original
        # Aspas avulsas, controles e continuação são ambíguos neste subconjunto.
        if "'" in value or '"' in value or value.endswith("\\"):
            raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line)
        return value.strip(" \t")
    quote = raw[0]
    output: list[str] = []
    index = 1
    while index < len(raw):
        char = raw[index]
        if char == quote:
            remainder = raw[index + 1 :]
            if remainder.strip(" \t") and not (
                remainder[0] in " \t" and remainder.lstrip(" \t").startswith("#")
            ):
                raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line)
            return "".join(output)
        if char == "\\" and quote == '"':
            index += 1
            if index == len(raw) or raw[index] not in ('"', "\\"):
                raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line)
            char = raw[index]
        output.append(char)
        index += 1
    raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line)


def parse(text: str, limits: Limits) -> Node:
    values: dict[str, object] = {}
    # Apenas LF e CRLF; splitlines aceitaria silenciosamente outros controles.
    for line, raw in enumerate(text.split("\n"), 1):
        raw = raw.removesuffix("\r")
        if any(ord(char) < 32 and char != "\t" for char in raw) or "\x7f" in raw:
            raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line)
        raw = raw.strip(" \t")
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("export") and len(raw) > 6 and raw[6] in " \t":
            raw = raw[6:].lstrip(" \t")
        key, separator, value = raw.partition("=")
        key = key.strip(" \t")
        if not separator or not _KEY.fullmatch(key):
            raise ConfigError(ErrorCode.INVALID_SYNTAX, line=line)
        if key in values:
            raise ConfigError(ErrorCode.DUPLICATE_KEY, line=line)
        if len(values) + 2 > limits.max_nodes:
            raise ConfigError(ErrorCode.NODE_LIMIT, line=line)
        values[key] = _value(value, line)
    return canonicalize(values, limits)
