"""Auditoria Linux do RC2: origens binárias e fontes fixadas, sem alterar o executável."""

import ast
import hashlib
import json
import subprocess
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.request import urlopen

from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, algorithm).hexdigest()


def deb822(text: str) -> list[dict[str, str]]:
    records = []
    for stanza in text.split("\n\n"):
        fields: dict[str, str] = {}
        key = ""
        for line in stanza.splitlines():
            if line.startswith((" ", "\t")) and key:
                fields[key] += "\n" + line.strip()
            elif ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.strip()
        if fields:
            records.append(fields)
    return records


def source_lock(records: list[dict[str, str]], needed: set[tuple[str, str]]) -> dict[str, object]:
    packages = {}
    files: dict[str, dict[str, object]] = {}
    for fields in records:
        key = (fields.get("Package", ""), fields.get("Version", ""))
        if key not in needed or key in packages:
            continue
        directory = fields["Directory"]
        if PurePosixPath(directory).is_absolute() or ".." in PurePosixPath(directory).parts:
            raise ValueError("Diretório de fonte inválido")
        paths = []
        for line in fields["Checksums-Sha256"].splitlines():
            if not line:
                continue
            digest, size, name = line.split()
            if PurePosixPath(name).name != name:
                raise ValueError("Nome de fonte inválido")
            path = directory + "/" + name
            base = (
                "https://security.debian.org/debian-security/"
                if directory.startswith("pool/updates/")
                else "https://deb.debian.org/debian/"
            )
            item = {"path": path, "sha256": digest, "bytes": int(size), "url": base + path}
            if path in files and files[path] != item:
                raise ValueError("Hash conflitante no índice de fontes")
            files[path] = item
            paths.append(path)
        packages[key] = {
            "package": key[0],
            "version": key[1],
            "format": fields.get("Format"),
            "files": paths,
        }
    if missing := needed - set(packages):
        raise ValueError("Versão fonte exata ausente: " + repr(sorted(missing)))
    return {
        "origin": "local apt-cache showsrc; authenticated APT indices configured on build host",
        "packages": [packages[key] for key in sorted(packages)],
        "files": [files[key] for key in sorted(files)],
    }


def download(item: dict[str, object], directory: Path) -> None:
    relative = PurePosixPath(str(item["path"]))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Caminho de download inválido")
    target = directory / Path(*relative.parts)
    if target.exists() and hash_file(target) == item["sha256"]:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    try:
        for attempt in range(3):
            try:
                with (
                    urlopen(str(item["url"]), timeout=60) as response,
                    partial.open("wb") as output,
                ):
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)
                break
            except HTTPError:
                if attempt == 2:
                    raise
                time.sleep(0.5)
        if hash_file(partial) != item["sha256"]:
            raise ValueError("Checksum divergente: " + str(item["path"]))
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)


def wheels() -> list[dict[str, object]]:
    supported = {tag: index for index, tag in enumerate(sys_tags())}
    result = []
    for name in ["PySide6-Essentials", "shiboken6", "PyYAML"]:
        installed = version(name)
        with urlopen(f"https://pypi.org/pypi/{name}/{installed}/json", timeout=30) as source:
            metadata = json.load(source)
        candidates = []
        for asset in metadata["urls"]:
            if asset["packagetype"] != "bdist_wheel":
                continue
            tags = parse_wheel_filename(asset["filename"])[3]
            if ranks := [supported[tag] for tag in tags if tag in supported]:
                candidates.append((min(ranks), asset))
        if not candidates:
            raise ValueError("Wheel compatível não encontrado")
        asset = min(candidates, key=lambda pair: pair[0])[1]
        item = {
            "name": name,
            "version": installed,
            "path": asset["filename"],
            "url": asset["url"],
            "sha256": asset["digests"]["sha256"],
        }
        download(item, ROOT / "dist/provenance-wheels")
        result.append(item)
    return result


