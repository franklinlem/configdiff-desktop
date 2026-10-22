"""Pacote auxiliar de evidências/fontes Debian. Preserva o RC2 já aceito."""

import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def validate_sources(root: Path, items: list[dict]) -> list[tuple[Path, str]]:
    files = []
    for item in items:
        relative = PurePosixPath(item["path"])
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("Caminho fonte inválido")
        source = root / Path(*relative.parts)
        if source.is_symlink() or not source.is_file() or digest(source) != item["sha256"]:
            raise ValueError("Fonte ausente ou divergente")
        files.append((source, relative.as_posix()))
    return files


def main() -> None:
    provenance = json.loads((ROOT / "third_party/binary-provenance.json").read_text())
    if provenance["mismatches"]:
        raise ValueError("Auditoria tem divergências; pacote bloqueado")
    lock = json.loads((ROOT / "third_party/debian-sources.json").read_text())
    files = validate_sources(ROOT / "dist/debian-sources", lock["files"])
    version = provenance["bundle_version"]
    output = ROOT / "dist" / f"configdiff-{version}-debian-sources-and-provenance.tar"
    with tarfile.open(output, "w") as archive:
        for source, relative in files:
            archive.add(source, arcname="ConfigDiff-provenance/dist/debian-sources/" + relative)
        for name in [
            "debian-sources.json",
            "binary-provenance.json",
            "published-wheels.json",
            "upstream-sources.json",
        ]:
            archive.add(
                ROOT / "third_party" / name, arcname="ConfigDiff-provenance/third_party/" + name
            )
        archive.add(ROOT / "docs/provenance-audit.md", arcname="ConfigDiff-provenance/README.md")
        archive.add(ROOT / "LICENSE", arcname="ConfigDiff-provenance/LICENSE")
        archive.add(
            ROOT / "THIRD_PARTY_NOTICES.md", arcname="ConfigDiff-provenance/THIRD_PARTY_NOTICES.md"
        )
        archive.add(
            ROOT / "docs/provenance-audit.md",
            arcname="ConfigDiff-provenance/docs/provenance-audit.md",
        )
        for name in ["audit_provenance.py", "package_provenance.py"]:
            archive.add(ROOT / "scripts" / name, arcname="ConfigDiff-provenance/scripts/" + name)
    output.with_suffix(".tar.sha256").write_text(f"{digest(output)}  {output.name}\n")
    print(f"Pacote auxiliar: {output.name}; {len(files)} arquivos fonte verificados.")


if __name__ == "__main__":
    main()
