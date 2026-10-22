import multiprocessing
import signal
import sys
import tempfile
from pathlib import Path
from types import FrameType


def main() -> int:
    # Precisa anteceder Qt e processamento dos argumentos no executável congelado.
    multiprocessing.freeze_support()
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtWidgets import QApplication

    from configdiff.settings.preferences import PreferenceStore
    from configdiff.ui.window import MainWindow

    application = QApplication([sys.argv[0]])
    interrupted = False

    def request_interrupt(signum: int, frame: FrameType | None) -> None:
        nonlocal interrupted
        # O handler só marca intenção; limpeza ocorre no loop Qt.
        interrupted = True

    previous_handler = signal.signal(signal.SIGINT, request_interrupt)
    smoke = "--smoke-test" in sys.argv
    temporary = tempfile.TemporaryDirectory(prefix="configdiff-smoke-") if smoke else None
    root = Path(temporary.name) if temporary else None
    store = (
        PreferenceStore(QSettings(str(root / "preferences.ini"), QSettings.Format.IniFormat))
        if root
        else None
    )
    window = MainWindow(store)
    application.aboutToQuit.connect(window.invalidate)
    interrupt_timer = QTimer(application)
    interrupt_timer.setInterval(50)

    def check_interrupt() -> None:
        if interrupted:
            window.close()
            application.exit(130)

    interrupt_timer.timeout.connect(check_interrupt)
    interrupt_timer.start()
    window.show()
    if root is not None:
        from configdiff.ui.smoke import schedule_smoke

        schedule_smoke(window, application, root)
    try:
        return application.exec()
    finally:
        interrupt_timer.stop()
        window.invalidate()
        signal.signal(signal.SIGINT, previous_handler)
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
