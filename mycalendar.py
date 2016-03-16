#!/usr/bin/env python
# encoding: utf-8
import datetime

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QCalendarWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, \
    QCheckBox, QSpinBox, QGridLayout


class Calendar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.initUI()
        self.defaultDate()

    def initUI(self):

        self.layout = QHBoxLayout()

        self.groupboxCal = QGroupBox("Calendar")
        self.groupboxDataset = QGroupBox("Dataset")
        self.groupboxCal.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")
        self.groupboxDataset.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")
        self.layoutCal = QVBoxLayout()
        self.layoutDataset = QGridLayout()
        self.groupboxCal.setLayout(self.layoutCal)
        self.groupboxDataset.setLayout(self.layoutDataset)

        self.layout_but = QHBoxLayout()
        self.cal = QCalendarWidget(self)
        self.cal.setGridVisible(True)
        self.cal.clicked[QDate].connect(self.showDate)
        self.lbl = QLabel(self)
        date = self.cal.selectedDate()

        self.lbl.setText(date.toString())
        self.buttonSave = QPushButton("Save")
        self.buttonSave.clicked.connect(self.closeEvent)

        self.checkboxRealTime = QCheckBox("Real Time Data Monitoring")
        self.checkboxPastRuns = QCheckBox("Visualize Past Runs")
        self.spinboxDays = QSpinBox()
        self.spinboxDays.setRange(1, 100)
        self.spinboxDays.setValue(1)
        self.checkboxRealTime.stateChanged.connect(self.realTimeMode)
        self.checkboxPastRuns.stateChanged.connect(self.oldData)

        self.checkboxRealTime.setCheckState(2)

        self.layoutDataset.addWidget(self.checkboxRealTime, 0, 0, 2, 1)

        self.layoutDataset.addWidget(QLabel("Duration (Days)"), 2, 1, 1, 1)
        self.layoutDataset.addWidget(self.checkboxPastRuns, 3, 0, 1, 1)
        self.layoutDataset.addWidget(self.spinboxDays, 3, 1, 1, 1)

        self.layoutCal.addWidget(self.cal)
        self.layout_but.addWidget(self.lbl)
        self.layout_but.addWidget(self.buttonSave)
        self.layoutCal.addLayout(self.layout_but)

        self.layout.addWidget(self.groupboxCal)
        self.layout.addWidget(self.groupboxDataset)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Calendar')
        self.setWindowModality(Qt.WindowModal)
        self.show()

    def defaultDate(self):
        mydate = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                   datetime.datetime.today().day)
        self.mydate_num = self.parent.db.convertTimetoAstro(mydate.strftime("%d/%m/%Y %H:%M:%S"))

    def getChosenDate(self):
        mydate = datetime.datetime.combine(self.cal.selectedDate().toPyDate(), datetime.datetime.min.time())
        self.mydate_num = self.parent.db.convertTimetoAstro(mydate.strftime("%d/%m/%Y %H:%M:%S"))

    def showDate(self, date):

        self.lbl.setText(date.toString())

    def realTimeMode(self):

        if self.checkboxRealTime.isChecked():
            self.parent.dataset = "real_time"
            self.checkboxPastRuns.setCheckState(0)
        else:
            self.checkboxPastRuns.setCheckState(2)

    def oldData(self):
        if self.checkboxPastRuns.isChecked():
            self.parent.dataset = "past_run"
            self.checkboxRealTime.setCheckState(0)
        else:
            self.checkboxRealTime.setCheckState(2)

    def closeEvent(self, event):
        self.hide()
        self.getChosenDate()
        try:
            event.accept()
        except AttributeError:
            pass
