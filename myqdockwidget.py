#!/usr/bin/env python
# encoding: utf-8

from PyQt5.QtWidgets import QDockWidget

class myQDockWidget(QDockWidget):
    def __init__(self):
        super(myQDockWidget, self).__init__()

    def closeEvent(self, event):
        self.hide()
        event.accept()





