"""Captura limitada, somente leitura; sem arquivos temporários de conteúdo."""

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import DEFAULT_LIMITS, Limits
from configdiff.domain.results import Format


@dataclass(frozen=True, slots=True)
class FileIdentity:
    device: int
    inode: int
    size: int
    modified_ns: int
    changed_ns: int

    @classmethod
    def from_stat(cls, value: os.stat_result) -> "FileIdentity":
        return cls(value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


@dataclass(frozen=True, slots=True)
class Snapshot:
    data: bytes = field(repr=False)
    identity: FileIdentity


def detect_format(path: Path) -> Format | None:
    name = path.name.lower()
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        return Format.ENV
    return {".json": Format.JSON, ".yaml": Format.YAML, ".yml": Format.YAML}.get(
        path.suffix.lower()
    )


def read_snapshot(path: Path, limits: Limits = DEFAULT_LIMITS) -> Snapshot:
    try:
        # Evita abrir FIFO/dispositivo conhecido. fstat confirma o objeto aberto.
        if not stat.S_ISREG(path.stat().st_mode):
            raise ConfigError(ErrorCode.INVALID_FILE)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(path, flags)
        try:
            before_stat = os.fstat(descriptor)
            if not stat.S_ISREG(before_stat.st_mode):
                raise ConfigError(ErrorCode.INVALID_FILE)
            before = FileIdentity.from_stat(before_stat)
            if before.size > limits.max_bytes:
                raise ConfigError(ErrorCode.SIZE_LIMIT)
            chunks: list[bytes] = []
            total = 0
            while total <= limits.max_bytes:
                chunk = os.read(descriptor, min(64 * 1024, limits.max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            if total > limits.max_bytes:
                raise ConfigError(ErrorCode.SIZE_LIMIT)
            after = FileIdentity.from_stat(os.fstat(descriptor))
            if before != after or total != after.size:
                raise ConfigError(ErrorCode.FILE_CHANGED)
            return Snapshot(b"".join(chunks), after)
        finally:
            os.close(descriptor)
    except PermissionError:
        raise ConfigError(ErrorCode.ACCESS_DENIED) from None
    except (OSError, ValueError):
        raise ConfigError(ErrorCode.INVALID_FILE) from None
