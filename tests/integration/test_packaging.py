import importlib.util
import subprocess
import tarfile
from pathlib import Path


def load_build_module():
    path = Path(__file__).parents[2] / "scripts/build_candidate.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_bundle_excludes_untracked_user_files(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "app.py").write_text('print("safe")')
    (tmp_path / "relatorio-privado.md").write_text("SENTINEL-PRIVATE")
    subprocess.run(["git", "-C", str(tmp_path), "add", "app.py"], check=True)
    archive = tmp_path / "source.tar.gz"
    load_build_module().tracked_sources(tmp_path, archive)
    with tarfile.open(archive) as bundle:
        assert bundle.getnames() == ["configdiff-source/app.py"]
        assert b"SENTINEL" not in bundle.extractfile(bundle.getmembers()[0]).read()


def test_notice_paths_cannot_escape(tmp_path, monkeypatch):
    import pytest

    scripts = Path(__file__).parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    from collect_upstream_notices import safe_relative

    assert safe_relative("qtbase/LICENSE") == Path("qtbase/LICENSE")
    for invalid in ["/tmp/outside", "../outside", "inside/../../outside", "."]:
        with pytest.raises(ValueError):
            safe_relative(invalid)


def test_source_hash_mismatch_is_not_published(tmp_path, monkeypatch):
    import io

    import pytest

    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "scripts"))
    import fetch_upstream_sources as fetcher

    monkeypatch.setattr(fetcher, "ROOT", tmp_path)
    monkeypatch.setattr(fetcher, "urlopen", lambda *args, **kwargs: io.BytesIO(b"wrong-content"))
    item = {
        "filename": "source.tar.xz",
        "url": "https://example.invalid/source",
        "sha256": "0" * 64,
    }
    with pytest.raises(ValueError, match="divergente"):
        fetcher.fetch(item)
    assert not (tmp_path / "dist/dependency-sources/source.tar.xz").exists()
    assert not list((tmp_path / "dist/dependency-sources").glob("*.part"))


def test_debian_source_versions_are_exact(monkeypatch):
    import pytest

    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "scripts"))
    from audit_provenance import deb822, source_lock

    text = """Package: demo
Version: 1.0-1
Directory: pool/main/d/demo
Format: 3.0 (quilt)
Checksums-Sha256:
 abc 10 demo_1.0.orig.tar.xz
 def 20 demo_1.0-1.debian.tar.xz

Package: demo
Version: 2.0-1
Directory: pool/main/d/demo
Checksums-Sha256:
 ghi 30 demo_2.0.orig.tar.xz
"""
    lock = source_lock(deb822(text), {("demo", "1.0-1")})
    assert lock["packages"][0]["version"] == "1.0-1"
    assert len(lock["files"]) == 2
    assert lock["files"][0]["url"].startswith("https://deb.debian.org/debian/pool/")
    with pytest.raises(ValueError, match="exata ausente"):
        source_lock(deb822(text), {("demo", "missing")})


def test_provenance_download_rejects_path_escape(tmp_path, monkeypatch):
    import pytest

    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "scripts"))
    from audit_provenance import download

    for name in ["../private", "/tmp/private", "pool/../../private"]:
        with pytest.raises(ValueError, match="inválido"):
            download({"path": name}, tmp_path)


def test_auxiliary_archive_rejects_changed_sources(tmp_path, monkeypatch):
    import hashlib

    import pytest

    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "scripts"))
    from package_provenance import validate_sources

    source = tmp_path / "source.tar.xz"
    source.write_bytes(b"official-example")
    item = {"path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    assert validate_sources(tmp_path, [item]) == [(source, source.name)]
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="divergente"):
        validate_sources(tmp_path, [item])
    with pytest.raises(ValueError, match="inválido"):
        validate_sources(tmp_path, [{"path": "../outside"}])
