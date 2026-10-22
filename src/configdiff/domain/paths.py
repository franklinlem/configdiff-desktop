"""Caminho estrutural inequívoco: chave string é distinta de índice inteiro."""

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Key:
    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise TypeError("Chave deve ser string")


@dataclass(frozen=True, slots=True)
class Index:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value < 0:
            raise ValueError("Índice deve ser inteiro não negativo")


type Path = tuple[Key | Index, ...]


def render_path(path: Path) -> str:
    # ensure_ascii também impede controles bidi invisíveis na apresentação.
    return "$" + "".join(
        f"[{json.dumps(segment.value, ensure_ascii=True)}]"
        if isinstance(segment, Key)
        else f"[{segment.value}]"
        for segment in path
    )
