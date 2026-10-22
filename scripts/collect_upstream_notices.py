"""Reúne metadados/textos dos arquivos fonte verificados; não afirma uso de cada item."""

import json
import posixpath
import tarfile
from pathlib import Path, PurePosixPath

from fetch_upstream_sources import ROOT, sha256


def safe_relative(name: str) -> Path:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Caminho inválido no arquivo de fontes")
    return Path(*path.parts)


def collect() -> dict[str, object]:
    manifest = json.loads((ROOT / "third_party/upstream-sources.json").read_text())
    records = []
    missing = []
    copied = 0
    destination = ROOT / "third_party/attributions"
    for item in manifest["sources"]:
        source = ROOT / "dist/dependency-sources" / item["filename"]
        if sha256(source) != item["sha256"]:
            raise ValueError("Fonte não confere com o manifesto")
        with tarfile.open(source) as archive:
            members = {member.name: member for member in archive.getmembers() if member.isfile()}
            selected: set[str] = set()
            for name, member in members.items():
                path = PurePosixPath(name)
                base = path.name.casefold()
                if (
                    "LICENSES" in path.parts
                    or base.startswith(("license", "copying", "copyright", "notice"))
                ) and path.suffix.casefold() not in (
                    ".cpp",
                    ".c",
                    ".h",
                    ".py",
                    ".cmake",
                    ".sh",
                    ".qdoc",
                ):
                    selected.add(name)
                if base == "licenses.rst":
                    selected.add(name)
                if base != "qt_attribution.json":
                    continue
                selected.add(name)
                content = json.loads(archive.extractfile(member).read(), strict=False)
                for record in content if isinstance(content, list) else [content]:
                    records.append(
                        {"source_component": item["component"], "source_file": name, **record}
                    )
                    files = record.get("LicenseFile", [])
                    files = [files] if isinstance(files, str) else files
                    for license_file in files:
                        normalized = posixpath.normpath(str(path.parent / license_file))
                        safe_relative(normalized)
                        if normalized in members:
                            selected.add(normalized)
                        else:
                            missing.append({"metadata": name, "file": license_file})
            for name in sorted(selected):
                relative = safe_relative(name)
                output = destination / item["component"] / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(archive.extractfile(members[name]).read())
                copied += 1
    index = {
        "scope": "Upstream source metadata; not proof every listed component is in binary",
        "copied_files": copied,
        "records": records,
        "unresolved_license_references": missing,
    }
    (ROOT / "third_party/attributions-index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=True) + "\n"
    )
    print(
        f"Atribuições upstream: {len(records)} registros, {copied} arquivos, {len(missing)} referências pendentes."
    )
    return index


if __name__ == "__main__":
    collect()
