#!/usr/bin/env python
# encoding: utf-8
import matplotlib

matplotlib.use("Qt5Agg")

from matplotlib import ticker, rcParams

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from figure import PFigure
from transform import make_format, indFinder
from navigationtoolbar import NavigationToolbar

from PyQt5.QtWidgets import QSizePolicy, QCheckBox, QHBoxLayout
from PyQt5.QtCore import QTimer

rcParams.update({'figure.autolayout': True})
plt.style.use('ggplot')


def draw(func):
    def wrapper(self, *args, **kwargs):
        self.fig.lock()

        ret = func(self, *args, **kwargs)
        self.checkScales()
        self.relim()

        self.fig.unlock()
        self.figure.canvas.draw()
        return ret

    return wrapper


class Graph(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, plotWindow, customAxe, width=4, height=2, dpi=100):
        self.fig = PFigure(self, width, height, dpi)
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.plotWindow = plotWindow
        toolbarLayout = QHBoxLayout()
        self.onDrawing = False

        self.toolbar = NavigationToolbar(self, self.plotWindow)
        self.smartScale = self.getSmartScale()

        self.buildAxes(customAxe)

        toolbarLayout.addWidget(self.toolbar)
        toolbarLayout.addWidget(self.smartScale)

        self.plotWindow.graph_layout.addLayout(toolbarLayout)

    @property
    def axes(self):
        return self.plotWindow.axes

    @property
    def line2Curve(self):
        return self.plotWindow.line2Curve

    @property
    def isZoomed(self):
        return self.toolbar.isZoomed()

    def buildAxes(self, custom):
        subplotsize = 210 if 2 in [newAxe.id for newAxe in custom] else 110
        newAxes = {}

        for newAxe in custom:

            if newAxe.id == 0:
                axe = self.fig.add_subplot(subplotsize + 1)
            elif newAxe.id == 1:
                axe = newAxes[0].twinx()
                axe.format_coord = make_format(axe, newAxes[0])
            elif newAxe.id == 2:
                axe = self.fig.add_subplot(subplotsize + 2, sharex=newAxes[0])
            elif newAxe.id == 3:
                axe = newAxes[2].twinx()
                axe.format_coord = make_format(axe, newAxes[2])

            try:
                oldaxe = self.axes[newAxe.id]
                for curve in self.plotWindow.axe2curves[oldaxe]:
                    curve.currAxe = axe

            except KeyError:
                pass

            newAxes[newAxe.id] = axe

        self.plotWindow.setAxes(newAxes)

        self.plotCurves()

    def plot_date(self, curve):
        ax = curve.currAxe
        if ax is None:
            return
        empty = False if ax.get_lines() else True

        line, = ax.plot_date(curve.get_xdata(), curve.get_ydata(), '-', color=curve.color, label=curve.label)
        curve.setLine(line)

        if empty:
            self.setNewScale(curve)

    @draw
    def plotCurves(self, new_curve=False):

        Curves = [new_curve] if new_curve else self.plotWindow.curveList
        for curve in Curves:
            self.plot_date(curve)

    @draw
    def removeCurve(self, curve):

        self.removeLine(curve)
        if curve.watcher:
            curve.watcher.stop()
        del curve

    @draw
    def updateScale(self, axe, scale):
        axe.set_yscale(scale, basey=10)

    def switchCurve(self, axe, curve):

        self.removeLine(curve)
        curve.currAxe = axe

        self.plotCurves(curve)

    def removeLine(self, curve):
        line = curve.currLine
        if line:
            lines = curve.currAxe.lines

            lines.remove(line)
            del line
            curve.currLine = False

    def relim(self):

        tmin, tmax = self.get_xlim()
        ylims = [self.get_ylim(axe) for axe in self.axes.values()]

        limits = [(tmin, tmax, ymin, ymax) for ymin, ymax in ylims]

        if not self.isZoomed:
            for axe, (tmin, tmax, ymin, ymax) in zip(self.axes.values(), limits):
                axe.set_xlim(tmin, tmax)
                axe.set_ylim(ymin, ymax)
        else:
            self.toolbar.setNewHome(limits)

    def get_xlim(self):
        lines = []

        for axe in self.axes.values():
            lines += axe.get_lines()

        curves = [self.line2Curve[line] for line in lines]

        try:
            tmin = np.min([np.min(curve.get_xdata()) for curve in curves])
            tmax = np.max([np.max(curve.get_xdata()) for curve in curves])

            tmin, tmax = self.calc_lim(tmin, tmax, f1=0, f2=0.15)

        except ValueError:
            (tmin, tmax) = (726602, 726603)

        return tmin, tmax

    def get_ylim(self, axe):
        lines = axe.get_lines()
        curves = [self.line2Curve[line] for line in lines]

        try:
            ymin = np.min([np.min(curve.get_ydata()) for curve in curves])
            ymax = np.max([np.max(curve.get_ydata()) for curve in curves])

            ymin, ymax = self.calc_lim(ymin, ymax)

        except ValueError:
            (ymin, ymax) = (0.0, 1.0)

        return ymin, ymax

    def calc_lim(self, dmin, dmax, f1=0.05, f2=0.05):

        delta = (dmax - dmin)

        dmin -= (f1 * delta)
        dmax += (f2 * delta)

        return dmin, dmax

    def checkScales(self):
        for id, axe in self.axes.items():
            comboScale = self.plotWindow.customize.allAxes[id].comscale
            if axe.get_yscale() != comboScale.currentText():
                axe.set_yscale(comboScale.currentText())

    def setNewScale(self, curve):
        axe = curve.currAxe
        comboScale = self.plotWindow.customize.allAxes[self.plotWindow.axe2id[axe]].comscale

        if curve.yscale != comboScale.currentText():
            comboScale.setCurrentText(curve.yscale)

    def updatePlot(self, curve, xdata, ydata):

        axe = curve.currAxe
        line = curve.currLine

        if line:
            line.set_data(np.append(line.get_xdata(), xdata), np.append(line.get_ydata(), ydata))
        else:
            return

        if self.isZoomed:
            doDraw = False
        else:
            doDraw = self.updateLimits(axe, xdata)

        self.displayLine(doDraw=doDraw)

    def updateLimits(self, axe, xdata, doDraw=False):
        tmin, tmax = axe.get_xlim()

        if np.max(xdata) > (tmax - 0.01 * (tmax - tmin)):
            axe.set_xlim(self.calc_lim(tmin, np.max(xdata), f1=0, f2=0.15))
            doDraw = True

        for axe in self.axes.values():
            if axe.get_lines():
                ymin, ymax = axe.get_ylim()
                delta = 0.03 * (ymax - ymin)

                curves = [self.line2Curve[line] for line in axe.get_lines()]
                indices = [indFinder(curve.get_xdata(), tmin) for curve in curves]

                newMin = np.min([np.min(curve.get_ydata()[ind:]) for curve, ind in zip(curves, indices)])
                newMax = np.max([np.max(curve.get_ydata()[ind:]) for curve, ind in zip(curves, indices)])

                newMin = newMin if newMin < (ymin + delta) else ymin
                newMax = newMax if newMax > (ymax - delta) else ymax

                if not (newMin == ymin and newMax == ymax):
                    axe.set_ylim(self.calc_lim(newMin, newMax))
                    doDraw = True

        return doDraw

    def displayLine(self, doDraw):

        if not self.onDrawing:
            self.onDrawing = 'doDraw' if doDraw else 'doArtist'
            timer = QTimer.singleShot(5000, self.doDraw)

        else:
            self.onDrawing = 'doDraw' if doDraw else self.onDrawing

    def doDraw(self):

        if self.onDrawing == 'doDraw':
            self.fig.canvas.draw()
        else:
            self.fig.canvas.restore_region(self.background)
            for curve in self.plotWindow.curveList:
                axe = curve.currAxe
                if axe is not None:
                    axe.draw_artist(curve.currLine)

            self.fig.canvas.blit(self.fig.bbox)

        self.onDrawing = False

    def colorStyle(self):
        fontsize = 10 if 2 in self.axes.keys() else 12
        for id, axe in self.axes.items():
            try:
                primAxe = not id % 2
                colorLine = axe.get_lines()[0]
                curve = self.line2Curve[colorLine]
                axe.set_ylabel(curve.ylabel, color=curve.color, fontsize=fontsize)
                self.setTickLocator(axe)

                for tick in (axe.yaxis.get_major_ticks() + axe.yaxis.get_minor_ticks()):
                    self.pimpTicks(tick, primAxe, curve.color)

                [maj_style, min_style, alpha2] = ['--', '-', 0.15] if primAxe else [':', '-.', 0.1]

                axe.grid(which='major', alpha=0.6, color=curve.color, linestyle=maj_style)
                axe.grid(which='minor', alpha=alpha2, color=curve.color, linestyle=min_style)

                axe.tick_params(axis='y', labelsize=fontsize)
            except IndexError:
                pass

        self.addLegend()

    def addLegend(self):
        if not self.axes.items():
            return
        t0, tmax = self.axes[0].get_xlim()

        for sub in range(2):
            lns = []
            for twin in range(2):
                try:
                    lns += self.axes[2 * sub + twin].get_lines()
                except KeyError:
                    pass

            try:
                self.axes[2 * sub].get_legend().remove()
            except (AttributeError, KeyError):
                pass

            if lns:
                indices = [indFinder(line.get_xdata(), tmax) for line in lns]
                vals = [(line.get_xdata()[ind], line.get_ydata()[ind]) for line, ind in zip(lns, indices)]

                coords = [self.line2Curve[line].currAxe.transData.transform((x, y)) for line, (x, y) in zip(lns, vals)]

                toSort = [(pix_y, line, line.get_label()) for line, (pix_x, pix_y) in zip(lns, coords)]

                toSort.sort(key=lambda row: row[0])

                lns = [tup[1] for tup in reversed(toSort)]
                labs = [tup[2] for tup in reversed(toSort)]

                size = 8.5 - 0.12 * len(lns)

                self.axes[2 * sub].legend(lns, labs, loc='best', prop={'size': size})

    def setTickLocator(self, axe):

        if axe.get_yscale() in ["log"]:
            axe.yaxis.set_minor_locator(ticker.LogLocator(subs=[2, 3, 6]))
            axe.yaxis.set_minor_formatter(ticker.FormatStrFormatter("%.1e"))

        else:
            minor_locatory = ticker.AutoMinorLocator(5)
            axe.yaxis.set_minor_locator(minor_locatory)
            axe.get_yaxis().get_major_formatter().set_useOffset(False)

        minor_locatorx = ticker.AutoMinorLocator(5)
        axe.xaxis.set_minor_locator(minor_locatorx)

    def pimpTicks(self, tick, primAxe, color):
        tick.label1On = True if primAxe else False
        tick.label2On = False if primAxe else True

        coloredTick = tick.label1 if primAxe else tick.label2
        coloredTick.set_color(color=color)

    def pimpGrid(self, tick, primAxe, color):
        tick.label1On = True if primAxe else False
        tick.label2On = False if primAxe else True

        coloredTick = tick.label1 if primAxe else tick.label2
        coloredTick.set_color(color=color)

    def getSmartScale(self):

        smartScale = QCheckBox("Enhance Performances")
        smartScale.setChecked(2)
        smartScale.stateChanged.connect(self.fig.canvas.draw)
        return smartScale


    def close(self, *args, **kwargs):
        for widget in [self.toolbar, self.smartScale]:
            widget.close()
            widget.deleteLater()

        FigureCanvas.close(self, *args, **kwargs)
