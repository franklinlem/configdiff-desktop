"""Exportação exclusiva: nunca trunca nem substitui arquivos existentes."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.results import SanitizedReportDTO
from configdiff.services.files import FileIdentity
from configdiff.services.reports import render_markdown


@dataclass(frozen=True, slots=True)
class SourceRef:
    path: Path = field(repr=False)
    resolved_path: Path = field(repr=False)
    identity: FileIdentity

    @classmethod
    def capture(cls, path: Path, identity: FileIdentity) -> "SourceRef":
        return cls(path.absolute(), path.resolve(), identity)


def export_report(
    report: SanitizedReportDTO, destination: Path, sources: tuple[SourceRef, ...]
) -> None:
    # Sem acesso a ComparisonResult ou aos documentos de origem.
    text = render_markdown(report)
    try:
        absolute = destination.absolute()
        resolved = destination.resolve()
        for source in sources:
            if absolute == source.path or resolved == source.resolved_path:
                raise ConfigError(ErrorCode.PROTECTED_SOURCE)
        try:
            existing = destination.stat()
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if any(
                (existing.st_dev, existing.st_ino)
                == (source.identity.device, source.identity.inode)
                for source in sources
            ):
                raise ConfigError(ErrorCode.PROTECTED_SOURCE)
            raise ConfigError(ErrorCode.OUTPUT_EXISTS)
        # O_EXCL cobre corridas, hard links e symlinks, inclusive dangling links.
        descriptor = os.open(
            destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600
        )
        with os.fdopen(descriptor, "wb") as output:
            output.write(text.encode("utf-8"))
    except FileExistsError:
        raise ConfigError(ErrorCode.OUTPUT_EXISTS) from None
    except (OSError, ValueError, RuntimeError):
        # Uma escrita incompleta pode deixar relatório parcial, sempre sem valores.
        raise ConfigError(ErrorCode.EXPORT_FAILED) from None
