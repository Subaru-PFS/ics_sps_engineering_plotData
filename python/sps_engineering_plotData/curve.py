import numpy as np
from matplotlib.lines import Line2D
from PyQt5.QtCore import QTimer

from widgets import ComboColor


class Curve(Line2D):
    def __init__(self, plotWindow, curveConf):
        Line2D.__init__(self, [], [], label=curveConf.label)
        self.ax = None
        self.line = False
        self.watcher = False

        self.plotWindow = plotWindow
        self.comboColor = ComboColor(len(self.plotWindow.curveList))
        self.comboColor.currentIndexChanged.connect(self.updateColor)
        self.deviceLabel = curveConf.deviceLabel
        self.label = curveConf.label
        self.type = curveConf.type
        self.ylabel = curveConf.ylabel
        self.unit = curveConf.unit
        self.tablename = curveConf.tablename
        self.key = curveConf.key
        self.ranges = [float(rang) for rang in curveConf.trange.split(';')]

        self.yscale = 'linear' if 'pressure' not in self.type else 'log'
        self.extremum = np.inf, -np.inf

        self.idstart = self.db.closestId(self.tablename, date=self.dateplot.datetime)
        if not self.dateplot.realtime:
            self.idend = self.db.closestId(self.tablename, date=self.dateplot.dateEnd)
        else:
            self.idend = False

        self.getData(start=True)
        if not self.idend:
            self.startUpdating()

    def __del__(self):
        self.removeLine()
        if self.watcher:
            self.stop()

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

            values = dataset[self.key].as_matrix()
            dates = dataset['tai'].as_matrix()
            mask = self.checkValues(values)
            xdata, ydata = dates[mask], values[mask]

            self.set_data(np.append(self.get_xdata(), xdata), np.append(self.get_ydata(), ydata))
            self.idstart = dataset['id'].as_matrix()[-1]

            if not start:
                self.graph.updatePlot(self, xdata, ydata)
            else:
                if not len(self.get_xdata()):
                    raise Exception("All values are NaN")

        except ValueError as e:
            pass

    def startUpdating(self):
        self.watcher = QTimer(self.plotWindow)
        self.watcher.setInterval(2500)
        self.watcher.timeout.connect(self.getData)
        self.watcher.start()

    def setAxes(self, ax):
        self.ax = ax

    def getAxes(self):
        return self.ax

    def setLine(self, line):
        self.line = line

    def checkValues(self, values):
        l_range, u_range = self.ranges
        return np.logical_and(values >= l_range, values <= u_range)

    def updateColor(self):
        if self.line:
            self.line.set_color(self.color)
            self.graph.fig.canvas.draw()

    def removeLine(self):

        if self.line:
            self.ax.lines.remove(self.line)
            del self.line
            self.line = False

    def stop(self):
        self.watcher.stop()

    def restart(self):
        self.getData()
        self.watcher.start()
