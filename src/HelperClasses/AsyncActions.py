"""GUI-owned callbacks; workers only perform I/O and never access widgets."""
from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal, Slot
from HelperClasses.BackgroundJob import BackgroundJob


class _Action(QObject):
    def __init__(self, owner, key, function, callback):
        super().__init__(owner)
        self.owner, self.key, self.callback = owner, key, callback
        self.job = BackgroundJob(function)
        self.job.signals.completed.connect(self.complete)

    @Slot(object, object)
    def complete(self, result, error):
        self.owner.pending.pop(self.key, None)
        try:
            self.callback(result, error)
        finally:
            self.deleteLater()


class AsyncActions(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pending = {}

    def busy(self, key):
        return key in self.pending

    def start(self, key, function, callback):
        if self.busy(key):
            return False
        action = _Action(self, key, function, callback)
        self.pending[key] = action
        QThreadPool.globalInstance().start(action.job)
        return True


class LatestValueAction(QObject):
    """One hardware write at a time, coalescing rapid slider changes."""
    completed = Signal(int, object, object)

    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function = function
        self.actions = AsyncActions(self)
        self.value = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(120)
        self.timer.timeout.connect(self._start)

    def set_value(self, value):
        self.value = int(value)
        self.timer.start()

    def _start(self):
        if self.actions.busy('write'):
            return
        value, function = self.value, self.function
        self.actions.start('write', lambda: function(value),
                           lambda result, error: self._finished(value, result, error))

    def _finished(self, value, result, error):
        if value != self.value:
            self.timer.stop()
            self._start()
        else:
            self.completed.emit(value, result, error)
