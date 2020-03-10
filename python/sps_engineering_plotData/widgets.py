__author__ = 'alefur'

from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QComboBox, QCheckBox, QPushButton, QLabel
from matplotlib.dates import num2date
from sps_engineering_plotData.transform import indFinder

colorList = ['#1e71ab', '#f3790d', '#2a982a', '#cc2526', '#8d62b4', '#855247', '#d871b9', '#797979', '#b3b420',
             '#16b5c5', '#000000', '#a9c1e1', '#f8b675', '#94d986', '#f89492', '#bfabcf', '#be9790', '#f0b1cc',
             '#c1c1c1', '#d5d589', '#99d4de']


class PIcon(QIcon):
    def __init__(self, path):
        pix = QPixmap()
        pix.load(path)
        QIcon.__init__(self, pix)


class ComboColor(QComboBox):
    def __init__(self, index):
        QComboBox.__init__(self)

        for color in colorList:
            self.addColor(color)

        self.setFixedWidth(45)
        self.setCurrentIndex(index % len(colorList))

    @property
    def color(self):
        return colorList[self.currentIndex()]

    def addColor(self, color):

        self.addItem('')
        self.setItemIcon(self.count() - 1, PQColor(color))

    def newColor(self, color):
        color = color[:7]
        if color not in colorList:
            colorList.append(color)
            self.addColor(color)

        for i, col in enumerate(colorList):
            if col == color:
                break

        self.setCurrentIndex(i)


class PQColor(QIcon):
    def __init__(self, color):
        QIcon.__init__(self)
        qcolor = QColor()
        qcolor.setNamedColor(color)
        pixmap = QPixmap(20, 20)
        pixmap.fill(qcolor)
        self.addPixmap(pixmap)


class PQCheckBox(QCheckBox):
    def __init__(self, tabActor, curveConf):
        self.tabActor = tabActor
        self.curveConf = curveConf
        self.doNone = False
        QCheckBox.__init__(self, curveConf.label, tabActor)
        self.stateChanged.connect(self.handleChecking)

    def handleChecking(self):

        if not self.doNone:
            if self.isChecked():
                try:
                    curve = self.tabActor.plotWindow.addCurve(self.curveConf)
                    curve.checkbox = self
                    self.setEnabled(False)
                except Exception as e:
                    self.doNone = True
                    self.setCheckState(0)
                    self.tabActor.mainwindow.showError(str(e))

            else:
                self.setEnabled(True)
        else:
            self.doNone = False


class ExtraLine(object):
    def __init__(self, line, label):
        object.__init__(self)
        label.setWordWrap(True)
        self.line = line
        self.label = label

    def __del__(self):

        self.remove()

    def remove(self):
        try:
            ax = self.line.axes
            ax.lines.remove(self.line)
            del self.line
            self.label.hide()
            self.label.close()
            self.label.deleteLater()
        except ValueError:
            pass


class VCursor(QPushButton):
    offsetY = {0: 0.01, 2: 0.05}

    def __init__(self, graph):
        QPushButton.__init__(self)
        self.graph = graph
        self.setIcon(self.plotWindow.mainwindow.icon_vcursor)
        self.setCheckable(True)
        self.clicked.connect(self.cursorOn)
        self.setStyleSheet("border: 0px")
        self.vLines = {}

    @property
    def plotWindow(self):
        return self.graph.plotWindow

    @property
    def fig(self):
        return self.graph.fig

    def cursorOn(self):
        if self.isChecked():
            if not self.graph.allAxes.keys():
                self.setChecked(0)
                return

            tmin, tmax = self.graph.allAxes[0].get_xlim()

            for axesId in self.graph.primaryAxes:
                axes = self.graph.allAxes[axesId]
                vLine = axes.axvline((tmin + tmax) / 2, visible=True)
                label = QLabel(self.graph)
                self.vLines[axesId] = ExtraLine(vLine, label)

            self.plotWindow.extraLines += [vLine for vLine in self.vLines.values()]
            self.graph.doArtist()

            self.setIcon(self.plotWindow.mainwindow.icon_vcursor_on)
        else:
            for axesId, vLine in list(self.vLines.items()):
                self.graph.removeExtraLine(vLine, doArtist=False)
                self.vLines.pop(axesId, None)

            self.graph.doArtist()

            self.setIcon(self.plotWindow.mainwindow.icon_vcursor)

    def moveLines(self, x, y):
        if not self.graph.allAxes.keys() or not self.isChecked():
            return

        frameSize = self.graph.frameSize()
        axes2curves = self.plotWindow.axes2curves

        inv = self.graph.allAxes[0].transData.inverted()
        [tpoint, __] = inv.transform((x, y))

        fact = {idAxes: float((2 * i + 1) / (2 * (len(self.vLines)))) for i, idAxes in
                enumerate(list(self.vLines.keys()))}

        for idAxes, vLine in self.vLines.items():
            cvs = axes2curves[self.graph.allAxes[idAxes]]
            try:
                cvs += axes2curves[self.graph.allAxes[idAxes + 1]]
            except KeyError:
                pass

            vLine.line.set_xdata((tpoint, tpoint))
            yOffset = self.buildText(vLine, tpoint, cvs)
            xOffset = 0 if (x + vLine.label.width()) < frameSize.width() else vLine.label.width()

            vLine.label.move(x - xOffset, (fact[idAxes] - VCursor.offsetY[idAxes]) * frameSize.height() - yOffset)

        self.graph.doArtist()

    def buildText(self, vLine, tpoint, curves):

        txt = (num2date(tpoint).isoformat()[:19] + "\r\n")
        toSort = []

        for curve in curves:
            ind = indFinder(curve.get_xdata(), tpoint)
            x, y = curve.get_xdata()[ind], curve.get_ydata()[ind]
            pix_x, pix_y = curve.getAxes().transData.transform((x, y))
            toSort.append((pix_y, y, curve.label))

        toSort.sort(key=lambda row: row[0])
        txt += "\r\n".join(["%s : %g " % (label, valy) for pix, valy, label in reversed(toSort)])

        vLine.label.setText(txt)
        vLine.label.show()

        return (vLine.label.height()) / 2

    def doArtist(self):
        try:
            for background in self.graph.bck:
                self.fig.canvas.restore_region(background)

            lines = [curve.line for curve in self.plotWindow.extraLines]

            for line in lines:
                axes = line.axes
                axes.draw_artist(line)

            self.graph.doBlit()

        except (RuntimeError, AttributeError):
            pass

        self.graph.displayLine(doDraw=True, delay=15000)
