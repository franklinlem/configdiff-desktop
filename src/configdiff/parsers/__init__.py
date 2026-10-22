"""Única entrada pública para parsing: bytes limitados em UTF-8 (BOM opcional)."""

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import DEFAULT_LIMITS, Limits
from configdiff.domain.nodes import Node
from configdiff.domain.results import Format


def parse_bytes(data: bytes, format: Format, limits: Limits = DEFAULT_LIMITS) -> Node:
    if len(data) > limits.max_bytes:
        raise ConfigError(ErrorCode.SIZE_LIMIT)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ConfigError(ErrorCode.INVALID_ENCODING) from None
    if format == Format.JSON:
        from configdiff.parsers.json_parser import parse
    elif format == Format.YAML:
        from configdiff.parsers.yaml_parser import parse
    elif format == Format.ENV:
        from configdiff.parsers.env_parser import parse
    else:
        raise ConfigError(ErrorCode.UNSUPPORTED)
    return parse(text, limits)
