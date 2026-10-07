from threading import get_ident
from time import perf_counter, sleep

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from app.gui.background import BackgroundJobs


def wait_until(predicate):
    deadline = perf_counter() + 3
    while not predicate() and perf_counter() < deadline:
        QTest.qWait(10)
    assert predicate()


def test_slow_operation_keeps_ui_ticking_and_delivers_on_main_thread():
    app = QApplication.instance() or QApplication([])
    host = QWidget()
    jobs = BackgroundJobs(host)
    main_thread = get_ident()
    results, ticks = [], []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start(10)

    def work():
        sleep(0.15)
        return get_ident()

    jobs.submit(work, lambda worker_thread: results.append((worker_thread, get_ident())),
                lambda error: results.append(error))
    wait_until(lambda: bool(results))
    timer.stop()
    assert len(ticks) >= 3
    assert results[0][0] != main_thread
    assert results[0][1] == main_thread
    host.close()


def test_background_errors_are_delivered_and_close_drops_callbacks():
    app = QApplication.instance() or QApplication([])
    host = QWidget()
    jobs = BackgroundJobs(host)
    errors = []

    def failed():
        raise ValueError('database unavailable')

    jobs.submit(failed, lambda result: None, errors.append)
    wait_until(lambda: bool(errors))
    assert errors == ['database unavailable']
    jobs.submit(lambda: sleep(0.05), lambda result: errors.append('late'), errors.append)
    jobs.detach()
    QTest.qWait(100)
    assert errors == ['database unavailable']
    host.close()
