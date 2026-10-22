import hashlib
import os
import stat

import pytest

from configdiff.domain.errors import ConfigError, ErrorCode
from configdiff.domain.results import Format, SanitizedReportDTO
from configdiff.services.exporting import SourceRef, export_report
from configdiff.services.files import read_snapshot


@pytest.fixture
def sources(tmp_path):
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    first.write_bytes(b'{"secret":"SENTINEL_A"}')
    second.write_bytes(b'{"secret":"SENTINEL_B"}')
    return tuple(SourceRef.capture(path, read_snapshot(path).identity) for path in (first, second))


def digest(path):
    return hashlib.sha256(path.read_bytes()).digest()


def test_new_report_private_and_sources_unchanged(tmp_path, sources):
    before = [digest(source.path) for source in sources]
    output = tmp_path / "report.md"
    export_report(SanitizedReportDTO(Format.JSON, ()), output, sources)
    text = output.read_text(encoding="utf-8")
    assert "Valores omitidos" in text
    assert not any(str(source.path) in text for source in sources)
    assert "SENTINEL" not in text
    assert before == [digest(source.path) for source in sources]
    if os.name == "posix":
        assert stat.S_IMODE(output.stat().st_mode) & 0o077 == 0


@pytest.mark.parametrize("side", [0, 1])
def test_same_source_rejected(side, sources):
    before = digest(sources[side].path)
    with pytest.raises(ConfigError) as error:
        export_report(SanitizedReportDTO(Format.JSON, ()), sources[side].path, sources)
    assert error.value.code == ErrorCode.PROTECTED_SOURCE
    assert digest(sources[side].path) == before


@pytest.mark.skipif(os.name != "posix", reason="Links sem privilégios no Linux")
@pytest.mark.parametrize("linktype", ["symlink", "hardlink"])
def test_links_to_sources_are_rejected(tmp_path, sources, linktype):
    alias = tmp_path / "alias.md"
    source = sources[0].path
    before = digest(source)
    if linktype == "symlink":
        alias.symlink_to(source)
    else:
        os.link(source, alias)
    with pytest.raises(ConfigError) as error:
        export_report(SanitizedReportDTO(Format.JSON, ()), alias, sources)
    assert error.value.code == ErrorCode.PROTECTED_SOURCE
    assert digest(source) == before


def test_existing_report_not_overwritten(tmp_path, sources):
    output = tmp_path / "existing.md"
    output.write_text("existing-data")
    with pytest.raises(ConfigError) as error:
        export_report(SanitizedReportDTO(Format.JSON, ()), output, sources)
    assert error.value.code == ErrorCode.OUTPUT_EXISTS
    assert output.read_text() == "existing-data"


def test_deleted_source_path_stays_protected(sources):
    path = sources[0].path
    path.unlink()
    with pytest.raises(ConfigError) as error:
        export_report(SanitizedReportDTO(Format.JSON, ()), path, sources)
    assert error.value.code == ErrorCode.PROTECTED_SOURCE
    assert not path.exists()


@pytest.mark.skipif(os.name != "posix", reason="Hard link sem privilégios no Linux")
def test_link_race_does_not_truncate_source(tmp_path, sources, monkeypatch):
    destination = tmp_path / "race.md"
    before = digest(sources[0].path)
    original_open = os.open

    def link_before_open(path, flags, mode):
        os.link(sources[0].path, path)
        return original_open(path, flags, mode)

    monkeypatch.setattr(os, "open", link_before_open)
    with pytest.raises(ConfigError) as error:
        export_report(SanitizedReportDTO(Format.JSON, ()), destination, sources)
    assert error.value.code == ErrorCode.OUTPUT_EXISTS
    assert digest(sources[0].path) == before


def test_io_error_is_sanitized(tmp_path, sources):
    with pytest.raises(ConfigError) as error:
        export_report(SanitizedReportDTO(Format.JSON, ()), tmp_path / "missing" / "out.md", sources)
    assert error.value.code == ErrorCode.EXPORT_FAILED
    assert str(tmp_path) not in str(error.value)
