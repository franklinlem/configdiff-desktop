from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Limits:
    max_bytes: int = 5 * 1024 * 1024
    max_depth: int = 64
    max_nodes: int = 50_000
    max_tokens: int = 200_000
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value < 1
            for value in (
                self.max_bytes,
                self.max_nodes,
                self.max_tokens,
            )
        ):
            raise ValueError("Limites de tamanho, nós e tokens devem ser inteiros positivos")
        if type(self.max_depth) is not int or not 0 <= self.max_depth <= 64:
            raise ValueError("Profundidade deve estar entre 0 e 64")
        import math

        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("Timeout deve ser finito e positivo")


DEFAULT_LIMITS = Limits()
