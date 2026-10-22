from dataclasses import dataclass

from configdiff.domain.errors import ConfigError, ErrorCode, Side


@dataclass(frozen=True, slots=True)
class Failure:
    code: ErrorCode
    side: Side | None = None
    line: int | None = None
    column: int | None = None

    def exception(self) -> ConfigError:
        return ConfigError(self.code, side=self.side, line=self.line, column=self.column)
