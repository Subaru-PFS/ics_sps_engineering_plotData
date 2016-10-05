#!/usr/bin/env python
# encoding: utf-8


import matplotlib
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QInputDialog, \
    QMessageBox

from myqdockwidget import myQDockWidget

matplotlib.use("Qt5Agg")

from functools import partial

from ics_sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
import ConfigParser
import os
from mycalendar import Calendar
from alarm import alarmChecker
from tab import Tab
from matplotlib import rcParams
import datetime as dt

rcParams.update({'figure.autolayout': True})


class MainWindow(QMainWindow):
    def __init__(self, os_path, ip, port):
        super(MainWindow, self).__init__()

        self.os_path = os_path
        self.config_path = os_path.split('ics_sps_engineering_plotData')[
                               0] + 'ics_sps_engineering_Lib_dataQuery/config/'
        self.path_img = self.os_path + "/img/"

        self.readCfg(self.config_path)
        self.db = DatabaseManager(ip, port)
        no_err = self.db.initDatabase()
        if no_err != -1:
            self.getIcons()
            self.getWidgets()
        else:
            self.showError(no_err)

        self.width = 1024
        self.height = 768
        self.center = [300, 300]
        self.currWidget = 0
        self.title = "AIT-PFS Monitoring CU"
        self.resize(self.width, self.height)
        self.move(self.center[0], self.center[1])
        self.setWindowTitle(self.title)
        self.showMaximized()
        self.show()

    def getIcons(self):

        arrow_left = QPixmap()
        arrow_right = QPixmap()
        arrow_left.load(self.path_img + 'arrow_left.png')
        arrow_right.load(self.path_img + 'arrow_right.png')
        self.icon_arrow_left = QIcon(arrow_left)
        self.icon_arrow_right = QIcon(arrow_right)
        icon_math = QPixmap()
        icon_math.load(self.path_img + 'xy2.png')
        icon_math_on = QPixmap()
        icon_math_on.load(self.path_img + 'xy2_on.png')
        self.icon_vcursor = QIcon(icon_math)
        self.icon_vcursor_on = QIcon(icon_math_on)
        icon_fit = QPixmap()
        icon_fit.load(self.path_img + 'infini.png')
        self.icon_fit = QIcon(icon_fit)

    def getWidgets(self):

        self.tab_widget = QTabWidget()
        self.tab_widget.tabCloseRequested.connect(self.delTab)
        self.tab_widget.currentChanged.connect(self.changeTab)
        self.tab_widget.setTabsClosable(True)
        self.getdockCalendar()
        self.getdockAlarm()
        self.getMenu()
        self.addDockWidget(Qt.TopDockWidgetArea, self.qdockalarm)
        self.setCentralWidget(self.tab_widget)

    def getMenu(self):

        self.menubar = self.menuBar()
        self.database_action = QAction('Database', self)
        self.curves_action = QAction('Update Configuration', self)
        self.new_tab_action = QAction('Open a new tab', self)
        self.about_action = QAction('About', self)

        self.curves_action.triggered.connect(self.setNewConfig)
        self.new_tab_action.triggered.connect(self.addTab)
        self.database_action.triggered.connect(self.calendar.show)
        self.about_action.triggered.connect(
            partial(self.showInformation, "PlotData 0.8 working with lib_DataQuery 0.7\n\r made for PFS by ALF"))

        self.WindowsMenu = self.menubar.addMenu('&Windows')
        self.WindowsMenu.addAction(self.new_tab_action)
        self.configurationMenu = self.menubar.addMenu('&Configuration')
        self.configurationMenu.addAction(self.database_action)
        self.configurationMenu.addAction(self.curves_action)
        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)

    def getdockCalendar(self):

        self.calendar = Calendar(self)

    def getdockAlarm(self):
        self.qdockalarm_widget = alarmChecker(parent=self)
        self.qdockalarm = myQDockWidget()

        self.qdockalarm.setWidget(self.qdockalarm_widget)

    def readCfg(self, path, last=True):
        res = []
        all_file = next(os.walk(path))[-1]
        for f in all_file:
            config = ConfigParser.ConfigParser()
            config.readfp(open(path + f))
            try:
                date = config.get('config_date', 'date')
                res.append((f, dt.datetime.strptime(date, "%d/%m/%Y")))
            except ConfigParser.NoSectionError:
                pass
        config = ConfigParser.ConfigParser()
        if last:
            res.sort(key=lambda tup: tup[1])
            config.readfp(open(path + res[-1][0]))
        else:
            res2 = []
            for f, datetime in res:
                if self.calendar.mydatetime > datetime:
                    res2.append((f, self.calendar.mydatetime - datetime))
            if res2:
                res2.sort(key=lambda tup: tup[1])
                config.readfp(open(path + res2[0][0]))
            else:
                res.sort(key=lambda tup: tup[1])
                config.readfp(open(path + res[0][0]))

        self.device_dict = {}
        for a in config.sections():
            if a != 'config_date':
                inter = {}
                for b in config.options(a):
                    if b == "label_device":
                        self.device_dict[a] = {"label_device": config.get(a, b)}
                    else:
                        inter[b] = config.get(a, b).split(',')
                        inter[b] = self.cleanSpace(inter[b])

                for keys, types, labels, units, ylabels in zip(inter["key"], inter["type"], inter["label"],
                                                               inter["unit"],
                                                               inter["ylabel"]):
                    self.device_dict[a][keys] = {}
                    self.device_dict[a][keys]["type"] = types
                    self.device_dict[a][keys]["label"] = labels
                    self.device_dict[a][keys]["unit"] = units
                    self.device_dict[a][keys]["ylabel"] = ylabels

    def setNewConfig(self):
        self.readCfg(self.config_path)
        self.qdockalarm_widget.getTimeout()
        self.showInformation("New configuration loaded")

    def addTab(self):

        text, ok = QInputDialog.getText(self, 'Name your tab', 'Name')
        if ok:
            name = str(text)
            widget = Tab(self)
            self.tab_widget.addTab(widget, name)
            self.tab_widget.setCurrentWidget(widget)

    def changeTab(self):
        currWidget = self.tab_widget.currentWidget()
        if self.currWidget != currWidget:
            if type(self.currWidget)==Tab:
                self.currWidget.goActive(False)
            if type(currWidget)==Tab:
                currWidget.goActive(True)
            self.currWidget = currWidget

    def delTab(self, k):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to close this window?", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tab_widget.removeTab(k)

    def showError(self, nb_error):
        error_code = {-1: "The database is unreachable, check your network and your configuration",
                      -2: "They're not such columns / rows in your database", -3: "Bad format date",
                      -4: "No data to display", -5: "network lost"}
        reply = QMessageBox.critical(self, 'Message', error_code[nb_error], QMessageBox.Ok)

    def showInformation(self, information):
        reply = QMessageBox.information(self, 'Message', information, QMessageBox.Ok)

    def getNumdate(self):
        return self.calendar.mydate_num

    def cleanSpace(self, tab):
        for i, s in enumerate(tab):
            if tab[i][0] == ' ':
                tab[i] = tab[i][1:]
            if tab[i][-1] == ' ':
                tab[i] = tab[i][:-1]

        return tab
