from PySide6.QtCore import QSettings

from configdiff.settings.preferences import Preferences, PreferenceStore


def test_corrupt_preferences_fall_back(tmp_path):
    settings = QSettings(str(tmp_path / "prefs.ini"), QSettings.Format.IniFormat)
    settings.setValue("width", "invalid")
    settings.setValue("height", "-50")
    settings.setValue("theme", "<invalid>")
    settings.setValue("format", "bad")
    store = PreferenceStore(settings)
    assert store.load() == Preferences()
    settings.setValue("schema", "99")
    assert store.load() == Preferences()
    settings.setValue("unexpected-secret", "SENTINEL")
    assert store.save(Preferences(theme="dark", format="json"))
    assert "SENTINEL" not in (tmp_path / "prefs.ini").read_text()
    assert store.load().theme == "dark"
