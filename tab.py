from functools import partial

from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout

from plot_window import PlotWindow


class Tab(QWidget):
    def __init__(self, parent):
        super(Tab, self).__init__()
        self.parent = parent
        self.list = []
        self.button_add_graph = QPushButton("Add Graph")
        self.button_add_graph.clicked.connect(partial(self.addGraph))

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_add_graph)
        self.setLayout(self.layout)

    def addGraph(self):
        self.parent.readCfg(self.parent.config_path, last=False)
        widget = PlotWindow(self)
        self.layout.addWidget(widget)
        self.layout.addWidget(self.button_add_graph)
        return widget

    def delGraph(self, widget):
        widget.close()
        self.layout.removeWidget(widget)

    def goActive(self, bool):
        for w in self.getPlotWindow():
            w.goAwake() if bool else w.goSleep()

    def getPlotWindow(self):
        res = [self.layout.itemAt(i).widget() for i in range(self.layout.count())]

        return [w for w in res if w != self.button_add_graph]
