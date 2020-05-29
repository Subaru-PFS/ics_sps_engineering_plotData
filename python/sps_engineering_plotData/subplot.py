from functools import partial

from PyQt5.QtWidgets import QComboBox, QVBoxLayout, QHBoxLayout, \
    QPushButton, QGroupBox, QCheckBox, QGridLayout, QLabel


class CurveRow():
    def __init__(self, customize, curve):
        self.customize = customize
        self.curve = curve
        self.comboAxe = False

        self.buttonDelete = self.buttonDelete()
        self.label = QLabel(curve.label)

    @property
    def widgetList(self):
        return [self.comboAxe, self.label, self.curve.comboColor, self.buttonDelete]

    def addWidgets(self, layout, ind):
        if self.comboAxe:
            layout.removeWidget(self.comboAxe)
            self.comboAxe.deleteLater()

        self.comboAxe = self.getComboAxes()

        for j, widget in enumerate(self.widgetList):
            layout.addWidget(widget, ind, j)

    def buttonDelete(self):
        button = QPushButton('')
        button.setIcon(self.customize.plotWindow.mainwindow.icon_delete)
        button.clicked.connect(partial(self.customize.removeRow, self))
        return button

    def updateCombo(self, layout, ind):
        old_combo = self.widgetList[0]
        layout.removeWidget(old_combo)
        old_combo.removeLater()

        combo = self.getComboAxes()
        layout.addWidget(combo, ind, 0)
        self.widgetList[0] = combo

    def getComboAxes(self):

        axesId = self.customize.plotWindow.axes2id[self.curve.getAxes()]

        combo = QComboBox()
        availables = [Customize.id2axStr[id] for id in self.customize.axesAvailables] + ['none']
        combo.addItems(availables)

        combo.setCurrentText(Customize.id2axStr[axesId])
        combo.currentIndexChanged.connect(partial(self.customize.switchSubplot, self))
        self.comboAxe = combo

        return combo


class Customize(QGroupBox):
    tup = [(0, 'ax1'), (1, 'ax2'), (2, 'ax3'), (3, 'ax4'), (None, 'none')]
    id2axStr = dict(tup)
    axStr2id = dict([(val, key) for key, val in tup])

    def __init__(self, plotWindow):
        self.plotWindow = plotWindow
        QGroupBox.__init__(self, 'Figure')
        layout = QVBoxLayout()
        self.sublayout = QGridLayout()
        self.curvelayout = QGridLayout()
        self.customAxes = []

        self.rowList = []
        self.allAxes = {}

        for id, axStr in Customize.id2axStr.items():
            if id is not None:
                self.constructAxe(id, axStr)

        self.checkAvailable()
        layout.addLayout(self.sublayout)
        layout.addLayout(self.curvelayout)

        self.setLayout(layout)

    def constructAxe(self, id, name):
        self.allAxes[id] = Subplot(self, id, name)
        self.sublayout.addLayout(self.allAxes[id], id // 2, id % 2)

    def appendRow(self, curve):

        self.rowList.append(CurveRow(self, curve))
        self.cleanRows()

    def removeRow(self, row):
        for widget in row.widgetList:
            self.curvelayout.removeWidget(widget)
            widget.deleteLater()

        try:
            self.rowList.remove(row)
        except ValueError:
            pass

        self.cleanRows()
        self.plotWindow.removeCurve(row.curve)

    def cleanRows(self):
        for ind, row in enumerate(self.rowList):
            row.addWidgets(self.curvelayout, ind)

    def switchSubplot(self, curveRow):
        axesId = Customize.axStr2id[curveRow.comboAxe.currentText()]
        self.plotWindow.switchCurve(axesId, curveRow.curve)

    def checkAvailable(self):
        self.allAxes[1].checkbox.setEnabled(self.allAxes[0].checkbox.isChecked())
        self.allAxes[3].checkbox.setEnabled(self.allAxes[2].checkbox.isChecked())

        self.allAxes[2].checkbox.setEnabled(
            self.allAxes[0].checkbox.isChecked() and not self.allAxes[3].checkbox.isChecked())

        self.allAxes[0].checkbox.setEnabled(not (self.allAxes[1].checkbox.isChecked() or
                                                 self.allAxes[2].checkbox.isChecked()))

        self.cleanRows()

    @property
    def axesAvailables(self):
        return [i for i in range(4) if self.allAxes[i].checkbox.isChecked()]

    def deleteLater(self):
        while len(self.rowList):
            self.removeRow(self.rowList[0])
        QGroupBox.deleteLater(self)


class Subplot(QHBoxLayout):
    def __init__(self, customize, id, name):
        QHBoxLayout.__init__(self)

        self.customize = customize
        self.checkbox = QCheckBox(name)
        self.eraseUserPreferences()
        self.id = id
        self.ignore = False
        self.checkbox.setCheckState(0)
        self.checkbox.stateChanged.connect(self.handleChecking)

        self.comscale = QComboBox()
        self.comscale.addItems(['linear', 'log'])
        self.comscale.currentIndexChanged.connect(self.updateScale)

        self.addWidget(self.checkbox)
        self.addWidget(self.comscale)

    @property
    def customAxes(self):
        return self.customize.customAxes

    @property
    def axe(self):
        return self.customize.plotWindow.allAxes[self.id]

    @property
    def typedCurve(self):
        return [curve for curve in self.customize.plotWindow.axes2curves[self.axe] if curve.type != 'none']

    @property
    def typedAxe(self):
        return len(set([curve.type for curve in self.typedCurve])) == 1

    @property
    def autoLabel(self):
        return self.typedCurve[0].ylabel if self.typedAxe else f'YAXIS_{self.id + 1} (..)'

    @property
    def autoScale(self):
        return self.typedCurve[0].yscale if self.typedAxe else self.comscale.currentText()

    @property
    def yscale(self):
        return self.userScale if self.userScale is not None else self.autoScale

    @property
    def ylabel(self):
        return self.userLabel if self.userLabel is not None else self.autoLabel

    @property
    def graph(self):
        return self.customize.plotWindow.graph

    def eraseUserPreferences(self):
        self.userScale = None
        self.userLabel = None

    def handleChecking(self):
        if self.checkbox.isChecked():
            self.customAxes.append(self)
        else:
            self.customAxes.remove(self)

        self.eraseUserPreferences()
        self.customize.plotWindow.createGraph(self.customAxes)
        self.customize.checkAvailable()

    def updateScale(self):
        self.userScale = str(self.comscale.currentText())
        try:
            self.graph.updateScale(self.axe, self.yscale)
        except Exception as e:
            print(e)

    def setAxisAndScale(self):
        self.comscale.blockSignals(True)
        self.axe.set_ylabel(self.ylabel)
        self.axe.set_yscale(self.yscale, basey=10)
        self.comscale.setCurrentText(self.yscale)
        self.comscale.blockSignals(False)

    def overrideAxisAndScale(self, ylabel=None, yscale=None):
        ylabel = self.axe.get_ylabel() if ylabel is None else ylabel
        yscale = self.axe.get_yscale() if yscale is None else yscale

        self.userLabel = ylabel if ylabel != self.autoLabel else self.userLabel

        self.axe.set_ylabel(ylabel)
        self.comscale.setCurrentText(yscale)
