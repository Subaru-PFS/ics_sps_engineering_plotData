import numpy as np
from matplotlib.lines import Line2D

from PyQt5.QtCore import QTimer


class Curve(Line2D):
    def __init__(self, parent, graph, label, type, ylabel, unit, tableName, keyword, combo):
        super(Curve, self).__init__([], [], label=label)
        self.parent = parent
        self.graph = graph
        self.dataset = self.graph.dataset
        self.label = label
        self.type = type
        self.ylabel = ylabel
        self.unit = unit
        self.tableName = tableName
        self.keyword = keyword
        self.combo = combo
        self.last_id = 0
        self.end_id = np.inf
        self.firstCall = True
        self.findAcceptableRange()
        self.watcher = QTimer(self.parent.parent)
        self.watcher.setInterval(700)
        self.watcher.timeout.connect(self.getData)
        self.getIdBoundaries()
        self.setLineStyle()

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

    def getData(self, getStarted=False):
        if getStarted:
            return_values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, self.end_id)
            if type(return_values) is int:
                self.parent.parent.showError(return_values)
            else:
                new_id, dates, values = return_values
                dates, values = self.checkValues(dates, values)
                if values.any():
                    self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
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
                self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
                self.graph.updateLine(self.currLine, self)
                self.last_id = new_id

    def setLineStyle(self, marker=2.):
        color = self.graph.color_tab[self.combo.currentIndex()]
        self.color = color
        self.set_color(color)
        self.set_markerfacecolor(color)
        self.set_markeredgecolor(color)
        self.set_marker("o")
        self.set_markersize(marker)

    def setLine(self, line):
        self.currLine = line

    def findAcceptableRange(self):
        rangeVals = {"temperature_k": [15, 330], "temperature_c": [-10, 50], "pressure": [1e-9, 1e4], "power": [0, 400]}
        for types, range in rangeVals.iteritems():
            if types in self.type:
                self.minVal = rangeVals[types][0]
                self.maxVal = rangeVals[types][1]

    def checkValues(self, date, value):
        if hasattr(self, "minVal"):
            i = 0
            while i < len(value):
                if not self.minVal <= value[i] <= self.maxVal:
                    date = np.delete(date, i)
                    value = np.delete(value, i)
                else:
                    i += 1
        return date, value
