#!/usr/bin/env python
# encoding: utf-8
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from transform import indFinder


class PFigure(Figure):
    def __init__(self, graph, width, height, dpi):
        Figure.__init__(self, figsize=(width, height), dpi=dpi)
        self.graph = graph
        self.locked = False

    def draw(self, event):
        # if hasattr(self.graph, "linev"):
        #     if not self.graph.exceptCursor:
        #         self.graph.linev.set_visible(False)
        #         self.graph.label_cursor.hide()
        #         self.saveBackground(event)
        #         self.graph.linev.set_visible(True)
        #         self.graph.ax.draw_artist(self.graph.linev)
        #         self.graph.label_cursor.show()
        # else:
        #     self.graph.removePoint()
        if not self.locked:
            self.saveBackground(event)

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def saveBackground(self, event):
        #self.setLineData()
        self.graph.colorStyle()
        self.formatDate()

        self.subplots_adjust(hspace=0.05)
        Figure.draw(self, event)

        self.graph.background = self.canvas.copy_from_bbox(self.graph.axes[0].bbox) if self.graph.axes.keys() else None

    def formatDate(self):
        if not self.graph.axes.keys():
            return

        idAxis = 2 if 2 in self.graph.axes.keys() else 0

        if idAxis:
            for tic in self.graph.axes[0].xaxis.get_major_ticks():
                tic.tick1On = tic.tick2On = False
                tic.label1On = tic.label2On = False

        dateAxis = self.graph.axes[idAxis]
        t0, tmax = dateAxis.get_xlim()
        if tmax - t0 > 7:
            format_date = "%Y-%m-%d"
        elif tmax - t0 > 1:
            format_date = "%a %H:%M"
        else:
            format_date = "%H:%M:%S"

        dateAxis.xaxis.set_major_formatter(DateFormatter(format_date))
        plt.setp(dateAxis.xaxis.get_majorticklabels(), rotation=20, horizontalalignment='center')

    def setLineData(self):

        tmin, tmax = self.graph.axes[0].get_xlim()
        delta = tmax - tmin
        tmin -= delta * 0.05
        tmax += delta * 0.05

        for curve in self.graph.plotWindow.curveList:
            imin = indFinder(curve.get_xdata(), tmin)
            imax = indFinder(curve.get_xdata(), tmax)
            curve.currLine.set_data(curve.get_xdata()[imin:imax + 1], curve.get_ydata()[imin:imax + 1])

            # from matplotlib.dates import num2date
            # print (num2date(tmin))
            # maxPt = 700
            # step = (tmax - tmin) / maxPt
            # time = np.arange(tmin - step, tmax + step, step)
            #
            # for curve in self.graph.plotWindow.curveList:
            #     if self.graph.smartScale.isChecked():
            #         curve.currLine.set_data(computeScale(time, curve.get_data()))
            #     else:
            #         curve.currLine.set_data(curve.get_data())
