"""A fixed quote area: full source text stays readable without resizing the clock."""
import time
from pathlib import Path
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QScroller, QSizePolicy, QVBoxLayout, QWidget


# This QuranEnc export uses legacy Quran-font slots for open tanwin.
# Map only the display representation to the Unicode open-tanwin characters;
# the packaged source remains byte-for-byte unchanged.
ARABIC_DISPLAY_MAP = str.maketrans({'\u0656': '\u08f2', '\u0657': '\u08f0', '\u065e': '\u08f1'})


def arabic_display_text(text):
    return text.translate(ARABIC_DISPLAY_MAP)


class QuranQuotePanel(QFrame):
    _font_loaded = False

    def __init__(self, parent=None):
        super().__init__(parent)
        if not type(self)._font_loaded:
            font_path = Path(__file__).resolve().parents[1] / 'Fonts' / 'AmiriQuran-Regular.ttf'
            type(self)._font_loaded = QFontDatabase.addApplicationFont(str(font_path)) >= 0
        self.setObjectName('quran_panel')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.scroll = QScrollArea()
        self.scroll.setObjectName('quran_scroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName('quran_content')
        column = QVBoxLayout(content)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        self.arabic = QLabel()
        self.arabic.setObjectName('quran_arabic')
        self.translation = QLabel()
        self.translation.setObjectName('quran_translation')
        for label in (self.arabic, self.translation):
            label.setTextFormat(Qt.PlainText)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            column.addWidget(label)
        self.scroll.setWidget(content)
        QScroller.grabGesture(self.scroll.viewport(), QScroller.TouchGesture)
        self.scroll.viewport().installEventFilter(self)
        layout.addWidget(self.scroll, 1)
        self.reference = QLabel()
        self.reference.setObjectName('quran_reference')
        self.reference.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.reference)
        self.source = QLabel('Bubenheim/Elyas · Tanzil.net')
        self.source.setObjectName('quran_source')
        self.source.setAlignment(Qt.AlignCenter)
        self.source.setToolTip('Arabischer Text: QuranEnc / quran-json. Deutsche Bedeutungsübersetzung: Bubenheim & Elyas / Tanzil.')
        layout.addWidget(self.source)
        self.resume_at = time.monotonic() + 12
        self.timer = QTimer(self)
        self.timer.setInterval(60)
        self.timer.timeout.connect(self._scroll_text)
        self.timer.start()

    def set_verse(self, arabic, translation, reference):
        self.arabic.setText(arabic_display_text(arabic))
        self.translation.setText(translation)
        self.reference.setText(reference)
        self.scroll.verticalScrollBar().setValue(0)
        self.resume_at = time.monotonic() + 12

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.TouchBegin, QEvent.TouchUpdate, QEvent.Wheel,
                             QEvent.MouseButtonPress, QEvent.MouseMove):
            self.resume_at = time.monotonic() + 30
        return super().eventFilter(watched, event)

    def _scroll_text(self):
        if not self.isVisible() or time.monotonic() < self.resume_at:
            return
        bar = self.scroll.verticalScrollBar()
        if bar.maximum() == 0:
            return
        if bar.value() >= bar.maximum():
            bar.setValue(0)
            self.resume_at = time.monotonic() + 12
        else:
            bar.setValue(bar.value() + 1)
            if bar.value() >= bar.maximum():
                self.resume_at = time.monotonic() + 12
