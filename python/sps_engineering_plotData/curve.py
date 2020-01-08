import numpy as np
from PyQt5.QtCore import QTimer
from matplotlib import colors as mcolors
from widgets import ComboColor


class Curve(object):
    def __init__(self, plotWindow, curveConf):
        object.__init__(self)
        self.axes = None
        self.line = False

        self.watcher = QTimer(plotWindow)
        self.watcher.setInterval(2500)
        self.watcher.timeout.connect(self.getData)

        self.xdata = []
        self.ydata = []

        self.plotWindow = plotWindow
        self.comboColor = ComboColor(len(self.plotWindow.curveList))
        self.comboColor.currentIndexChanged.connect(self.updateColor)
        self.deviceLabel = curveConf.deviceLabel
        self.label = '%s - %s' % (curveConf.deviceLabel, curveConf.label)
        self.baseType = curveConf.type
        self.ylabel = curveConf.ylabel
        self.unit = curveConf.unit
        self.tablename = curveConf.tablename
        self.key = curveConf.key

        self.ranges = [float(rang) for rang in curveConf.trange.split(';')]

        self.idstart = self.db.closestId(self.tablename, date=self.dateplot.datetime)

        if not self.dateplot.realtime:
            self.idend = self.db.closestId(self.tablename, date=self.dateplot.dateEnd, reverse=True)
        else:
            self.idend = False

        self.getData(start=True)

        if not self.idend:
            self.startUpdating()

    def __del__(self):
        self.removeLine()
        self.stop()

    @property
    def type(self):
        if self.axes is not None and self.baseType == 'none' and self.axes.get_yscale() != 'linear':
            return 'pressurenone'

        return self.baseType

    @property
    def yscale(self):
        return 'linear' if 'pressure' not in self.type else 'log'

    @property
    def graph(self):
        return self.plotWindow.graph

    @property
    def dateplot(self):
        return self.plotWindow.dateplot

    @property
    def db(self):
        return self.plotWindow.mainwindow.db

    @property
    def color(self):
        return self.comboColor.color

    def getData(self, start=False):
        try:
            dataset = self.db.dataBetween(table=self.tablename,
                                          cols=self.key,
                                          start=self.idstart,
                                          end=self.idend,
                                          raw_id=True)

            values = dataset[self.key].values
            dates = dataset['tai'].values
            mask = self.checkValues(values)
            xdata, ydata = dates[mask], values[mask]

            self.set_data(np.append(self.get_xdata(), xdata), np.append(self.get_ydata(), ydata))
            self.idstart = dataset['id'].values[-1]

            if not start:
                self.graph.updatePlot(self, xdata, ydata)
            else:
                if not len(self.get_xdata()):
                    raise Exception("All values are NaN")

        except ValueError as e:
            pass

    def startUpdating(self):
        self.watcher.start()

    def setAxes(self, axes):
        self.axes = axes

    def getAxes(self):
        return self.axes

    def setLine(self, line):
        self.line = line

    def checkValues(self, values):
        l_range, u_range = self.ranges
        return np.logical_and(values >= l_range, values <= u_range)

    def updateColor(self):
        if self.line:
            self.line.set_color(self.color)
            self.graph.draw_idle()

    def updateProp(self):
        yscale = self.axes.get_yscale()
        ylabel = self.axes.get_ylabel()
        label = self.line.get_label()
        color = mcolors.to_hex(self.line.get_color())

        self.yscale = yscale
        self.label = label
        self.ylabel = ylabel
        self.comboColor.newColor(color)

    def removeLine(self):

        if self.line:
            self.axes.lines.remove(self.line)
            del self.line
            self.line = False

    def stop(self):
        self.watcher.stop()

    def restart(self):
        self.getData()
        self.watcher.start()

    def get_data(self):
        return self.xdata, self.ydata

    def set_data(self, xdata, ydata):
        if self.dateplot.realtime:
            timeClippingMask = (xdata[-1] - xdata) < self.dateplot.maximumTimeStretch
            xdata = xdata[timeClippingMask]
            ydata = ydata[timeClippingMask]

        self.xdata = xdata
        self.ydata = ydata

    def get_xdata(self):
        return self.xdata

    def get_ydata(self):
        return self.ydata
