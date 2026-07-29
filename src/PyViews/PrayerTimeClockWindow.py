import math

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class IslamicGirihOrnament(QWidget):
    """Curved Islamic mandala inspired by carved arabesque and illuminated girih."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(154, 154)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._layer_cache = None
        self._animation_clock = QElapsedTimer()
        self._animation_clock.start()
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self.update)
        self._animation_timer.start(80)

    @staticmethod
    def _star(center, outer_radius, inner_radius, points=12, rotation=-math.pi / 2):
        vertices = []
        for index in range(points * 2):
            angle = rotation + index * math.pi / points
            radius = outer_radius if index % 2 == 0 else inner_radius
            vertices.append(QPointF(center.x() + math.cos(angle) * radius, center.y() + math.sin(angle) * radius))
        return QPolygonF(vertices)

    @staticmethod
    def _regular_polygon(center, radius, points, rotation=-math.pi / 2):
        return QPolygonF([
            QPointF(center.x() + math.cos(rotation + index * math.tau / points) * radius,
                    center.y() + math.sin(rotation + index * math.tau / points) * radius)
            for index in range(points)
        ])

    def _render(self, layer):
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(int(self.width() * ratio), int(self.height() * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) * 0.475

        if layer == "base":
            # This field does not rotate; every ornamental path above it remains
            # exactly the same as in the approved design.
            painter.setPen(QPen(QColor(225, 188, 98, 125), 1.5))
            painter.setBrush(QColor(5, 30, 35, 142))
            painter.drawEllipse(center, radius * 0.92, radius * 0.92)

        def petal_path(angle, inner, shoulder, outer, half_width, pointed=False):
            radial = QPointF(math.cos(angle), math.sin(angle))
            tangent = QPointF(-math.sin(angle), math.cos(angle))
            base = center + radial * inner
            tip = center + radial * outer
            left = center + radial * shoulder + tangent * half_width
            right = center + radial * shoulder - tangent * half_width
            path = QPainterPath(base)
            if pointed:
                path.cubicTo(base + tangent * half_width * 0.55, left, tip)
                path.cubicTo(right, base - tangent * half_width * 0.55, base)
            else:
                crown_left = tip + tangent * half_width * 0.22 - radial * 2
                crown_right = tip - tangent * half_width * 0.22 - radial * 2
                path.cubicTo(base + tangent * half_width * 0.62, left, crown_left)
                path.quadTo(tip + radial * 1.5, crown_right)
                path.cubicTo(right, base - tangent * half_width * 0.62, base)
            return path

        if layer == "outer":
            # Scalloped outer halo, comparable to the rounded lobes of a mandala.
            for index in range(24):
                angle = -math.pi / 2 + index * math.tau / 24
                petal = petal_path(angle, radius * 0.70, radius * 0.82, radius * 0.97, radius * 0.105)
                painter.setPen(QPen(QColor(224, 187, 96, 178), 1.25))
                painter.setBrush(QColor(18, 105, 98, 44) if index % 2 == 0 else QColor(181, 132, 49, 35))
                painter.drawPath(petal)

            # A dotted illuminated border, like the beadwork in the first reference.
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(235, 201, 115, 175))
            for index in range(72):
                angle = index * math.tau / 72
                point = center + QPointF(math.cos(angle), math.sin(angle)) * radius * 0.885
                painter.drawEllipse(point, 0.95, 0.95)

            # Final enclosing ring from the approved preview. It is deliberately
            # drawn last so the outer silhouette stays visible above the petals.
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(239, 204, 118, 205), 1.35))
            painter.drawEllipse(center, radius * 0.985, radius * 0.985)

        # Two interleaved rings of curved lancets.  Their shoulders are broad,
        # so the visible shapes read as leaves rather than narrow triangles.
        if layer == "middle":
            for ring, rotation, color in (
                ((0.43, 0.59, 0.78, 0.175), 0.0, QColor(35, 151, 139, 88)),
                ((0.32, 0.47, 0.67, 0.155), math.pi / 12, QColor(176, 124, 43, 68)),
            ):
                inner, shoulder, outer, width = ring
                for index in range(12):
                    angle = -math.pi / 2 + rotation + index * math.tau / 12
                    path = petal_path(angle, radius * inner, radius * shoulder, radius * outer, radius * width)
                    painter.setPen(QPen(QColor(236, 202, 119, 190), 1.25))
                    painter.setBrush(color)
                    painter.drawPath(path)

            # Curved interlace belt: three strokes create a dark separation,
            # turquoise ribbon and thin gold inlay.
            belt = QPainterPath()
            for index in range(25):
                angle = -math.pi / 2 + index * math.tau / 24
                wave = radius * (0.535 + (0.075 if index % 2 == 0 else -0.025))
                point = center + QPointF(math.cos(angle), math.sin(angle)) * wave
                belt.moveTo(point) if index == 0 else belt.lineTo(point)
            for width, color in ((9.0, QColor(2, 13, 16, 220)), (6.0, QColor(28, 137, 130, 190)), (1.35, QColor(240, 207, 125, 220))):
                painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(belt)

        # Fine central flower: 24 curved petals, two lace circles and a rosette.
        if layer == "inner":
            for index in range(24):
                angle = -math.pi / 2 + index * math.tau / 24
                painter.setPen(QPen(QColor(230, 194, 107, 170), 0.85))
                painter.setBrush(QColor(13, 85, 82, 82))
                painter.drawPath(petal_path(angle, radius * 0.10, radius * 0.22, radius * 0.37, radius * 0.055, True))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(236, 202, 117, 185), 1.1))
            painter.drawEllipse(center, radius * 0.285, radius * 0.285)
            painter.drawEllipse(center, radius * 0.17, radius * 0.17)
            painter.setBrush(QColor(192, 139, 49, 210))
            painter.drawPolygon(self._star(center, radius * 0.12, radius * 0.072, points=12))
            painter.setBrush(QColor(7, 36, 40, 235))
            painter.drawEllipse(center, radius * 0.035, radius * 0.035)
        painter.end()
        return pixmap

    def paintEvent(self, event):
        if self._layer_cache is None:
            self._layer_cache = {
                layer: self._render(layer)
                for layer in ("base", "outer", "middle", "inner")
            }
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self._layer_cache["base"])
        seconds = self._animation_clock.elapsed() / 1000.0
        # Deliberately calm but still perceptible: the approved rings retain
        # their geometry and only rotate more slowly.
        rotations = (
            ("outer", seconds * 360.0 / 174.0),
            ("middle", -seconds * 360.0 / 204.0),
            ("inner", seconds * 360.0 / 150.0),
        )
        center = QPointF(self.width() / 2, self.height() / 2)
        for layer, angle in rotations:
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.translate(-center)
            painter.drawPixmap(0, 0, self._layer_cache[layer])
            painter.restore()

    def resizeEvent(self, event):
        self._layer_cache = None
        super().resizeEvent(event)


class IslamicPatternBackground(QWidget):
    """Continuous, restrained stepped-star pattern used across the whole screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache = None

    def _render_tile(self):
        ratio = self.devicePixelRatioF()
        width, height = 192, 128
        pixmap = QPixmap(int(width * ratio), int(height * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        line = QColor(67, 92, 87, 42)
        painter.setPen(QPen(line, 1.35, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))

        star = QPolygonF([
            QPointF(72, 16), QPointF(84, 28), QPointF(108, 28), QPointF(120, 16),
            QPointF(120, 40), QPointF(136, 56), QPointF(136, 72), QPointF(120, 88),
            QPointF(120, 112), QPointF(108, 100), QPointF(84, 100), QPointF(72, 112),
            QPointF(72, 88), QPointF(56, 72), QPointF(56, 56), QPointF(72, 40),
        ])
        painter.drawPolygon(star)
        painter.drawEllipse(QPointF(96, 64), 27, 27)

        paths = (
            ((0, 0), (48, 0), (64, 16), (72, 16)),
            ((120, 16), (128, 16), (144, 0), (192, 0)),
            ((0, 128), (48, 128), (64, 112), (72, 112)),
            ((120, 112), (128, 112), (144, 128), (192, 128)),
            ((0, 24), (40, 64), (56, 64)),
            ((0, 40), (32, 72), (56, 96), (56, 112)),
            ((192, 24), (152, 64), (136, 64)),
            ((192, 40), (160, 72), (136, 96), (136, 112)),
            ((0, 104), (40, 64), (56, 64)),
            ((192, 104), (152, 64), (136, 64)),
        )
        for points in paths:
            painter.drawPolyline(QPolygonF([QPointF(x, y) for x, y in points]))
        painter.end()
        return pixmap

    def paintEvent(self, event):
        if self._cache is None:
            self._cache = self._render_tile()
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#071217"))
        painter.drawTiledPixmap(self.rect(), self._cache)

    def changeEvent(self, event):
        self._cache = None
        super().changeEvent(event)


class OrientalClockPanel(QFrame):
    """Paints a calm mihrab silhouette over the shared background lattice."""

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(202, 166, 91, 34), 1.2))
        painter.drawLine(26, 32, self.width() - 26, 32)

        # Nested pointed mihrab arches frame the time.
        arch = QPainterPath()
        left, right, top, bottom = 34.0, self.width() - 34.0, 51.0, 286.0
        arch.moveTo(left, bottom)
        arch.lineTo(left, 138)
        arch.cubicTo(left, 92, self.width() * 0.34, 77, self.width() / 2, top)
        arch.cubicTo(self.width() * 0.66, 77, right, 92, right, 138)
        arch.lineTo(right, bottom)
        painter.setPen(QPen(QColor(86, 215, 193, 26), 1.3))
        painter.drawPath(arch)
        inner_arch = QPainterPath()
        inner_arch.moveTo(left + 8, bottom)
        inner_arch.lineTo(left + 8, 143)
        inner_arch.cubicTo(left + 8, 102, self.width() * 0.36, 87, self.width() / 2, top + 12)
        inner_arch.cubicTo(self.width() * 0.64, 87, right - 8, 102, right - 8, 143)
        inner_arch.lineTo(right - 8, bottom)
        painter.setPen(QPen(QColor(202, 166, 91, 22), 1.0))
        painter.drawPath(inner_arch)

        # Small ornamental corner fans.
        painter.setPen(QPen(QColor(86, 215, 193, 34), 1.0))
        for mirrored in (False, True):
            origin_x = 34 if not mirrored else self.width() - 34
            direction = 1 if not mirrored else -1
            for radius in (10, 17, 24):
                painter.drawArc(QRectF(origin_x - radius if not mirrored else origin_x,
                                       337, radius, radius), 0 if not mirrored else 90 * 16, 90 * 16)
            painter.drawLine(origin_x, 361, origin_x + direction * 31, 361)


