#!/usr/bin/env python
# encoding: utf-8
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure
from sps_engineering_plotData.transform import computeScale


class PFigure(Figure):
    def __init__(self, graph, width, height, dpi):
        Figure.__init__(self, figsize=(width, height), dpi=dpi)
        self.editAxes = False
        self.graph = graph

    def draw(self, event):
        # save user customization.
        self.graph.userCustom()

        self.graph.colorStyle()
        self.formatDate()
        self.subplots_adjust(hspace=0.05)
        self.graph.hideExtraLines()
        self.setLineData()

        Figure.draw(self, event)

        try:
            self.graph.bck = self.saveBackground()
            self.graph.showExtraLines()
        except AttributeError:
            pass

    def saveBackground(self):
        bck = [self.canvas.copy_from_bbox(self.graph.allAxes[idAxes].bbox) for idAxes in self.graph.primaryAxes]
        return bck

    def formatDate(self):
        if not self.graph.allAxes.keys():
            return

        idAxes = 2 if 2 in self.graph.allAxes.keys() else 0

        if idAxes:
            for tic in self.graph.allAxes[0].xaxis.get_major_ticks():
                tic.tick1line.set_visible(False)
                tic.tick2line.set_visible(False)
                tic.label1.set_visible(False)
                tic.label2.set_visible(False)

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

    def setLineData(self, maxPt=800):
        if not self.graph.allAxes.keys():
            return

        tmin, tmax = self.graph.allAxes[0].get_xlim()
        delta = tmax - tmin

        step = delta / maxPt
        time = np.arange(tmin, tmax + step, step)

        for curve in self.graph.curvesOnAxes:
            data = computeScale(time, curve.get_data()) if self.graph.smartScale.isChecked() else curve.get_data()
            curve.line.set_data(data)
