"""Indicador auxiliar por nome; o mascaramento não depende desta heurística."""

import re

from configdiff.domain.paths import Key, Path

_MARKERS = ("password", "passwd", "token", "secret", "apikey", "privatekey")


def potentially_sensitive(path: Path) -> bool:
    return any(
        any(marker in re.sub(r"[^a-z0-9]", "", segment.value.casefold()) for marker in _MARKERS)
        for segment in path
        if isinstance(segment, Key)
    )
