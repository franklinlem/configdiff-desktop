"""Erros públicos transportam somente metadados controlados, nunca a entrada."""

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_SYNTAX = "invalid_syntax"
    INVALID_ENCODING = "invalid_encoding"
    DUPLICATE_KEY = "duplicate_key"
    UNSUPPORTED = "unsupported"
    SIZE_LIMIT = "size_limit"
    DEPTH_LIMIT = "depth_limit"
    NODE_LIMIT = "node_limit"
    INVALID_FILE = "invalid_file"
    FILE_CHANGED = "file_changed"
    ACCESS_DENIED = "access_denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    WORKER_FAILED = "worker_failed"


class Side(StrEnum):
    A = "A"
    B = "B"


_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_SYNTAX: "Sintaxe inválida",
    ErrorCode.INVALID_ENCODING: "Codificação inválida; use UTF-8",
    ErrorCode.DUPLICATE_KEY: "Chave duplicada",
    ErrorCode.UNSUPPORTED: "Estrutura ou recurso não suportado",
    ErrorCode.SIZE_LIMIT: "Limite de tamanho excedido",
    ErrorCode.DEPTH_LIMIT: "Limite de profundidade excedido",
    ErrorCode.NODE_LIMIT: "Limite de nós excedido",
    ErrorCode.INVALID_FILE: "Selecione um arquivo regular acessível",
    ErrorCode.FILE_CHANGED: "Arquivo alterado durante a leitura; tente novamente",
    ErrorCode.ACCESS_DENIED: "Não foi possível acessar o arquivo",
    ErrorCode.TIMEOUT: "Tempo limite atingido",
    ErrorCode.CANCELLED: "Comparação cancelada",
    ErrorCode.WORKER_FAILED: "Falha no processo de comparação",
}


class ConfigError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        *,
        side: Side | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        self.code = code
        self.side = side
        self.line = line
        self.column = column
        # args contém apenas a mensagem sanitizada, para repr e logs acidentais.
        super().__init__(self.message)

    @property
    def message(self) -> str:
        prefix = f"Arquivo {self.side.value}: " if self.side else ""
        position = f" (linha {self.line}" if self.line is not None else ""
        if position:
            if self.column is not None:
                position += f", coluna {self.column}"
            position += ")"
        return prefix + _MESSAGES[self.code] + position