class IslamicBorderFrame(QFrame):
    """Fine illuminated frame with small eightfold arabesques in the corners."""

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        inset = 4.5
        painter.setPen(QPen(QColor(211, 170, 93, 76), 1.0))
        painter.drawRoundedRect(
            QRectF(inset, inset, self.width() - 2 * inset, self.height() - 2 * inset),
            10,
            10,
        )
        painter.setPen(QPen(QColor(86, 215, 193, 64), 0.9))
        for x, y, sx, sy in (
            (inset + 9, inset + 9, 1, 1),
            (self.width() - inset - 9, inset + 9, -1, 1),
            (inset + 9, self.height() - inset - 9, 1, -1),
            (self.width() - inset - 9, self.height() - inset - 9, -1, -1),
        ):
            path = QPainterPath(QPointF(x, y + sy * 8))
            path.quadTo(QPointF(x + sx * 2, y + sy * 2), QPointF(x + sx * 8, y))
            path.quadTo(QPointF(x + sx * 2, y - sy * 2), QPointF(x, y - sy * 8))
            painter.drawPath(path)


class SpecialEventTags(QWidget):
    """A shared day heading followed by every matching event tag."""

    def __init__(self, heading="", parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(7, 3, 7, 3)
        row.setSpacing(6)
        self.heading = QLabel(heading)
        self.heading.setObjectName("eventHeading")
        self.heading.setVisible(bool(heading))
        row.addWidget(self.heading, 0, Qt.AlignVCenter)
        self.row = row
        self.tags = []
        row.addStretch(1)
        self.hide()

    def setTags(self, values):
        values = list(values)
        while len(self.tags) < len(values):
            tag = QLabel()
            tag.setObjectName("eventTag")
            tag.setAlignment(Qt.AlignCenter)
            self.tags.append(tag)
            self.row.insertWidget(self.row.count() - 1, tag, 0, Qt.AlignVCenter)
        for index, tag in enumerate(self.tags):
            if index < len(values):
                tag.setText(values[index])
                tag.show()
            else:
                tag.clear()
                tag.hide()
        self.setVisible(bool(values))


class Ui_MainWindow:
    PRAYERS = (
        ("fajr", "FAJR"),
        ("shroq", "SHURŪQ"),
        ("zohr", "DHUHR"),
        ("asr", "ASR"),
        ("magrb", "MAGHRIB"),
        ("isha", "ISHA"),
    )

    def setupUi(self, main_window: QMainWindow):
        main_window.setObjectName("MainWindow")
        main_window.resize(1024, 600)
        main_window.setMinimumSize(800, 480)

        self.centralwidget = IslamicPatternBackground(main_window)
        self.centralwidget.setObjectName("centralwidget")
        root = QVBoxLayout(self.centralwidget)
        root.setContentsMargins(24, 18, 24, 16)
        root.setSpacing(12)

        content = QHBoxLayout()
        content.setSpacing(18)
        content.addWidget(self._build_clock_panel(), 3)
        content.addWidget(self._build_today_panel(), 2)
        root.addLayout(content, 1)
        root.addWidget(self._build_tomorrow_panel())

        main_window.setCentralWidget(self.centralwidget)
        self.retranslateUi(main_window)

    def _build_clock_panel(self):
        self.clockPanel = OrientalClockPanel()
        self.clockPanel.setObjectName("clockPanel")
        layout = QVBoxLayout(self.clockPanel)
        layout.setContentsMargins(24, 15, 24, 16)
        layout.setSpacing(0)

        status_row = QHBoxLayout()
        self.current_location = QLabel()
        self.current_location.setObjectName("current_location")
        status_row.addWidget(self.current_location)
        status_row.addStretch()

        self.led_sign = QLabel("●")
        self.led_sign.setObjectName("led_sign")
        self.led_sign.setToolTip("Datenverbindung")
        status_row.addWidget(self.led_sign)

        self.last_updated_descrition = QLabel()
        self.last_updated_descrition.setObjectName("last_updated_descrition")
        status_row.addWidget(self.last_updated_descrition)
        self.last_updated_time = QLabel()
        self.last_updated_time.setObjectName("last_updated_time")
        self.last_updated_time.setMinimumWidth(132)
        self.last_updated_time.setAlignment(Qt.AlignCenter)
        status_row.addWidget(self.last_updated_time)

        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("refresh_button")
        self.refresh_button.setFixedSize(34, 34)
        status_row.addWidget(self.refresh_button)
        status_row.setSpacing(7)
        layout.addLayout(status_row)

        time_row = QHBoxLayout()
        time_row.setSpacing(8)
        self.current_time = QLabel()
        self.current_time.setObjectName("current_time")
        self.current_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        time_row.addWidget(self.current_time, 1)

        ornament_column = QVBoxLayout()
        ornament_column.setContentsMargins(0, 18, 0, 0)
        ornament_column.addStretch(1)
        self.islamic_ornament = IslamicGirihOrnament()
        ornament_column.addWidget(self.islamic_ornament, 0, Qt.AlignHCenter | Qt.AlignBottom)
        time_row.addLayout(ornament_column)
        layout.addLayout(time_row, 1)

        self.current_date = QLabel()
        self.current_date.setObjectName("current_date")
        layout.addWidget(self.current_date)

        self.hijri_date = QLabel()
        self.hijri_date.setObjectName("hijri_date")
        layout.addWidget(self.hijri_date)

        self.islamic_event = SpecialEventTags("HEUTE")
        self.islamic_event.setObjectName("islamic_event")
        layout.addWidget(self.islamic_event)

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.HLine)
        layout.addWidget(divider)

        next_row = QHBoxLayout()
        next_col = QVBoxLayout()
        self.rest_time_description = QLabel()
        self.rest_time_description.setObjectName("rest_time_description")
        next_col.addWidget(self.rest_time_description)
        self.rest_time = QLabel()
        self.rest_time.setObjectName("rest_time")
        next_col.addWidget(self.rest_time)
        next_row.addLayout(next_col, 1)

        midnight_col = QVBoxLayout()
        self.midnight_label = QLabel()
        self.midnight_label.setObjectName("midnight_label")
        midnight_col.addWidget(self.midnight_label)
        self.midnight_time = QLabel()
        self.midnight_time.setObjectName("midnight_time")
        midnight_col.addWidget(self.midnight_time)
        next_row.addLayout(midnight_col)
        layout.addLayout(next_row)

        self.retry_time = QLabel()
        self.retry_time.setObjectName("retry_time")
        layout.addWidget(self.retry_time)

        self.quran_arabic = QLabel()
        self.quran_arabic.setObjectName("quran_arabic")
        self.quran_arabic.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.quran_arabic)
        self.quran_translation = QLabel()
        self.quran_translation.setObjectName("quran_translation")
        self.quran_translation.setAlignment(Qt.AlignCenter)
        self.quran_translation.setWordWrap(True)
        layout.addWidget(self.quran_translation)
        return self.clockPanel

    def _build_today_panel(self):
        panel = IslamicBorderFrame()
        panel.setObjectName("todayPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)

        title = QLabel("HEUTIGE GEBETSZEITEN")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        for key, title_text in self.PRAYERS:
            box = QGroupBox()
            box.setObjectName(f"{key}_box")
            row = QHBoxLayout(box)
            row.setContentsMargins(15, 5, 15, 5)

            name = QLabel(title_text)
            name.setObjectName(f"current_day_{key}")
            time = QLabel("00:00")
            time.setObjectName(f"current_day_{key}_time")
            time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(name)
            row.addStretch()
            row.addWidget(time)
            setattr(self, f"current_day_{key}", name)
            setattr(self, f"current_day_{key}_time", time)
            setattr(self, f"{key}_box", box)
            layout.addWidget(box, 1)
        return panel

    def _build_tomorrow_panel(self):
        self.next_day_prayers_box = IslamicBorderFrame()
        self.next_day_prayers_box.setObjectName("next_day_prayers_box")
        layout = QVBoxLayout(self.next_day_prayers_box)
        layout.setContentsMargins(18, 8, 18, 10)
        layout.setSpacing(5)

        heading = QHBoxLayout()
        heading.setSpacing(18)
        self.next_day_description = QLabel()
        self.next_day_description.setObjectName("next_day_description")
        self.next_day_description.setMinimumWidth(100)
        self.next_day_description.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        heading.addWidget(self.next_day_description, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.next_day_date = QLabel()
        self.next_day_date.setObjectName("next_day_date")
        self.next_day_date.setMinimumWidth(120)
        self.next_day_date.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.next_day_date.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.next_day_date.hide()
        self.tomorrow_islamic_notice = SpecialEventTags()
        self.tomorrow_islamic_notice.setObjectName("tomorrow_islamic_notice")
        self.tomorrow_islamic_notice.hide()
        heading.addWidget(self.tomorrow_islamic_notice, 1)
        heading.addStretch()
        layout.addLayout(heading)

        prayers = QGridLayout()
        prayers.setHorizontalSpacing(8)
        for column, (key, title_text) in enumerate(self.PRAYERS):
            box = QGroupBox()
            box.setObjectName(f"next_day_{key}_box")
            inner = QVBoxLayout(box)
            inner.setContentsMargins(7, 4, 7, 5)
            inner.setSpacing(0)
            name = QLabel(title_text)
            name.setAlignment(Qt.AlignCenter)
            name.setObjectName(f"next_day_{key}")
            time = QLabel("00:00")
            time.setAlignment(Qt.AlignCenter)
            time.setObjectName(f"next_day_{key}_time")
            inner.addWidget(name)
            inner.addWidget(time)
            setattr(self, f"next_day_{key}_box", box)
            setattr(self, f"next_day_{key}", name)
            setattr(self, f"next_day_{key}_time", time)
            prayers.addWidget(box, 0, column)
        layout.addLayout(prayers)
        return self.next_day_prayers_box

    def retranslateUi(self, main_window: QMainWindow):
        main_window.setWindowTitle("PrayerTimeClock")
        self.current_location.setText("BERLIN")
        self.current_time.setText("23:35")
        self.current_date.setText("Dienstag, 04. Februar 2025")
        self.hijri_date.setText("5. Schaʿbān 1446")
        self.islamic_event.setTags([])
        self.last_updated_descrition.setText("AKTUELL")
        self.last_updated_time.setText("04.02.2025 · 23:35")
        self.refresh_button.setText("↻")
        self.rest_time_description.setText("NÄCHSTES GEBET · FAJR")
        self.rest_time.setText("06:08:18")
        self.midnight_label.setText("ISLAMISCHE MITTERNACHT")
        self.midnight_time.setText("00:47")
        self.retry_time.setText("Neuer Verbindungsversuch in 05:00")
        self.quran_arabic.setText("إِنَّ مَعَ الْعُسْرِ يُسْرًا")
        self.quran_translation.setText("„Gewiss, mit der Erschwernis ist Erleichterung.“ · Qurʾān 94:6")
        self.next_day_description.setText("MORGEN")
        self.next_day_date.setText("05.02.2025")
