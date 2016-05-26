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
        self.layout.addWidget(PlotWindow(self))
        self.layout.addWidget(self.button_add_graph)

    def delGraph(self, widget):
        widget.close()
        self.layout.removeWidget(widget)
