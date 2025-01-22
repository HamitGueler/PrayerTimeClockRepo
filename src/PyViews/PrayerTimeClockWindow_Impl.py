
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
from datetime import datetime
import pygame
import schedule
import time
import os

class TaskScheduler(QThread):
    task_started = Signal()

    def run(self):
        schedule.every().day.at("00:02").do(self.run_task)
        while True:
            schedule.run_pending()
            self.msleep(1000)

    def run_task(self):
        print("Task started!")
        self.task_started.emit()
        
class PrayerTimeClockWindow(QMainWindow, Ui_MainWindow):


    def __init__(self):

        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Clock")

        pygame.mixer.init()
        pygame.mixer.music.load("./src/AudioFiles/adhan.mp3")

        self.scraper = WebScraperClass()
        self.prayer_times = {}
        self.toggle_bool = False
        self.toggle_count = 0
        self.current_prayer_index = 0
        self.current_prayers = [self.current_day_fajr_time, self.current_day_shroq_time, 
                               self.current_day_zohr_time, self.current_day_asr_time, self.current_day_magrb_time, 
                               self.current_day_isha_time]
        
        self.current_prayers_labels = [self.current_day_fajr, self.current_day_shroq, 
                               self.current_day_zohr, self.current_day_asr, self.current_day_magrb, 
                               self.current_day_isha]
            
        self.tomorrows_prayers = [self.next_day_fajr_time, self.next_day_shroq_time, 
                                self.next_day_zohr_time, self.next_day_asr_time, self.next_day_magrb_time,
                                self.next_day_isha_time]
        
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
            box.setStyleSheet("background-color: #96b9ce")
            
        self.setStyleSheet(open("./style.css").read())
        
    def closeEvent(self, event):
        # Terminate the thread when the GUI is closed
        event.accept()
        
    def __setupData(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        prayer_times = self.scraper.get_prayer_times()
        
        if(prayer_times["requestSuccess"][0] == True):
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
            
            self.__rest_timer = QTimer()
            self.__rest_timer.timeout.connect(self.update_timer)
            self.__rest_timer.start(1000)
        else:
            self.last_updated_date.setText(prayer_times["requestSuccess"][1])
            self.last_updated_time.setText(current_time)
            self.led_sign.setStyleSheet("color: red")

    def set_prayer_times(self):
            
            for index in range(6):
                self.current_prayers[index].setText(self.prayer_times["Prayers"][index])
                self.tomorrows_prayers[index].setText(self.prayer_times["nextDayPrayers"]["prayers"][index])
                
            
    def __update_clock(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        self.current_time.setText(current_time)
       
    def update_timer(self):
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
        next_prayer_time = self.prayer_times["nextDayPrayers"]["prayers"][0]
        
        for _ in range(len(self.prayer_times)):
            current_datetime = QDateTime.fromString(current_time, "hh:mm:ss")
            next_prayer_time =  self.prayer_times["Prayers"][self.current_prayer_index]
            next_prayer_datetime = QDateTime.fromString(self.prayer_times["Prayers"][self.current_prayer_index], "hh:mm")
            
            if(self.current_prayer_index < 5):
                if current_datetime >= next_prayer_datetime:
                    self.current_prayer_index = self.current_prayer_index+1

            if(self.current_prayer_index == 5):
                if current_datetime >= QDateTime.fromString(self.prayer_times["nextDayPrayers"]["prayers"][self.current_prayer_index], "hh:mm"):
                    print("hallo")
                    next_prayer_time = self.prayer_times["nextDayPrayers"]["prayers"][0]
                next_prayer_datetime = QDateTime.fromString(next_prayer_time, "hh:mm")
        
        time_difference = current_datetime.secsTo(next_prayer_datetime)
        if time_difference < 0:
            time_difference += 24 * 3600
   
        hours = time_difference // 3600
        minutes = (time_difference % 3600) // 60
        seconds = time_difference % 60
        self.__style_current_prayer()
        self.rest_time.setText(f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")

        if(current_time == QDateTime.fromString(self.prayer_times["Prayers"][self.current_prayer_index-1], "hh:mm").toString("hh:mm:ss")):
            self.call_to_prayer()
        
    def call_to_prayer(self):
        self.toggle_timer.start(1000)
        if self.current_prayer_index == 0:
            pygame.mixer.music.load("./src/AudioFiles/fajr_adhan.mp3")
        else:
            pygame.mixer.music.load("./src/AudioFiles/adhan.mp3")
        pygame.mixer.music.play()
    
    def __style_current_prayer(self):
        next_prayer_datetime = QDateTime.fromString(self.prayer_times["Prayers"][self.current_prayer_index], "hh:mm")
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
        current_datetime = QDateTime.fromString(current_time, "hh:mm:ss")
        index = self.current_prayer_index
        if index == 0 or (index == 1 and current_datetime <= next_prayer_datetime):
                    self.__reset_style(index)
                    self.fajr_box.setStyleSheet(self._current_prayer_style)
        elif index == 2 and (current_datetime <= next_prayer_datetime):
                    self.__reset_style(index)
                    self.shroq_box.setStyleSheet(self._current_prayer_style)
        elif index == 3 and (current_datetime <= next_prayer_datetime):
                    self.__reset_style(index)
                    self.zohr_box.setStyleSheet(self._current_prayer_style)
        elif index == 4 and (current_datetime <= next_prayer_datetime):    
                    self.__reset_style(index)
                    self.asr_box.setStyleSheet(self._current_prayer_style)
        elif index == 5 and (current_datetime <= next_prayer_datetime):
                    self.__reset_style(index)
                    self.magrb_box.setStyleSheet(self._current_prayer_style)
        elif index == 5 and (current_datetime > next_prayer_datetime):
                    self.__reset_style(index) 
                    self.isha_box.setStyleSheet(self._current_prayer_style) 
                    
        
    
    def __reset_style(self, index):
        boxes = [self.fajr_box, self.shroq_box, self.zohr_box, self.asr_box, self.magrb_box, self.isha_box]          
        boxes.pop(index)
        
        for box in boxes:
            box.setStyleSheet("")
        
    def __indicate_prayer(self):
        next_prayer_datetime = QDateTime.fromString(self.prayer_times["Prayers"][self.current_prayer_index], "hh:mm")
        current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
        current_datetime = QDateTime.fromString(current_time, "hh:mm:ss")
        
        index = self.current_prayer_index
        if (index == 1 and (current_datetime <= next_prayer_datetime)):
            self.toggle_prayer(0)
        elif (index == 2 and (current_datetime <= next_prayer_datetime)):
            self.toggle_prayer(1)
        elif (index == 3 and (current_datetime <= next_prayer_datetime)):
            self.toggle_prayer(2)
        elif (index == 4 and (current_datetime <= next_prayer_datetime)):
            self.toggle_prayer(3)
        elif (index == 5 and (current_datetime <= next_prayer_datetime)):
            self.toggle_prayer(4)
        elif (index == 5 and (current_datetime > next_prayer_datetime)):
            self.toggle_prayer(5)
            
        self.toggle_count +=1
        if(self.toggle_count == 170):
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
        
        
        
