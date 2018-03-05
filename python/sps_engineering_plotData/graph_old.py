#!/usr/bin/env python
# encoding: utf-8
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import ticker, rcParams
import numpy as np
from functools import partial
from myfigure import myFigure
from matplotlib.dates import DateFormatter
from matplotlib.dates import num2date
from PyQt5.QtWidgets import QSizePolicy, QLabel
from collections import OrderedDict
from curve import Curve
from PyQt5.QtCore import QTimer
from transform import transformCoord2Log, indFinder
from math import floor, log10

rcParams.update({'figure.autolayout': True})
plt.style.use('ggplot')


class Graph(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, plotWindow, width=4, height=2, dpi=100):
        self.fig = myFigure(self, width, height, dpi)
        FigureCanvas.__init__(self, self.fig)
        # self.setParent(parent.parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.plotWindow = plotWindow
        self.rdy_check = False
        self.onDrawing = False
        self.dictofline = OrderedDict({})
        self.ax = self.fig.add_subplot(212)
        self.ax.xaxis_date()

        self.ax2 = self.fig.add_subplot(211, sharex=self.ax)
        #self.ax2.format_coord = self.make_format(self.ax2, self.ax)

        self.label_cursor = QLabel(self)
        self.label_cursor.setWordWrap(True)
        self.label_cursor.hide()


    def addCurve(self, curveConf, combo):

        ax = self.getAxe(curveConf.type)
        plt.subplots_adjust(hspace = .001)
        new_curve = Curve(self.plotWindow, curveConf, combo)
        line, = ax.plot_date(new_curve.get_xdata(), new_curve.get_ydata(), '-', label=curveConf.label)
        ax.set_yscale(new_curve.yscale, basey=10)
        if ax ==self.ax2:
            self.ax.set_xticklabels(())




        self.dictofline[line] = new_curve
        new_curve.setLine(line)
        self.figure.canvas.draw()

    def delCurve(self, label, tablename):

        if self.button_vcursor.isChecked():
            self.button_vcursor.click()
        for ax in self.fig.get_axes():
            for i, line in enumerate([l for l in ax.get_lines() if l in self.dictofline.keys()]):
                curv = self.dictofline[line]
                if curv.label == label and curv.tablename == tablename:
                    self.dictofline.pop(line, None)
                    ax.lines.pop(i)
                    save_ax1, save_ax2 = self.orderAxe()
                    self.clearGraph()
                    self.rebuild(save_ax1, save_ax2)
                    self.figure.canvas.draw()
                    del line

    def getAxe(self, type):

        if 'pressure' in type:
            if self.ax.get_lines() and not self.ax2.get_lines() and not self.dictofline[
                self.ax.get_lines()[0]].type == type:
                save_ax1, save_ax2 = self.orderAxe()
                self.clearGraph()
                self.rebuild([], save_ax1)

        for i, ax in enumerate(self.fig.get_axes()):
            if ax.get_lines():
                ax_type = self.dictofline[ax.get_lines()[0]].type
                if ax_type == type:
                    return ax
                else:
                    if i == 1:
                        raise ValueError('No Axe available')
            else:
                return ax

    def orderAxe(self):

        ax_curve = [self.dictofline[line] for line in self.ax.get_lines() if self.isinDict(line)]
        ax2_curve = [self.dictofline[line] for line in self.ax2.get_lines() if self.isinDict(line)]
        if not ax_curve:
            ax_curve = ax2_curve
            ax2_curve = []

        return ax_curve, ax2_curve

    def clearGraph(self):
        while self.fig.get_axes():
            ax = self.fig.get_axes()[0]
            lines = ax.get_lines()
            for i in range(len(lines)):
                lines.pop(0).remove()
            ax.cla()
            self.fig.delaxes(ax)
            del ax
        self.ax = self.fig.add_subplot(111)
        self.ax.set_autoscaley_on(True)
        self.ax.xaxis_date()
        self.ax2 = self.ax.twinx()
        self.ax2.format_coord = self.make_format(self.ax2, self.ax)

    def rebuild(self, save_ax1, save_ax2):

        for ax, save_ax in zip(self.fig.get_axes(), [save_ax1, save_ax2]):
            for curve in save_ax:
                old_line = curve.currLine
                line, = ax.plot_date(curve.get_xdata(), curve.get_ydata(), '-', label=curve.label)
                self.dictofline[line] = curve
                self.dictofline.pop(old_line, None)
                self.dictofline[line].setLine(line)
                del old_line

                ax.set_yscale(curve.yscale, basey=10)

    def updateLine(self, line, dates, values, dtime=3300):
        line.set_data(np.append(line.get_xdata(), dates), np.append(line.get_ydata(), values))

        if hasattr(self, "linev"):
            if not self.onDrawing:
                self.onDrawing = True
                timer = QTimer.singleShot(15000, partial(self.updateLimit, bool_draw=True))
        else:
            if not self.onDrawing:
                self.onDrawing = True
                timer = QTimer.singleShot(dtime, self.updateLimit)

    def updateLimit(self, bool_draw=False):
        if not bool_draw:
            self.fig.canvas.restore_region(self.background)

        list_tmax = []
        t0, tmax = self.ax.get_xlim()
        for i, ax in enumerate(self.fig.get_axes()):
            min_values = []
            max_values = []
            for line in ax.lines:
                if self.isinDict(line):
                    curve = self.dictofline[line]
                    min_value, max_value = curve.currExtremum
                    list_tmax.append(curve.get_xdata()[-1])
                    if ax.get_yscale() == "log":
                        min_values.append(10 ** (floor(log10(min_value))))
                        max_values.append(10 ** (floor(log10(max_value)) + 1))
                    else:
                        min_values.append(min_value)
                        max_values.append(max_value)
                if not bool_draw:
                    ax.draw_artist(line)

            if min_values and (not (self.toolbar.isZoomed() or self.toolbar.isPanned())):
                if np.max(max_values) != np.min(min_values):
                    if np.min(min_values) < min(ax.get_ylim()):
                        if ax.get_yscale() == "log":
                            ax.set_ylim(np.min(min_values), max(ax.get_ylim()))
                        else:
                            ax.set_ylim(
                                np.min(min_values) - (np.max(max_values) - np.min(min_values)) * 0.05,
                                max(ax.get_ylim()))
                        bool_draw = True
                    if np.max(max_values) > max(ax.get_ylim()):
                        if ax.get_yscale() == "log":
                            ax.set_ylim(min(ax.get_ylim()), np.max(max_values))
                        else:
                            ax.set_ylim(
                                min(ax.get_ylim()),
                                np.max(max_values) + (np.max(max_values) - np.min(min_values)) * 0.05)
                        bool_draw = True

        if list_tmax:
            if np.max(list_tmax) > tmax and not self.toolbar.isZoomed():
                samp_time = 0.28 * (np.max(list_tmax) - t0)
                self.ax.set_xlim(t0, np.add(np.max(list_tmax), samp_time))
                bool_draw = True

        if bool_draw:
            self.fig.canvas.draw()
        else:
            self.fig.canvas.blit(self.fig.bbox)
        self.onDrawing = False

    def updateStyle(self):
        lns = []
        labs = []
        vmax = []
        # self.ax.set_xlabel('Time')
        for i, ax in enumerate(self.fig.get_axes()):
            if ax.get_lines():
                ax.set_ylabel(self.dictofline[ax.get_lines()[0]].ylabel, color=self.dictofline[ax.get_lines()[0]].color)
                for tick in ax.yaxis.get_major_ticks():
                    if i == 0:
                        tick.label1On = True
                        tick.label2On = False
                        tick.label1.set_color(color=self.dictofline[ax.get_lines()[0]].color)
                        self.ax2.grid(which='major', alpha=0.0)
                        ax.grid(which='major', alpha=0.5, color=self.dictofline[ax.get_lines()[0]].color)
                        ax.grid(which='minor', alpha=0.25, color=self.dictofline[ax.get_lines()[0]].color,
                                linestyle='--')
                    elif i == 1:
                        tick.label1On = False
                        tick.label2On = True
                        tick.label2.set_color(color=self.dictofline[ax.get_lines()[0]].color)
                        ax.grid(which='major', alpha=1.0, color=self.dictofline[ax.get_lines()[0]].color,
                                linestyle='dashdot')
                for line in ax.get_lines():
                    if self.isinDict(line) and line.get_xdata().size:
                        t0, tmax = self.ax.get_xlim()
                        ind = indFinder(line.get_xdata(), tmax)
                        try:
                            new_coord = ax.transData.transform((line.get_xdata()[ind], line.get_ydata()[ind]))
                        except TypeError:
                            new_coord = transformCoord2Log((line.get_xdata()[ind], line.get_ydata()[ind]), self.ax,
                                                           self.ax2, inv=True)

                        vmax.append([new_coord[1], line.get_label(), line])
                        self.setLineStyle(line)

                if ax.get_yscale() in ["log", "symlog"]:
                    subs = [1.0, 2.0, 3.0, 6.0]  # ticks to show per decade
                    ax.yaxis.set_minor_locator(ticker.LogLocator(subs=subs))  # set the ticks position
                else:
                    minor_locatory = ticker.AutoMinorLocator(5)
                    ax.yaxis.set_minor_locator(minor_locatory)
                    ax.get_yaxis().get_major_formatter().set_useOffset(False)

                minor_locatorx = ticker.AutoMinorLocator(5)
                ax.xaxis.set_minor_locator(minor_locatorx)

            else:
                ax.set_ylabel("")
                for tick in ax.yaxis.get_major_ticks():
                    tick.label1On = False
                    tick.label2On = False

        vmax.sort(key=lambda row: row[0])
        for [v, label, line] in reversed(vmax):
            lns.append(line)
            labs.append(label)

        labs = self.checkDuplicate(labs, [self.dictofline[l].tablename.split('__')[0] for l in lns])

        if len(lns) < 7:
            size = 10
        else:
            size = 10 - 0.82 * len(lns) / 7
        self.ax.legend(lns, labs, loc='best', prop={'size': size})

    def setColorLine(self, curveName):
        for ax in self.fig.get_axes():
            for line in ax.get_lines():
                if line.get_label() == curveName:
                    self.setLineStyle(line)
                    self.figure.canvas.draw()

    def setLineStyle(self, line, color=None, marker=2.):
        self.dictofline[line].setLineStyle()
        color = self.dictofline[line].color if color is None else color
        line.set_color(color)
        # line.set_markerfacecolor(color)
        # line.set_markeredgecolor(color)
        # line.set_markersize(marker)

    def checkDuplicate(self, labels, prefix):
        labs = []
        for i, (label, pref) in enumerate(zip(labels, prefix)):
            inter = labels[:i] + labels[i + 1:]
            newLabel = '%s_%s' % (pref, label) if label in inter else label
            labs.append(newLabel)

        return labs

    def setDateFormat(self, format_date):
        self.ax.xaxis.set_major_formatter(DateFormatter(format_date))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=75, horizontalalignment='right')

    def make_format(self, current, other):
        # current and other are axes
        def format_coord(x, y):
            display_coord = current.transData.transform((x, y))
            if not self.button_vcursor.isChecked():
                inv = other.transData.inverted()
                try:
                    ax_coord = inv.transform(display_coord)
                except IndexError:
                    ax_coord = transformCoord2Log(display_coord, other, current)

                if other.get_lines():
                    unit1 = "(%s)" % self.dictofline[other.get_lines()[0]].unit
                else:
                    return ""
                if current.get_lines():
                    unit2 = "(%s)" % self.dictofline[current.get_lines()[0]].unit
                else:
                    return ('{:<}   y1%s = {:<}'.format(
                        *[num2date(x).isoformat()[:19], '{:g}'.format(ax_coord[1])])) % unit1

                return ('{:<}   y1%s = {:<}   y2%s = {:<}'.format(*[num2date(x).isoformat()[:19],
                                                                    '{:g}'.format(ax_coord[1]),
                                                                    '{:g}'.format(y)])) % (unit1, unit2)
            else:
                self.verticalCursor(x, display_coord)
                return ""

        return format_coord

    def verticalCursor(self, time, display_coord):

        i = 0
        res = []
        self.exceptCursor = False
        if hasattr(self, "linev"):
            try:
                self.fig.canvas.restore_region(self.background)
                self.linev.set_xdata((time, time))
                self.ax.draw_artist(self.linev)
                self.fig.canvas.blit(self.fig.bbox)

            except RuntimeError:
                self.exceptCursor = True
        else:
            self.linev = self.ax.axvline(time, visible=True)

        if not self.exceptCursor:
            for ax in self.fig.get_axes():
                for lines in ax.get_lines():
                    if self.isinDict(lines):
                        try:
                            ind = indFinder(lines.get_xdata(), time)
                        except RuntimeError:
                            self.exceptCursor = True
                        except IndexError:
                            ind = len(lines.get_xdata()) - 1
                        if not self.exceptCursor:
                            if i == 0:
                                txt = (num2date(lines.get_xdata()[ind]).isoformat()[:19] + "\r\n")
                                i += 1

                            try:
                                new_coord = ax.transData.transform((lines.get_xdata()[ind], lines.get_ydata()[ind]))
                            except TypeError:
                                new_coord = transformCoord2Log((lines.get_xdata()[ind], lines.get_ydata()[ind]),
                                                               self.ax, self.ax2, inv=True)

                            res.append([lines.get_label(), lines.get_ydata()[ind], new_coord[1]])
            res.sort(key=lambda row: row[2])

            txt += "\r\n".join(["%s : %g " % (val[0], val[1]) for val in reversed(res)])

            if not self.exceptCursor:
                if self.label_cursor.width() + display_coord[0] > self.frameSize().width():
                    self.label_cursor.move(display_coord[0] - self.label_cursor.width(), 200)
                else:
                    self.label_cursor.move(display_coord[0], 200)

                self.label_cursor.setText(txt)
                self.label_cursor.show()

    def mouseDoubleClickEvent(self, event):
        if not self.button_vcursor.isChecked():
            vals = []
            result = []
            inv = self.ax.transData.inverted()
            inv2 = self.ax2.transData.inverted()
            try:
                [time_ax, val_ax] = inv.transform((event.x(), self.frameSize().height() - event.y()))
            except IndexError:
                [time_ax, val_ax] = transformCoord2Log((event.x(), self.frameSize().height() - event.y()), self.ax,
                                                       self.ax2)
            t0, tmax = self.ax.get_xlim()

            for ax in self.fig.get_axes():
                for lines in ax.get_lines():
                    if self.isinDict(lines):
                        try:
                            ind_t0 = indFinder(lines.get_xdata(), t0)
                            ind_tmax = indFinder(lines.get_xdata(), tmax)
                            step = 1 + (ind_tmax - ind_t0) / 400
                            ind = indFinder(lines.get_xdata(), time_ax)

                            for i in range(int(ind - step), int(ind + step)):
                                if 0 <= i < len(lines.get_xdata()):
                                    try:
                                        new_coord = ax.transData.transform((lines.get_xdata()[i], lines.get_ydata()[i]))
                                    except TypeError:
                                        new_coord = transformCoord2Log((lines.get_xdata()[i], lines.get_ydata()[i]),
                                                                       self.ax, self.ax2, inv=True)
                                    if new_coord is not None:
                                        vals.append(np.sqrt((new_coord[0] - event.x()) ** 2 + (
                                            new_coord[1] - (self.frameSize().height() - event.y())) ** 2))
                                        result.append(
                                            [lines.get_xdata()[i], lines.get_ydata()[i], ax, lines.get_label()])
                        except IndexError:
                            pass

            if result:
                label_point = QLabel(self)
                label_point.setWordWrap(True)
                point = result[np.argmin(vals)]

                txt = "%s \r\n %s : %g" % (num2date(point[0]).isoformat()[:19], point[3], point[1])

                if label_point.width() + event.x() > self.frameSize().width():
                    label_point.move(event.x() - label_point.width(), event.y() - 16)
                else:
                    label_point.move(event.x(), event.y() - 16)
                line, = point[2].plot(point[0], point[1], 'o', color='k', markersize=4.)

                self.fig.canvas.restore_region(self.background)
                for ax in self.fig.get_axes():
                    for lines in ax.get_lines():
                        ax.draw_artist(lines)
                self.fig.canvas.blit(self.fig.bbox)
                label_point.setText(txt)
                label_point.show()

                timer = QTimer.singleShot(10000, partial(self.hidePoint, line, label_point, point[2]))

    def removePoint(self):
        for ax in self.fig.get_axes():
            for lines in ax.get_lines():
                if not self.isinDict(lines):
                    lines.remove()

    def hidePoint(self, line, label_point, ax):
        label_point.close()
        if line in ax.get_lines():
            line.remove()
        self.fig.canvas.restore_region(self.background)
        for ax in self.fig.get_axes():
            for lines in ax.get_lines():
                ax.draw_artist(lines)
        self.fig.canvas.blit(self.fig.bbox)

    def isinDict(self, line):
        for key in self.dictofline.keys():
            if key == line:
                return True
        return False