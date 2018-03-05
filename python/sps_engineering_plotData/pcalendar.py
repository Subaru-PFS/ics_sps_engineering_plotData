from functools import partial
import datetime as dt

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
    QPushButton, QGroupBox, QCheckBox, QGridLayout, QLineEdit, QCalendarWidget, QLabel, QSpinBox

from PyQt5.QtCore import QDate, Qt

from sps_engineering_Lib_dataQuery.confighandler import loadConf
from sps_engineering_Lib_dataQuery.dates import str2date


class Calendar(QWidget):
    def __init__(self, dateplot):
        self.dateplot = dateplot
        QWidget.__init__(self)
        self.layout = QHBoxLayout()

        self.cal = QCalendarWidget(self)
        self.cal.setGridVisible(True)
        self.cal.clicked[QDate].connect(self.showDate)
        self.cal.activated.connect(self.hide)

        gbCalendar = QGroupBox('Calendar')
        gbDataset = QGroupBox('Dataset')
        gbCalendar.setStyleSheet('QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}')
        gbDataset.setStyleSheet('QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}')

        self.checkboxRealTime = QCheckBox('Real-time')
        self.checkboxPastRuns = QCheckBox('Archived')
        self.spinboxDays = QSpinBox()
        self.spinboxDays.setRange(1, 100)
        self.spinboxDays.setValue(1)
        self.checkboxRealTime.stateChanged.connect(self.realtime)
        self.checkboxPastRuns.stateChanged.connect(self.archivedData)

        self.checkboxRealTime.setCheckState(2)
        layoutDataset = QGridLayout()
        layoutDataset.addWidget(self.checkboxRealTime, 0, 0, 2, 1)
        layoutDataset.addWidget(QLabel('Duration (Days)'), 2, 1, 1, 1)
        layoutDataset.addWidget(self.checkboxPastRuns, 3, 0, 1, 1)
        layoutDataset.addWidget(self.spinboxDays, 3, 1, 1, 1)

        layoutCalendar = QVBoxLayout()
        layoutCalendar.addWidget(self.cal)

        gbCalendar.setLayout(layoutCalendar)
        gbDataset.setLayout(layoutDataset)

        self.layout.addWidget(gbCalendar)
        self.layout.addWidget(gbDataset)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Calendar')
        self.setWindowModality(Qt.WindowModal)

    def showDate(self, date=None):
        date = self.cal.selectedDate() if date is None else date

        date = dt.datetime.combine(date.toPyDate(), dt.datetime.min.time())
        self.dateplot.updateDate(date)

    def closeEvent(self, event):
        self.hide()
        try:
            event.accept()
        except AttributeError:
            pass

    def realtime(self):
        state = 0 if self.checkboxRealTime.isChecked() else 2
        self.checkboxPastRuns.setCheckState(state)

    def archivedData(self):
        state = 0 if self.checkboxPastRuns.isChecked() else 2
        self.checkboxRealTime.setCheckState(state)


class DatePlot(QWidget):
    def __init__(self, plotWindow):
        QWidget.__init__(self)
        self.plotWindow = plotWindow
        self.dateStr = QLineEdit()
        self.dateStr.textChanged.connect(self.loadConf)
        self.cal = Calendar(self)
        self.cal.showDate()

        self.choseDate = QPushButton(self)
        self.choseDate.setIcon(self.mainwindow.icon_calendar)
        self.choseDate.clicked.connect(partial(self.cal.setVisible, True))

        self.layout = QGridLayout()
        self.layout.addWidget(self.choseDate, 0, 0)
        self.layout.addWidget(self.dateStr, 0, 1, 1, 5)

        self.setLayout(self.layout)

    @property
    def mainwindow(self):
        return self.plotWindow.mainwindow

    @property
    def realtime(self):
        return self.cal.checkboxRealTime.isChecked()

    @property
    def dateEnd(self):
        return self.datetime + dt.timedelta(days=self.cal.spinboxDays.value())

    def updateDate(self, datetime):
        self.dateStr.setText(datetime.isoformat()[:-3])

    def loadConf(self):
        datestr = self.dateStr.text()
        if len(datestr) in [10, 16]:
            self.datetime = str2date(datestr)
            self.config = loadConf(self.dateStr.text())
            self.plotWindow.constructGroupbox(self.config)
        else:
            pass
