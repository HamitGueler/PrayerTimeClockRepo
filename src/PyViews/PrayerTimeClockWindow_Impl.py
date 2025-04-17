
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect, QThread, Signal,
    QSize, QTime, QTimer, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGroupBox, QLabel, QMainWindow,
    QMenuBar, QSizePolicy, QStatusBar, QWidget)

from PyViews.PrayerTimeClockWindow import Ui_MainWindow
from HelperClasses.WebScraperClass import WebScraperClass
from datetime import datetime, timedelta
import pygame
import schedule
import time
import os

class TaskScheduler(QThread):
    task_started = Signal()

    def run(self):
        schedule.every().day.at("00:00").do(self.run_task)
        while True:
            schedule.run_pending()
            self.msleep(1000)

    def run_task(self):
        print("Task started!")
        print("UPDATEEEE: ")
        self.task_started.emit()
        
class PrayerTimeClockWindow(QMainWindow, Ui_MainWindow):


    def __init__(self):

        super().__init__()
        self.setupUi(self)
        self.showFullScreen()
        self.setWindowTitle("Clock")

        pygame.mixer.init()
        pygame.mixer.music.load("./src/AudioFiles/adhan.mp3")

        self.scraper = WebScraperClass()
        self.prayer_times = {}
        self.toggle_bool = False
        self.toggle_count = 0
        self.current_prayer_index = 0
        self.current_prayer_time = None
        self.current_prayers = [self.current_day_fajr_time, self.current_day_shroq_time, 
                               self.current_day_zohr_time, self.current_day_asr_time, self.current_day_magrb_time, 
                               self.current_day_isha_time]
        
        self.current_prayers_labels = [self.current_day_fajr, self.current_day_shroq, 
                               self.current_day_zohr, self.current_day_asr, self.current_day_magrb, 
                               self.current_day_isha]
            
        self.tomorrows_prayers = [self.next_day_fajr_time, self.next_day_shroq_time, 
                                self.next_day_zohr_time, self.next_day_asr_time, self.next_day_magrb_time,
                                self.next_day_isha_time]
        
        self.__retry_timer = QTimer()
        self.__retry_timer.timeout.connect(self.update_retry_timer)
        self.retry_time.hide()
        
        self.__setupData()
        
        self.__clock_timer = QTimer()
        self.__clock_timer.timeout.connect(self.__update_clock)
        self.__clock_timer.start(1000)

        
        self.toggle_timer = QTimer(self)
        self.toggle_timer.timeout.connect(self.__indicate_prayer)
        
        self.refresh_button.clicked.connect(self.__refresh_data)
        
        self.task_scheduler = TaskScheduler()
        self.task_scheduler.task_started.connect(self.__setupData)
        self.task_scheduler.start()
        
        self.refresh_button.setCursor(QCursor(Qt.PointingHandCursor))
        self._current_prayer_style = ("background-color: #37a7ed")
        #self.next_day_prayers_box.setObjectName("next_prayers_box")
       # self.next_day_prayers_box.setStyleSheet("border: 1px solid #37a7ed")
            
        self.next_day_prayer_boxes = [self.next_day_fajr_box, self.next_day_shroq_box, self.next_day_zohr_box, self.next_day_fajr_box,
                                 self.next_day_asr_box, self.next_day_magrb_box, self.next_day_isha_box]
        
        for box in self.next_day_prayer_boxes:
            box.setStyleSheet("background-color: #68b8e8")
            
        self.setStyleSheet(open("./style.css").read())
        
    def closeEvent(self, event):
        # Terminate the thread when the GUI is closed
        event.accept()
        
    def __setupData(self):
        now = datetime.now()
        self.current_prayer_index = 0
        current_time = now.strftime("%H:%M")
        prayer_times = self.scraper.get_prayer_times()
        
        if(prayer_times["requestSuccess"][0] == True):
            self.__retry_timer.stop()
            now = datetime.now()
            self.prayer_times = prayer_times
            
            self.current_time.setText(current_time)
            self.current_location.setText("Berlin")
            self.current_date.setText(prayer_times["requestSuccess"][1])
            self.next_day_date.setText(prayer_times["nextDayPrayers"]["date"])
            
            self.set_prayer_times()
            
            self.last_updated_date.setText(prayer_times["requestSuccess"][1])
            self.last_updated_time.setText(current_time)
            self.led_sign.setStyleSheet("color: white")
            
            time1 = datetime.strptime(self.prayer_times["Prayers"][4], "%H:%M")
            time2 = datetime.strptime(self.prayer_times["Prayers"][0], "%H:%M")

            # Falls time2 kleiner ist, ist es am nächsten Tag
            if time2 <= time1:
                time2 += timedelta(days=1)

            diff = time2 - time1
            half_diff = diff / 2
            # Neue Zeit: Isha + halbe Differenz
            midnight_time = time1 + half_diff
            # Formatieren
            midnight_str = midnight_time.strftime("%H:%M")
            self.midnight_time.setText(midnight_str)

            self.__rest_timer = QTimer()
            self.__rest_timer.timeout.connect(self.update_timer)
            self.__rest_timer.start(1000)
        else:
            self.last_updated_date.setText(prayer_times["requestSuccess"][1])
            self.last_updated_time.setText(current_time)
            self.led_sign.setStyleSheet("color: red")
            
            self.retry_countdown = QTime(0, 5, 0)
            self.__retry_timer.start(1000)
            self.retry_time.show()
            
            
    def update_retry_timer(self):
        self.retry_countdown = self.retry_countdown.addSecs(-1)
        self.retry_time.setText(self.retry_countdown.toString('mm:ss'))

        if self.retry_countdown == QTime(0, 0, 0):
            self.__retry_timer.stop()
            self.retry_time.hide()
            self.__refresh_data()

    def set_prayer_times(self):
            
            for index in range(6):
                self.current_prayers[index].setText(self.prayer_times["Prayers"][index])
                self.tomorrows_prayers[index].setText(self.prayer_times["nextDayPrayers"]["prayers"][index])
                
            
    def __update_clock(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        self.current_time.setText(current_time)
       
    def update_timer(self):
        now = QDateTime.currentDateTime()
        today_str = now.toString("yyyy-MM-dd")
        
        # Bestimme den aktuell aktiven Gebetsindex, also das letzte Gebet, das bereits begonnen hat.
        if self.current_prayer_time is None:
            next_prayer_time_str = self.prayer_times["Prayers"][0]
            self.current_prayer_time = QDateTime.fromString(today_str + " " + next_prayer_time_str, "yyyy-MM-dd hh:mm")
        else:
            self.current_prayer_time = QDateTime.fromString(today_str + " " + self.prayer_times["Prayers"][self.current_prayer_index], "yyyy-MM-dd hh:mm")
            
        active_index = None
        for i, pt in enumerate(self.prayer_times["Prayers"]):
            prayer_dt = QDateTime.fromString(today_str + " " + pt, "yyyy-MM-dd hh:mm")
            if now >= prayer_dt:
                active_index = i
            else:
                break
        # Falls noch kein Gebet begonnen hat (z. B. vor Fajr), setze den aktiven Index auf 0.
        if active_index is None:
            active_index = 0
        # Bestimme das nächste Gebet:
        # Berechne das nächste Gebet auf Basis von active_index
        if now < QDateTime.fromString(today_str + " " + self.prayer_times["Prayers"][0], "yyyy-MM-dd hh:mm"):
            # Noch vor Fajr → nächstes Gebet ist Fajr
            next_prayer_str = self.prayer_times["Prayers"][0]
            next_prayer_dt = QDateTime.fromString(today_str + " " + next_prayer_str, "yyyy-MM-dd hh:mm")
        elif active_index < 5:
            # Normalfall → nächstes Gebet ist +1
            next_prayer_str = self.prayer_times["Prayers"][active_index + 1]
            next_prayer_dt = QDateTime.fromString(today_str + " " + next_prayer_str, "yyyy-MM-dd hh:mm")
        else:
            # Nach Isha → nächstes Gebet ist Fajr morgen
            tomorrow = now.addDays(1).toString("yyyy-MM-dd")
            next_prayer_str = self.prayer_times["nextDayPrayers"]["prayers"][0]
            next_prayer_dt = QDateTime.fromString(tomorrow + " " + next_prayer_str, "yyyy-MM-dd hh:mm")

        
        # Berechne die verbleibende Zeit bis zum nächsten Gebet.
        secs_to = now.secsTo(next_prayer_dt)
        if secs_to < 0:
            secs_to += 24 * 3600
        hours = secs_to // 3600
        minutes = (secs_to % 3600) // 60
        seconds = secs_to % 60
        self.rest_time.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        # Setze den Marker auf das aktuell aktive Gebet.
        self.current_prayer_index = active_index
        self.__style_current_prayer()
        # Wenn die aktuelle Zeit (hh:mm) exakt der nächsten Gebetszeit entspricht, wird der Azan ausgelöst.
        if now.toString("hh:mm:ss") == self.current_prayer_time.toString("hh:mm:ss"):
            self.call_to_prayer()


        
    def call_to_prayer(self):
        self.toggle_timer.start(1000)
        print("1")
        if self.current_prayer_index == 0:
            pygame.mixer.music.load("./src/AudioFiles/fajr_adhan.mp3")
        else:
            pygame.mixer.music.load("./src/AudioFiles/adhan.mp3")
        pygame.mixer.music.play()
    
    def __style_current_prayer(self):
        self.__reset_style()
        index = self.current_prayer_index
        if index == 0:
            self.fajr_box.setStyleSheet(self._current_prayer_style)
        elif index == 1:
            self.shroq_box.setStyleSheet(self._current_prayer_style)
        elif index == 2:
            self.zohr_box.setStyleSheet(self._current_prayer_style)
        elif index == 3:
            self.asr_box.setStyleSheet(self._current_prayer_style)
        elif index == 4:
            self.magrb_box.setStyleSheet(self._current_prayer_style)
        elif index == 5:
            self.isha_box.setStyleSheet(self._current_prayer_style)

    def __reset_style(self):
        for box in [self.fajr_box, self.shroq_box, self.zohr_box, self.asr_box, self.magrb_box, self.isha_box]:
            box.setStyleSheet("")
        
    def __indicate_prayer(self):
        # Toggle die Anzeige des aktuell aktiven Gebets (ohne Index-Verschiebung)
        self.toggle_prayer(self.current_prayer_index)
        self.toggle_count += 1
        # Hier kannst Du anpassen, wie lange der Toggle-Effekt andauern soll.
        if self.toggle_count >= 10:
            self.toggle_timer.stop()
            self.toggle_count = 0
    
    def toggle_prayer(self, index):
            if self.toggle_bool == False:
                    self.current_prayers[index].hide()
                    self.current_prayers_labels[index].hide()
                    self.toggle_bool = True
            else:
                    self.current_prayers[index].show()
                    self.current_prayers_labels[index].show()
                    self.toggle_bool = False
            
    def __refresh_data(self):
        self.refresh_button.setDisabled(True)
        self.__setupData()
        QTimer.singleShot(3000, lambda: self.refresh_button.setDisabled(False))
        
        
        
