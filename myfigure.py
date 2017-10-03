#!/usr/bin/env python
# encoding: utf-8
import numpy as np
from matplotlib.figure import Figure

from transform import computeScale


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
        self.setSmartScale()
        self.parent.updateStyle()
        Figure.draw(self, event)
        self.parent.background = self.canvas.copy_from_bbox(self.parent.ax.bbox)

    def setSmartScale(self):
        t0, tmax = self.parent.ax.get_xlim()
        maxPt = 700
        if tmax - t0 > 7:
            format_date = "%Y-%m-%d"
        elif tmax - t0 > 1:
            format_date = "%a %H:%M"
        else:
            format_date = "%H:%M:%S"

        step = (tmax - t0) / maxPt
        t = np.arange(t0 - step, tmax + step, step)
        for line, curve in self.parent.dictofline.iteritems():
            if self.parent.smartScale.isChecked():
                if curve.getLim() != (t0, tmax):
                    line.set_data(computeScale(t, curve.get_data()))
                    curve.setLim((t0, tmax))
            else:
                line.set_data(curve.get_data())
                curve.setLim((t0, 0))

        self.parent.setDateFormat(format_date)
