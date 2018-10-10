from functools import partial

from PyQt5.QtWidgets import QScrollArea, QComboBox, QDoubleSpinBox, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, \
    QPushButton, QGroupBox, QGridLayout
from sps_engineering_plotData.curve import Curve
from sps_engineering_plotData.graph import Graph
from sps_engineering_plotData.pcalendar import DatePlot
from sps_engineering_plotData.subplot import Customize
from sps_engineering_plotData.widgets import PQCheckBox


class PlotWindow(QWidget):
    def __init__(self, tab):
        super(PlotWindow, self).__init__()
        self.tab = tab
        self.allAxes = {}
        self.curveList = []
        self.extraLines = []
        self.layout = QHBoxLayout()
        self.graph_layout = QVBoxLayout()
        self.gbox_layout = QVBoxLayout()

        self.tabGBActor = QTabWidget()

        self.dateplot = DatePlot(self)
        self.customize = Customize(self)
        self.button_arrow = self.ButtonArrow()
        self.button_del_graph = self.ButtonDelete()

        self.gbox_layout.addWidget(self.dateplot)
        self.gbox_layout.addWidget(self.customize)
        self.gbox_layout.addWidget(self.tabGBActor)
        self.gbox_layout.addWidget(self.button_del_graph)

        self.layout.addLayout(self.graph_layout)
        self.layout.addWidget(self.button_arrow)
        self.layout.addLayout(self.gbox_layout)

        for widget in [self.dateplot, self.customize, self.tabGBActor]:
            widget.setMaximumWidth(400)

        self.setLayout(self.layout)

    @property
    def mainwindow(self):
        return self.tab.mainwindow

    @property
    def config(self):
        return self.dateplot.config

    @property
    def axes2curves(self):
        d = {ax: [] for ax in [None] + list(self.allAxes.values())}

        for curve in self.curveList:
            d[curve.getAxes()].append(curve)

        return d

    @property
    def line2Curve(self):
        return {curve.line: curve for curve in self.curveList}

    @property
    def axes2id(self):
        d = {ax: id for id, ax in self.allAxes.items()}
        d[None] = None
        return d

    def createGraph(self, custom):
        try:
            self.graph.close()
            self.graph_layout.removeWidget(self.graph)
            self.graph.deleteLater()
        except AttributeError:
            pass

        self.graph = Graph(self, custom)
        self.graph_layout.insertWidget(0, self.graph)

    def getAxes(self, newType, i=-1):

        for i, ax in self.allAxes.items():
            try:
                curve = self.axes2curves[ax][0]
                if curve.type == newType:
                    return ax
            except IndexError:
                return ax

            if i == 3:
                raise ValueError('No Axe available')
        return i + 1

    def setAxes(self, allAxes):
        for idAxes, oldAxes in list(self.allAxes.items()):
            self.unsetLines(oldAxes, allAxes)
            self.allAxes.pop(idAxes, None)

        self.allAxes = allAxes

    def unsetLines(self, axes, newAxes):
        while axes.lines:
            line = axes.lines[0]
            axes.lines.remove(line)
            try:
                curve = self.line2Curve[line]
                curve.line = False
                if curve.getAxes() not in newAxes.values():
                    curve.setAxes(None)
            except KeyError:
                pass
            del line

    def addCurve(self, curveConf):

        new_curve = Curve(self, curveConf)
        axes = self.getAxes(new_curve.type)

        if isinstance(axes, int):
            idAxes = axes
            self.customize.allAxes[idAxes].checkbox.setChecked(2)
            axes = self.allAxes[idAxes]

        new_curve.setAxes(axes)
        self.appendCurve(new_curve)
        self.graph.plotCurves(new_curve)

        return new_curve

    def appendCurve(self, new_curve):

        self.curveList.append(new_curve)
        self.customize.appendRow(new_curve)

    def switchCurve(self, axeId, curve):
        ax = self.allAxes[axeId] if axeId is not None else None
        self.graph.switchCurve(ax, curve)

    def removeCurve(self, curve):
        self.curveList.remove(curve)
        self.graph.removeCurve(curve)

        try:
            checkbox = curve.checkbox
            checkbox.setCheckable(True)
            checkbox.setChecked(0)
        except RuntimeError:
            pass  # Checkbox could have been already deleted

    def constructGroupbox(self, config):

        while self.tabGBActor.count():
            widget = self.tabGBActor.widget(0)
            self.clearLayout(widget.layout())
            self.tabGBActor.removeTab(0)
            widget.close()
            widget.deleteLater()

        sortedModule = self.sortCfg(config)

        for actorname in sorted(sortedModule):
            config = sortedModule[actorname]
            if config:
                t = TabActor(self, config)
                self.tabGBActor.addTab(t, actorname)

    def showhideConfig(self, button_arrow):

        if not self.tabGBActor.isHidden():
            self.tabGBActor.hide()
            self.dateplot.hide()
            self.customize.hide()
            self.button_del_graph.hide()
            button_arrow.setIcon(self.mainwindow.icon_arrow_left)
        else:
            self.tabGBActor.show()
            self.button_del_graph.show()
            self.dateplot.show()
            self.customize.show()
            button_arrow.setIcon(self.mainwindow.icon_arrow_right)

    def ButtonDelete(self):
        button = QPushButton('Remove Graph')
        button.clicked.connect(partial(self.removeGraph, self.layout))
        return button

    def ButtonArrow(self):

        button_arrow = QPushButton()
        button_arrow.setIcon(self.mainwindow.icon_arrow_right)
        button_arrow.clicked.connect(partial(self.showhideConfig, button_arrow))
        button_arrow.setStyleSheet('border: 0px')

        return button_arrow

    def removeGraph(self, layout):
        self.clearLayout(layout)
        self.tab.removeGraph(self)

    def clearLayout(self, layout):

        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def table2label(self, tablename, mergeAIT=False):
        for key, label in self.mainwindow.cuArms.items():
            if key in tablename:
                return label
        if mergeAIT:
            return 'AIT'
        else:
            return tablename.split('__')[0].upper()

    def sortCfg(self, config):
        sortedDict = {}
        for dev in config:
            label = self.table2label(tablename=dev.tablename, mergeAIT=False)
            try:
                sortedDict[label].append(dev)
            except KeyError:
                sortedDict[label] = [dev]
        return sortedDict


