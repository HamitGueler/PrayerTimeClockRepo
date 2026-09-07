import os
import pytest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


@pytest.fixture(scope='session')
def qapp():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QThreadPool
    app = QApplication.instance() or QApplication([])
    yield app
    QThreadPool.globalInstance().waitForDone(2000)
