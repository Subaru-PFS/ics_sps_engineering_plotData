#!/usr/bin/env python
# encoding: utf-8

from PyQt5.QtWidgets import QCheckBox


class myQCheckBox(QCheckBox):
    def __init__(self, name, curveName, plotArea):
        QCheckBox.__init__(self, name, plotArea)
        self.curveName = curveName