def audit(
    rows: list[tuple[str, str, str]], bundle: Path, inventory: dict, wheel_records: list[dict]
) -> dict:
    wheel_members: dict[str, tuple[str, str]] = {}
    for record in wheel_records:
        with zipfile.ZipFile(ROOT / "dist/provenance-wheels" / record["path"]) as archive:
            for name in archive.namelist():
                if name.startswith(("PySide6/", "shiboken6/", "yaml/")) and (
                    name.endswith(".so") or ".so." in name
                ):
                    wheel_members[name] = (
                        record["name"],
                        hashlib.sha256(archive.read(name)).hexdigest(),
                    )
    binaries = []
    mismatches = []
    for target, origin, kind in rows:
        if kind not in ("BINARY", "EXTENSION"):
            continue
        item = next(row for row in inventory["binaries"] if row["path"] == "_internal/" + target)
        actual = hash_file(bundle / "_internal" / target)
        entry = {"path": item["path"], "sha256": actual}
        if actual != item["sha256"] or actual != hash_file(Path(origin)):
            mismatches.append(target)
        if "/site-packages/" in origin:
            if target not in wheel_members or wheel_members[target][1] != actual:
                mismatches.append(target)
            entry["wheel"] = wheel_members.get(target, (None, None))[0]
        else:
            provider = item["provider"]
            md5_file = Path("/var/lib/dpkg/info") / (provider + ".md5sums")
            if not md5_file.exists():
                md5_file = Path("/var/lib/dpkg/info") / (provider.split(":")[0] + ".md5sums")
            expected = dict(line.split(None, 1)[::-1] for line in md5_file.read_text().splitlines())
            relative = str(Path(origin).resolve()).lstrip("/")
            if expected.get(relative) != hash_file(Path(origin), "md5"):
                mismatches.append(target)
            entry["debian_provider"] = provider
            entry["package_database_md5_matches"] = target not in mismatches
        binaries.append(entry)
    return {
        "binaries": binaries,
        "mismatches": sorted(set(mismatches)),
        "limits": [
            "Exact identity to published wheels is verified, not a rebuild of their toolchain",
            "Debian file verification uses local dpkg md5 records and SHA256 identity to bundle",
        ],
    }


def main() -> None:
    bundle = ROOT / "dist/ConfigDiff"
    inventory = json.loads((bundle / "bundle-inventory.json").read_text())
    needed = {
        (row["source_package"], row["source_version"])
        for row in inventory["debian_providers"].values()
    }
    result = subprocess.run(
        ["apt-cache", "showsrc", "--only-source", *sorted({name for name, _ in needed})],
        check=True,
        capture_output=True,
        text=True,
    )
    sources = source_lock(deb822(result.stdout), needed)
    (ROOT / "third_party/debian-sources.json").write_text(json.dumps(sources, indent=2) + "\n")
    print(
        "Fontes Debian:",
        len(sources["packages"]),
        "pacotes,",
        len(sources["files"]),
        "arquivos.",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda item: download(item, ROOT / "dist/debian-sources"), sources["files"]))
    print("Fontes Debian baixadas e verificadas.", flush=True)
    published = wheels()
    (ROOT / "third_party/published-wheels.json").write_text(json.dumps(published, indent=2) + "\n")
    rows = ast.literal_eval((ROOT / "build/ConfigDiff/COLLECT-00.toc").read_text())[0]
    report = audit(rows, bundle, inventory, published)
    report["bundle_version"] = json.loads((bundle / "build-info.json").read_text())["version"]
    report["inventory_sha256"] = hash_file(bundle / "bundle-inventory.json")
    report["project_source_snapshot_sha256"] = hash_file(bundle / "source/configdiff-source.tar.gz")
    report["generated_executables"] = []
    for item in inventory["binaries"]:
        if item["kind"] == "EXECUTABLE":
            actual = hash_file(bundle / item["path"])
            if actual != item["sha256"]:
                report["mismatches"].append(item["path"])
            report["generated_executables"].append({"path": item["path"], "sha256": actual})
    (ROOT / "third_party/binary-provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        "Binários auditados:",
        len(report["binaries"]),
        "divergências:",
        len(report["mismatches"]),
        flush=True,
    )
    if report["mismatches"]:
        raise ValueError("Divergências na proveniência; consulte o relatório")


if __name__ == "__main__":
    main()
