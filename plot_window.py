import operator
from functools import partial

from PyQt5.QtGui import QPixmap, QColor, QIcon
from PyQt5.QtWidgets import QGridLayout, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, \
    QCheckBox, QScrollArea, QComboBox, QDoubleSpinBox, QTabWidget

from graph import Graph
from mynavigationtoolbar import myNavigationToolbar
from myqcheckbox import myQCheckBox


class PlotWindow(QWidget):
    def __init__(self, parent):
        super(PlotWindow, self).__init__()
        self.parent = parent

        self.layout = QHBoxLayout()
        graph_layout = QVBoxLayout()
        toolbar_layout = QHBoxLayout()
        gbox_layout = QVBoxLayout()

        self.graph = Graph(self.parent)
        self.graph.toolbar = myNavigationToolbar(self.graph, self.parent)
        self.button_arrow = self.getButtonArrow()
        self.graph.button_vcursor = self.getVerticalCursor()
        self.graph.smartScale = self.getSmartScale()
        self.button_del_graph = self.getButtonDelete()
        self.getColors()
        self.getGroupbox()
        graph_layout.addWidget(self.graph)
        toolbar_layout.addWidget(self.graph.toolbar)
        toolbar_layout.addWidget(self.graph.smartScale)
        toolbar_layout.addWidget(self.graph.button_vcursor)
        graph_layout.addLayout(toolbar_layout)

        self.layout.addLayout(graph_layout)
        self.layout.addWidget(self.button_arrow)
        gbox_layout.addWidget(self.scrollArea)
        gbox_layout.addWidget(self.button_del_graph)
        self.layout.addLayout(gbox_layout)
        self.setLayout(self.layout)

    def getGroupbox(self):
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMaximumWidth(325)
        tabWidget = QTabWidget()

        for actorname, dict in self.sortActor(self.parent.parent.device_dict):
            t = TabActor(self, dict)
            tabWidget.addTab(t, actorname)

        self.scrollArea.setWidget(tabWidget)

    def getColors(self):

        self.color_tab = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
                          (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                          (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                          (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                          (188, 189, 34), (224, 198, 17), (23, 190, 207), (158, 218, 229)]

        for i, colors in enumerate(self.color_tab):
            r, g, b = colors
            self.color_tab[i] = (r / 255., g / 255., b / 255.)
        self.graph.color_tab = self.color_tab

    def getButtonArrow(self):

        button_arrow = QPushButton()
        button_arrow.setIcon(self.parent.parent.icon_arrow_right)
        button_arrow.clicked.connect(partial(self.showhideConfig, button_arrow))
        button_arrow.setStyleSheet("border: 0px")

        return button_arrow

    def showhideConfig(self, button_arrow):

        if not self.scrollArea.isHidden():
            self.scrollArea.hide()
            button_arrow.setIcon(self.parent.parent.icon_arrow_left)
        else:
            self.scrollArea.show()
            button_arrow.setIcon(self.parent.parent.icon_arrow_right)

    def getVerticalCursor(self):

        button_vcursor = QPushButton()
        button_vcursor.setIcon(self.parent.parent.icon_vcursor)
        button_vcursor.setCheckable(True)
        button_vcursor.clicked.connect(partial(self.cursorOn, button_vcursor))
        button_vcursor.setStyleSheet("border: 0px")
        return button_vcursor

    def getSmartScale(self):
        smartScale = QCheckBox("Optimize Performances")
        smartScale.setChecked(2)
        smartScale.stateChanged.connect(self.graph.fig.canvas.draw)
        return smartScale

    def getButtonDelete(self):
        button = QPushButton("Delete Graph")
        button.clicked.connect(partial(self.clearLayout, self.layout, True))
        return button

    def cursorOn(self, button_vcursor):
        if button_vcursor.isChecked():
            if self.graph.ax.get_lines():
                self.graph.fig.canvas.draw()
                button_vcursor.setIcon(self.parent.parent.icon_vcursor_on)
            else:
                button_vcursor.setChecked(False)

        else:
            button_vcursor.setIcon(self.parent.parent.icon_vcursor)
            if hasattr(self.graph, "linev"):
                self.graph.label_cursor.hide()
                self.graph.linev.remove()
                delattr(self.graph, "linev")
                self.graph.fig.canvas.draw()

    def goAwake(self):
        for line, curve in self.graph.dictofline.iteritems():
            if not curve.watcher.isActive():
                curve.getData(getStarted=False, dtime=0.5)
                curve.watcher.start()

    def goSleep(self):
        for line, curve in self.graph.dictofline.iteritems():
            curve.watcher.stop()

    def clearLayout(self, layout, firstTimer=False):
        if firstTimer:
            for curve in self.graph.dictofline.itervalues():
                curve.watcher.stop()
            del (self.graph.dictofline)
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

        self.parent.delGraph(self)

    def sortActor(self, dic):
        res = {}
        for key, val in dic.iteritems():
            actor = key.split('__')[0]
            if 'xcu' in actor or 'ccd' in actor:
                tkey = 'xcu_%s' % (key.split('_')[1])
            else:
                tkey = 'ait'

            tkey = tkey.upper()
            if tkey not in res.iterkeys():
                res[tkey] = {}

            res[tkey][key] = val
        return res.iteritems()


class TabActor(QWidget):
    def __init__(self, plotWindow, device_dict):
        QWidget.__init__(self)
        self.clayout = QVBoxLayout()
        self.plotWindow = plotWindow
        self.device_dict = device_dict
        self.getGroupbox()

    @property
    def graph(self):
        return self.plotWindow.graph

    @property
    def color_tab(self):
        return self.plotWindow.color_tab

    def getGroupbox(self):
        index = 0
        sorted_dict = sorted(self.device_dict.items(), key=operator.itemgetter(0))
        for (device, dict) in sorted_dict:
            groupBox = QGroupBox(dict["label_device"])
            groupBox.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")
            groupBox.setFlat(True)
            grid = QGridLayout()
            groupBox.setLayout(grid)
            sorted_curves = sorted(dict.items(), key=operator.itemgetter(1))
            for i, (keys, curves) in enumerate(sorted_curves):
                if keys != "label_device":
                    curveName = "%s_%s" % (dict["label_device"], curves["label"])
                    combo = self.getComboColor(index, curveName=curveName)

                    checkbox = myQCheckBox(curves["label"], curveName, self)
                    checkbox.stateChanged.connect(partial(self.graph.addordelCurve, checkbox,
                                                          label="%s_%s" % (dict["label_device"], curves["label"]),
                                                          type=curves["type"], ylabel=curves["ylabel"],
                                                          unit=curves["unit"],
                                                          tableName=device,
                                                          keyword=keys,
                                                          combo=combo))
                    grid.addWidget(checkbox, i, 1)
                    grid.addWidget(combo, i, 0)
                    index += 1
                    curveName = "%s_d%s_dt" % (dict["label_device"], curves["label"])
                    combo_deriv = self.getComboColor(index, curveName=curveName)
                    checkbox_deriv = myQCheckBox("d%s_dt" % curves["label"], curveName, self)
                    integ_time = self.getSpinBox()
                    combo_unit = self.getComboUnit(curves["unit"])
                    checkbox_deriv.stateChanged.connect(partial(self.graph.addordelCurve, checkbox_deriv,
                                                                label="%s_d%s_dt" % (dict["label_device"],
                                                                                     curves["label"]),
                                                                type="d%s_dt" % curves["type"],
                                                                ylabel="d%s_dt (%s)" % (curves["type"].capitalize(),
                                                                                        str(combo_deriv.currentText())),
                                                                unit=curves["unit"],
                                                                tableName=device,
                                                                keyword=keys,
                                                                combo=combo_deriv,
                                                                spinbox=integ_time,
                                                                cmb_unit=combo_unit))

                    setattr(checkbox, "ident", device + "%s_%s" % (dict["label_device"], curves["label"]))
                    setattr(checkbox_deriv, "ident", device + "%s_d%s_dt" % (dict["label_device"], curves["label"]))

                    grid.addWidget(combo_deriv, i + len(sorted_curves), 0)
                    grid.addWidget(checkbox_deriv, i + len(sorted_curves), 1)
                    grid.addWidget(combo_unit, i + len(sorted_curves), 2)
                    grid.addWidget(integ_time, i + len(sorted_curves), 3)
            self.clayout.addWidget(groupBox)

        #
        # self.groupbox_layout.addWidget(self.button_del_graph)
        self.setLayout(self.clayout)

    def getComboColor(self, index, curveName):
        combo_color = QComboBox()
        for i, colors in enumerate(self.color_tab):
            r, g, b = colors
            label = QIcon()
            color = QColor()
            color.setRgbF(r, g, b, 1.0)
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            label.addPixmap(pixmap)
            combo_color.addItem("")
            combo_color.setItemIcon(i, label)
            combo_color.setFixedWidth(45)
        combo_color.setCurrentIndex(index % len(self.color_tab))
        combo_color.currentIndexChanged.connect(partial(self.graph.setColorLine, curveName))

        return combo_color

    def getSpinBox(self):
        integ_time = QDoubleSpinBox()
        integ_time.setRange(15, 86400)
        integ_time.setValue(600)
        integ_time.setFixedWidth(80)
        return integ_time

    def getComboUnit(self, unit):
        combo = QComboBox()
        combo.addItems(["%s/%s" % (unit, t) for t in ["min", "hour"]])
        return combo
