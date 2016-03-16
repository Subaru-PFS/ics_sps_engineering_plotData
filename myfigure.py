#!/usr/bin/env python
# encoding: utf-8
from matplotlib.figure import Figure


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
        self.setDateFormat()
        self.parent.updateStyle()
        Figure.draw(self, event)
        self.parent.background = self.canvas.copy_from_bbox(self.parent.ax.bbox)


    def setDateFormat(self):
        t0, tmax = self.parent.ax.get_xlim()
        if tmax - t0 > 7:
            format_date = "%d/%m/%Y"
        elif tmax - t0 > 1:
            format_date = "%a %H:%M"
        else:
            format_date = "%H:%M:%S"

        self.parent.setDateFormat(format_date)

