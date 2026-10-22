from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from configdiff.workers.probe import ProbeJob


class ProbeWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ConfigDiff Desktop — Fase 0")
        self.resize(640, 360)
        self.job: ProbeJob | None = None
        self.status = QLabel("Protótipo de viabilidade. Comparação ainda não implementada.")
        self.start_button = QPushButton("Iniciar trabalho sintético (30 s)")
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setEnabled(False)
        self.start_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(self.cancel)
        panel = QWidget()
        layout = QVBoxLayout(panel)
        for widget in (self.status, self.start_button, self.cancel_button):
            layout.addWidget(widget)
        self.setCentralWidget(panel)
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll)

    def start(self) -> None:
        self.job = ProbeJob()
        self.status.setText("Processando — limite de 10 segundos")
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.timer.start()

    def poll(self) -> None:
        if self.job is not None:
            state = self.job.poll()
            if state != "running":
                self.finish(state)

    def finish(self, state: str) -> None:
        self.timer.stop()
        self.job = None
        self.status.setText(
            {
                "done": "Concluído",
                "cancelled": "Cancelado",
                "timeout": "Tempo limite atingido",
                "error": "Falha no processo",
            }[state]
        )
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def cancel(self) -> None:
        if self.job is not None:
            self.job.cancel()
            self.finish("cancelled")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.cancel()
        event.accept()
