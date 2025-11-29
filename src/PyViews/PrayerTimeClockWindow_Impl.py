from PySide6.QtCore import (QDateTime, QThread, Signal,
QTime, QTimer, Qt)
from PySide6.QtGui import (QCursor)
from PySide6.QtWidgets import (QMainWindow)

from PyViews.PrayerTimeClockWindow import Ui_MainWindow
from HelperClasses.WebScraperClass import WebScraperClass
from datetime import datetime, timedelta
import pygame
import schedule
import time
import os
import subprocess


class ReconnectWorker(QThread):
    finished = Signal(bool, str)  # (success, message)

    def __init__(self, method="nmcli", ssid=None, iface="wlan0", parent=None):
        super().__init__(parent)
        self.method = method     # "nmcli" | "wpa" | "networking"
        self.ssid = ssid
        self.iface = iface

    def run(self):
        try:
            # Versuche Reconnect je nach Methode
            if self.method == "nmcli":
                subprocess.run(["nmcli", "radio", "wifi", "off"], check=False)
                time.sleep(0.5)
                subprocess.run(["nmcli", "radio", "wifi", "on"], check=False)
                # <<< NEU: statt "device wifi connect" -> gespeicherte Connection hochfahren
                if self.ssid:
                    subprocess.run(
                        ["nmcli", "connection", "up", "id", self.ssid],
                        check=False
                    )

            elif self.method == "wpa":   # Raspberry Pi OS Lite
                subprocess.run(["wpa_cli", "-i", self.iface, "reassociate"], check=False)
                subprocess.run(["dhclient", "-r", self.iface], check=False)
                subprocess.run(["dhclient", self.iface], check=False)

            elif self.method == "networking":
                # Achtung: benötigt meist sudo/NOPASSWD
                subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False)

            # Nach dem Versuch kurz warten und prüfen
            for _ in range(10):
                if PrayerTimeClockWindow._is_online_static():
                    self.finished.emit(True, "Reconnected")
                    return
                time.sleep(1)

            self.finished.emit(False, "Reconnect failed")
        except Exception as e:
            self.finished.emit(False, f"Reconnect error: {e}")


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

        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.current_dir, ".."))
        self.fajr_adhan_path = os.path.join(self.project_root, "AudioFiles", "fajr_adhan.mp3")
        self.adhan_path = os.path.join(self.project_root, "AudioFiles", "adhan.mp3")
        pygame.mixer.music.load(self.adhan_path)
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
        
        # <<< NEU: hier einmal deinen WiFi-Connection-Namen eintragen (NAME aus `nmcli connection show`)
        self.wifi_connection_name = "DEIN_WIFI_NAME_HIER"
        
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
            
    @staticmethod
    def _is_online_static(host="8.8.8.8", port=53, timeout=3) -> bool:
        try:
            import socket
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            return True
        except OSError:
            return False

    def _is_online(self) -> bool:
        return PrayerTimeClockWindow._is_online_static()

    def _try_reconnect_and_refresh(self):
        if self._is_online():
            self.__setupData()
            return

        self.reconnect_worker = ReconnectWorker(
            method="nmcli",
            ssid=self.wifi_connection_name,  # <<< NEU: hier den Namen übergeben
            iface="wlan0",
            parent=self
        )
        self.reconnect_worker.finished.connect(self._after_reconnect_then_refresh)
        self.reconnect_worker.start()

    def _after_reconnect_then_refresh(self, ok: bool, msg: str):
        if ok:
            self.retry_countdown = QTime(0, 0, 0)
            self.__retry_timer.stop()
            self.retry_time.hide()
            self.__setupData()
        else:
            self.retry_countdown = QTime(0, 5, 0)
            if not self.__retry_timer.isActive():
                self.__retry_timer.start(1000)
            self.retry_time.show()


    def __setupData(self):
        now = datetime.now()
        self.current_prayer_index = 0
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
            
            self._try_reconnect_and_refresh()
            
            
    def update_retry_timer(self):
        self.retry_countdown = self.retry_countdown.addSecs(-1)
        self.retry_time.setText(self.retry_countdown.toString('mm:ss'))

        if self.retry_countdown == QTime(0, 0, 0):
            self.__retry_timer.stop()
            self.retry_time.hide()
            self._try_reconnect_and_refresh()

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
        
        if self.current_prayer_time is None:
            next_prayer_time_str = self.prayer_times["Prayers"][0]
            self.current_prayer_time = QDateTime.fromString(today_str + " " + next_prayer_time_str, "yyyy-MM-dd hh:mm")
        else:
            if self.current_prayer_index == 5 or self.current_prayer_index == 0:
                print(self.current_prayer_index)
                self.current_prayer_time = QDateTime.fromString(today_str + " " + self.prayer_times["Prayers"][self.current_prayer_index], "yyyy-MM-dd hh:mm")
            else:
                print(self.current_prayer_index)
                self.current_prayer_time = QDateTime.fromString(today_str + " " + self.prayer_times["Prayers"][self.current_prayer_index+1], "yyyy-MM-dd hh:mm")
                
        active_index = None
        for i, pt in enumerate(self.prayer_times["Prayers"]):
            prayer_dt = QDateTime.fromString(today_str + " " + pt, "yyyy-MM-dd hh:mm")
            if now >= prayer_dt:
                active_index = i
            else:
                break

        if active_index is None:
            active_index = 0

        if now < QDateTime.fromString(today_str + " " + self.prayer_times["Prayers"][0], "yyyy-MM-dd hh:mm"):
            next_prayer_str = self.prayer_times["Prayers"][0]
            next_prayer_dt = QDateTime.fromString(today_str + " " + next_prayer_str, "yyyy-MM-dd hh:mm")
        elif active_index < 5:
            next_prayer_str = self.prayer_times["Prayers"][active_index + 1]
            next_prayer_dt = QDateTime.fromString(today_str + " " + next_prayer_str, "yyyy-MM-dd hh:mm")
        else:
            tomorrow = now.addDays(1).toString("yyyy-MM-dd")
            next_prayer_str = self.prayer_times["nextDayPrayers"]["prayers"][0]
            next_prayer_dt = QDateTime.fromString(tomorrow + " " + next_prayer_str, "yyyy-MM-dd hh:mm")

        secs_to = now.secsTo(next_prayer_dt)
        if secs_to < 0:
            secs_to += 24 * 3600
        hours = secs_to // 3600
        minutes = (secs_to % 3600) // 60
        seconds = secs_to % 60
        self.rest_time.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        self.current_prayer_index = active_index
        self.__style_current_prayer()
        print(now.toString("hh:mm:ss") + " || " + self.current_prayer_time.toString("hh:mm:ss"))
        if now.toString("hh:mm:ss") == self.current_prayer_time.toString("hh:mm:ss"):
            self.call_to_prayer()

    def call_to_prayer(self):
        self.toggle_timer.start(1000)
        if self.current_prayer_index == 0:
            pygame.mixer.music.load(self.fajr_adhan_path)
        else:
            pygame.mixer.music.load(self.adhan_path)
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
        self.toggle_prayer(self.current_prayer_index)
        self.toggle_count += 1
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
