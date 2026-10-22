"""Regressão POSIX real: SIGINT encerra Qt e o filho sem traceback."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="Ensaio de grupo de processos POSIX")
@pytest.mark.parametrize("running", [False, True])
def test_terminal_interrupt(tmp_path, running):
    ready = tmp_path / "ready"
    script = """
from pathlib import Path
from PySide6.QtCore import QTimer
from configdiff.ui.window import ProbeWindow
from configdiff.app import main
original = ProbeWindow.show

def show(self):
    original(self)
    def ready():
        if RUNNING:
            self.start()
        Path(MARKER).write_text(str(self.job.process.pid) if self.job else "idle")
    QTimer.singleShot(200, ready)
ProbeWindow.show = show
raise SystemExit(main())
""".replace("RUNNING", repr(running)).replace("MARKER", repr(str(ready)))
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), "Aplicativo não iniciou dentro do prazo"
        child = ready.read_text()
        # Alvo é o pai; Ctrl+C no grupo é testado pelo cenário com trabalho ativo.
        if running:
            time.sleep(0.3)  # permite que o filho spawn configure seu handler
            os.killpg(process.pid, signal.SIGINT)
        else:
            process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 130, (stdout, stderr)
        assert b"Traceback" not in stderr
        assert b"KeyboardInterrupt" not in stderr
        if child != "idle":
            assert not Path(f"/proc/{child}").exists()
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)
