import time
from functools import partial

import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout
from sps_engineering_plotData.plotwin import PlotWindow


class DataTimer(object):
    MIN_PERIOD = 2
    MAX_PERIOD = 120

    def __init__(self, tab):
        self.watcher = QTimer(tab)
        self.watcher.timeout.connect(tab.getData)
        self.period = 10 * [0.1]

    @property
    def isActive(self):
        return self.watcher.isActive()

    def updatePeriod(self, tdelta):
        self.period.append(tdelta)
        self.period = self.period[-10:]
        self.setPeriod()

    def setPeriod(self, period=0):
        if not period:
            period = 100 * np.mean(self.period)
            period = min(max(DataTimer.MIN_PERIOD, period), DataTimer.MAX_PERIOD)

        self.watcher.setInterval(int(period) * 1000)


class Tab(QWidget):
    def __init__(self, tabwidget):
        QWidget.__init__(self)
        self.tabwidget = tabwidget
        self.active = False

        self.button_add_graph = QPushButton("Add Graph")
        self.button_add_graph.clicked.connect(partial(self.addPlot))

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_add_graph)
        self.setLayout(self.layout)

        self.plotWindow = self.addPlot()
        self.dataTimer = DataTimer(self)

    @property
    def mainwindow(self):
        return self.tabwidget.mainwindow

    def addPlot(self):
        widget = PlotWindow(self)
        self.layout.addWidget(widget)
        self.button_add_graph.hide()

        return widget

    def removeGraph(self, widget):
        widget.close()
        self.layout.removeWidget(widget)
        self.button_add_graph.show()

    def getData(self):
        if not self.plotWindow.graph:
            return

        timing = dict()
        start = time.time()

        for curve in self.plotWindow.curveList:
            if not curve.realtime:
                continue

            xdata, ydata = curve.getData(doRaise=False)

            line = curve.line
            if not line:
                continue

            line.set_data(np.append(line.get_xdata(), xdata), np.append(line.get_ydata(), ydata))
            tmax = max(xdata) if xdata.size else 0

            if curve.getAxes() not in timing:
                timing[curve.getAxes()] = tmax
            else:
                timing[curve.getAxes()] = max(tmax, timing[curve.getAxes()])

        if self.active:
            self.plotWindow.graph.updatePlot(timing)
            self.dataTimer.updatePeriod(time.time() - start)

    def start(self):
        if not self.dataTimer.isActive:
            self.dataTimer.watcher.start()

        self.active = True
        self.getData()
        self.dataTimer.setPeriod()

    def stop(self):
        self.active = False
        self.dataTimer.setPeriod(600)

        if not self.plotWindow.graph or self.plotWindow.graph.isZoomed:
            return

        self.alignXAxis()

    def alignXAxis(self):
        timing = dict()

        for curve in self.plotWindow.curveList:
            if not curve.realtime:
                continue

            line = curve.line
            if not line:
                continue

            if curve.getAxes() not in timing:
                timing[curve.getAxes()] = [], []

            minX, maxX = timing[curve.getAxes()]

            minX.append(np.min(line.get_xdata()))
            maxX.append(np.max(line.get_xdata()))

        for ax, (minX, maxX) in timing.items():
            ax.set_xlim(np.min(minX), np.max(maxX))
