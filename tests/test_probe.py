import time

import pytest
from PySide6.QtCore import QTimer

from configdiff.ui.window import ProbeWindow
from configdiff.workers.probe import ProbeJob


def wait(job):
    deadline = time.monotonic() + 5
    while job.poll() == "running" and time.monotonic() < deadline:
        time.sleep(0.01)
    return job.state


def test_result():
    job = ProbeJob(delay=0, timeout=5)
    try:
        assert wait(job) == "done"
        assert not job.process.is_alive()
    finally:
        job.close()


@pytest.mark.parametrize("action", ["cancel", "timeout", "crash"])
def test_stop(action):
    job = ProbeJob(timeout=0.05 if action == "timeout" else 10)
    try:
        if action == "cancel":
            job.cancel()
        elif action == "crash":
            job.process.kill()
        assert wait(job) == {"cancel": "cancelled", "timeout": "timeout", "crash": "error"}[action]
        assert not job.process.is_alive()
    finally:
        job.close()


def test_window_cancel_and_close(qtbot):
    window = ProbeWindow()
    qtbot.addWidget(window)
    window.show()
    window.start()
    first = window.job
    ticks = []
    heartbeat = QTimer(window)
    heartbeat.setInterval(5)
    heartbeat.timeout.connect(lambda: ticks.append(1))
    heartbeat.start()
    qtbot.waitUntil(lambda: len(ticks) >= 3, timeout=2000)
    window.cancel_button.click()
    assert window.status.text() == "Cancelado"
    assert not first.process.is_alive()
    window.start()
    second = window.job
    window.close()
    assert not second.process.is_alive()
