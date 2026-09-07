import threading
from PySide6.QtCore import QCoreApplication, QEventLoop, QObject, QThreadPool, QTimer, Slot
from HelperClasses.BackgroundJob import BackgroundJob


def test_blocking_work_keeps_qt_responsive_and_delivers_result_on_gui_thread(qapp):
    loop = QEventLoop()
    release = threading.Event()
    gui_thread = threading.get_ident()
    received = []

    class Receiver(QObject):
        @Slot(object, object)
        def finished(self, result, error):
            received.append((result, error, threading.get_ident()))
            loop.quit()

    def slow_io():
        worker_thread = threading.get_ident()
        assert release.wait(1), 'Qt timer did not fire while I/O was waiting'
        return worker_thread

    receiver = Receiver()
    job = BackgroundJob(slow_io)
    job.signals.completed.connect(receiver.finished)
    QThreadPool.globalInstance().start(job)
    QTimer.singleShot(30, release.set)
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(loop.quit)
    watchdog.start(2000)
    loop.exec()
    watchdog.stop()
    QThreadPool.globalInstance().waitForDone(2000)
    assert len(received) == 1
    worker_thread, error, callback_thread = received[0]
    assert error is None
    assert worker_thread != gui_thread
    assert callback_thread == gui_thread
