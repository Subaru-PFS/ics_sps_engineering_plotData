__author__ = 'alefur'
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QComboBox, QCheckBox

colorList = ['#1f78c5', '#ff801e', '#2ca13c', '#d82738', '#9568cf', '#8d565b', '#e578c3', '#17bfd1',
             '#f2f410', '#808080', '#000000', '#acc5f5', '#fcb986', '#96dc98', '#fc96a4', '#c3aee2',
             '#c29aa2', '#f4b4cf', '#9cd7e2', '#caca76', '#c5c5c5']


class PIcon(QIcon):
    def __init__(self, path):
        pix = QPixmap()
        pix.load(path)
        QIcon.__init__(self, pix)


class ComboColor(QComboBox):
    def __init__(self, index):
        QComboBox.__init__(self)
        for i, colors in enumerate(colorList):
            label = QIcon()
            color = QColor()
            color.setNamedColor(colors)
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            label.addPixmap(pixmap)
            self.addItem("")
            self.setItemIcon(i, label)

        self.setFixedWidth(45)
        self.setCurrentIndex(index % len(colorList))

    @property
    def color(self):
        return colorList[self.currentIndex()]


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
