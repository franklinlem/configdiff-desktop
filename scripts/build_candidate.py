"""Build nativo e candidato local; nunca publica nem inclui arquivos não versionados."""

import ast
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import zipfile
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def tracked_sources(root: Path, output: Path) -> None:
    listing = (
        subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True)
        .stdout.decode()
        .split("\0")
    )
    with tarfile.open(output, "w:gz") as archive:
        for name in sorted(filter(None, listing)):
            path = root / name
            if path.is_file() or path.is_symlink():
                archive.add(path, arcname=f"configdiff-source/{name}", recursive=False)


def copy_licenses(bundle: Path) -> list[dict[str, str]]:
    versions = []
    for name in [
        "PySide6-Essentials",
        "shiboken6",
        "PyYAML",
        "PyInstaller",
        "pyinstaller-hooks-contrib",
    ]:
        distribution = metadata.distribution(name)
        versions.append(
            {
                "name": name,
                "version": distribution.version,
                "license_metadata": distribution.metadata.get("License-Expression")
                or distribution.metadata.get("License", "Não declarado"),
            }
        )
        for file in distribution.files or ():
            parts = str(file).lower().split("/")
            if any(part.startswith(("license", "copying", "notice")) for part in parts):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    target = bundle / "licenses" / name / str(file)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sysconfig.get_path("stdlib")) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, bundle / "licenses" / "Python-LICENSE.txt")
    common = Path("/usr/share/common-licenses")
    if common.exists():
        shutil.copytree(common, bundle / "licenses" / "common", dirs_exist_ok=True)
    return versions


def bundle_inventory(bundle: Path) -> dict[str, object]:
    rows = ast.literal_eval((ROOT / "build/ConfigDiff/COLLECT-00.toc").read_text())[0]
    binaries = []
    providers: dict[str, dict[str, str]] = {}
    for target, origin, kind in rows:
        if kind not in ("BINARY", "EXTENSION", "EXECUTABLE"):
            continue
        installed = bundle / ("_internal/" + target if kind != "EXECUTABLE" else target)
        provider = "python-wheel-or-build"
        if target.startswith("PySide6/"):
            provider = "PySide6-Essentials; Qt/ICU embedded components need attribution review"
        elif target.startswith("shiboken6/"):
            provider = "shiboken6"
        elif target.startswith("yaml/"):
            provider = "PyYAML"
        if platform.system() == "Linux" and str(origin).startswith(("/usr/", "/lib/")):
            lookup = subprocess.run(
                ["dpkg-query", "-S", str(Path(origin).resolve())],
                check=False,
                capture_output=True,
                text=True,
            )
            if lookup.returncode == 0:
                provider = lookup.stdout.splitlines()[0].split(": ", 1)[0]
                if provider not in providers:
                    details = command(
                        "dpkg-query",
                        "-W",
                        "-f=${Version}\t${source:Package}\t${source:Version}",
                        provider,
                    ).split("\t")
                    providers[provider] = dict(
                        zip(("version", "source_package", "source_version"), details, strict=True)
                    )
                    copyright_file = Path("/usr/share/doc") / provider.split(":")[0] / "copyright"
                    if copyright_file.is_file():
                        output = (
                            bundle / "licenses/debian" / provider.replace(":", "_") / "copyright"
                        )
                        output.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(copyright_file, output)
        binaries.append(
            {
                "path": str(installed.relative_to(bundle)),
                "kind": kind,
                "provider": provider,
                "sha256": digest(installed),
            }
        )
    return {
        "binaries": binaries,
        "debian_providers": providers,
        "limitations": [
            "Wheel Qt/ICU third-party attributions and corresponding sources need review",
            "Not an SPDX SBOM; unresolved providers are labelled explicitly",
        ],
    }


def main() -> None:
    version = metadata.version("configdiff-desktop")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--name",
            "ConfigDiff",
            "--paths",
            "src",
            "packaging/entrypoint.py",
        ],
        cwd=ROOT,
        check=True,
    )
    bundle = ROOT / "dist/ConfigDiff"
    paths = command("git", "ls-files", "-z").split("\0")
    for name in filter(None, paths):
        relative = None
        if name.startswith("docs/"):
            relative = name
        elif name.startswith("third_party/licenses/"):
            relative = "licenses/project-collected/" + name.removeprefix("third_party/licenses/")
        elif name.startswith("tests/fixtures/"):
            relative = "examples/" + name.removeprefix("tests/fixtures/")
        if relative is not None:
            target = bundle / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
    for name in ["THIRD_PARTY_NOTICES.md", "LICENSE.proposed", "CHANGELOG.md"]:
        shutil.copy2(ROOT / name, bundle / name)
    shutil.copy2(ROOT / "packaging/README-portable.md", bundle / "README.md")
    (bundle / "source").mkdir(exist_ok=True)
    tracked_sources(ROOT, bundle / "source/configdiff-source.tar.gz")
    packages = copy_licenses(bundle)
    inventory = bundle_inventory(bundle)
    (bundle / "bundle-inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    info = {
        "version": version,
        "built_at_utc": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "git_commit": command("git", "rev-parse", "HEAD"),
        "tracked_changes": bool(command("git", "status", "--porcelain", "--untracked-files=no")),
        "packages": packages,
        "status": "local-candidate-not-for-public-release",
    }
    (bundle / "build-info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    manifest = []
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and not path.is_symlink():
            manifest.append(f"{digest(path)}  {path.relative_to(bundle).as_posix()}")
    (bundle / "files.sha256").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    stem = f"configdiff-{version}-{platform.system().lower()}-{platform.machine()}"
    if platform.system() == "Windows":
        artifact = ROOT / "dist" / (stem + ".zip")
        with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    archive.write(path, arcname="ConfigDiff/" + path.relative_to(bundle).as_posix())
    else:
        artifact = ROOT / "dist" / (stem + ".tar.gz")
        with tarfile.open(artifact, "w:gz", dereference=False) as archive:
            archive.add(bundle, arcname="ConfigDiff")
    artifact.with_suffix(artifact.suffix + ".sha256").write_text(
        f"{digest(artifact)}  {artifact.name}\n"
    )
    print(f"Candidato local: {artifact.name}; inventário e checksums incluídos.")


if __name__ == "__main__":
    main()
