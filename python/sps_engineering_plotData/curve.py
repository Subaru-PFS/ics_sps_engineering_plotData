import numpy as np

from matplotlib import colors as mcolors
from sps_engineering_plotData.widgets import ComboColor


class Curve(object):
    def __init__(self, plotWindow, curveConf):
        object.__init__(self)
        self.axes = None
        self.line = False

        self.xdata = []
        self.ydata = []

        self.plotWindow = plotWindow
        self.comboColor = ComboColor(len(self.plotWindow.curveList))
        self.comboColor.currentIndexChanged.connect(self.updateColor)

        self.type = curveConf.type
        self.label = curveConf.fullLabel
        self.tablename = curveConf.tablename
        self.key = curveConf.key
        self.trange = curveConf.trange
        self.ylabel = curveConf.ylabel
        self.yscale = curveConf.yscale

        self.ranges = [float(rang) for rang in curveConf.trange.split(';')]

        self.initialize()

    def __del__(self):
        self.removeLine()

    def __str__(self):
        return f'{self.tablename}__{self.key}'

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

    def getData(self, doRaise=False):

        try:
            dataset = self.db.dataBetweenId(self.tablename, self.key, self.idstart, maxId=self.idend)
            values = dataset[self.key].values
            dates = dataset['tai'].values
            mask = self.checkValues(values)
            xdata, ydata = dates[mask], values[mask]

            self.set_data(np.append(self.get_xdata(), xdata), np.append(self.get_ydata(), ydata))
            self.idstart = dataset['id'].values[-1] + 1

            if doRaise and not len(self.get_xdata()):
                raise Exception("All values are NaN")

        except ValueError:
            xdata = ydata = np.array([])
        except UserWarning as e:
            self.plotWindow.mainwindow.showError(str(e))
            return

        return xdata, ydata

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
        self.label = self.line.get_label()
        self.comboColor.newColor(mcolors.to_hex(self.line.get_color()))

    def removeLine(self):

        if self.line:
            self.axes.lines.remove(self.line)
            del self.line
            self.line = False

    def initialize(self):
        try:
            self.idstart = self.db.idFromDate(self.tablename, date=self.dateplot.datetime)
        except:
            raise ValueError(f'{self.tablename} does not contain any data on {self.dateplot.datetime}')

        if not self.dateplot.realtime:
            self.idend, __ = self.db.fetchone(self.db.rangeMax(end=str(self.dateplot.dateEnd)))
        else:
            self.idend = False

        self.getData(doRaise=True)

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

    def as_dict(self):
        return dict(fullLabel=self.label, type=self.type, tablename=self.tablename, key=self.key)
