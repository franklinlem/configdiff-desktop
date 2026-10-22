import multiprocessing
import signal
import sys
from types import FrameType


def main() -> int:
    # Precisa anteceder Qt e processamento dos argumentos no executável congelado.
    multiprocessing.freeze_support()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from configdiff.ui.window import ProbeWindow

    application = QApplication([sys.argv[0]])
    interrupted = False

    def request_interrupt(signum: int, frame: FrameType | None) -> None:
        nonlocal interrupted
        # O handler só marca intenção; limpeza ocorre no loop Qt.
        interrupted = True

    previous_handler = signal.signal(signal.SIGINT, request_interrupt)
    window = ProbeWindow()
    application.aboutToQuit.connect(window.cancel)
    interrupt_timer = QTimer(application)
    interrupt_timer.setInterval(50)

    def check_interrupt() -> None:
        if interrupted:
            window.close()
            application.exit(130)

    interrupt_timer.timeout.connect(check_interrupt)
    interrupt_timer.start()
    window.show()
    if "--smoke-test" in sys.argv:
        # Exercita também spawn e cancelamento dentro do pacote.
        QTimer.singleShot(100, window.start)
        QTimer.singleShot(1000, window.cancel)

        def verify_smoke() -> None:
            success = window.job is None and window.status.text() == "Cancelado"
            application.exit(0 if success else 1)

        QTimer.singleShot(1200, verify_smoke)
    try:
        return application.exec()
    finally:
        interrupt_timer.stop()
        window.cancel()
        signal.signal(signal.SIGINT, previous_handler)


if __name__ == "__main__":
    raise SystemExit(main())
