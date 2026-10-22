from dataclasses import dataclass

from PySide6.QtCore import QSettings


@dataclass(frozen=True)
class Preferences:
    theme: str = "system"
    width: int = 1100
    height: int = 700
    format: str = "auto"


def _dimension(value: object, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(str(value))
    except ValueError:
        return default
    return number if minimum <= number <= maximum else default


class PreferenceStore:
    def __init__(self, settings: QSettings | None = None) -> None:
        self.settings = (
            settings
            if settings is not None
            else QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "FranklinMartins",
                "ConfigDiff",
            )
        )
        self.settings.setAtomicSyncRequired(True)

    def load(self) -> Preferences:
        if self.settings.value("schema", "1") != "1":
            return Preferences()
        theme = self.settings.value("theme", "system")
        format = self.settings.value("format", "auto")
        return Preferences(
            theme=theme if theme in ("system", "light", "dark") else "system",
            format=format if format in ("auto", "json", "yaml", "env") else "auto",
            width=_dimension(self.settings.value("width"), 1100, 480, 3840),
            height=_dimension(self.settings.value("height"), 700, 320, 2160),
        )

    def save(self, preferences: Preferences) -> bool:
        # Lista fechada: elimina inclusive dados desconhecidos de versões/corrupção.
        self.settings.clear()
        for key, value in {
            "schema": "1",
            "theme": preferences.theme,
            "format": preferences.format,
            "width": str(preferences.width),
            "height": str(preferences.height),
        }.items():
            self.settings.setValue(key, value)
        self.settings.sync()
        return self.settings.status() == QSettings.Status.NoError
