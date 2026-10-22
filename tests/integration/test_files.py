import hashlib
import os

import pytest

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.limits import Limits
from configdiff.domain.results import Format
from configdiff.services.files import detect_format, read_snapshot


@pytest.mark.parametrize(
    "name,format",
    [
        ("file.JSON", Format.JSON),
        ("file.yml", Format.YAML),
        ("file.yaml", Format.YAML),
        (".env", Format.ENV),
        (".env.test", Format.ENV),
        ("file.env", Format.ENV),
        ("unknown", None),
        ("file.env.backup", None),
    ],
)
def test_detect_format(tmp_path, name, format):
    assert detect_format(tmp_path / name) == format


def test_snapshot_preserves_source_and_hides_content(tmp_path):
    file = tmp_path / "config.json"
    data = b'{"key":"SENTINEL"}'
    file.write_bytes(data)
    before = hashlib.sha256(file.read_bytes()).digest()
    snapshot = read_snapshot(file, Limits(max_bytes=len(data)))
    assert snapshot.data == data
    assert snapshot.identity.size == len(data)
    assert "SENTINEL" not in repr(snapshot)
    assert hashlib.sha256(file.read_bytes()).digest() == before
    with pytest.raises(ConfigError) as error:
        read_snapshot(file, Limits(max_bytes=len(data) - 1))
    assert error.value.code == ErrorCode.SIZE_LIMIT


def test_invalid_files(tmp_path):
    for file in [tmp_path, tmp_path / "missing"]:
        with pytest.raises(ConfigError) as error:
            read_snapshot(file)
        assert error.value.code == ErrorCode.INVALID_FILE


@pytest.mark.skipif(os.name != "posix", reason="FIFO POSIX")
def test_fifo_and_device_never_read(tmp_path):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    for path in [fifo, type(fifo)("/dev/null")]:
        with pytest.raises(ConfigError) as error:
            read_snapshot(path)
        assert error.value.code == ErrorCode.INVALID_FILE


@pytest.mark.skipif(os.name != "posix", reason="Symlink sem privilégios no Linux")
def test_symlink_to_regular_file(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"{}")
    link = tmp_path / "link"
    link.symlink_to(target)
    assert read_snapshot(link).identity == read_snapshot(target).identity


def test_permission_error_is_safe(tmp_path, monkeypatch):
    file = tmp_path / "private-file"
    file.write_text("{}")

    def denied(*args):
        raise PermissionError("SENTINEL path and content")

    monkeypatch.setattr(os, "open", denied)
    with pytest.raises(ConfigError) as error:
        read_snapshot(file)
    assert error.value.code == ErrorCode.ACCESS_DENIED
    assert "SENTINEL" not in str(error.value)


@pytest.mark.parametrize("overflow", [False, True])
def test_growing_file_is_bounded_and_invalidated(tmp_path, monkeypatch, overflow):
    file = tmp_path / "growing"
    file.write_bytes(b"{}")
    read = os.read
    changed = False

    def grow(descriptor, size):
        nonlocal changed
        if not changed:
            changed = True
            with file.open("ab") as writer:
                writer.write(b" " * (100 if overflow else 1))
        return read(descriptor, size)

    monkeypatch.setattr(os, "read", grow)
    with pytest.raises(ConfigError) as error:
        read_snapshot(file, Limits(max_bytes=20))
    assert error.value.code == (ErrorCode.SIZE_LIMIT if overflow else ErrorCode.FILE_CHANGED)
