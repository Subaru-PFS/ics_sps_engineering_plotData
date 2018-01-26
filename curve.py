import numpy as np
from PyQt5.QtCore import QTimer
from matplotlib.lines import Line2D

from transform import indFinder


class Curve(Line2D):
    def __init__(self, parent, graph, label, type, ylabel, unit, tableName, keyword, combo, xxx_todo_changeme):
        (l_range, u_range) = xxx_todo_changeme
        super(Curve, self).__init__([], [], label=label)
        self.parent = parent
        self.graph = graph
        self.dataset = self.graph.dataset
        self.label = label
        self.type = type
        self.ylabel = ylabel
        self.yscale = "linear" if "pressure" not in type else 'log'
        self.unit = unit
        self.tableName = tableName
        self.keyword = keyword
        self.combo = combo
        self.l_range = l_range if l_range is not None else -np.inf
        self.u_range = u_range if u_range is not None else np.inf
        self.last_id = 0
        self.end_id = np.inf
        self.firstCall = True

        self.watcher = QTimer(self.parent.parent)
        self.watcher.setInterval(700)
        self.watcher.timeout.connect(self.getData)
        self.getIdBoundaries()
        self.setLineStyle()
        self.currLim = (0, 0)

    def getIdBoundaries(self):
        date_num = self.graph.numDate
        self.last_id = self.parent.parent.db.getrowrelative2Date(self.tableName, 'id', date_num, True)
        if self.last_id < 0:
            self.parent.parent.showError(self.last_id)
        elif self.dataset == "past_run":
            self.end_id = self.parent.parent.db.getrowrelative2Date(self.tableName, 'id',
                                                                    self.graph.numDate + self.parent.parent.calendar.spinboxDays.value() * 86400,
                                                                    True, True)
            if self.end_id < 0:
                self.parent.parent.showError(self.end_id)
                self.last_id = -4
            else:
                self.getData(True)
        else:
            self.getData(True)

    def getData(self, getStarted=False, dtime=3300):
        if getStarted:
            return_values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, self.end_id)
            if type(return_values) is int:
                self.parent.parent.showError(return_values)
            else:
                new_id, dates, values = return_values
                dates, values = self.checkValues(dates, values)
                if values.size:
                    self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
                    self.getExtremum(values, firstTime=True)
                    self.last_id = new_id
                    if self.dataset == "real_time":
                        self.watcher.start()
                else:
                    self.parent.parent.showError(-4)
                    self.last_id = -4
        else:
            return_values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, self.end_id)
            if return_values in [-5, -4]:
                pass
            elif type(return_values) == int:
                self.parent.parent.showError(return_values)
                self.watcher.stop()
            else:
                new_id, dates, values = return_values
                dates, values = self.checkValues(dates, values)
                if values.size:
                    self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
                    self.getExtremum(values)
                    self.graph.updateLine(self.currLine, dates, values, dtime)
                    self.last_id = new_id

    def setLineStyle(self, marker=2.):
        color = self.graph.color_tab[self.combo.currentIndex()]
        self.color = color
        self.set_color(color)
        # self.set_markerfacecolor(color)
        # self.set_markeredgecolor(color)
        # self.set_marker("o")
        # self.set_markersize(marker)

    def setLine(self, line):
        self.currLine = line

    def checkValues(self, date, value):
        value = value[:, 0]
        ind = np.logical_and(value >= self.l_range, value <= self.u_range)
        return date[ind], value[ind]

    def getExtremum(self, values, firstTime=False):
        if firstTime:
            self.currExtremum = np.min(values), np.max(values)
        else:
            currMin, currMax = self.currExtremum
            self.currExtremum = np.min([currMin, np.min(values)]), np.max([currMax, np.max(values)])

    def getLim(self):
        return self.currLim

    def setLim(self, xxx_todo_changeme1):
        (t0, tmax) = xxx_todo_changeme1
        self.currLim = t0, tmax
        ind = indFinder(self.get_xdata(), t0)
        self.currExtremum = np.min(self.get_ydata()[ind:]), np.max(self.get_ydata()[ind:])