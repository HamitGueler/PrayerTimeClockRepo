"""Run blocking I/O in Qt's pool and deliver results to the GUI thread."""
import logging
from PySide6.QtCore import QObject, QRunnable, Signal


class JobSignals(QObject):
    completed = Signal(object, object)


class BackgroundJob(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = JobSignals()

    def run(self):
        try:
            result = self.function()
        except Exception as error:
            logging.getLogger(__name__).warning("Background job failed: %s", type(error).__name__)
            self.signals.completed.emit(None, error)
        else:
            self.signals.completed.emit(result, None)
