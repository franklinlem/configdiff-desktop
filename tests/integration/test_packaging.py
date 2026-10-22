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
