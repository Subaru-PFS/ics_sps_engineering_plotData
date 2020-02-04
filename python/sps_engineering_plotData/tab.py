from functools import partial

from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout
from sps_engineering_plotData.plotwin import PlotWindow


class Tab(QWidget):
    def __init__(self, tabwidget):
        QWidget.__init__(self)
        self.tabwidget = tabwidget
        self.list = []
        self.button_add_graph = QPushButton("Add Graph")
        self.button_add_graph.clicked.connect(partial(self.addPlot))

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_add_graph)
        self.setLayout(self.layout)

        self.plotWindow = self.addPlot()

    @property
    def mainwindow(self):
        return self.tabwidget.mainwindow

    def addPlot(self):
        widget = PlotWindow(self)
        self.layout.addWidget(widget)
        self.button_add_graph.hide()

        return widget

    def removeGraph(self, widget):
        widget.close()
        self.layout.removeWidget(widget)
        self.button_add_graph.show()

    def restart(self):
        for curve in self.plotWindow.curveList:
            if curve.watcher and not curve.watcher.isActive():
                curve.restart()

    def stop(self):
        for curve in self.plotWindow.curveList:
            if curve.watcher and curve.watcher.isActive():
                curve.stop()
