import json
import time

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    QTimer,
)

from configdiff.domain.nodes import Scalar
from configdiff.domain.paths import render_path
from configdiff.domain.results import DiffEntry
from configdiff.domain.sensitivity import potentially_sensitive
from configdiff.services.reports import LABELS

MASK = "Oculto"
_ROOT = QModelIndex()
HEADERS = ("Caminho", "Categoria", "Tipo A", "Tipo B", "Valor A", "Valor B", "Atenção")


class DiffTableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.entries: tuple[DiffEntry, ...] = ()
        self.revealed: tuple[int, int] | None = None
        self.expires_at = 0.0
        self.reveal_timer = QTimer(self)
        self.reveal_timer.setSingleShot(True)
        self.reveal_timer.setInterval(15_000)
        self.reveal_timer.timeout.connect(self.hide_values)

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT) -> int:
        return 0 if parent.isValid() else len(self.entries)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _ROOT) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return HEADERS[section] if 0 <= section < len(HEADERS) else None
        return None

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> str | None:
        if not index.isValid() or not 0 <= index.row() < len(self.entries):
            return None
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.AccessibleTextRole):
            return None  # Nunca valores em tooltips, EditRole ou UserRole.
        entry = self.entries[index.row()]
        column = index.column()
        if column == 0:
            return render_path(entry.path)
        if column == 1:
            return LABELS[entry.category]
        if column in (2, 3):
            kind = entry.kind_a if column == 2 else entry.kind_b
            return kind.value if kind is not None else "ausente"
        if column in (4, 5):
            node = entry.a if column == 4 else entry.b
            if node is None:
                return "—"
            if self.revealed == (index.row(), column) and time.monotonic() < self.expires_at:
                if isinstance(node, Scalar):
                    # Prévia limitada e escapada, sem rich text/controles invisíveis.
                    value = node.value
                    if isinstance(value, str):
                        suffix = "… (prévia)" if len(value) > 512 else ""
                        return json.dumps(value[:512], ensure_ascii=True) + suffix
                    return json.dumps(value, ensure_ascii=True)
                return f"<{node.kind.value}>"  # Não revela subárvores inteiras.
            return MASK
        if column == 6:
            return "Potencial segredo" if potentially_sensitive(entry.path) else ""
        return None

    def set_entries(self, entries: tuple[DiffEntry, ...]) -> None:
        self.hide_values()
        self.beginResetModel()
        self.entries = entries
        self.endResetModel()

    def hide_values(self) -> None:
        previous = self.revealed
        self.revealed = None
        self.reveal_timer.stop()
        if previous is not None:
            index = self.index(*previous)
            self.dataChanged.emit(index, index)

    def reveal(self, index: QModelIndex | QPersistentModelIndex) -> bool:
        self.hide_values()
        if (
            not index.isValid()
            or index.column() not in (4, 5)
            or not 0 <= index.row() < len(self.entries)
        ):
            return False
        entry = self.entries[index.row()]
        node = entry.a if index.column() == 4 else entry.b
        if node is None:
            return False
        self.revealed = (index.row(), index.column())
        self.expires_at = time.monotonic() + 15
        self.reveal_timer.start()
        self.dataChanged.emit(index, index)
        return True

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.hide_values()
        if not 0 <= column < 4:
            return  # Nunca ordenar ou buscar por valores.

        def key(entry: DiffEntry) -> str:
            if column == 0:
                return render_path(entry.path)
            if column == 1:
                return entry.category.value
            kind = entry.kind_a if column == 2 else entry.kind_b
            return kind.value if kind is not None else ""

        self.set_entries(
            tuple(sorted(self.entries, key=key, reverse=order == Qt.SortOrder.DescendingOrder))
        )
