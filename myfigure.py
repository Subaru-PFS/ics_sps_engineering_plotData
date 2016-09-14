#!/usr/bin/env python
# encoding: utf-8
import numpy as np
from matplotlib.figure import Figure

from transform import indFinder


class myFigure(Figure):
    def __init__(self, parent, width, height, dpi):
        Figure.__init__(self, figsize=(width, height), dpi=dpi)
        self.parent = parent

    def draw(self, event):
        if hasattr(self.parent, "linev"):
            if not self.parent.exceptCursor:
                self.parent.linev.set_visible(False)
                self.parent.label_cursor.hide()
                self.saveBackground(event)
                self.parent.linev.set_visible(True)
                self.parent.ax.draw_artist(self.parent.linev)
                self.parent.label_cursor.show()
        else:
            self.parent.removePoint()
            self.saveBackground(event)

    def saveBackground(self, event):
        self.subplots_adjust(left=0.1, right=0.90, bottom=0.15, top=0.92, wspace=0.4, hspace=0.05)
        self.setSmartScale()
        self.parent.updateStyle()
        Figure.draw(self, event)
        self.parent.background = self.canvas.copy_from_bbox(self.parent.ax.bbox)

    def setSmartScale(self):
        t0, tmax = self.parent.ax.get_xlim()
        if tmax - t0 > 7:
            format_date = "%d/%m/%Y"
        elif tmax - t0 > 1:
            format_date = "%a %H:%M"
        else:
            format_date = "%H:%M:%S"
        for line, curve in self.parent.dictofline.iteritems():
            i, j, step = self.computeStep((t0, tmax), curve)
            line.set_data(np.array([curve.get_xdata()[p] for p in range(i, j, step)]),np.array([curve.get_ydata()[p] for p in range(i, j, step)]))
            curve.getExtremum(i)

        self.parent.setDateFormat(format_date)
        # for ax in self.parent.fig.get_axes():
        #     for line in ax.get_lines():
        #         curve = self.parent.dictofline[line]
        #         i, j, step = self.computeStep((t0, tmax), curve)
        #         line.set_data(np.array([curve.get_xdata()[p] for p in range(i, j, step)]),
        #                       np.array([curve.get_ydata()[p] for p in range(i, j, step)]))
        #         curve.getExtremum(i)


    def computeStep(self, timeRange, curve):
        maxPt = 1500
        t0, tmax = timeRange
        i = indFinder(t0, curve.get_xdata())
        j = indFinder(tmax, curve.get_xdata())
        step = int((j - i) / maxPt)
        step = 1 if step == 0 else step
        return i, j, step
