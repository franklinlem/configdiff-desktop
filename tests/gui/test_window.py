import os
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QSettings, Qt
from PySide6.QtWidgets import QApplication, QFileDialog

from configdiff.domain.limits import Limits
from configdiff.domain.results import Category
from configdiff.settings.preferences import PreferenceStore
from configdiff.ui.model import MASK
from configdiff.ui.window import MainWindow

FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.fixture
def window(qtbot, tmp_path):
    store = PreferenceStore(
        QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    )
    window = MainWindow(store)
    qtbot.addWidget(window)
    window.show()
    yield window
    window.close()


def select(window):
    window.set_file(0, FIXTURES / "example.json")
    window.set_file(1, FIXTURES / "example-b.json")


def finish(window, qtbot):
    select(window)
    window.compare_button.click()
    qtbot.waitUntil(lambda: window.state != "processing", timeout=10000)
    assert window.state == "done", window.status.text()


def password_row(window):
    return next(
        i for i, entry in enumerate(window.model.entries) if "DB_PASSWORD" in str(entry.path)
    )


def reveal(window):
    row = password_row(window)
    index = window.model.index(row, 4)
    window.table.setCurrentIndex(index)
    window.reveal_selected()
    assert window.model.data(index) == '"synthetic-example-only"'
    return index


def test_real_flow_mask_filter_export(window, qtbot, tmp_path):
    finish(window, qtbot)
    assert window.model.rowCount() == 5
    assert "Visão: 5 de 5" in window.counts.text()
    for row in range(window.model.rowCount()):
        for column in (4, 5):
            assert window.model.data(window.model.index(row, column)) in (MASK, "—")
    reveal(window)
    window.search.setText("PASSWORD")
    assert window.model.rowCount() == 1
    assert window.model.revealed is None
    window.reveal_selected()
    destination = tmp_path / "filtered.md"
    assert window.export_to(destination)
    text = destination.read_text(encoding="utf-8")
    assert "DB_PASSWORD" in text and "APP_ENV" not in text
    assert "synthetic-" not in text
    assert window.model.revealed is None
    assert not window.export_to(FIXTURES / "example.json")
    assert "origem" in window.status.text()


@pytest.mark.parametrize(
    "action",
    ["filter", "sort", "focus", "deactivate", "file", "format", "escape", "clear", "selection"],
)
def test_reveal_is_revoked(window, qtbot, action):
    finish(window, qtbot)
    reveal(window)
    if action == "filter":
        window.categories[Category.MISSING_A].setChecked(False)
    elif action == "sort":
        window.table.sortByColumn(1, Qt.SortOrder.DescendingOrder)
    elif action == "focus":
        QApplication.sendEvent(window.table, QEvent(QEvent.Type.FocusOut))
    elif action == "deactivate":
        QApplication.sendEvent(window.table, QEvent(QEvent.Type.WindowDeactivate))
    elif action == "file":
        window.set_file(0, FIXTURES / "example.json")
    elif action == "format":
        window.formats[0].setCurrentIndex(window.formats[0].findData("yaml"))
    elif action == "escape":
        window.escape()
    elif action == "clear":
        window.clear()
    else:
        window.table.setCurrentIndex(window.model.index(0, 0))
    assert window.model.revealed is None
    if action in ("file", "format", "clear"):
        assert window.compared is None and not window.model.entries


