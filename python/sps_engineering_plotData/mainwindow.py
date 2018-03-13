#!/usr/bin/env python
# encoding: utf-8


import os
from functools import partial

import sps_engineering_plotData as plotData
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox
from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
from sps_engineering_plotData.tabwidget import PTabWidget
from sps_engineering_plotData.widgets import PIcon


class MainWindow(QMainWindow):
    cuArms = {'_r1__': 'SM1 RCU',
              '_b1__': 'SM1 BCU',
              '_r0__': 'Thermal RCU',
              }

    def __init__(self, ip, port):
        super(MainWindow, self).__init__()

        self.imgPath = os.path.abspath(os.path.join(os.path.dirname(plotData.__file__), '../..', 'img'))
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
        self.icon_arrow_left = PIcon('%s/%s' % (self.imgPath, 'arrow_left.png'))
        self.icon_arrow_right = PIcon('%s/%s' % (self.imgPath, 'arrow_right.png'))
        self.icon_vcursor = PIcon('%s/%s' % (self.imgPath, 'xy2.png'))
        self.icon_vcursor_on = PIcon('%s/%s' % (self.imgPath, 'xy2_on.png'))
        self.icon_fit = PIcon('%s/%s' % (self.imgPath, 'infini.png'))
        self.icon_calendar = PIcon('%s/%s' % (self.imgPath, 'calendar.png'))
        self.icon_delete = PIcon('%s/%s' % (self.imgPath, 'delete.png'))
        self.icon_refresh = PIcon('%s/%s' % (self.imgPath, 'refresh.png'))

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
            partial(self.showInformation, 'ics_sps_engineering_plotData made for PFS by ALF'))

        self.load_layout_action.triggered.connect(self.loadLayout)
        self.save_layout_action.triggered.connect(self.saveLayout)

        self.WindowsMenu = self.menubar.addMenu('&Windows')
        self.WindowsMenu.addAction(self.new_tab_action)
        self.WindowsMenu.addAction(self.load_layout_action)
        self.WindowsMenu.addAction(self.save_layout_action)

        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)

    def loadLayout(self):
        pass
        # (fname, fmt) = QFileDialog.getOpenFileName(self, 'Open file',
        #                                            self.os_path.split('ics_sps_engineering_plotData')[0])
        # if fname:
        #     with open(fname, 'r') as fichier:
        #         unpickler = pickle.Unpickler(fichier)
        #         customLayout = unpickler.load()

    def saveLayout(self):
        pass

    def showError(self, error):
        reply = QMessageBox.critical(self, 'Exception', error, QMessageBox.Ok)

    def showInformation(self, information):
        reply = QMessageBox.information(self, 'Message', information, QMessageBox.Ok)
