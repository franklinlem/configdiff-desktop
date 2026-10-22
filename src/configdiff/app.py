import multiprocessing
import sys


def main() -> int:
    # Precisa anteceder Qt e processamento dos argumentos no executável congelado.
    multiprocessing.freeze_support()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from configdiff.ui.window import ProbeWindow

    application = QApplication([sys.argv[0]])
    window = ProbeWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        # Exercita também spawn e cancelamento dentro do pacote.
        QTimer.singleShot(100, window.start)
        QTimer.singleShot(1000, window.cancel)

        def verify_smoke() -> None:
            success = window.job is None and window.status.text() == "Cancelado"
            application.exit(0 if success else 1)

        QTimer.singleShot(1200, verify_smoke)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
