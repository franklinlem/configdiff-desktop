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