class TabActor(QScrollArea):
    def __init__(self, plotWindow, config):
        QScrollArea.__init__(self)
        self.widget = QWidget()
        self.clayout = QGridLayout()

        self.plotWindow = plotWindow
        self.config = config
        self.getGroupbox()

        self.setWidgetResizable(True)
        self.setWidget(self.widget)

    @property
    def graph(self):
        return self.plotWindow.graph

    @property
    def color_tab(self):
        return self.plotWindow.color_tab

    @property
    def mainwindow(self):
        return self.plotWindow.mainwindow

    def getGroupbox(self):
        index = 0
        for nb, device in enumerate(self.config):
            groupBox = QGroupBox(device.deviceLabel)
            groupBox.setStyleSheet('QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}')
            groupBox.setFlat(True)
            grid = QGridLayout()
            groupBox.setLayout(grid)
            grid.setSpacing(0)
            for i, curve in enumerate(device.labels):
                curveConf = device.curveConf(i)
                checkbox = PQCheckBox(self, curveConf)
                grid.addWidget(checkbox, i, 1)
                index += 1

            self.clayout.addWidget(groupBox, nb // 2, nb % 2)

        self.clayout.setSpacing(1)
        self.widget.setLayout(self.clayout)

    def getSpinBox(self):
        integ_time = QDoubleSpinBox()
        integ_time.setRange(15, 86400)
        integ_time.setValue(600)
        integ_time.setFixedWidth(80)
        return integ_time

    def getComboUnit(self, unit):
        combo = QComboBox()
        combo.addItems(['%s/%s' % (unit, t) for t in ['min', 'hour']])
        return combo
