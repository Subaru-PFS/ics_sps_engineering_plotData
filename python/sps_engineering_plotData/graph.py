#!/usr/bin/env python
# encoding: utf-8
import matplotlib

matplotlib.use('Qt5Agg')

from matplotlib import ticker, rcParams

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.dates import num2date
from functools import partial

from sps_engineering_plotData.figure import PFigure
from sps_engineering_plotData.transform import make_format, indFinder
from sps_engineering_plotData.navigationtoolbar import NavigationToolbar
from sps_engineering_plotData.widgets import VCursor, ExtraLine
from PyQt5.QtWidgets import QSizePolicy, QCheckBox, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer
from pandas.plotting import register_matplotlib_converters


def getTimeZone():
    """ Return the timezone. Extracted from a DNS TXT record. """
    defaultTimeZone = 'UTC'

    import dns.resolver
    try:
        ans = dns.resolver.query('pfs-site.', 'TXT')
        site = ans[0].strings[0].decode('latin-1')
        timezone = 'US/Hawaii' if site == 'S' else defaultTimeZone
    except dns.resolver.NXDOMAIN:
        timezone = defaultTimeZone

    print('timezone=', timezone)
    return timezone


register_matplotlib_converters()

rcParams.update({'figure.autolayout': True,
                 'timezone': getTimeZone()})
plt.style.use('ggplot')


def draw(func):
    def wrapper(self, *args, **kwargs):
        ret = func(self, *args, **kwargs)
        self.relim()
        self.colorStyle()
        self.draw_idle()
        return ret

    return wrapper