def test_one_cell_timeout_and_no_tooltip_or_copy_values(window, qtbot):
    finish(window, qtbot)
    index = reveal(window)
    second = window.model.index(index.row(), 5)
    window.model.reveal(second)
    assert window.model.data(index) == MASK
    assert window.model.data(second) == '"synthetic-production-only"'
    assert window.model.data(second, Qt.ItemDataRole.ToolTipRole) is None
    assert window.model.data(second, Qt.ItemDataRole.EditRole) is None
    assert window.model.reveal_timer.interval() == 15000
    window.model.reveal_timer.start(20)
    qtbot.waitUntil(lambda: window.model.revealed is None, timeout=2000)
    assert window.model.data(second) == MASK
    QApplication.clipboard().setText("unchanged")
    window.table.setCurrentIndex(index)
    window.reveal_selected()
    qtbot.keyClick(window.table, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    assert QApplication.clipboard().text() == "unchanged"
    window.copy_path()
    assert "DB_PASSWORD" in QApplication.clipboard().text()
    assert "synthetic-" not in QApplication.clipboard().text()


def test_cancel_and_close_stop_worker(window, qtbot):
    select(window)
    window.start()
    job = window.job
    window.cancel_button.click()
    assert window.state == "cancelled"
    assert window.compared is None and not window.model.entries
    assert not job.process.is_alive()
    window.start()
    job = window.job
    window.close()
    assert not job.process.is_alive()
    assert window.compared is None and not window.model.entries


def test_old_result_cleared_on_retry_and_error(window, qtbot, tmp_path):
    finish(window, qtbot)
    bad = tmp_path / "bad.json"
    bad.write_text('{"value":"SENTINEL",')
    window.set_file(1, bad)
    assert window.compared is None and not window.model.entries
    window.start()
    qtbot.waitUntil(lambda: window.state != "processing", timeout=10000)
    assert window.state == "error"
    assert "Arquivo B" in window.status.text()
    assert "SENTINEL" not in window.status.text()
    assert not window.export_button.isEnabled()


def test_ambiguous_format_and_mismatch(window, qtbot, tmp_path):
    unknown = tmp_path / "unknown"
    unknown.write_text("{}")
    select(window)
    window.set_file(0, unknown)
    window.start()
    assert window.job is None
    assert "explicitamente" in window.status.text()
    window.formats[0].setCurrentIndex(window.formats[0].findData("yaml"))
    window.start()
    assert window.state == "error" and window.job is None
    assert "mesmo formato" in window.status.text()


def test_timeout(qtbot, tmp_path):
    store = PreferenceStore(QSettings(str(tmp_path / "prefs.ini"), QSettings.Format.IniFormat))
    window = MainWindow(store, Limits(timeout_seconds=0.00001))
    qtbot.addWidget(window)
    select(window)
    window.start()
    job = window.job
    qtbot.waitUntil(lambda: window.state != "processing", timeout=5000)
    assert "Tempo limite" in window.status.text()
    assert not job.process.is_alive() and not window.model.entries


def test_dialog_selection_and_export(window, qtbot, monkeypatch, tmp_path):
    names = iter([str(FIXTURES / "example.json"), str(FIXTURES / "example-b.json")])
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (next(names), ""))
    window.file_buttons[0].click()
    window.file_buttons[1].click()
    window.compare_button.click()
    qtbot.waitUntil(lambda: window.state != "processing", timeout=10000)
    destination = tmp_path / "report.md"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(destination), "")
    )
    window.export_button.click()
    assert destination.exists()
    assert "synthetic-" not in destination.read_text(encoding="utf-8")


def test_plain_text_filename_and_preferences_without_content(window, qtbot, tmp_path):
    file = tmp_path / ("SENTINEL.json" if os.name == "nt" else "<b>SENTINEL.json")
    file.write_text("{}")
    window.set_file(0, file)
    assert window.file_labels[0].textFormat() == Qt.TextFormat.PlainText
    assert not window.details.isVisible()
    window.details_button.click()
    assert str(file) in window.details.text()
    window.theme.setCurrentIndex(window.theme.findData("dark"))
    window.close()
    text = Path(window.store.settings.fileName()).read_text()
    assert "SENTINEL" not in text and str(tmp_path) not in text
    assert set(window.store.settings.allKeys()) == {"schema", "theme", "width", "height", "format"}


def test_all_categories_can_be_disabled(window, qtbot):
    finish(window, qtbot)
    for check in window.categories.values():
        check.setChecked(False)
    assert window.model.rowCount() == 0
    assert "Visão: 0" in window.counts.text()


def test_keyboard_shortcuts_and_small_window_scroll(window, qtbot):
    finish(window, qtbot)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow, timeout=2000)
    window.table.setFocus()
    qtbot.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert window.search.hasFocus()
    window.search.clear()
    row = password_row(window)
    window.table.setCurrentIndex(window.model.index(row, 4))
    window.table.setFocus()
    qtbot.keyClick(window, Qt.Key.Key_R, Qt.KeyboardModifier.AltModifier)
    assert window.model.revealed == (row, 4)
    qtbot.keyClick(window, Qt.Key.Key_Escape)
    assert window.model.revealed is None
    window.resize(640, 360)
    qtbot.waitUntil(lambda: window.scroll_area.verticalScrollBar().maximum() > 0, timeout=2000)
    window.scroll_area.ensureWidgetVisible(window.export_button)
    window.export_button.setFocus()
    assert window.export_button.hasFocus()
