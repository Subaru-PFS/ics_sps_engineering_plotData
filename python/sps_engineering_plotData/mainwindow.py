#!/usr/bin/env python
# encoding: utf-8


import importlib
import os
from functools import partial

import sps_engineering_Lib_dataQuery.confighandler as confighandler
import sps_engineering_plotData as plotData
import yaml
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QFileDialog
from sps_engineering_plotData.archiver import ArchiverHandler
from sps_engineering_plotData.tabwidget import PTabWidget
from sps_engineering_plotData.widgets import PIcon


class MainWindow(QMainWindow):

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__()

        self.imgPath = os.path.abspath(os.path.join(os.path.dirname(plotData.__file__), '../..', 'img'))

        self.cuArms = self.getCuArms()
        self.getIcons()
        self.getWidgets()

        self.resize(1024, 768)
        self.move(300, 300)
        self.setWindowTitle('ics_sps_engineering_plotData')
        #self.showMaximized()
        self.show()
        self.db = ArchiverHandler(**kwargs)
        try:
            self.db.connect()
        except Exception as e:
            self.showError(str(e))

    def getCuArms(self):
        cuArms = []
        for specId in [1, 2, 3, 4]:
            cuArms += [('_%s%d__' % (arm, specId), 'SM%d %sCU' % (specId, arm.upper())) for arm in ['r', 'b', 'n']]
        return dict(cuArms)

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
        importlib.reload(confighandler)
        failed = []

        filepath, fmt = QFileDialog.getOpenFileName(self, 'Open File', '/home/', "(*.yaml)")
        if not filepath:
            return

        try:
            with open(os.path.expandvars(filepath), 'r') as cfgFile:
                layout = yaml.load(cfgFile, Loader=yaml.FullLoader)

        except PermissionError as e:
            self.showError(str(e))
            return

        try:
            title, __ = os.path.splitext(os.path.basename(filepath))
            self.tabWidget.addNameTab(title)
            plotWindow = self.tabWidget.currentWidget().plotWindow
            plotWindow.dateplot.cal.exec_()
            plotWindow.addAxes(layout.keys())

            for axeId, axeProperty in layout.items():
                id = int(axeId[-1]) - 1
                axes = plotWindow.allAxes[id]
                for curveProperty in axeProperty['curves']:
                    try:
                        plotWindow.addCurve(confighandler.SavedCurve(**curveProperty), axes=axes)
                    except Exception as e:
                        failed.append(f'{curveProperty["fullLabel"]}:{str(e)}')

                subplot = plotWindow.customize.allAxes[id]
                subplot.overrideAxisAndScale(ylabel=axeProperty['ylabel'], yscale=axeProperty['yscale'])

        except Exception as e:
            self.tabWidget.removeTab(self.tabWidget.currentIndex())
            self.showError(f'{filepath} is badly formatted : \n {str(e)}')

        if failed:
            self.showError('\r\n'.join(failed))

    def saveLayout(self):
        layout = dict()

        try:
            tab = self.tabWidget.currentWidget()
            curves = tab.plotWindow.axes2curves
        except AttributeError:
            self.showError('There are not any tabs...')
            return

        try:
            axes = tab.plotWindow.graph.allAxes
            for axeId, axe in axes.items():
                axeCurves = curves[axe]
                axeProperty = dict(ylabel=axe.get_ylabel(), yscale=axe.get_yscale(),
                                   curves=[curve.as_dict() for curve in axeCurves])

                layout[f'ax{axeId + 1}'] = axeProperty
            filepath, fmt = QFileDialog.getSaveFileName(self, 'Save File',
                                                        f'/home/{self.tabWidget.tabText()}.yaml', "(*.yaml)")
            if filepath:
                with open(os.path.expandvars(filepath), 'w') as savedFile:
                    yaml.dump(layout, savedFile)

        except AttributeError:
            self.showError('Current tab does not hold any graph...')

        except PermissionError as e:
            self.showError(str(e))

    def showError(self, error):
        reply = QMessageBox.critical(self, 'Exception', error, QMessageBox.Ok)

    def showInformation(self, information):
        reply = QMessageBox.information(self, 'Message', information, QMessageBox.Ok)