class Graph(FigureCanvas):
    '''Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).'''

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
        self.VCursor = VCursor(self)

        self.buildAxes(customAxe)

        toolbarLayout.addWidget(self.toolbar)
        toolbarLayout.addWidget(self.smartScale)
        toolbarLayout.addWidget(self.VCursor)

        self.plotWindow.graph_layout.addLayout(toolbarLayout)

    @property
    def allAxes(self):
        return self.plotWindow.allAxes

    @property
    def primaryAxes(self):
        idAxes = []
        idAxes += ([0] if 0 in self.allAxes.keys() else [])
        idAxes += ([2] if 2 in self.allAxes.keys() else [])
        return idAxes

    @property
    def isZoomed(self):
        return self.toolbar.isZoomed()

    @property
    def isPanned(self):
        return self.toolbar.isPanned()

    @property
    def curvesOnAxes(self):
        return [curve for curve in self.plotWindow.curveList if curve.getAxes() is not None]

    def buildAxes(self, custom):
        subplotsize = 210 if 2 in [newAxes.id for newAxes in custom] else 110
        AllAxes = {}

        oldAffect = self.plotWindow.axes2curves

        for newAxes in custom:
            if newAxes.id == 0:
                axes = self.fig.add_subplot(subplotsize + 1)
                # declaring xaxis is date.
                axes.xaxis.axis_date()
            elif newAxes.id == 1:
                axes = AllAxes[0].twinx()
                axes.format_coord = make_format(axes, AllAxes[0])
            elif newAxes.id == 2:
                axes = self.fig.add_subplot(subplotsize + 2, sharex=AllAxes[0])
            elif newAxes.id == 3:
                axes = AllAxes[2].twinx()
                axes.format_coord = make_format(axes, AllAxes[2])
            try:
                oldAxes = self.allAxes[newAxes.id]
                for curve in oldAffect[oldAxes]:
                    curve.setAxes(axes)

            except KeyError:
                pass

            AllAxes[newAxes.id] = axes

        self.plotWindow.setAxes(AllAxes)
        self.plotCurves()

    def plot_date(self, curve):
        ax = curve.getAxes()

        # retrieving which plotting function to use from dataType.
        plotFunc = ax.plot if curve.dataType == 'real' else ax.step
        line, = plotFunc(curve.get_xdata(), curve.get_ydata(), '-', color=curve.color, label=curve.label)

        curve.setLine(line)

    @draw
    def plotCurves(self, new_curve=False):
        Curves = [new_curve] if new_curve else self.plotWindow.curveList
        onAxe = [curve for curve in Curves if curve.getAxes() is not None]

        for curve in onAxe:
            self.plot_date(curve)

        self.setAxisAndScale()

    @draw
    def removeCurve(self, curve):
        del curve

    @draw
    def updateScale(self, ax, scale):
        ax.set_yscale(scale, base=10)

    def switchCurve(self, axes, curve):

        curve.removeLine()
        curve.setAxes(axes)

        self.plotCurves(curve)

    def relim(self):

        tmin, tmax = self.get_xlim()
        limits = {}

        for ax in self.allAxes.values():
            ymin, ymax = self.get_ylim(ax)
            limits[ax] = (tmin, tmax, ymin, ymax)

        if not (self.isZoomed or self.isPanned):
            for ax, (tmin, tmax, ymin, ymax) in limits.items():
                ax.set_xlim(tmin, tmax)
                ax.set_ylim(ymin, ymax)

        self.toolbar.setNewHome(limits)

    def get_xlim(self):

        curves = []

        for ax in self.allAxes.values():
            curves += self.plotWindow.axes2curves[ax]

        try:
            tmin = np.min([np.min(curve.get_xdata()) for curve in curves])
            tmax = np.max([np.max(curve.get_xdata()) for curve in curves])

            tmin, tmax = self.calc_lim(tmin, tmax, f1=0, f2=0.15)

        except ValueError:
            (tmin, tmax) = (726602, 726603)

        return tmin, tmax

    def get_ylim(self, axes):
        curves = self.plotWindow.axes2curves[axes]
        logy = True if axes.get_yscale() == 'log' else False

        try:
            ymin = np.min([np.min(curve.get_ydata()) for curve in curves])
            ymax = np.max([np.max(curve.get_ydata()) for curve in curves])

            ymin, ymax = self.calc_lim(ymin, ymax, logy=logy)

        except ValueError:
            (ymin, ymax) = (0.0, 1.0)

        return ymin, ymax

    def calc_lim(self, dmin, dmax, logy=False, f1=0.05, f2=0.05):

        if not logy:
            delta = (dmax - dmin)

            dmin -= (f1 * delta)
            dmax += (f2 * delta)
        else:

            dmin = 1.0 * 10 ** (np.floor(np.log10(dmin)))
            dmax = 1.0 * 10 ** (np.ceil(np.log10(dmax)))

        return dmin, dmax

    def setAxisAndScale(self):
        for id, ax in self.allAxes.items():
            subplot = self.plotWindow.customize.allAxes[id]
            subplot.setAxisAndScale()

    def overrideAxisAndScale(self):
        for id, ax in self.allAxes.items():
            subplot = self.plotWindow.customize.allAxes[id]
            subplot.overrideAxisAndScale()

    def updatePlot(self, timing):
        doDraw = False

        if not self.isZoomed:
            for axes, tmax in timing.items():
                needDraw = self.updateLimits(axes, tmax, scaleY=(not self.isPanned))
                doDraw = needDraw if needDraw else doDraw

        self.displayLine(doDraw=doDraw)

    def updateLimits(self, axes, tmax, scaleY=True, doDraw=False):
        ax_tmin, ax_tmax = axes.get_xlim()
        ax_duration = ax_tmax - ax_tmin

        tmin = np.min([np.min(curve.get_xdata()) for curve in self.plotWindow.axes2curves[axes]])

        if tmax > (ax_tmax - 0.01 * ax_duration) or tmin > (ax_tmin + 0.02 * ax_duration):
            tmin = max(tmin, ax_tmin)
            axes.set_xlim(self.calc_lim(tmin, tmax, f1=0, f2=0.15))
            doDraw = True

        if scaleY:
            for ax in self.allAxes.values():
                if self.plotWindow.axes2curves[ax]:
                    ymin, ymax = ax.get_ylim()
                    delta = 0.03 * (ymax - ymin)

                    curves = self.plotWindow.axes2curves[ax]
                    indices = [indFinder(curve.get_xdata(), ax_tmin) for curve in curves]

                    newMin = np.min([np.min(curve.get_ydata()[ind:]) for curve, ind in zip(curves, indices)])
                    newMax = np.max([np.max(curve.get_ydata()[ind:]) for curve, ind in zip(curves, indices)])

                    newMin = newMin if newMin < (ymin + delta) else ymin
                    newMax = newMax if newMax > (ymax - delta) else ymax

                    if not (newMin == ymin and newMax == ymax):
                        logy = True if ax.get_yscale() == 'log' else False
                        ymin, ymax = self.calc_lim(newMin, newMax, logy=logy)
                        if np.isfinite(ymin) and np.isfinite(ymax):
                            ax.set_ylim(ymin, ymax)
                            doDraw = True

        return doDraw

    def displayLine(self, doDraw, delay=500):

        if not self.onDrawing:
            self.onDrawing = 'doDraw' if doDraw else 'doArtist'
            delay = delay if doDraw else 100
            timer = QTimer.singleShot(delay, self.doDraw)

        else:
            self.onDrawing = 'doDraw' if doDraw else self.onDrawing

    def doDraw(self):

        if self.onDrawing == 'doDraw':
            self.draw_idle()
        else:
            self.doArtist()

        self.onDrawing = False

    def doArtist(self):
        try:
            for background in self.bck:
                self.fig.canvas.restore_region(background)

            lines = [curve.line for curve in self.curvesOnAxes + self.plotWindow.extraLines]

            for line in lines:
                axes = line.axes
                axes.draw_artist(line)

            self.doBlit()

        except (RuntimeError, AttributeError):
            pass

    def colorStyle(self):
        fontsize = 10 if 2 in self.allAxes.keys() else 12
        for id, ax in self.allAxes.items():
            try:
                primAxess = not id % 2
                curve = self.plotWindow.axes2curves[ax][0]
                ax.set_ylabel(ax.get_ylabel(), color=curve.color, fontsize=fontsize)
                self.setTickLocator(ax)

                for tick in (ax.yaxis.get_major_ticks() + ax.yaxis.get_minor_ticks()):
                    self.pimpTicks(tick, primAxess, curve.color)

                [maj_style, min_style, alpha2] = ['--', '-', 0.15] if primAxess else [':', '-.', 0.1]

                ax.grid(which='major', alpha=0.6, color=curve.color, linestyle=maj_style)
                ax.grid(which='minor', alpha=alpha2, color=curve.color, linestyle=min_style)

                ax.tick_params(axis='y', labelsize=fontsize)

            except IndexError:
                pass

        self.addLegend()

    def addLegend(self):
        if not self.allAxes.items():
            return

        t0, tmax = self.allAxes[0].get_xlim()

        for axesId in self.primaryAxes:
            cvs = []
            for twin in range(2):
                try:
                    ax = self.allAxes[axesId + twin]
                    cvs += self.plotWindow.axes2curves[ax]
                except KeyError:
                    pass

            try:
                self.allAxes[axesId].get_legend().remove()
            except (AttributeError, KeyError):
                pass

            if cvs:
                indices = [indFinder(curve.get_xdata(), tmax) for curve in cvs]
                vals = [(curve.get_xdata()[ind], curve.get_ydata()[ind]) for curve, ind in zip(cvs, indices)]

                coords = [curve.getAxes().transData.transform((x, y)) for curve, (x, y) in zip(cvs, vals)]

                toSort = [(pix_y, curve.line, curve.label) for curve, (pix_x, pix_y) in zip(cvs, coords)]

                toSort.sort(key=lambda row: row[0])

                lns = [line for pix, line, label in reversed(toSort)]
                labs = [line.get_label() for line in lns]

                size = 8.5 - 0.12 * len(lns)

                self.allAxes[axesId].legend(lns, labs, loc='best', prop={'size': size})

    def setTickLocator(self, ax):

        if ax.get_yscale() in ['log']:
            ax.yaxis.set_minor_locator(ticker.LogLocator(subs=[2, 3, 6]))
            ax.yaxis.set_minor_formatter(ticker.FormatStrFormatter('%.1e'))

        else:
            minor_locatory = ticker.AutoMinorLocator(5)
            ax.yaxis.set_minor_locator(minor_locatory)
            ax.get_yaxis().get_major_formatter().set_useOffset(False)

        minor_locatorx = ticker.AutoMinorLocator(5)
        ax.xaxis.set_minor_locator(minor_locatorx)

    def pimpTicks(self, tick, primAxes, color):
        primLabelOn = True if primAxes else False
        tick.label1.set_visible(primLabelOn)
        tick.label2.set_visible(not primLabelOn)

        coloredTick = tick.label1 if primAxes else tick.label2
        coloredTick.set_color(color=color)

    def pimpGrid(self, tick, primAxes, color):
        primLabelOn = True if primAxes else False
        tick.label1.set_visible(primLabelOn)
        tick.label2.set_visible(not primLabelOn)

        coloredTick = tick.label1 if primAxes else tick.label2
        coloredTick.set_color(color=color)

    def getSmartScale(self):

        smartScale = QCheckBox('Enhance Performances')
        smartScale.setChecked(2)
        smartScale.stateChanged.connect(self.draw_idle)
        return smartScale

    def mouseDoubleClickEvent(self, event):
        if not self.allAxes.keys():
            return
        results = []

        pix_point_x = event.x()
        pix_point_y = self.frameSize().height() - event.y()
        inv = self.allAxes[0].transData.inverted()

        [t_point, __] = inv.transform((pix_point_x, pix_point_y))

        for curve in self.curvesOnAxes:
            ax = curve.getAxes()

            t0, tmax = ax.get_xlim()
            ind_min = indFinder(curve.get_xdata(), t0)
            ind_max = indFinder(curve.get_xdata(), tmax)
            resolution = (ind_max - ind_min) / (self.frameSize().width())
            t_ind = indFinder(curve.get_xdata(), t_point)
            imin, imax = int(t_ind - 4 * resolution), int(t_ind + 4 * resolution) + 1
            imin = 0 if imin < 0 else imin
            imax = len(curve.get_xdata()) if imax >= len(curve.get_xdata()) else imax

            data = [ax.transData.transform((curve.get_xdata()[i], curve.get_ydata()[i])) for i in range(imin, imax)]
            delta = [np.sqrt((x - pix_point_x) ** 2 + (y - pix_point_y) ** 2) for x, y in data]

            if not len(delta):
                continue

            results.append((np.argmin(delta) + imin, np.min(delta), curve))

        if not len(results):
            return

        ind_dist, min_dist, curve = results[np.argmin([mini for argmin, mini, curve in results])]
        valx, valy = curve.get_xdata()[ind_dist], curve.get_ydata()[ind_dist]

        labelPoint = QLabel(self)
        labelPoint.setText('%s \r\n %s : %g' % (num2date(valx).isoformat()[:19], curve.label, valy))
        labelPoint.show()

        offset = 0 if (event.x() + labelPoint.width()) < self.frameSize().width() else labelPoint.width()
        labelPoint.move(event.x() - offset, event.y())

        point, = curve.getAxes().plot(valx, valy, 'o', color='k', markersize=4.)

        curve.getAxes().draw_artist(point)
        self.doBlit()

        extraLine = ExtraLine(point, labelPoint)
        self.plotWindow.extraLines.append(extraLine)

        timer = QTimer.singleShot(6000, partial(self.removeExtraLine, extraLine))

    def mouseMoveEvent(self, event):
        FigureCanvas.mouseMoveEvent(self, event)
        self.VCursor.moveLines(x=event.x(),
                               y=self.frameSize().height() - event.y())

    def close(self, *args, **kwargs):
        for widget in [self.toolbar, self.smartScale, self.VCursor]:
            widget.close()
            widget.deleteLater()

        FigureCanvas.close(self, *args, **kwargs)

    def removeExtraLine(self, extraLine, doArtist=True):
        self.plotWindow.extraLines.remove(extraLine)
        if doArtist:
            self.doArtist()

    def hideExtraLines(self):
        for line in [point.line for point in self.plotWindow.extraLines]:
            line.set_visible(False)

    def showExtraLines(self):
        for line in [point.line for point in self.plotWindow.extraLines]:
            line.set_visible(True)

    def doBlit(self):
        self.fig.canvas.blit(self.fig.bbox)

    def userCustom(self):
        for curve in self.curvesOnAxes:
            curve.updateProp()

        self.overrideAxisAndScale()
