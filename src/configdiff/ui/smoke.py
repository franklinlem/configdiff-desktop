"""Ensaio explícito com dados sintéticos; não usa preferências pessoais."""

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from configdiff.ui.model import MASK
from configdiff.ui.window import MainWindow


def schedule_smoke(window: MainWindow, application: QApplication, root: Path) -> None:
    a, b = root / "a.json", root / "b.json"
    a.write_text('{"password":"SENTINEL_A"}')
    b.write_text('{"password":"SENTINEL_B"}')
    window.set_file(0, a)
    window.set_file(1, b)
    window.start()
    checker = QTimer(window)
    checker.setInterval(50)

    def verify() -> None:
        if window.state == "processing":
            return
        checker.stop()
        success = window.state == "done" and window.model.rowCount() == 1
        if success:
            success = window.model.data(window.model.index(0, 4)) == MASK
            success = success and window.export_to(root / "report.md")
            success = success and "SENTINEL" not in (root / "report.md").read_text(encoding="utf-8")
            window.start()
            job = window.job
            window.cancel()
            success = success and job is not None and not job.process.is_alive()
        window.close()
        application.exit(0 if success else 1)

    checker.timeout.connect(verify)
    checker.start()
    QTimer.singleShot(15_000, lambda: application.exit(1))
