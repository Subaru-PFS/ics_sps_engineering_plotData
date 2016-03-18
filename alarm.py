from functools import partial
import datetime

from PyQt5.QtWidgets import QGridLayout, QPushButton, QLabel, QMessageBox, QWidget
from PyQt5.QtCore import QTimer


class alarmChecker(QWidget):
    def __init__(self, parent):
        super(alarmChecker, self).__init__()
        self.parent = parent
        self.getAlarm(["pressure", "turbo", "gatevalve", "cooler"])
        self.getTimeout()
        self.getTimer()
        self.setLayout(self.alarm_layout)

    def getTimeout(self):
        self.timeout_limit = 90
        self.list_timeout = []
        self.last_date = {}
        self.last_time = {}
        for key, value in self.parent.device_dict.iteritems():
            self.last_date[key] = 0
            self.last_time[key] = datetime.datetime.now()

    def getTimer(self):

        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(2000, partial(self.showTimeout, 0))
        self.checker_timeout = QTimer(self)
        self.checker_timeout.setInterval(15000)
        self.checker_timeout.timeout.connect(self.checkTimeout)
        self.checker_timeout.start()

    def showTimeout(self, i):
        if self.list_timeout:
            if i < len(self.list_timeout):
                self.label_acq.setText("TIME OUT ON %s" % self.list_timeout[i])
                self.setColor("QLabel", self.label_acq, "red")
                i += 1
            else:
                i = 0
        else:
            self.label_acq.setText("ACQUISITION")
            self.setColor("QLabel", self.label_acq, "green")

        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(2000, partial(self.showTimeout, i))

    def checkTimeout(self):
        for key, value in self.parent.device_dict.iteritems():
            date, [id] = self.parent.db.getLastData(key, "id")
            if date not in [-1, -2, -3, -4]:
                if date != self.last_date[key]:
                    self.last_time[key] = datetime.datetime.now()
                    self.last_date[key] = date
                    if key in self.list_timeout:
                        self.list_timeout.remove(key)
                else:
                    if (datetime.datetime.now() - self.last_time[key]).total_seconds() > self.timeout_limit:
                        if key not in self.list_timeout:
                            self.list_timeout.append(key)
            else:
                self.parent.showError(date)

    def getAlarm(self, devices):

        self.alarm_layout = QGridLayout()
        self.label_acq = QLabel("ACQUISITION")
        self.alarm_layout.addWidget(self.label_acq, 0, 0, 1, 2)
        self.setColor("QLabel", self.label_acq, "green")

        for i, device in enumerate(devices):
            button = QPushButton(device.upper())
            self.setColor("QPushButton", button, "green")
            button.clicked.connect(partial(self.showWarning, "msg_%s" % device))
            self.alarm_layout.addWidget(button, 0, i + 2, 1, 1)
            setattr(self, "alarm_%s" % device, button)

        self.watcher_alarm = QTimer(self)
        self.watcher_alarm.setInterval(5000)
        self.watcher_alarm.timeout.connect(self.checkCriticalValue)
        self.watcher_alarm.start()

    def checkCriticalValue(self):
        self.checkPressure()
        self.checkTurbo()
        self.checkGatevalve()
        self.checkCooler()

    def checkPressure(self):
        pressure_date, [pressure_val] = self.parent.db.getLastData("xcu_r1__" + "pressure", "val1")
        if float(pressure_val) > 1e-4:
            self.msg_pressure = " Warning ! PRESSURE : %0.3e Torr is above 1e-4 Torr" % pressure_val
            self.setColor("QPushButton", self.alarm_pressure, "red")
        else:
            self.msg_pressure = "Pressure OK"
            self.setColor("QPushButton", self.alarm_pressure, "green")

    def checkTurbo(self):
        turbospeed_date, [turbospeed_val] = self.parent.db.getLastData("xcu_r1__" + "turbospeed", "val1")
        if turbospeed_val < 90000:
            self.msg_turbo = " Warning ! TURBO SPEED is LOW : %i on 90000 RPM" % int(turbospeed_val)
            self.setColor("QPushButton", self.alarm_turbo, "red")
        else:
            self.msg_turbo = "Turbo OK"
            self.setColor("QPushButton", self.alarm_turbo, "green")

    def checkGatevalve(self):
        gatevalve_date, [gatevalve_val] = self.parent.db.getLastData("xcu_r1__" + "gatevalve", "val1")
        if gatevalve_val != 253:
            self.msg_gatevalve = " Warning ! GATEVALVE is CLOSED"
            self.setColor("QPushButton", self.alarm_gatevalve, "red")
        else:
            self.msg_gatevalve = "Gatevalve OK"
            self.setColor("QPushButton", self.alarm_gatevalve, "green")

    def checkCooler(self):
        coolerPower_date, [coolerPower_val] = self.parent.db.getLastData("xcu_r1__" + "coolertemps", "power")
        if coolerPower_val < 70 or coolerPower_val > 245:
            self.msg_cooler = " Warning ! COOLER POWER : % i W  Out of range 70-245 W" % int(coolerPower_val)
            self.setColor("QPushButton", self.alarm_cooler, "red")
        else:
            self.msg_cooler = "Cooler OK"
            self.setColor("QPushButton", self.alarm_cooler, "green")

    def setColor(self, type, widget, color):
        if type == "QLabel":
            widget.setStyleSheet(
                "%s { background-color : %s; color : white; qproperty-alignment: AlignCenter; font: 15pt;}" % (
                    type, color))
        else:
            widget.setStyleSheet("%s { background-color : %s; color : white; font: 15pt;}" % (type, color))

    def showWarning(self, attr):
        reply = QMessageBox.warning(self, 'Message', str(getattr(self, attr)), QMessageBox.Ok)
