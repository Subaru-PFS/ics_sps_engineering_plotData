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
        self.firstCall = True
        self.findAcceptableRange()
        self.watcher = QTimer(self.parent.parent)
        self.watcher.setInterval(1000)
        self.watcher.timeout.connect(self.getData)
        self.getFirstId()
        self.setLineStyle()

    def getFirstId(self):
        date_num = self.graph.numDate
        last_id = self.parent.parent.db.getrowrelative2Date(self.tableName, 'id', date_num, True)
        if last_id not in [-1, -2, -3, -4]:
            self.last_id = last_id
            self.getData()
        elif last_id is not -5:
            self.parent.parent.showError(last_id)

    def getData(self):

        end_id = "Now" if self.dataset == "real_time" else self.parent.parent.db.getrowrelative2Date(self.tableName,
                                                                                                     'id',
                                                                                                     self.graph.numDate + self.parent.parent.calendar.spinboxDays.value() * 86400,
                                                                                                     True)
        if end_id != -5:
            new_id, dates, values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, end_id)

        if type(dates) == np.ndarray:
            if dates.any():
                if hasattr(self, "minVal"):
                    dates, values = self.checkValues(dates, values)
                if dates.any():
                    self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
                    self.last_id = new_id
                    if not self.firstCall:
                        self.graph.updateLine(self.getLine(), self)
                    elif self.dataset == "real_time":
                        self.watcher.start()
                else:
                    if self.firstCall:
                        self.parent.parent.showError(-4)
                        self.last_id = 0
            else:
                if self.firstCall:
                    self.parent.parent.showError(-4)
                    self.last_id = 0
        else:
            if self.firstCall:
                if dates is not -5:
                    self.parent.parent.showError(dates)
                self.last_id = 0

        self.firstCall = False

    def setLineStyle(self, marker=2.):
        color = self.graph.color_tab[self.combo.currentIndex()]
        self.color = color
        self.set_color(color)
        self.set_markerfacecolor(color)
        self.set_markeredgecolor(color)
        self.set_marker("o")
        self.set_markersize(marker)

    def getLine(self):
        for line2D, curve in self.graph.dictofline.iteritems():
            if curve == self:
                return line2D

    def findAcceptableRange(self):
        rangeVals = {"temperature_k": [15, 330], "temperature_c": [-10, 50], "pressure": [1e-9, 1e4], "power": [0, 400]}
        for types, range in rangeVals.iteritems():
            if types in self.type:
                self.minVal = rangeVals[types][0]
                self.maxVal = rangeVals[types][1]

    def checkValues(self, date, value):
        i = 0
        while i < len(value):
            if not self.minVal <= value[i] <= self.maxVal:
                date = np.delete(date, i)
                value = np.delete(value, i)
            else:
                i += 1

        return date, value
