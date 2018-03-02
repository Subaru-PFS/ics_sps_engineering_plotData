#!/usr/bin/env python
# encoding: utf-8


import pickle
import os
from functools import partial

from PyQt5.QtWidgets import QGroupBox, QFileDialog, QMainWindow, QAction, QMessageBox

from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
import sps_engineering_Lib_dataQuery as dataQuery
import sps_engineering_plotData.img as imgFolder
from sps_engineering_plotData.widgets import PIcon
from sps_engineering_plotData.tabwidget import PTabWidget


class MainWindow(QMainWindow):
    cuArms = {"_r1__": "SM1 RCU",
              "_b1__": "SM1 BCU",
              "_r0__": "Thermal RCU",
              }

    def __init__(self, ip, port):
        super(MainWindow, self).__init__()

        self.configPath = '%s/config/' % os.path.dirname(dataQuery.__file__)
        self.imgPath = '%s/' % os.path.dirname(imgFolder.__file__)

        self.db = DatabaseManager(ip, port)
        self.db.init()

        self.getIcons()
        self.getWidgets()

        self.resize(1024, 768)
        self.move(300, 300)
        self.setWindowTitle('ics_sps_engineering_plotData')
        self.showMaximized()
        self.show()

    def getIcons(self):
        self.icon_arrow_left = PIcon(self.imgPath + 'arrow_left.png')
        self.icon_arrow_right = PIcon(self.imgPath + 'arrow_right.png')
        self.icon_vcursor = PIcon(self.imgPath + 'xy2.png')
        self.icon_vcursor_on = PIcon(self.imgPath + 'xy2_on.png')
        self.icon_fit = PIcon(self.imgPath + 'infini.png')
        self.icon_calendar = PIcon(self.imgPath + 'calendar.png')
        self.icon_delete = PIcon(self.imgPath + 'delete.png')

    def getWidgets(self):

        self.tabWidget = PTabWidget(self)

        self.getMenu()
        self.setCentralWidget(self.tabWidget)

    def getMenu(self):

        self.menubar = self.menuBar()
        self.database_action = QAction('Database', self)
        self.curves_action = QAction('Update Configuration', self)
        self.new_tab_action = QAction('Open a new tab', self)
        self.load_layout_action = QAction('Load Layout', self)
        self.save_layout_action = QAction('Save current Layout', self)

        self.about_action = QAction('About', self)

        self.new_tab_action.triggered.connect(self.tabWidget.dialogTab)
        self.about_action.triggered.connect(
            partial(self.showInformation, "ics_sps_engineering_plotData made for PFS by ALF"))

        self.load_layout_action.triggered.connect(self.loadLayout)
        self.save_layout_action.triggered.connect(self.saveLayout)

        self.WindowsMenu = self.menubar.addMenu('&Windows')
        self.WindowsMenu.addAction(self.new_tab_action)
        self.WindowsMenu.addAction(self.load_layout_action)
        self.WindowsMenu.addAction(self.save_layout_action)

        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)

    def loadLayout(self):
        (fname, fmt) = QFileDialog.getOpenFileName(self, 'Open file',
                                                   self.os_path.split('ics_sps_engineering_plotData')[0])
        if fname:
            with open(fname, 'r') as fichier:
                unpickler = pickle.Unpickler(fichier)
                customLayout = unpickler.load()

            for savedTab in customLayout:
                tab = self.addTab(savedTab["name"])
                for graph in savedTab["graphs"]:
                    plotWindow = tab.addGraph()
                    for curveName, tableName in graph:
                        tabWidget = plotWindow.scrollArea.widget()
                        allTabActor = [tabWidget.widget(i) for i in range(tabWidget.count())]
                        allgroupbox = []
                        for l in [t.clayout for t in allTabActor]:
                            allgroupbox += self.getListWidget(l)

                        for groupbox in allgroupbox:
                            if type(groupbox) == QGroupBox:
                                for widget in self.getListWidget(groupbox.layout()):
                                    if hasattr(widget, "ident") and widget.ident == tableName + curveName:
                                        widget.setCheckState(2)

    def saveLayout(self):

        customLayout = []
        for i in range(self.tab_widget.count()):
            name = self.tab_widget.tabText(i)
            dict = {"name": str(name)}
            plotWindows = self.tab_widget.widget(i).getPlotWindow()
            inter = []
            for plotWindow in plotWindows:
                inter.append([(curve.label, curve.tableName) for curve in plotWindow.graph.dictofline.itervalues()])
            dict["graphs"] = inter
            customLayout.append(dict)

        (fname, fmt) = QFileDialog.getSaveFileName(self, 'Save file',
                                                   self.os_path.split('ics_sps_engineering_plotData')[0])
        if fname:
            with open(fname, 'w') as fichier:
                pickler = pickle.Pickler(fichier)
                pickler.dump(customLayout)

    def getListWidget(self, layout):
        return [layout.itemAt(i).widget() for i in range(layout.count())]

    def showError(self, error):

        reply = QMessageBox.critical(self, 'Exception', error, QMessageBox.Ok)

    def showInformation(self, information):
        reply = QMessageBox.information(self, 'Message', information, QMessageBox.Ok)

    def getNumdate(self):
        return self.calendar.mydate_num

    def cleanSpace(self, tab):
        return [t.strip() for t in tab]
