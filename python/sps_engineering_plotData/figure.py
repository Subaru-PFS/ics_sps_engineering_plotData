#!/usr/bin/env python
# encoding: utf-8
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import numpy as np

from transform import computeScale


class PFigure(Figure):
    def __init__(self, graph, width, height, dpi):
        Figure.__init__(self, figsize=(width, height), dpi=dpi)
        self.graph = graph
        self.locked = False

    def draw(self, event):

        if not self.locked:
            self.graph.colorStyle()
            self.formatDate()
            self.subplots_adjust(hspace=0.05)

            self.graph.hideExtraLines()
            self.setLineData()
            Figure.draw(self, event)
            self.graph.bck = self.saveBackground()
            self.graph.showExtraLines()

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def saveBackground(self):

        bck = [self.canvas.copy_from_bbox(self.graph.allAxes[idAxes].bbox) for idAxes in self.graph.primaryAxes]

        return bck

    def formatDate(self):
        if not self.graph.allAxes.keys():
            return

        idAxes = 2 if 2 in self.graph.allAxes.keys() else 0

        if idAxes:
            for tic in self.graph.allAxes[0].xaxis.get_major_ticks():
                tic.tick1On = tic.tick2On = False
                tic.label1On = tic.label2On = False

        dateAxes = self.graph.allAxes[idAxes]
        t0, tmax = dateAxes.get_xlim()
        if tmax - t0 > 7:
            format_date = '%Y-%m-%d'
        elif tmax - t0 > 1:
            format_date = '%a %H:%M'
        else:
            format_date = '%H:%M:%S'

        dateAxes.xaxis.set_major_formatter(DateFormatter(format_date))
        plt.setp(dateAxes.xaxis.get_majorticklabels(), rotation=20, horizontalalignment='center')

    def setLineData(self, maxPt=200):
        if not self.graph.allAxes.keys():
            return

        tmin, tmax = self.graph.allAxes[0].get_xlim()
        delta = tmax - tmin
        tmin -= delta * 0.05
        tmax += delta * 0.05

        step = delta / maxPt
        time = np.arange(tmin - step, tmax + step, step)

        for curve in self.graph.curvesOnAxes:
            data = computeScale(time, curve.get_data()) if self.graph.smartScale.isChecked() else curve.get_data()
            curve.line.set_data(data)