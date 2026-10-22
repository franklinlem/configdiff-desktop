"""Fontes oficiais fixadas por hash; não extrai código executável nem altera o app."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch(item: dict[str, str]) -> str:
    directory = ROOT / "dist/dependency-sources"
    directory.mkdir(parents=True, exist_ok=True)
    name = item["filename"]
    if Path(name).name != name:
        raise ValueError("Nome inválido no manifesto de fontes")
    destination = directory / name
    if destination.exists() and sha256(destination) == item["sha256"]:
        return name
    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        with urlopen(item["url"], timeout=60) as response, partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if sha256(partial) != item["sha256"]:
            raise ValueError("Hash de fonte divergente: " + name)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return name


def main() -> None:
    manifest = json.loads((ROOT / "third_party/upstream-sources.json").read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        for name in pool.map(fetch, manifest["sources"]):
            print("Fonte verificada:", name, flush=True)


if __name__ == "__main__":
    main()
