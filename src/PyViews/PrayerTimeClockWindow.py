# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PrayerTime_Clock_WindowJHkCNr.ui'
##
## Created by: Qt User Interface Compiler version 6.5.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGroupBox, QLabel, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QStatusBar,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1024, 685)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.current_time = QLabel(self.centralwidget)
        self.current_time.setObjectName(u"current_time")
        self.current_time.setGeometry(QRect(0, 0, 671, 171))
        font = QFont()
        font.setPointSize(150)
        font.setBold(True)
        self.current_time.setFont(font)
        self.current_date = QLabel(self.centralwidget)
        self.current_date.setObjectName(u"current_date")
        self.current_date.setGeometry(QRect(10, 240, 631, 51))
        font1 = QFont()
        font1.setPointSize(30)
        self.current_date.setFont(font1)
        self.current_location = QLabel(self.centralwidget)
        self.current_location.setObjectName(u"current_location")
        self.current_location.setGeometry(QRect(10, 170, 281, 71))
        font2 = QFont()
        font2.setPointSize(50)
        self.current_location.setFont(font2)
        self.rest_time_description = QLabel(self.centralwidget)
        self.rest_time_description.setObjectName(u"rest_time_description")
        self.rest_time_description.setGeometry(QRect(10, 290, 661, 41))
        font3 = QFont()
        font3.setPointSize(20)
        self.rest_time_description.setFont(font3)
        self.rest_time = QLabel(self.centralwidget)
        self.rest_time.setObjectName(u"rest_time")
        self.rest_time.setGeometry(QRect(10, 330, 341, 51))
        font4 = QFont()
        font4.setPointSize(40)
        font4.setBold(True)
        self.rest_time.setFont(font4)
        self.last_updated_descrition = QLabel(self.centralwidget)
        self.last_updated_descrition.setObjectName(u"last_updated_descrition")
        self.last_updated_descrition.setGeometry(QRect(230, 160, 321, 41))
        self.last_updated_descrition.setFont(font3)
        self.last_updated_date = QLabel(self.centralwidget)
        self.last_updated_date.setObjectName(u"last_updated_date")
        self.last_updated_date.setGeometry(QRect(320, 200, 141, 21))
        self.last_updated_date.setFont(font3)
        self.last_updated_time = QLabel(self.centralwidget)
        self.last_updated_time.setObjectName(u"last_updated_time")
        self.last_updated_time.setGeometry(QRect(230, 200, 71, 21))
        self.last_updated_time.setFont(font3)
        self.led_sign = QLabel(self.centralwidget)
        self.led_sign.setObjectName(u"led_sign")
        self.led_sign.setGeometry(QRect(460, 200, 81, 91))
        font5 = QFont()
        font5.setPointSize(180)
        self.led_sign.setFont(font5)
        self.refresh_button = QPushButton(self.centralwidget)
        self.refresh_button.setObjectName(u"refresh_button")
        self.refresh_button.setGeometry(QRect(220, 240, 101, 41))
        font6 = QFont()
        font6.setBold(True)
        self.refresh_button.setFont(font6)
        self.fajr_box = QGroupBox(self.centralwidget)
        self.fajr_box.setObjectName(u"fajr_box")
        self.fajr_box.setGeometry(QRect(720, 0, 301, 81))
        self.current_day_fajr = QLabel(self.fajr_box)
        self.current_day_fajr.setObjectName(u"current_day_fajr")
        self.current_day_fajr.setGeometry(QRect(0, 0, 221, 41))
        font7 = QFont()
        font7.setPointSize(25)
        font7.setBold(True)
        font7.setUnderline(False)
        font7.setStrikeOut(False)
        font7.setKerning(True)
        self.current_day_fajr.setFont(font7)
        self.current_day_fajr_time = QLabel(self.fajr_box)
        self.current_day_fajr_time.setObjectName(u"current_day_fajr_time")
        self.current_day_fajr_time.setGeometry(QRect(0, 40, 301, 41))
        font8 = QFont()
        font8.setPointSize(35)
        font8.setBold(True)
        self.current_day_fajr_time.setFont(font8)
        self.next_day_prayers_box = QGroupBox(self.centralwidget)
        self.next_day_prayers_box.setObjectName(u"next_day_prayers_box")
        self.next_day_prayers_box.setGeometry(QRect(0, 390, 711, 111))
        self.next_day_description = QLabel(self.next_day_prayers_box)
        self.next_day_description.setObjectName(u"next_day_description")
        self.next_day_description.setGeometry(QRect(10, -10, 341, 51))
        self.next_day_description.setFont(font3)
        self.next_day_date = QLabel(self.next_day_prayers_box)
        self.next_day_date.setObjectName(u"next_day_date")
        self.next_day_date.setGeometry(QRect(290, 0, 301, 31))
        self.next_day_date.setFont(font3)
        self.next_day_magrb_box = QGroupBox(self.next_day_prayers_box)
        self.next_day_magrb_box.setObjectName(u"next_day_magrb_box")
        self.next_day_magrb_box.setGeometry(QRect(460, 40, 131, 71))
        self.next_day_magrb = QLabel(self.next_day_magrb_box)
        self.next_day_magrb.setObjectName(u"next_day_magrb")
        self.next_day_magrb.setGeometry(QRect(0, 0, 141, 31))
        font9 = QFont()
        font9.setPointSize(20)
        font9.setBold(True)
        self.next_day_magrb.setFont(font9)
        self.next_day_magrb_time = QLabel(self.next_day_magrb_box)
        self.next_day_magrb_time.setObjectName(u"next_day_magrb_time")
        self.next_day_magrb_time.setGeometry(QRect(0, 30, 131, 41))
        self.next_day_magrb_time.setFont(font9)
        self.next_day_asr_box = QGroupBox(self.next_day_prayers_box)
        self.next_day_asr_box.setObjectName(u"next_day_asr_box")
        self.next_day_asr_box.setGeometry(QRect(350, 40, 111, 71))
        self.next_day_asr = QLabel(self.next_day_asr_box)
        self.next_day_asr.setObjectName(u"next_day_asr")
        self.next_day_asr.setGeometry(QRect(0, 0, 111, 31))
        self.next_day_asr.setFont(font9)
        self.next_day_asr_time = QLabel(self.next_day_asr_box)
        self.next_day_asr_time.setObjectName(u"next_day_asr_time")
        self.next_day_asr_time.setGeometry(QRect(0, 30, 111, 41))
        self.next_day_asr_time.setFont(font9)
        self.next_day_zohr_box = QGroupBox(self.next_day_prayers_box)
        self.next_day_zohr_box.setObjectName(u"next_day_zohr_box")
        self.next_day_zohr_box.setGeometry(QRect(240, 40, 111, 71))
        self.next_day_zohr = QLabel(self.next_day_zohr_box)
        self.next_day_zohr.setObjectName(u"next_day_zohr")
        self.next_day_zohr.setGeometry(QRect(0, 0, 111, 31))
        self.next_day_zohr.setFont(font9)
        self.next_day_zohr_time = QLabel(self.next_day_zohr_box)
        self.next_day_zohr_time.setObjectName(u"next_day_zohr_time")
        self.next_day_zohr_time.setGeometry(QRect(0, 30, 111, 41))
        self.next_day_zohr_time.setFont(font9)
        self.next_day_shroq_box = QGroupBox(self.next_day_prayers_box)
        self.next_day_shroq_box.setObjectName(u"next_day_shroq_box")
        self.next_day_shroq_box.setGeometry(QRect(120, 40, 121, 71))
        self.next_day_shroq = QLabel(self.next_day_shroq_box)
        self.next_day_shroq.setObjectName(u"next_day_shroq")
        self.next_day_shroq.setGeometry(QRect(0, 0, 121, 31))
        self.next_day_shroq.setFont(font9)
        self.next_day_shroq_time = QLabel(self.next_day_shroq_box)
        self.next_day_shroq_time.setObjectName(u"next_day_shroq_time")
        self.next_day_shroq_time.setGeometry(QRect(0, 30, 121, 41))
        self.next_day_shroq_time.setFont(font9)
        self.next_day_fajr_box = QGroupBox(self.next_day_prayers_box)
        self.next_day_fajr_box.setObjectName(u"next_day_fajr_box")
        self.next_day_fajr_box.setGeometry(QRect(0, 40, 121, 71))
        self.next_day_fajr = QLabel(self.next_day_fajr_box)
        self.next_day_fajr.setObjectName(u"next_day_fajr")
        self.next_day_fajr.setGeometry(QRect(0, 0, 81, 31))
        self.next_day_fajr.setFont(font9)
        self.next_day_fajr_time = QLabel(self.next_day_fajr_box)
        self.next_day_fajr_time.setObjectName(u"next_day_fajr_time")
        self.next_day_fajr_time.setGeometry(QRect(0, 30, 121, 41))
        self.next_day_fajr_time.setFont(font9)
        self.next_day_isha_box = QGroupBox(self.next_day_prayers_box)
        self.next_day_isha_box.setObjectName(u"next_day_isha_box")
        self.next_day_isha_box.setGeometry(QRect(590, 40, 121, 71))
        self.next_day_isha = QLabel(self.next_day_isha_box)
        self.next_day_isha.setObjectName(u"next_day_isha")
        self.next_day_isha.setGeometry(QRect(0, 0, 111, 31))
        self.next_day_isha.setFont(font9)
        self.next_day_isha_time = QLabel(self.next_day_isha_box)
        self.next_day_isha_time.setObjectName(u"next_day_isha_time")
        self.next_day_isha_time.setGeometry(QRect(0, 30, 121, 41))
        self.next_day_isha_time.setFont(font9)
        self.zohr_box = QGroupBox(self.centralwidget)
        self.zohr_box.setObjectName(u"zohr_box")
        self.zohr_box.setGeometry(QRect(720, 160, 301, 81))
        self.current_day_zohr = QLabel(self.zohr_box)
        self.current_day_zohr.setObjectName(u"current_day_zohr")
        self.current_day_zohr.setGeometry(QRect(0, 0, 181, 41))
        font10 = QFont()
        font10.setPointSize(25)
        font10.setBold(True)
        self.current_day_zohr.setFont(font10)
        self.current_day_zohr_time = QLabel(self.zohr_box)
        self.current_day_zohr_time.setObjectName(u"current_day_zohr_time")
        self.current_day_zohr_time.setGeometry(QRect(0, 40, 301, 41))
        self.current_day_zohr_time.setFont(font8)
        self.shroq_box = QGroupBox(self.centralwidget)
        self.shroq_box.setObjectName(u"shroq_box")
        self.shroq_box.setGeometry(QRect(720, 80, 301, 81))
        self.current_day_shroq = QLabel(self.shroq_box)
        self.current_day_shroq.setObjectName(u"current_day_shroq")
        self.current_day_shroq.setGeometry(QRect(0, 0, 221, 41))
        self.current_day_shroq.setFont(font10)
        self.current_day_shroq_time = QLabel(self.shroq_box)
        self.current_day_shroq_time.setObjectName(u"current_day_shroq_time")
        self.current_day_shroq_time.setGeometry(QRect(0, 40, 301, 41))
        self.current_day_shroq_time.setFont(font8)
        self.asr_box = QGroupBox(self.centralwidget)
        self.asr_box.setObjectName(u"asr_box")
        self.asr_box.setGeometry(QRect(720, 240, 301, 81))
        self.current_day_asr = QLabel(self.asr_box)
        self.current_day_asr.setObjectName(u"current_day_asr")
        self.current_day_asr.setGeometry(QRect(0, 0, 181, 41))
        self.current_day_asr.setFont(font10)
        self.current_day_asr_time = QLabel(self.asr_box)
        self.current_day_asr_time.setObjectName(u"current_day_asr_time")
        self.current_day_asr_time.setGeometry(QRect(0, 40, 301, 41))
        self.current_day_asr_time.setFont(font8)
        self.magrb_box = QGroupBox(self.centralwidget)
        self.magrb_box.setObjectName(u"magrb_box")
        self.magrb_box.setGeometry(QRect(720, 320, 301, 81))
        self.current_day_magrb = QLabel(self.magrb_box)
        self.current_day_magrb.setObjectName(u"current_day_magrb")
        self.current_day_magrb.setGeometry(QRect(0, 0, 221, 41))
        self.current_day_magrb.setFont(font10)
        self.current_day_magrb_time = QLabel(self.magrb_box)
        self.current_day_magrb_time.setObjectName(u"current_day_magrb_time")
        self.current_day_magrb_time.setGeometry(QRect(0, 40, 301, 41))
        self.current_day_magrb_time.setFont(font8)
        self.isha_box = QGroupBox(self.centralwidget)
        self.isha_box.setObjectName(u"isha_box")
        self.isha_box.setGeometry(QRect(720, 400, 301, 81))
        self.current_day_isha = QLabel(self.isha_box)
        self.current_day_isha.setObjectName(u"current_day_isha")
        self.current_day_isha.setGeometry(QRect(0, 0, 181, 41))
        self.current_day_isha.setFont(font10)
        self.current_day_isha_time = QLabel(self.isha_box)
        self.current_day_isha_time.setObjectName(u"current_day_isha_time")
        self.current_day_isha_time.setGeometry(QRect(0, 40, 301, 41))
        self.current_day_isha_time.setFont(font8)
        MainWindow.setCentralWidget(self.centralwidget)
        self.current_time.raise_()
        self.current_location.raise_()
        self.rest_time.raise_()
        self.last_updated_descrition.raise_()
        self.last_updated_date.raise_()
        self.last_updated_time.raise_()
        self.fajr_box.raise_()
        self.next_day_prayers_box.raise_()
        self.zohr_box.raise_()
        self.shroq_box.raise_()
        self.asr_box.raise_()
        self.magrb_box.raise_()
        self.isha_box.raise_()
        self.current_date.raise_()
        self.rest_time_description.raise_()
        self.refresh_button.raise_()
        self.led_sign.raise_()
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1024, 37))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.current_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.current_date.setText(QCoreApplication.translate("MainWindow", u"DD.MM.YY", None))
        self.current_location.setText(QCoreApplication.translate("MainWindow", u"Location", None))
        self.rest_time_description.setText(QCoreApplication.translate("MainWindow", u"Verbleibende Zeit bis zum n\u00e4chsten Gebet", None))
        self.rest_time.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.last_updated_descrition.setText(QCoreApplication.translate("MainWindow", u"Letzte Aktualisierung:", None))
        self.last_updated_date.setText(QCoreApplication.translate("MainWindow", u"DD:MM:YY", None))
        self.last_updated_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.led_sign.setText(QCoreApplication.translate("MainWindow", u":", None))
        self.refresh_button.setText(QCoreApplication.translate("MainWindow", u"Aktualisieren", None))
        self.fajr_box.setTitle("")
        self.current_day_fajr.setText(QCoreApplication.translate("MainWindow", u"FAJR", None))
        self.current_day_fajr_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.next_day_prayers_box.setTitle("")
        self.next_day_description.setText(QCoreApplication.translate("MainWindow", u"Gebetszeiten f\u00fcr den", None))
        self.next_day_date.setText(QCoreApplication.translate("MainWindow", u"DD.MM:YY", None))
        self.next_day_magrb_box.setTitle("")
        self.next_day_magrb.setText(QCoreApplication.translate("MainWindow", u"MAGHRIB", None))
        self.next_day_magrb_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.next_day_asr_box.setTitle("")
        self.next_day_asr.setText(QCoreApplication.translate("MainWindow", u"ASR", None))
        self.next_day_asr_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.next_day_zohr_box.setTitle("")
        self.next_day_zohr.setText(QCoreApplication.translate("MainWindow", u"DHUHR", None))
        self.next_day_zohr_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.next_day_shroq_box.setTitle("")
        self.next_day_shroq.setText(QCoreApplication.translate("MainWindow", u"SHURUQ", None))
        self.next_day_shroq_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.next_day_fajr_box.setTitle("")
        self.next_day_fajr.setText(QCoreApplication.translate("MainWindow", u"FAJR", None))
        self.next_day_fajr_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.next_day_isha_box.setTitle("")
        self.next_day_isha.setText(QCoreApplication.translate("MainWindow", u"ISHA", None))
        self.next_day_isha_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.zohr_box.setTitle("")
        self.current_day_zohr.setText(QCoreApplication.translate("MainWindow", u"DHUHR", None))
        self.current_day_zohr_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.shroq_box.setTitle("")
        self.current_day_shroq.setText(QCoreApplication.translate("MainWindow", u"SHURUQ", None))
        self.current_day_shroq_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.asr_box.setTitle("")
        self.current_day_asr.setText(QCoreApplication.translate("MainWindow", u"ASR", None))
        self.current_day_asr_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.magrb_box.setTitle("")
        self.current_day_magrb.setText(QCoreApplication.translate("MainWindow", u"MAGHRIB", None))
        self.current_day_magrb_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
        self.isha_box.setTitle("")
        self.current_day_isha.setText(QCoreApplication.translate("MainWindow", u"ISHA", None))
        self.current_day_isha_time.setText(QCoreApplication.translate("MainWindow", u"00:00", None))
    # retranslateUi

