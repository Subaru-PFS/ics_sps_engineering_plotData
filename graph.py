#!/usr/bin/env python
# encoding: utf-8
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import ticker
import numpy as np
from functools import partial
from myfigure import myFigure
from matplotlib.dates import DateFormatter
from matplotlib.dates import num2date
from PyQt5.QtWidgets import QSizePolicy, QLabel
from matplotlib import rcParams
from curve import Curve
from derivate import Derivate
from PyQt5.QtCore import QTimer
from transform import transformCoord2Log, indFinder
from math import floor, log10

rcParams.update({'figure.autolayout': True})
plt.style.use('ggplot')

class Graph(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=4, height=2, dpi=100):
        self.fig = myFigure(self, width, height, dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent.parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.parent = parent
        self.dataset = self.parent.parent.dataset
        self.numDate = self.parent.parent.getNumdate()
        self.rdy_check = False
        self.onDrawing = False
        self.dictofline = {}
        self.ax = self.fig.add_subplot(111)
        self.ax.xaxis_date()
        # self.ax.set_autoscale_on(True)
        self.ax2 = self.ax.twinx()
        self.ax2.format_coord = self.make_format(self.ax2, self.ax)

        self.label_cursor = QLabel(self)
        self.label_cursor.setWordWrap(True)
        self.label_cursor.hide()

    def addordelCurve(self, checkbox, label, type, ylabel, unit, tableName, keyword, combo, spinbox=None,
                      cmb_unit=None):
        if not self.rdy_check:
            if checkbox.isChecked():
                if self.addCurve(label, type, ylabel, unit, tableName, keyword, combo, spinbox, cmb_unit):
                    return 1
                else:
                    self.rdy_check = True
                    checkbox.setCheckState(0)
            else:
                if self.delCurve(label):
                    return 1
                else:
                    checkbox.setCheckState(2)
                    self.rdy_check = True
        else:
            self.rdy_check = False

    def addCurve(self, label, type, ylabel, unit, tableName, keyword, combo, spinbox, cmb_unit):
        ax = self.getAxe(type)
        if ax is not None:
            if not spinbox:
                new_curve = Curve(self.parent, self, label, type, ylabel, unit, tableName, keyword, combo)
            else:
                new_curve = Derivate(self.parent, self, label, type, ylabel, unit, tableName, keyword, combo, spinbox,
                                     cmb_unit)
            if new_curve.last_id > 0:
                line, = ax.plot_date(new_curve.get_xdata(), new_curve.get_ydata(), '-', label=label)
                self.dictofline[line] = new_curve
                new_curve.setLine(line)
                self.figure.canvas.draw()
                return 1
            else:
                return 0
        else:
            return 0

    def delCurve(self, label):
        if self.button_vcursor.isChecked():
            self.button_vcursor.click()
        for ax in self.fig.get_axes():
            for i, line in enumerate(ax.get_lines()):
                if line.get_label() == label:
                    self.dictofline.pop(line, None)
                    ax.lines.pop(i)
                    save_ax1, save_ax2, scale_ax1, scale_ax2 = self.orderAxe()
                    self.clearGraph()
                    self.rebuild(save_ax1, save_ax2, scale_ax1, scale_ax2)
                    self.figure.canvas.draw()
                    del line
                    return 1
        return 0

    def getAxe(self, type):
        if 'pressure' in type and type[-2:] != "dt":
            if self.button_vcursor.isChecked():
                self.button_vcursor.click()
            if self.ax.get_lines():
                if self.dictofline[self.ax.get_lines()[0]].type != type:
                    if not self.ax2.get_lines():
                        for lines in self.ax.get_lines():
                            self.ax2.add_line(lines)
                            self.ax.lines.pop(0)
                        save_ax1, save_ax2 = self.ax.get_lines(), self.ax2.get_lines()
                        self.clearGraph()
                        self.rebuild(save_ax1, save_ax2)
                        self.ax.set_yscale('log', basey=10)
                    else:
                        return None
            self.ax.set_yscale('log', basey=10)
            return self.ax

        for i, ax in enumerate(self.fig.get_axes()):
            if ax.get_lines():
                ax_type = self.dictofline[ax.get_lines()[0]].type
                if ax_type == type:
                    return ax
                else:
                    if i == 1:
                        return None
                    else:
                        pass
            else:
                return ax

    def orderAxe(self):
        if not self.ax.get_lines():
            for l in self.ax2.get_lines():
                self.ax.add_line(l)
                self.ax2.lines.pop(0)
            self.ax.set_yscale("linear")
        return self.ax.get_lines(), self.ax2.get_lines(), self.ax.get_yscale(), self.ax2.get_yscale()

    def clearGraph(self):
        while self.fig.get_axes():
            ax = self.fig.get_axes()[0]
            ax.cla()
            self.fig.delaxes(ax)
            del ax
        self.ax = self.fig.add_subplot(111)
        self.ax.set_autoscaley_on(True)
        self.ax.xaxis_date()
        self.ax2 = self.ax.twinx()
        self.ax2.format_coord = self.make_format(self.ax2, self.ax)

    def rebuild(self, save_ax1, save_ax2, scale_ax1="linear", scale_ax2="linear"):

        for ax, save_ax, scale_ax in zip(self.fig.get_axes(), [save_ax1, save_ax2], [scale_ax1, scale_ax2]):
            for lines in save_ax:
                if self.isinDict(lines):
                    line, = ax.plot_date(self.dictofline[lines].get_xdata(), self.dictofline[lines].get_ydata(), '-',
                                         label=self.dictofline[lines].label)
                    self.dictofline[line] = self.dictofline[lines]
                    self.dictofline[line].setLine(line)
                    self.dictofline.pop(lines, None)
                    del lines

            ax.set_yscale(scale_ax)

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
                    min_value, max_value, max_time = curve.currMin, curve.currMax, curve.get_xdata()[-1]
                    list_tmax.append(max_time)
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
        self.ax.set_xlabel('Time')
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
                for lines in ax.get_lines():
                    if self.isinDict(lines):
                        t0, tmax = self.ax.get_xlim()
                        ind = indFinder(lines.get_xdata(), tmax)
                        try:
                            new_coord = ax.transData.transform((lines.get_xdata()[ind], lines.get_ydata()[ind]))
                        except TypeError:
                            new_coord = transformCoord2Log((lines.get_xdata()[ind], lines.get_ydata()[ind]), self.ax,
                                                           self.ax2, inv=True)

                        vmax.append([new_coord[1], lines.get_label(), lines])
                        self.setLineStyle(lines)

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
        for [v, labels, lines] in reversed(vmax):
            lns.append(lines)
            labs.append(labels)

        if len(lns) < 7:
            size = 10
        else:
            size = 10 - 0.82 * len(lns) / 7
        self.ax.legend(lns, labs, loc=0, prop={'size': size})

    def setColorLine(self, curveName):
        for ax in self.fig.get_axes():
            for lines in ax.get_lines():
                if lines.get_label() == curveName:
                    self.setLineStyle(lines)
                    self.figure.canvas.draw()

    def setLineStyle(self, line, marker=2.):
        self.dictofline[line].setLineStyle()
        color = self.dictofline[line].color
        line.set_color(color)
        # line.set_markerfacecolor(color)
        # line.set_markeredgecolor(color)
        # line.set_markersize(marker)

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
                    if unit1 == "(Torr)":
                        return ('{:<}   y1%s = {:<}'.format(
                            *[num2date(x).strftime("%a %d/%m  %H:%M:%S"), '{:.3e}'.format(ax_coord[1])])) % unit1
                    else:
                        return ('{:<}   y1%s = {:<}'.format(
                            *[num2date(x).strftime("%a %d/%m  %H:%M:%S"), '{:.2f}'.format(ax_coord[1])])) % unit1
                if unit1 == "(Torr)":
                    return ('{:<}   y1%s = {:<}   y2%s = {:<}'.format(
                        *[num2date(x).strftime("%a %d/%m  %H:%M:%S"), '{:.3e}'.format(ax_coord[1]),
                          '{:.2f}'.format(y)])) % (unit1, unit2)
                else:
                    return ('{:<}   y1%s = {:<}   y2%s = {:<}'.format(
                        *[num2date(x).strftime("%a %d/%m  %H:%M:%S"), '{:.3e}'.format(ax_coord[1]),
                          '{:.2f}'.format(y)])) % (unit1, unit2)
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
                                txt = (num2date(lines.get_xdata()[ind]).strftime("%d/%m/%Y %H:%M:%S") + "\r\n")
                                i += 1

                            if "pressure" in self.dictofline[lines].type and self.dictofline[lines].type[
                                                                             -2:] != "dt":
                                format = "%s : %0.3e \r\n"
                            else:
                                format = "%s : %0.2f \r\n"
                            try:
                                new_coord = ax.transData.transform((lines.get_xdata()[ind], lines.get_ydata()[ind]))
                            except TypeError:
                                new_coord = transformCoord2Log((lines.get_xdata()[ind], lines.get_ydata()[ind]),
                                                               self.ax, self.ax2, inv=True)

                            res.append([format, lines.get_label(), lines.get_ydata()[ind], new_coord[1]])
            res.sort(key=lambda row: row[3])
            txt += "".join(val[0] % (val[1], val[2]) for val in reversed(res))

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
                        ind_t0 = indFinder(lines.get_xdata(), t0)
                        ind_tmax = indFinder(lines.get_xdata(), tmax)
                        step = 1 + (ind_tmax - ind_t0) / 400
                        ind = indFinder(lines.get_xdata(), time_ax)

                        for i in range(ind - step, ind + step):
                            if i >= 0 and i < len(lines.get_xdata()):
                                try:
                                    new_coord = ax.transData.transform((lines.get_xdata()[i], lines.get_ydata()[i]))
                                except TypeError:
                                    new_coord = transformCoord2Log((lines.get_xdata()[i], lines.get_ydata()[i]),
                                                                   self.ax, self.ax2, inv=True)
                                if new_coord is not None:
                                    vals.append(np.sqrt((new_coord[0] - event.x()) ** 2 + (
                                        new_coord[1] - (self.frameSize().height() - event.y())) ** 2))
                                    result.append([lines.get_xdata()[i], lines.get_ydata()[i], ax, lines.get_label()])

            if result:
                label_point = QLabel(self)
                label_point.setWordWrap(True)
                point = result[np.argmin(vals)]
                txt = "%s \r\n" % point[3]
                if point[2].get_yscale() == "log":
                    txt += "%s \r\n % 0.3e" % (num2date(point[0]).strftime("%d/%m/%Y %H:%M:%S"), point[1])
                else:
                    txt += "%s \r\n % 0.2f" % (num2date(point[0]).strftime("%d/%m/%Y %H:%M:%S"), point[1])

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
        for key in self.dictofline.iterkeys():
            if key == line:
                return True
        return False
